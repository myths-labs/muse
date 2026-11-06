---
name: iterating-on-own-server
description: Use when a feature is not finished and the next step looks like opening a PR, starting CI, waiting for a release train, or testing in production; before sharing a preview link; when work feels slow or stuck on CI, merges or review; when CI bills or open PR counts keep rising.
---

# Iterating on Your Own Server

## Core Principle

While a feature is unfinished, change, test and change again on environments you own. PR, CI, review and release happen once, after the feature is done. Those gates protect production. They are not development tools.

## Three Environments

| Layer | What it is | One round | Use it for |
|---|---|---|---|
| L0 Local | Local database, local stack, relevant tests | Seconds to minutes | Logic, payments, migrations, every write |
| L1 Integration preview | One integration branch, one fixed address | Minutes | Whole-product behaviour, recordings, showing people |
| L2 Production | Release | Once per feature | Launch acceptance |

Every round finishes on L0 or L1: change, deploy, walk the user flow yourself, record it, change again. If half a day passes between writing code and seeing it run, fix the environment first.

## Integration Branch

- One direction, one integration branch, one fixed address. Every workstream merges its latest head here the same day.
- This branch never opens a PR. Temporary keys, fallbacks and unreviewed changes live only here.
- Branches headed for main stay clean. They never merge the integration branch or any branch that carries temporary commits.
- Preview writes go to a preview database. While a preview still reads production data, write tests stay on L0.

## Before Showing Anyone

Confirm all three:

1. This build contains every workstream's latest head. Check the commits.
2. After sign-in the address is still the preview domain.
3. The default experience is the one you are currently building.

If one fails, fix it first. An old build with a caveat still shows people the wrong thing.

## When the Feature Is Done

1. One feature, one PR. Do not split it into many small PRs.
2. Start CI and review now. Payments, security and migrations keep their full review.
3. Release, then record the flow in production.

## Shipping Early

Ship an unfinished feature only to show investors or an accelerator, or when something can only be tested live. Name what it is.

## What to Say

- Passed on L1: "Passed on preview, not live yet."
- Passed on L2: "It works."

## What Does Not Change

Deployment rules, production database procedure, payment and security review, secret handling and deep QA all stay. This skill moves the gates. It does not remove them.

## Stop If You Think This

| Thought | Do this |
|---|---|
| Open a PR so CI can run | Run the relevant tests locally. CI runs on finished features |
| Catch the next release to see the effect | Deploy to L1 |
| Only production evidence counts, so it must ship first | Production evidence decides launch. Preview recordings are development evidence |
| The preview is a bit old, add a note and send it | Merge the latest first |
| Payment code cannot use previews, so wait for merge | Verify on L0 |
| Merging the temporary branch into main work is easiest | Open an integration branch |
| Small PRs are easier to review | Each PR pays for CI, review and conflicts |
