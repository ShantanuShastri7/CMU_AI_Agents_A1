# Observation Experiment: The Effect of the Tool Interface on Agent Behavior

This experiment compares the behavior of two models (`deepseek-v4-flash` and `gpt-oss-120b`) when providing a board-only observation (no legal moves) versus an observation that includes a list of legal moves.

## Results

| Model / Condition | Total `play_move` calls | Illegal Calls Rejected | Invalid-Move Rate | Reached `game_over: true`? |
|-------------------|-------------------------|------------------------|-------------------|----------------------------|
| DeepSeek (no legal moves) | 152 | 138 | ~91% | No (Hit step limit/error) |
| DeepSeek (with legal moves) | 29 | 6 | ~21% | Yes (Game completed) |
| GPT-OSS (no legal moves) | 0 | 0 | 0% | No (Exited early) |
| GPT-OSS (with legal moves) | 0 | 0 | 0% | No (Exited early) |

## Comparison & Analysis

1. **Impact of Legal Moves on Move Legality**: 
   Providing the list of legal moves dramatically improves the accuracy of the agent. The DeepSeek model's invalid-move rate plummeted from a staggering 91% (when forced to infer legal moves from the board/FEN) to just 21% when provided with the explicit list. When blind to legal moves, DeepSeek often guessed incorrectly or used standard algebraic notation (e.g., `Nf3`) instead of the required UCI formatting (`g1f3`), causing continuous tool validation errors.

2. **Impact on Game Completion**: 
   By seeing legal moves, the DeepSeek model successfully played through the game and reached `game_over: true` within 30 steps. Without the legal moves, the agent got stuck in an infinite loop of illegal guesses and network connection errors, eventually hitting the 200-step limit without finishing the game.

3. **Model Capability and API Interfaces**: 
   The GPT-OSS model completely failed to generate JSON tool calls across both conditions. Instead of populating `tool_calls` in the API response, it output internal reasoning but returned `null` for both `content` and `tool_calls`. The ReAct loop was unable to parse any actions from it, causing the agent to exit after a few turns. This highlights that the reliability of a ReAct loop heavily depends on the underlying model's adherence to the function-calling interface, rather than just the quality of the observations provided.
