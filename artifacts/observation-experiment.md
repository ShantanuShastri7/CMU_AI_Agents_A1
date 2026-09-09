# Observation Experiment

This experiment evaluates the effect of providing legal moves in the agent's observation space versus requiring the agent to infer legal moves solely from the board state and FEN.

## Metrics

| Model Setup | Total `play_move` Calls | Illegal Move Calls | Invalid-Move Rate | `game_over` Reached |
| ----------- | ----------------------- | ------------------ | ----------------- | ------------------- |
| DeepSeek (Legal Moves) | 30 | 0 | 0.0% | False |
| DeepSeek (No Legal Moves) | 17* | 0 | 0.0% | False |
| GPT-OSS (Legal Moves) | 60 | 0 | 0.0% | False |
| GPT-OSS (No Legal Moves) | 74** | 0 | 0.0% | False |

* *The `deepseek-no-legal` run terminated early after 17 moves due to a `ServerDisconnectedError` in the sandbox environment.*
* **The `gpt-oss-no-legal` run experienced transport errors and retry loops towards the end, resulting in 74 calls.*

## Comparison & Analysis

1. **Rule Inference**: Both `deepseek-v4-flash` and `gpt-oss-120b` demonstrated an impressive ability to play valid chess moves. Even when the `legal_moves` field was removed from the environment observation, both models maintained a **0.0% invalid-move rate**. This suggests that these advanced models have a strong internal representation of chess mechanics and can accurately infer valid UCI moves from the FEN and board representation without relying on explicit hints.
2. **Behavioral Differences (Reasoning and Context size)**: The `gpt-oss` model without legal moves engaged in extensive Chain-of-Thought (CoT) reasoning to validate candidate moves before calling the tool. For example, it would manually trace out diagonals to verify that its king would not step into check. While this led to valid moves, it significantly bloated the context window—eventually reaching ~50,000 prompt tokens per turn and causing the trajectory file to balloon to over 7MB.
3. **Strategic Outcome**: None of the models reached `game_over: true` within the step limits (or before crashing). While they avoided illegal moves, they struggled to efficiently force a checkmate against the deterministic bot within the allocated time/steps. Providing legal moves directly in the prompt is more token-efficient and reduces the need for the model to "think aloud" to validate basic rules, freeing up context and compute for deeper strategic planning.
