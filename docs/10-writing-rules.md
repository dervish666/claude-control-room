# 10 Writing rules

Every session in this setup writes something a person reads: replies, vault notes, commit messages, PR bodies. Two rule sets in CLAUDE.md shape all of it. Both are in `templates/CLAUDE.md.template`.

## Brevity: how long

The default is a sentence or two, or three to five bullets. Lead with the answer. No restating the question, no recap of tool output I already saw, no closing offer of more help. Code changes name the file and line, not the code.

Brevity is about output, not effort. A short answer from a session that thought hard beats a long one from a session that narrated its thinking.

Verbosity is a deliberate choice for audits, research and plans with real trade-offs. Saying so in the rules matters: without it the model drifts back to long by default.

## Anti-slop: which words survive

A list of tells that mark text as generated, and a ban on each:

- **No em dashes.** The most reliable single tell. Swapping in a spaced hyphen or an en dash is the same tell in disguise.
- **Colons introduce lists or examples**, never join two clauses.
- **A banned-word list**: delve, leverage, robust, seamless, comprehensive, crucial and the rest in the template.
- **Banned shapes**: "not just X, but Y", the forced list of three, trailing "-ing" clauses that add a vague consequence, generic closers.
- **Name the mechanism.** If a sentence would sit unchanged in another project's docs, it says nothing about this one.
- **Numbers over adverbs.** "Significantly faster" becomes "from 2.1 s to 0.6 s".
- **Keep a voice.** An opinion beats a balanced pro and con list.

These apply to code comments too.

## Why bother

Two reasons, both practical. Vault notes are re-read by every future session, so padding costs tokens on every read, forever. And text I skim past is text I miss the one important line in.

## The longer checklist

I also use a longer editing-pass skill for documents. Mine is adapted from a public skill that carries no licence, so it is not included here. The rules above cover the tells that fire most often. If you want a deeper pass, write your own checklist from the text you keep having to fix.

## Output style

`templates/output-styles/tight.md` restates the reply-shape rules as a Claude Code output style, so they apply even in sessions where CLAUDE.md is long and the rules sit far from the top.
