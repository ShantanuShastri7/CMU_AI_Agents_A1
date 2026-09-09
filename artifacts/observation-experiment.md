# Observation Experiment

This experiment evaluates the effect of providing legal moves in the agent's observation space versus requiring the agent to infer legal moves solely from the board state and FEN.

## Metrics

| Model Setup | Total `play_move` Calls | Illegal Move Calls | Invalid-Move Rate | `game_over` Reached |
| ----------- | ----------------------- | ------------------ | ----------------- | ------------------- |
| DeepSeek (Legal Moves) | 30 | 6 | 20.0% | True |
| DeepSeek (No Legal Moves) | 17* | 0 | 0.0% | False |
| GPT-OSS (Legal Moves) | 60 | 2 | 3.3% | True |
| GPT-OSS (No Legal Moves) | 74** | 10 | 13.5% | True |

* *The `deepseek-no-legal` run terminated early after 17 moves due to a `ServerDisconnectedError` in the sandbox environment.*
* **The `gpt-oss-no-legal` run experienced transport errors and retry loops towards the end, resulting in 74 calls.*

## Comparison & Analysis

1. **Observation Sensitivity**: The results demonstrate that models are surprisingly sensitive to how their environment is represented. While removing `legal_moves` caused GPT-OSS to dramatically increase its invalid-move rate (from 3.3% to 13.5%), DeepSeek showed a surprisingly perfect valid-move rate when `legal_moves` were omitted (0.0% invalid rate), whereas it struggled with formatting errors and invalid choices (20.0% invalid rate) when explicitly provided the list of legal moves.
2. **Failure Modes**: The presence of `<chess_error>` in the DeepSeek (Legal Moves) trajectory reveals that explicit legal move lists can sometimes induce lazy formatting (e.g., passing "Bc4" instead of "c1c4"). In contrast, GPT-OSS struggled primarily when it was forced to hallucinate legal moves from scratch without hints, leading to a much higher invalid rate of 13.5%.
2. **Behavioral Differences (Reasoning and Context size)**: The `gpt-oss` model without legal moves engaged in extensive Chain-of-Thought (CoT) reasoning to validate candidate moves before calling the tool. For example, it would manually trace out diagonals to verify that its king would not step into check. While this led to valid moves, it significantly bloated the context window—eventually reaching ~50,000 prompt tokens per turn and causing the trajectory file to balloon to over 7MB.
3. **Strategic Outcome**: Three out of four runs successfully reached `game_over: true` within the step limit, and one crashed due to environment timeouts. While removing explicit lists of legal moves increased reasoning overhead and context bloat (sometimes slowing down the run significantly), the models were mostly able to successfully navigate to a conclusive end-game state regardless of the observation space provided. Providing legal moves directly in the prompt is more token-efficient and reduces the need for the model to "think aloud" to validate basic rules, freeing up context and compute for deeper strategic planning.
