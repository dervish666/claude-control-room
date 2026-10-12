# 06 Model routing

## The bug this fixes

Subagents inherit the calling session's model unless the call names one. If your main thread runs the most capable model at high effort, so does every grep, every file lookup and every log skim it hands off. Nothing warns you. You find out from the usage meter.

The fix is a rule in CLAUDE.md: **pass `model` on every Agent call**, chosen from a table.

## Tiers

I name tiers rather than models because model names change every few months and the table should not.

| Tier | Use it for | Current model (2026-10-12) | Alias in agent files |
|---|---|---|---|
| small | Lookups, exploration, log triage, templated prose | Haiku 5.5 | `haiku` |
| mid | Web research fan-out, browser and screenshot checks | Sonnet 5.5 | `sonnet` |
| top | Implementation, debugging, review, planning, security, orchestration | Opus 5.5 | `opus` |
| design | Public-facing UI only: landing pages, marketing sites, final polish | Fable 5.1 | `fable` |

Update the right-hand columns when models change. Leave the left two alone.

## The table I use

| Task | Tier | Why |
|---|---|---|
| Doc or library reference lookup | small | Read and summarise, no judgement |
| Codebase exploration, "where is X" | small | Find, don't judge. The caller verifies anyway |
| Log, build and test output triage | small | Pure compression |
| Vault reads, session-log drafts, journal entries | small | Templated prose, not code |
| Web research fan-out | mid | Wide net; synthesis happens above |
| Screenshot or browser verification | mid | The cost is the payload, not the reasoning |
| Implementing a step of an approved plan | top | Judgement needed when the plan meets reality |
| Root-cause debugging | top | Understanding is never where to save |
| Code review and audit | top | Severity judgement is where smaller models fall over |
| Adversarial check of another agent's finding | top | A smaller model confirming a smaller model is one observer |
| Anything security-shaped | top | Convincing wrong answers are the failure mode |
| Architecture planning | top | Cheap plans cost more downstream |
| Orchestration, synthesis of fan-out results | top | The one node whose mistakes multiply |
| Public-facing frontend build or final polish | design | Beat the top tier on design in my side-by-side builds |

Two rules sit beside the table:

- **Never the small tier for anything that writes or edits code.**
- **Escalation goes both ways.** A mid-tier main thread hands review and planning up; a top-tier main thread hands lookups down.

The main thread stays on whatever you picked at session start. The table only governs what it spawns.

## Why "design" is narrow

I started by sending all interface work to the design model. It got padding fixes on internal dashboards, button sizes on admin pages and a feature idea that happened to mention a page. The top model handles those fine. The design model earns its place on screens strangers see, when what to build is already settled. Planning and investigation about a UI are thinking jobs and go to the top tier.

## Measuring it

I ran small-tier and mid-tier agents blind against each other on lookups, exploration and vault writing. The small tier matched the mid tier on all three, which is why they moved down. Run your own trial before trusting my table: pick ten real briefs, run both tiers, and have a top-tier agent grade the outputs without knowing which is which.

## Automatic sizing

Picking a tier per brief by hand works. If you want it automatic, [07](07-jev-router.md) describes a classifier hook that sizes each message and hands it to a tier-matched helper. Without it, the table above in CLAUDE.md is the whole mechanism and costs nothing.
