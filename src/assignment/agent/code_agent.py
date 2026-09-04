"""The Part 1 coding agent: fix a software issue and submit a git patch."""

from __future__ import annotations

import json
from typing import Any

from assignment.agent.base import (
    DEFAULT_COMPACTION_KEEP_RECENT_STEPS,
    DEFAULT_COMPACTION_MAX_TOKENS,
    Agent,
    format_tool_output,
)
from assignment.agent.tools import EXECUTE_TOOL, SEND_MESSAGE_TOOL
from assignment.env import Environment

class CodeAgent(Agent):
    """An agent that fixes a software issue and submits a git patch."""

    def __init__(
        self,
        task: str,
        environment: Environment,
        model: str | None = None,
        logs_save_path: str | None = None,
        step_limit: int = 100,
        skills_path: str | None = None,
        auto_stop_environment: bool = True,
        compact_threshold_tokens: int | None = None,
        compaction_keep_recent_steps: int = DEFAULT_COMPACTION_KEEP_RECENT_STEPS,
        compaction_max_tokens: int = DEFAULT_COMPACTION_MAX_TOKENS,
    ):
        super().__init__(
            environment=environment,
            model=model,
            logs_save_path=logs_save_path,
            step_limit=step_limit,
            skills_path=skills_path,
            auto_stop_environment=auto_stop_environment,
            compact_threshold_tokens=compact_threshold_tokens,
            compaction_keep_recent_steps=compaction_keep_recent_steps,
            compaction_max_tokens=compaction_max_tokens,
        )
        self.task = task
        self.submitted_patch = ""

        # TODO(Part 1.3): Make the `execute` and `send_message` tools available
        # to the agent.
        self.tools.extend([EXECUTE_TOOL, SEND_MESSAGE_TOOL])

        # TODO(1.1.b): Construct the system prompt and task_prompt. These
        # should be usable by the `Agent.build_prompt` method.
        # TODO(1.4): If any skills are available to the agent, make their
        # descriptions/metadata available to the agent in the prompt.

        self.system_prompt = (
            "You are a coding agent. Inspect the repository, reproduce the issue, "
            "make the required fix, and verify it with tests.\n\n"
            "<system_information>\n"
            f"{{\n"
            f'  "machine": "{environment.machine}",\n'
            f'  "release": "{environment.release}",\n'
            f'  "system": "{environment.system}",\n'
            f'  "version": "{environment.version}"\n'
            "}\n"
            "</system_information>"
        )
        if self.skills:
            catalog = "\n".join(skill["metadata"] for skill in self.skills.values())
            self.system_prompt += (
                "\n\nAvailable skills:\n"
                f"{catalog}\n"
                "Invoke a skill before following its workflow."
            )

        self.task_prompt = self.task

    def execute_tool_calls(
        self, tool_calls: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Execute ``execute`` and ``send_message`` calls in the code sandbox."""

        # TODO(Part 1.3): Parse each call, execute recognized tools, and return
        # one message per call (there may be multiple tool calls in one agent
        # response!). Malformed JSON and unknown tools must become recoverable
        # observations relayed to the agent instead of exceptions.

        tool_responses: list[dict[str, str]] = []

        for call in tool_calls:
            call_id = call.get("id", "")
            function_info = call.get("function", {})
            func_name = function_info.get("name", "")
            raw_args = function_info.get("arguments", "{}")

            # 1. Safely parse JSON arguments
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            except json.JSONDecodeError as exc:
                tool_responses.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": f"Error: Malformed JSON arguments: {exc}",
                })
                continue

            # 2. Dispatch tool calls to execution targets
            try:
                if func_name == "execute":
                    command = args.get("command", "")
                    output = self.env.execute(command)
                    content = format_tool_output(output) if isinstance(output, dict) else str(output)

                elif func_name == "send_message":
                    message = args.get("summary", "")
                    patch_check = self.env.execute("test -s patch.txt")
                    if patch_check.get("returncode") != 0:
                        content = (
                            "Error: patch.txt is missing or empty. Invoke the "
                            "submit-task skill, create and verify patch.txt, then "
                            "call send_message again."
                        )
                    else:
                        self.finished = True
                        content = message

                elif func_name == "invoke_skill":
                    skill_name = args.get("name", "")
                    if skill_name in self.skills:
                        content = self.skills[skill_name]["content"]
                    else:
                        content = f"Error: Unknown skill '{skill_name}'."

                else:
                    content = f"Error: Unknown tool '{func_name}'."

            except Exception as exc:
                content = f"Error during tool execution: {type(exc).__name__}: {exc}"

            # 3. Construct tool observation message
            tool_responses.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": content,
            })

        return tool_responses
        
        
