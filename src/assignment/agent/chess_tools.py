"""Chess tool implementations, decoupled from the agent that registers them.

Every function here takes the HTTP client explicitly instead of reading it off
an agent, so the same code can run in the agent process or inside the sandbox
beside the server it talks to.
"""

from __future__ import annotations

import base64
import json
from typing import Any

import httpx

CHESS_PORT = 8000


def _request_state(
    client: httpx.Client, method: str, endpoint: str, **kwargs: Any
) -> dict[str, Any]:
    """Make one chess API request and validate its JSON response."""

    response = client.request(method, endpoint, **kwargs)
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(
            f"Chess server returned non-JSON ({response.status_code})."
        ) from exc
    if response.status_code >= 400:
        detail = (
            payload.get("detail", payload) if isinstance(payload, dict) else payload
        )
        raise ValueError(str(detail))
    if not isinstance(payload, dict):
        raise RuntimeError("Chess server response must be a JSON object.")
    return payload


def _simulate_move(client: httpx.Client, arguments: str) -> str:
    """New tool: inspect FEN or simulate one ply without changing the game.

    Takes the raw JSON arguments of one tool call and returns the observation
    to send back, so a bad argument or a server error reaches the model as a
    recoverable ``<chess_error>`` instead of ending the run.
    """
    try:
        try:
            parsed = json.loads(arguments)
        except ValueError as exc:
            return f"<chess_error>Invalid JSON in arguments: {exc}</chess_error>"

        if not isinstance(parsed, dict):
            return "<chess_error>Arguments must be a JSON object.</chess_error>"

        fen = parsed.get("fen")
        if not isinstance(fen, str):
            return "<chess_error>Missing or invalid fen argument.</chess_error>"

        body = {"fen": fen}
        move = parsed.get("move")
        if move is not None:
            if not isinstance(move, str):
                return "<chess_error>Invalid move argument: must be a string if provided.</chess_error>"
            body["move"] = move

        resp = _request_state(client, "POST", "/api/simulate", json=body)
        return json.dumps(resp)

    except ValueError as exc:
        return f"<chess_error>{str(exc)}</chess_error>"
    except httpx.RequestError as exc:
        return f"<chess_error>Chess server transport error: {exc}</chess_error>"
    except RuntimeError as exc:
        return f"<chess_error>Runtime error in simulate_move: {exc}</chess_error>"


def _play_move(client: httpx.Client, arguments: str) -> str:
    """Existing tool: play one move as White and return the resulting state.

    Takes the raw JSON arguments of one tool call. Returns the new state, or a
    `<chess_error>` observation if the move could not be played.
    """
    # TODO(3.1.b): Parse the arguments and POST {"move": <uci move>} to
    # /api/move. Return its JSON object. Catch any errors raised by the
    # tool and return an error message between `<chess_error></chess_error>`
    # for the agent to address. Cover malformed JSON arguments, arguments
    # that are not an object, a missing or non-string fen, a non-string move,
    # a position or move the server rejects, and a transport failure.
    try:
        try:
            parsed = json.loads(arguments)
        except ValueError as exc:
            return f"<chess_error>Invalid JSON in arguments: {exc}</chess_error>"

        if not isinstance(parsed, dict):
            return "<chess_error>Arguments must be a JSON object.</chess_error>"
        move = parsed.get("move")
        if not isinstance(move, str):
            return "<chess_error>Missing or invalid move argument.</chess_error>"

        # Get FEN from current state
        state_resp = _request_state(client, "GET", "/api/state")
        fen = state_resp.get("fen")
        if not isinstance(fen, str):
            return "<chess_error>Could not retrieve current game state or FEN.</chess_error>"

        # Call the server's play endpoint
        body = {"move": move}
        resp = _request_state(client, "POST", "/api/move", json=body)

        return json.dumps(resp)

    except ValueError as exc:
        # Server-side validation error
        return f"<chess_error>{str(exc)}</chess_error>"
    except httpx.RequestError as exc:
        # Transport failure
        return f"<chess_error>Chess server transport error: {exc}</chess_error>"
    except RuntimeError as exc:
        # Catch unexpected runtime errors
        return f"<chess_error>Runtime error in play_move: {exc}</chess_error>"


def _run_python(env: Any, port: int, arguments: str) -> str:
    """New tool: run Python with access to the existing registered tools."""
    try:
        try:
            parsed = json.loads(arguments)
        except ValueError as exc:
            return f"<chess_error>Invalid JSON in arguments: {exc}</chess_error>"

        if not isinstance(parsed, dict):
            return "<chess_error>Arguments must be a JSON object.</chess_error>"

        code = parsed.get("code")
        if not isinstance(code, str):
            return "<chess_error>Missing or invalid code argument.</chess_error>"

        encoded = base64.b64encode(code.encode("utf-8")).decode("utf-8")
        
        result = env.execute(f"python /opt/assignment/sandbox_python.py {port} {encoded}")
        
        if result["returncode"] != 0:
            error_msg = result.get("exception_info") or result.get("stderr") or "Unknown error"
            return f"<chess_error>{error_msg}</chess_error>"

        return result["stdout"]
    except Exception as exc:
        return f"<chess_error>Runtime error in run_python: {exc}</chess_error>"


def _invoke_skill(skills: dict[str, dict[str, str]], arguments: str) -> str:
    """Existing tool: load one skill's instructions into the conversation."""
    try:
        try:
            parsed = json.loads(arguments)
        except ValueError as exc:
            return f"<chess_error>Invalid JSON in arguments: {exc}</chess_error>"
        
        if not isinstance(parsed, dict):
            return "<chess_error>Arguments must be a JSON object.</chess_error>"
        
        skill_name = parsed.get("skill_name")
        if not isinstance(skill_name, str):
            return "<chess_error>Missing or invalid skill_name argument.</chess_error>"
            
        if skill_name not in skills:
            return f"<chess_error>Skill '{skill_name}' not found.</chess_error>"
            
        return skills[skill_name]["content"]
    except Exception as exc:
        return f"<chess_error>Runtime error in invoke_skill: {exc}</chess_error>"


def _game_state(client: httpx.Client, reset: bool = False) -> dict:
    """Read the live game, or start a new one and read the opening position."""

    method, endpoint = ("POST", "/api/reset") if reset else ("GET", "/api/state")
    return _request_state(client, method, endpoint)
