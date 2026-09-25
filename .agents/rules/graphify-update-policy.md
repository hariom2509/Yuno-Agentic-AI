## graphify-update-policy

Every prompt follows this decision tree:

```
Every prompt
    |
Use existing graphify-out/graph.json to answer / plan
    |
Does this prompt change code files?
    |-- NO  --> Answer using current graph. Stop.
    +-- YES --> Ponytail (minimal solution) --> Edit code --> Test
                   |
              Run: graphify update .
                   |
              Answer using the freshly updated graph.
```

### Rules

- **Always consult the graph first** before reading raw files or grepping.
  Run `graphify query "<question>"` (CLI) or use `query_graph` (MCP) for any
  architecture, flow, or relationship question.

- **Never regenerate on read-only prompts.**
  Explanation requests, "how does X work", trace requests -- use the graph as-is.

- **Always run Ponytail before code modifications.**
  For any code-changing prompt, apply Ponytail to find the simplest, most minimal
  implementation and avoid speculative bloat.

- **Always regenerate after code changes.**
  After any file edit that modifies logic (not just docs/comments), run:
  ```powershell
  graphify update .
  ```
  This is incremental (AST-only, no API cost, fast). Do it before answering
  any follow-up questions that depend on the new code.

- **Use `--update`, not a full rebuild**, unless the user explicitly asks for
  a full rebuild with `/graphify .`.

### Examples

| Prompt | Action |
|--------|--------|
| "Explain how HITL execution works." | `graphify query` -> answer. No rebuild. |
| "Add retry handling to HITL execution." | Graphify -> Ponytail -> edit code -> test -> `graphify update .` -> confirm. |
| "Now explain the updated HITL flow." | `graphify query` on the freshly updated graph. |
| "What calls CapabilityRegistry?" | `graphify path` or `graphify query`. No rebuild. |
| "Refactor agent_service.py." | Graphify -> Ponytail -> edit -> test -> `graphify update .` -> done. |
