# Chess Agent Evaluation: Trajectory Analysis

This document analyzes the behavior and failure modes of three different model configurations when running the ReAct chess agent harness. The analysis is based on the trajectory logs generated during the experiment.

## 1. The Default Agent (`make run-chess-agent`)
This run actually used the **exact same model** as the DeepSeek experiment (`deepseek/deepseek-v4-flash-0731`). 
- **Outcome:** Successfully completed the game.
- **Why it succeeded:** Since it used the same model as `run-obs-deepseek-legal`, its success compared to the experiment's failure comes down to non-determinism and transient infrastructure issues. In this specific run, the model managed to complete the game faster or through a different sequence of moves without the backend Modal chess server crashing or disconnecting. It didn't trigger the fatal `[Errno 54] Connection reset by peer` error that doomed the other run.

## 2. GPT-OSS (`run-obs-gpt-oss-legal` & `run-obs-gpt-oss-no-legal`)
This experiment used the `gpt-oss-120b` open-source model.
- **Outcome:** Failed at **Move 1** and entered an infinite error loop.
- **Why it failed:** The model fundamentally failed to use the structured OpenAI `tool_calls` API. Instead of populating the `tool_calls` array, it hallucinated its underlying raw text token template directly into the text `content` field.
  - *Example from trajectory:* `to=functions.play_move<|channel|>commentary <|constrain|>json<|message|>{"move": "e2e4"}<|call|>`
- **Result:** The ReAct loop looked for a populated `tool_calls` list, found it missing/empty, and replied with the fallback prompt: *"You did not provide a tool call."* The model stubbornly responded with the exact same raw tokens repeatedly, instantly falling into an infinite loop until the step limit was exhausted.

## 3. DeepSeek (`run-obs-deepseek-legal` & `run-obs-deepseek-no-legal`)
Unlike `gpt-oss`, DeepSeek *was* capable of tool calling and successfully played a remarkably deep game of chess in both runs.
- **Legal moves run:** Made it all the way to **Move 28** (`recent_history: 21:Ba4+ 22:Kd8 23:Bg5+ 24:Ne7 25:Rc1 26:e5 27:Nxe5 28:Qf5`).
- **No legal moves run:** Made it to **Move 22**.
- **Outcome:** Both runs ultimately crashed with a `StepLimitError` after exhausting the maximum budget of 200 steps.
- **Why they failed:**
  - **In `deepseek-legal`:** The backend chess server hosted on Modal crashed or disconnected midway through the game. The tool began returning `<chess_error>Chess server transport error: Server disconnected without sending a response.</chess_error>`. DeepSeek correctly reasoned that it should retry the move, but ended up retrying it over 150 times, completely exhausting the 200-step limit.
  - **In `deepseek-no-legal`:** The model struggled slightly with formatting. While it mostly used proper `tool_calls`, it occasionally hallucinated raw XML into the content field (e.g., `<play_move><move>e2e4</move></play_move>`). The harness rejected these XML tags, forcing DeepSeek to retry. Between formatting retries and making invalid moves (since `legal_moves` were hidden), the model burned through the 200-step budget before finishing the game.

## Summary Conclusion
- **Default Agent:** Demonstrated perfect tool call formatting, avoiding loops and finishing the game quickly.
- **GPT-OSS:** Formatting was completely broken, leading to instant infinite loops on Move 1 due to tool-calling token leakage.
- **DeepSeek:** Formatting was mostly correct, allowing it to play a deep game. However, it failed due to a combination of backend server timeouts/crashes and occasional XML hallucinations that ultimately exhausted the 200-step ReAct limit.
