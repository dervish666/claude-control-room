---
name: falsify-first
description: "Proves a check could have failed before its pass is believed. Use before trusting any green test, clean measurement, empty result, or tool that reports success. Triggers on: a passing suite, 'no differences', 'found nothing', 'zero results', a probe or script you wrote yourself, an agent's finding, a deploy or fallback that reports OK, or any number about to be reported to the user."
---

# Falsify first

"Did you run it?" is the first question. This skill asks the next one: **could it have failed?** Most bad reports I have seen ran the command and read the output. The output was green and wrong.

## The gate

Before reporting a pass, an empty result or a number, answer in one line each:

1. What would this check have shown if the thing were broken?
2. Have I seen it show that, on this input, today?

If the answer to 2 is no, do one of the moves below before reporting.

## Move 1: perturb and demand red

Before first use of any instrument you wrote (a test, a probe, a grep, a validation script), break the input on purpose and require a failure.

- A test: introduce the bug it is meant to catch, run it, see it fail, revert.
- A search that found nothing: plant a known match and confirm it is found.
- A diff that says identical: change one byte in one side and confirm it reports the change.

Ship the falsification next to the assertion where you can, so the next person can rerun it.

**When the falsification does not bite, that is a finding.** If breaking the code leaves the tests green, nothing tests that code.

## Move 2: a control, when you cannot break the input

Run the same instrument on something where the answer must be non-zero, for a reason unrelated to what you are measuring. Zero hits for a password in the logs means little until the same query finds a string you know is in the logs.

A number typed beside a command is not a control. Run it.

## Shapes this takes

- **A green result.** Tests pass, the build is clean, the deploy says OK. Check the tests ran the code you changed, the build included the file, and the deploy reached the target you think it did.
- **An absent result.** "No matches", "no errors", "nothing found". Distinguish "I looked and it was not there" from "I looked and I cannot see". A permission error, a wrong path, a filter or a `head -4` all produce silence.
- **Half the system.** A suite made only of reads passes while the code corrupts what it writes. Test the write path too.
- **A constant that was tuned on one sample.** Score it on data that was not used to pick it, and sweep its neighbours. A real effect is smooth in the parameter.
- **An exit code.** A zero exit is not a pass. Read the output line that says what happened.
- **An agent's "done".** A subagent's report is a claim. Check the file, the commit or the running thing.

## Silent evidence limiters

Each of these decides how much evidence you admit, and none announces itself: a default value, a tolerance, a comment that says "superseded", a viewport size, a header line skipped, a result capped at N. When a result is clean, list which of these sat between the data and your eyes.

## When the check disagrees with a tested implementation

The prior favours the implementation. A new validator that flags working code is more often wrong than the code. Check the validator against a case you know is right before trusting it against one you don't.

## Don't ritualise it

One perturbation that could have failed beats five that could not. If the falsification is trivial, say so in a word and move on; spend the effort where a wrong green would cost the most.
