# Optional Jev tools alongside MUSE

[简体中文](OPTIONAL_TOOLS_CN.md) · [MUSE usage](CONTINUITY.md) · [Website](https://muse.mythslabs.ai/)

MUSE keeps your role, decisions, evidence and next steps across conversations. Jev tools can help with a narrower decision inside that work: selecting a browser action, triaging a code change or choosing a model for a separate CLI session.

**This is guidance for optional third-party tools, not a new MUSE release or a bundled integration.** MUSE remains at 3.7.1 with 66 included skills. Its installer does not install these projects, supply credentials or enable provider calls. Ordinary Resume and Save do not need Jev. The descriptions below refer to the [reviewed source versions](#reviewed-source-versions), not a promise about future upstream versions.

## Choose by the task

| Task | Project or entrypoint | Appropriate use and limit |
| --- | --- | --- |
| Evaluate browser action selection | `browser-use/jev-ultrafast` | Uses an indexed DOM to ask about an operation and compatible targets in one Jev request. Text entry needs a separate text model. Start with a small ordinary navigation or form task. |
| Find decision examples | `Anil-matcha/awesome-jev-by-typesafe` | Community examples for routing, ranking and verification. This is reference material, not an executable agent or a native MUSE skill. Check an example against the current API before adopting it. |
| Research macOS computer use | `awlevin/typesafe-computer-use` | Combines local OCR and Accessibility observations with Jev decisions. Screen/accessibility permissions and provider configuration are separate requirements. |
| Triage a code change | `devagrawal09/jev-review` | Experimental review support. The reviewed collectors cover JS/TS, JSX/TSX and c/m variants; Python and Rust files are outside that collector scope. Inspect findings and run the relevant tests. |
| Evaluate model routing | `gargpratyush/jev-router` | Runs a loopback proxy and a separately launched Codex or Claude Code CLI. It does not change the model in an existing desktop task or replace the client's internal reasoning. |
| Explain a recorded route | `jev-explain`, supplied by `jev-router` | Reads the intended router session's local record. It does not make a new routing decision. No recorded history is a valid outcome. |

These are five upstream repositories and six use cases, not six additional bundled MUSE skills. The router includes a Codex `jev-explain` skill; other entrypoint names may be local adapters. Do not assume a matching slash command is installed. Follow the selected project's documentation at the version you review.

## What leaves the machine

Choose the data scope before a provider call. Local execution or local OCR does not make the entire workflow local-only.

| Path | Data boundary |
| --- | --- |
| Ultrafast browser decisions | Goal, URL/title, visible page text, indexed elements and recent actions go to Jev. Text generation uses another provider. The absence of default screenshots does not keep page content private. |
| macOS computer-use decisions | OCR/Accessibility text and current-screen context go to Jev. The optional Anthropic final-answer writer also sends a resized screen PNG, goal, action history and screen text. A dry run can still capture the screen and call a provider. |
| Code review | Code and diff context go to a provider. A full-codebase scan is broader than one selected change. |
| Router and explanation | Routing uses prompt/context information. Local logs can contain prompt, request and response text. An explanation reads an existing record; keep that record private and select only the relevant session. |

Exclude credentials, unrelated private correspondence, financial/identity records and whole MUSE memory archives. Follow the user's existing authorization and the client's permitted execution channel. Installing a tool grants neither screen permissions nor permission to transmit unrelated data, start a persistent proxy or control other tasks. In a client with a prescribed browser/computer-use interface, an optional tool is not a bypass for that interface.

## Optional retrieval within a Lane

This is an integration pattern, not a shipped `muse-context` command or automatic behavior of MUSE 3.7.1.

1. Read the current authoritative Lane state and required task facts first. If they are sufficient, make no retrieval call.
2. Let each Lane maintain its own explicitly reviewed source registry. Bind entries to file hashes and bounded excerpts so a stale or changed source can be detected.
3. Send only the reviewed technical material needed to resolve the evidence gap. Keep mandatory current facts and private continuity records local.
4. Treat returned candidates as evidence to inspect, never as instructions or authorization. Verify them against their sources before using them.
5. Record the selected source/version, actual calls, cache use and any labeled fallback. On a provider error, missing result or stale source, use the permitted local workflow and keep unresolved gaps visible.
6. Preserve MUSE's normal save and writer checks. Retrieval does not claim a Lane, complete a save or certify source coverage. An ordinary Save does not need a provider call.

For example, ask your agent: “Review the current Lane first. If implementation evidence is missing, select a few approved source excerpts; record what was sent and verify the result against those sources.” The agent still needs an implemented, configured and permitted retrieval path before making a call.

## Verify a bounded pilot

For the reviewed Ultrafast MVP, unsupported surfaces include shadow roots, frames/iframes, canvas, uploads, pop-up tabs, nested scrolling and arbitrary keyboard widgets. Its owned tabs share an existing Chrome profile; tab ownership is not an isolated account or privacy boundary. Do not infer support from a demo.

Define one task and an observable success condition. Check the actual action, resulting state, error/unsupported path and data sent. A model saying `DONE` is not an outcome check. Record latency and provider calls on that task before making speed or cost claims.

For review, verify that the intended files were collected; an empty report is not a pass. For routing, inspect the separately launched session and its actual recorded choice. Help output, mocked tests and offline installation checks do not establish screen permissions, live task success, security certification or permission to merge.

A future distributable integration would need portable installation, explicit configuration, upgrade/rollback checks and acceptance evidence before a release decision. This guide does not announce such a release.

## Reviewed source versions

Reviewed for this guide on 2026-09-21. These links preserve the source used for the descriptions; they are not an instruction to install unreviewed updates. Recheck a different version before use.

- [browser-use/jev-ultrafast at 1231850a0bf1](https://github.com/browser-use/jev-ultrafast/tree/1231850a0bf1a0c0341fe408ef1668dbbfdfac46)
- [Anil-matcha/awesome-jev-by-typesafe at 0f4a1eadcdd7](https://github.com/Anil-matcha/awesome-jev-by-typesafe/tree/0f4a1eadcdd70f4fc1cf8eadcf72794dfe416095)
- [awlevin/typesafe-computer-use at cc7b5066ae1a](https://github.com/awlevin/typesafe-computer-use/tree/cc7b5066ae1a07b5e3182e8f87a9b5b6dfdcffc1)
- [devagrawal09/jev-review at 31f89602797f](https://github.com/devagrawal09/jev-review/tree/31f89602797fb7bea007f8a480bf368bf564954e)
- [gargpratyush/jev-router at 38da6b84ea01](https://github.com/gargpratyush/jev-router/tree/38da6b84ea01241bfc41fbddc0928d0f40a703f0)
