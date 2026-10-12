# 07 The Jev router (optional)

[06](06-model-routing.md) picks a tier for each subagent brief. That leaves the message you type: the main thread does whatever you ask on whatever model the session started on. The router is a hook that sizes each typed message and tells the main thread to hand it to a helper on the right tier.

It depends on a paid third-party API, so it is off by default. The routing table in CLAUDE.md is the free fallback, and most of the saving comes from the table.

Code and install steps: [`optional/jev-router/`](../optional/jev-router/README.md).

## What happens to a message

1. The `UserPromptSubmit` hook fires before Claude sees the message. If `~/.claude/router/ON` is missing it exits in milliseconds.
2. `route.py` asks Jev, TypeSafe's classifier model, four questions in one request:
   - **size**: tiny, everyday, large or hardest
   - **kind**: public UI, other UI, thinking (planning, research, investigation) or other
   - **contextual**: is this a reply that only makes sense inside the conversation ("yes do that")?
   - **skill**: which of your installed skills, if any, fits
3. If a skill fits at 75% confidence or more, the hook suggests running it here.
4. Otherwise, if Jev is at least 60% sure of the size and the message stands on its own, the hook tells the main thread to call the matching helper agent.
5. Anything else, including every failure, injects nothing. The session behaves as if the router were not installed.

| Lane | Helper | Tier |
|---|---|---|
| tiny | `router-tiny` | small |
| everyday | `router-everyday` | top, medium effort |
| large | `router-large` | top, high effort |
| hardest | `router-hardest` | top, highest effort |
| public UI, small | `router-frontend` | design |
| public UI, big | `router-frontend-build` | design, high effort |

Two floors stop the classifier being too clever: thinking work never lands below `large`, and interface work that edits code never lands on the small tier.

## The honest limit

Claude Code fixes the main thread's model when the session starts. Nothing can change it per message. So the router does not make the main thread cheaper. It picks the model for the **work**: the main thread reads your message and delegates, and a helper on the chosen tier does the job. On a genuinely tiny job the delegation round trip can cost more than it saves.

## Why a skill beats delegating

"Ship it" reads as contextual, so the size half wants to keep it in the main thread, while the skill half is certain it means a release skill. Keeping it here is right: a skill needs this session's tools and history, which a fresh helper lacks. The suggestion is only ever a suggestion. Nothing auto-runs, which is what makes it safe to include skills that act in the world.

## What I measured

On my setup, over ten messages run one after another:

- 1.2 s mean added per message, 2.4 s worst. Size alone was 0.6 s; the skill question roughly doubles it.
- About $0.22 per 1,000 messages. Size alone was $0.03.
- Cutting the skill catalogue from 138 to the 36 I use took skill picks from 19 of 20 right to 20 of 20 and halved the latency. Trim `skills.allow`.

On a 40-case eval of my own messages, narrowing "public UI" to pages strangers see took routing from 17 of 28 right to 40 of 40, including 12 cases written after the criteria. Build your own `eval.json` from real messages; mine named private projects, so the repo ships five generic cases.

## Effort for the main thread

The router cannot reach messages kept in the main thread, which in my logs is most short replies. Switching model there would empty the prompt cache. Effort can change per request without touching the cache, so I run a second, smaller piece: a Claude Code plugin that asks Jev how much thinking each reply needs and lowers the turn's effort when it is safe. Over 54 real turns, 42 dropped from the highest effort to high, 6 to medium and 2 to low, and an effort change kept the cache in both directions. It needs Claude Code's plugin hooks API and is not shipped here.

## Privacy

While it is on, every message you type is posted to `api.typesafe.ai`. The effort plugin also sends the last 2,500 characters of the previous reply. Turn the router off for anything private, and keep the API key in your environment, never in a synced folder.
