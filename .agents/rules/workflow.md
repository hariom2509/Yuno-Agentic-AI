---
activation: always_on
---

# Mandatory Yuno Development Workflow

For every user prompt in this repository, follow this workflow.

## Graphify — Mandatory

Graphify must be used for every request that involves understanding, inspecting, modifying, debugging, or reviewing the codebase.

Before making any code-related decision:

1. Use the current Graphify knowledge graph to understand the repository.
2. Identify the relevant files, components, dependencies, callers, and relationships.
3. Use Graphify together with the actual source code. Do not rely only on assumptions or isolated file searches.
4. Treat Graphify as the primary tool for understanding repository-level architecture and relationships.

Do NOT require the user to manually run `/graphify .` for each request when the existing Graphify graph is available.

## Code Changes

When the user asks for a code change:

1. Use the current Graphify graph first.
2. Identify the affected components and files.
3. Inspect the actual source code.
4. Apply Ponytail (mandatory for code changes) to ensure the simplest, most minimal solution without over-engineering.
5. Make the smallest appropriate change.
6. Do not modify unrelated files.
7. Run appropriate tests or validation.
8. After the code changes are complete, regenerate Graphify from the current repository state (`graphify update .`).
9. Verify that the regenerated Graphify output reflects the updated codebase.

## Graphify Synchronization

After ANY successful code modification, Graphify must be regenerated so that the knowledge graph represents the latest repository state.

The workflow must be:

Graphify
→ identify affected code
→ inspect source
→ Ponytail
→ implement changes
→ validate/test
→ Graphify update (`graphify update .`)
→ use updated graph for subsequent requests

Never intentionally leave the Graphify graph stale after completing a code-changing task.

If Graphify regeneration fails:

- Do not claim that it succeeded.
- Report the failure clearly.
- Continue only when safe to do so.

## Read-Only Requests

For questions that do not modify the repository:

- Use the existing Graphify graph when the question concerns architecture, dependencies, relationships, execution flow, or codebase structure.
- Do not regenerate Graphify when no code changes occurred.
- Ponytail is not required for read-only / explanation prompts unless the user explicitly requests an over-engineering review or simplification audit.

## Ponytail — Mandatory for Code Changes

For EVERY prompt that results in a code modification, Ponytail must be used as part of the implementation workflow.

Ponytail must be applied after Graphify has identified and contextualized the affected code and before the implementation is finalized.

Mandatory flow:

Graphify
→ identify affected code
→ inspect source
→ Ponytail
→ implement changes
→ validate/test
→ Graphify update

Do not skip Ponytail for a code-changing request unless Ponytail is technically unavailable or its execution fails.

If Ponytail cannot be executed:
- Do not silently pretend it was used.
- Continue only if the code change can safely proceed.
- Clearly report that Ponytail was unavailable or failed.

Do not invent Ponytail commands or capabilities. Use only the Ponytail skills/workflows actually installed and available to the agent.

## Final Validation

After every code-changing task, verify:

- The requested change was implemented.
- Ponytail was applied to minimize bloat and over-engineering.
- Relevant tests/validation were performed.
- No unrelated files were changed.
- Graphify was regenerated successfully (`graphify update .`).

In the final response, briefly state what changed, what Ponytail decisions were made, what validation was performed, and whether Graphify was successfully regenerated.
