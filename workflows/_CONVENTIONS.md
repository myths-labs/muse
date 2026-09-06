---
description: Resolve portable MUSE project roots, preserve role identity and continue useful work
---

# Project paths and execution

Read the current project's `.muse/config.json`, or the explicit `MUSE_CONFIG` file.
`role_home` names the command center in `projects`; relative roots resolve against
the project containing `.muse/config.json`. The helper returns actual absolute paths.
Explicit legacy DYA_ROOT/PROMETHEUS_ROOT/MUSE_OSS_ROOT environment variables remain
supported for preexisting configured identities; explicit MUSE_CONFIG takes precedence.
The legacy `${DYA_ROOT}` placeholder means the configured command-center root, not
an author-machine directory. Unconfigured external project paths are unknown.

Preserve the role and Lane selected by the user; the subject workspace does not
change them. Follow the project's own role policy, including direct implementation
by Strategy if that is the user's chosen model. The agent derives goals, scope,
acceptance checks and next actions; do not ask the user to complete a template.
Keep the current Lane unless independently continuing authorized scope needs a new
one. A CLOSED Lane is not reopened by ordinary resume or provider switching.

Meaningful progress is saved incrementally. Context pressure triggers save and
reassessment after compaction, not full Bye or a new conversation. Unknown metrics
stay unknown. Read shared decisions and the selected Lane's required evidence;
do not reload every Lane or all historical transcripts by default.

Permissions remain scoped to the user's actual request. A receipt or role name
does not authorize deployment, publishing, destructive changes or messages to others.
