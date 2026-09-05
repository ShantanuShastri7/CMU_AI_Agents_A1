# Token Usage Analysis: Compaction vs. Baseline

This report compares the token usage and performance of the SWE-bench agent running the `django__django-15368` task under two conditions:
1. **With Compaction** (`artifacts/django__django-15368-trajectory.json`)
2. **Baseline (No Compaction)** (`artifacts/django__django-15368-baseline-trajectory.json`)

## Summary of Results

| Metric | With Compaction | Baseline (No Compaction) |
| :--- | :--- | :--- |
| **Total Steps** | 59 | 18 |
| **Total Prompt Tokens** | 285,201 | 149,535 |
| **Total Completion Tokens** | 18,413 | 3,534 |
| **Grand Total Tokens** | **303,614** | **153,069** |
| **Number of Compactions** | 10 | 0 |
| **Tokens spent on Compaction** | 51,418 | 0 |

## Breakdown & Analysis

### 1. Baseline Run (No Compaction)
- **Efficiency**: The baseline run successfully solved the task in just **18 steps**, generating a correct patch for `django/db/models/query.py`.
- **Token Growth**: Without compaction, the prompt size grew steadily with each step as the session history accumulated. By step 18, the total prompt tokens reached ~149k.

### 2. Run With Compaction (Pre-fix)
- **Token Inflation**: The run with compaction used nearly **double** the total tokens (~303k) and took **59 steps**. 
- **The Hallucination Loop**: This high token usage and step count was caused by the meta-prompt hallucination loop discussed earlier. During the third compaction, the LLM became confused by the nested JSON history and started generating repetitive garbage (e.g., `## I've been.`). 
- **Compaction Overhead**: The agent performed 10 compactions, spending ~51k tokens just on the summarization calls. Because the summaries generated were hallucinations, the agent was derailed from the main task, causing it to wander for 59 steps and execute failing bash commands.

## Conclusion

The baseline run demonstrates how efficiently the agent can solve the `django-15368` task (153k tokens, 18 steps) when it has a clear, uncorrupted context. 

The compaction run analyzed here represents the state *before* our recent fix to the `compact_context` method. Because of the hallucination bug, the compaction logic actually harmed performance, heavily inflating both the token usage and step count. 

Now that `compact_context` has been updated to use a readable chat transcript and explicit anti-hallucination instructions, running the agent with compaction enabled should yield a successful trajectory with a lower total prompt token count than the baseline.
