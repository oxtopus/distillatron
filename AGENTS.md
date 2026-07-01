# AGENTS — Distillatron

## SPEC.md is the source of truth

`SPEC.md` contains every key design decision for this project. Treat it as the single source of truth.

### Before any task

1. **Read SPEC.md.** Understand the mission, architecture, tech stack, conventions, and constraints before writing code.

### During any task

2. **Follow the conventions** in SPEC.md. Do not invent new patterns that contradict what is already established.

3. **When you make a non-trivial design decision**, update SPEC.md first:
   - Add the decision to the **Decision Log** table with date, what was decided, rationale, and trade-offs.
   - If the decision changes the architecture, update the **Architecture** section.
   - If the decision introduces a new constraint, update the **Constraints** section.
   - If the decision answers an open question, move it from **Open Questions** to the **Decision Log**.

   **A design decision includes, but is not limited to:**
   - Adding, removing, or replacing a dependency
   - Creating a new source module, package, or file
   - Changing the architecture diagram (how components connect or data flows)
   - Adding or removing a route, endpoint, or UI screen
   - Changing a technology choice (e.g. swapping libraries, frameworks, or patterns)
   - Changing a data model, schema, or storage format
   - Splitting or merging modules, packages, or responsibilities

   **When in doubt, treat it as a design decision.** The cost of an unnecessary spec update is low. The cost of spec drift is high.

4. **Before writing any new file**, check:
   - Is it listed in SPEC.md under Source modules? If not, update the spec first.
   - Does it depend on a library not in the Tech Stack? If so, update the spec first.
   - Does it introduce a new endpoint, screen, or data path? If so, update the Architecture or relevant section first.

5. **When you discover ambiguity** that needs a decision, add it to **Open Questions**.

6. **Do not implement spec changes until the user approves them.** Update the spec, present the changes, and wait for explicit approval before writing implementation code.

### After any task

7. **Verify SPEC.md is current.** Compare every section against the code:
   - Architecture diagram matches actual component wiring
   - Tech Stack lists every dependency in `pyproject.toml`
   - Source modules lists every file in `src/`
   - UI screens listed match what exists in `ui/screens/` and `web/templates/`
   - Decision Log has an entry for every non-bugfix change made
   - If anything disagrees, update the spec.

## General rules

- Prefer small, focused commits with clear messages.
- Write tests for new behavior. Run existing tests before pushing.
- Keep PRs small — one logical change per PR.
- Do not commit secrets, credentials, or generated files.
- Follow YAGNI principles
