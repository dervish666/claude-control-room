---
name: skill-refiner
description: "Reviews the current session and proposes updates to existing skills based on corrections, new techniques, or workflow changes found during the work. Use at the end of a session where a skill needed correcting, the workflow was corrected, or a reusable technique emerged, and on 'refine skills', 'update skills', 'improve skills', 'skill review', or 'what did we learn'."
---

# Skill refiner

Skills only get better if lessons flow back into them. Review this session and update the skills that should carry what was learned.

## Signals to look for

1. **User corrections**: "no, not like that", "stop doing X", feedback on tone, format or length.
2. **Workflow corrections**: the user changed the order of steps or the method.
3. **New techniques**: a workaround, a debugging path, a tool pattern that worked.
4. **Outdated skills**: a skill that was loaded and turned out wrong, incomplete or stale.
5. **Confirmed choices**: the user approved a non-obvious approach ("yes, exactly that").

## Where a lesson goes

Take the first that fits:

1. **A skill used this session.** Patch it directly.
2. **An existing skill that covers the territory.** Update it.
3. **A reference file** under that skill's `references/` folder, for detail too long for the main file.
4. **A new skill**, only when no existing skill covers the class of work. Name it for the class, never for this session's task.

## What to capture

- Preferences on style, format and workflow, written into the skill body so the next session starts knowing them.
- Pitfalls, as explicit steps or warnings at the point where they bite.
- Techniques, in the section where they apply.
- Changed APIs or tool behaviour, fixed where the old instruction sits.

## What not to capture

- Environment failures (a missing binary, a package not installed). They are transient.
- Negative tool claims ("X doesn't work"). They harden into false refusals.
- One-off narratives. One request is not a class of work.
- Errors that went away on retry.

## Process

1. List the skills used or relevant this session.
2. Find the signals in the conversation.
3. Decide which skill carries each lesson.
4. Read the current skill file.
5. Propose the edit as old versus new text.
6. Apply after the user confirms, or directly if they said to auto-update.
7. Re-read the edited section, and check the frontmatter still opens and closes with `---`. Tools that build skill catalogues parse `name` and `description` from it.

## Output

For each proposed update:

```
## Skill: <name>
Signal: <what triggered it>
Change: <what to add or modify>
Location: <file and section>
```
