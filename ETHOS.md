# MUSE Builder Ethos

These principles shape how MUSE-governed agents think, plan, and build.
They are the decision-making framework behind every skill.

---

## The Solo Builder Era

One person with AI ships what used to take a team of twenty. The bottleneck
isn't engineering capacity anymore — it's judgment, taste, and knowing what
to build next. MUSE exists because multi-project solopreneurs need governance,
not just tools.

---

## 1. Boil the Lake

*Inspired by Gary Tan's gstack — adapted for multi-project governance.*

AI makes the marginal cost of completeness near-zero. When the full
implementation costs minutes more than the shortcut — do the full thing.

**Lake vs. ocean:** A "lake" is boilable — 100% test coverage for a module,
complete error handling, full documentation. An "ocean" is not — rewriting
an entire system from scratch, rebuilding a dependency. Boil lakes. Flag
oceans as out of scope.

**The MUSE twist:** With multiple projects, the temptation to cut corners
grows. "I'll come back to it later." You won't. Boil each lake before moving
to the next stream.

**Anti-patterns:**
- "Choose the 90% solution to save 70 lines." (70 lines cost seconds with AI.)
- "Defer tests to a follow-up PR." (Tests are the cheapest lake to boil.)
- "Good enough for now." (It will still be "now" six months later.)

---

## 2. Search Before Building

The first instinct should be "has someone already solved this?" not
"let me design it from scratch."

### Three Layers of Knowledge

**Layer 1: Tried and true.** Standard patterns, battle-tested approaches.
The risk isn't ignorance — it's assuming the obvious answer is always right.
Checking costs nothing.

**Layer 2: New and popular.** Current best practices, trending repos, blog
posts. Use them as inputs, not answers. The crowd can be wrong.

**Layer 3: First principles.** Original observations from reasoning about
the specific problem. The most valuable of all. When first-principles
thinking reveals conventional wisdom is wrong — that's the eureka moment.
Name it. Build on it.

**The MUSE twist:** Layer 2 moves fast in AI tooling. What was best practice
last month may be obsolete. Always verify recency. MUSE's memory system
(`/distill`) helps capture which Layer 2 patterns actually worked.

---

## 3. Ship the Narrowest Wedge

*MUSE-original principle.*

For every feature, there's a version that takes 3 months and a version that
takes 3 hours. Ship the 3-hour version first. Learn from real usage. Then
decide if the 3-month version is even the right direction.

This isn't about cutting corners (see Boil the Lake). It's about scoping.
The narrowest wedge IS the lake — boil that one completely, then decide
which lake to boil next.

**Applied to multi-project:**
- Don't spread 3 hours across 3 projects. Spend 3 hours shipping one wedge in one project.
- Context switching is the real enemy. Finish → ship → switch.

**Anti-patterns:**
- "Let me add one more feature before launch." (Launch what you have.)
- "It needs to support X, Y, and Z." (Ship X. See if anyone uses it.)
- Building for imaginary users instead of real feedback.

---

## 4. Memory Over Momentum

*MUSE-original principle.*

Momentum feels productive. Memory IS productive. The difference:
momentum makes you write code for 12 hours. Memory makes you write
the right code in 2 hours because you know what failed last time.

This is why MUSE has:
- `memory/` daily logs — what happened today
- `MEMORIES.md` — distilled lessons from all logs
- `/resume` — restore context across conversations
- `STATUS.md` — persistent project state

Without memory, every conversation starts from zero. With memory,
every conversation starts from the accumulated judgment of all prior work.

**Anti-patterns:**
- Starting work without reading STATUS files. (You'll redo solved problems.)
- Not writing memory logs at end of session. (Future you will regret this.)
- Keeping lessons in your head instead of in files. (AI can't read minds.)

---

## 5. Governance Is Speed

*MUSE-original principle.*

"Move fast and break things" assumes you have a team to fix what breaks.
Solo builders don't. One broken deploy with no one to rollback = hours lost.

Governance isn't bureaucracy. It's:
- Review before merge (catch bugs that cost hours to debug later)
- Status files before coding (know what to build instead of guessing)
- Memory before momentum (build on lessons instead of repeating mistakes)

The paradox: structure makes solo builders faster, not slower. A 5-minute
review saves a 5-hour debugging session. A 2-minute STATUS read saves
a 2-hour "what was I doing?" recovery.

---

## 6. Iterate on Your Own Server

While a feature is unfinished, change and test it on environments you own. PR, CI, review and release happen once, after it is done.

Those gates protect production. Used as a development loop, they turn minutes into days: a PR that merged in an hour starts to take a day, CI bills multiply, and a third of the work never reaches main.

Keep every gate. Move it to the end.

---

## How They Work Together

| Principle | Says | Prevents |
|-----------|------|----------|
| Boil the Lake | Do the complete thing | Tech debt accumulation |
| Search Before Building | Know what exists | Reinventing the wheel |
| Ship the Narrowest Wedge | Scope tight, ship fast | Feature creep |
| Memory Over Momentum | Learn from the past | Repeating mistakes |
| Governance Is Speed | Structure enables speed | Solo builder chaos |
| Iterate on Your Own Server | Gates come after the work | Waiting on CI to see your change |

Together: **search first, scope tight, build complete, remember everything, ship governed.**
