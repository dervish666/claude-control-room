# 11 Engineering principles

These sit in CLAUDE.md as one-line rules, so they change behaviour on every session instead of being rediscovered each week. A lesson earns a place only after it has bitten more than once. Here is the evidence behind each, with the project details stripped.

## Subagents find; the main thread verifies

In my audits, subagents' top findings ran 40 to 60% false positives. They cast a wide net well and judge severity badly. The worst kind is "X is missing": a 37-agent setup audit reported a sync job as dead; it was running fine. Treat every finding as a lead and re-read the cited file:line before acting.

And scale is not coverage. Automated review finds what is wrong in the code. A person prodding the running thing finds what is missing from the behaviour. Both are needed.

## Two agents that share tooling are one observer

Two Claude sessions agreeing is weak evidence when they share the same vault, helper scripts and network: they make the same mistakes. Get independence by changing the method (a different model, such as the `codex-auditor` agent), the source, or the measurement.

## Check ground truth before trusting the abstraction

The costliest bugs I hit this year all looked correct in isolation. Confirm a theory against real rows, real responses and real logs before writing the fix.

## The running thing tells the truth

Only a real render or run confirms UI and device behaviour. When the harness cannot render the target (a phone viewport, a headset, hardware on a desk), say so and hand verification to a person. The journal's `## Not verified` heading exists for this.

## No silent catch

An empty `catch` is an outage waiting for a date. And a zero from a source that may not be speaking is not a measurement. My search index once watched nothing after a library upgrade, and every query still "worked". Distinguish "I looked and it was not there" from "I looked and I cannot see", and show the second as a distinct value (`unavailable`, not `-`).

The `falsify-first` skill turns this into a procedure: before believing a green result, break the input and demand red.

## Verify before sharing

Fetch the actual page. Search snippets have produced dead links and prices that did not exist.

## Absence of evidence is not "stalled"

A project that has gone quiet in the vault may have moved somewhere unlogged. Check before declaring it stuck.

## Curate living docs

They rot by accretion. One project's CLAUDE.md reached 62 KB before a restructure cut it to 15 KB with nothing lost. Past about 25 KB or a month since the last pass, restructure.

## Skills and templates are defaults, not laws

When a repo's convention contradicts a skill's built-in assumption, the local source of truth wins, and the session says why. The same goes for this repo: adapt it.

## Right-size the dependency fix

Read the advisory for applicability first. "Fix available" is not "fix applicable", and `npm audit fix --force` is often worse than the vulnerability. Verify any pin with a full build and the tests.

## Watch the cost of what you retain

Anything large in context is re-sent on every later turn. In one stretch, 27 browser screenshots cost 670k tokens across four sessions, against 14k for all 103 clicks and waits around them. Put big payloads behind a subagent and take back the verdict, not the evidence.
