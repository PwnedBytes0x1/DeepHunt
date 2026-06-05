# Token Optimization — Module Index

Strategies for AI agents to consume fewer tokens while maintaining high effectiveness.

| File | Focus | Key Techniques |
|------|-------|---------------|
| agent-token-budget.md | Budget allocation, context math | Allocation framework, dynamic loading, monitoring |
| prompt-compression.md | Shrink prompts 50-90% | Filler removal, abbreviations, ML compression |
| efficient-recon.md | Recon with minimum calls | Filter-first, batch tools, structured summaries |
| output-format-optimization.md | Dense output formats | JSON schema, compact notation, structured findings |
| tool-use-patterns.md | Efficient tool calling | Batching, caching, progressive disclosure |
| context-management.md | Sliding windows, memory | Hierarchical memory, scratchpad, summarization |

## Token Savings Quick Reference

```
Technique                    Typical Savings
─────────────────────────────────────────────
Remove prompt filler          20-40%
Batch tool calls              75% fewer calls
Filter recon before LLM       90-96%
Structured vs prose output    60-87%
Sliding window context        Prevents overflow
Session caching               100% on repeated reads
Progressive disclosure        90% on large files
Hierarchical summarization    80% reduction
```

## When to Apply

- **agent-token-budget.md** — At agent design time, setting up context limits
- **prompt-compression.md** — When building system prompts or task descriptions
- **efficient-recon.md** — During reconnaissance phase
- **output-format-optimization.md** — When designing tool return formats
- **tool-use-patterns.md** — When chaining multiple tool calls
- **context-management.md** — When conversation/task runs long (>20k tokens)
