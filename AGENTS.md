# AGENTS — Distillatron

## SPEC.md is the source of truth

`SPEC.md` contains every key design decision for this project. Treat it as the single source of truth.

### Before any task

1. **Read SPEC.md.** Understand the mission, architecture, tech stack, conventions, and constraints before writing code.

### During any task

2. **Follow the conventions** in SPEC.md. Do not invent new patterns that contradict what is already established.

3. **When you make a non-trivial design decision**, update SPEC.md:
   - Add the decision to the **Decision Log** table with date, what was decided, rationale, and trade-offs.
   - If the decision changes the architecture, update the **Architecture** section.
   - If the decision introduces a new constraint, update the **Constraints** section.
   - If the decision answers an open question, move it from **Open Questions** to the **Decision Log**.

4. **When you discover ambiguity** that needs a decision, add it to **Open Questions**.

### After any task

5. **Verify SPEC.md is current.** If the code disagrees with the spec, update whichever is wrong.

## General rules

- Prefer small, focused commits with clear messages.
- Write tests for new behavior. Run existing tests before pushing.
- Keep PRs small — one logical change per PR.
- Do not commit secrets, credentials, or generated files.
- Follow YAGNI principles
