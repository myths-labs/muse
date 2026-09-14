# Runtime dependency preflight

Ordinary MUSE continuity uses the Python standard library. This optional probe
checks the interpreter a workflow will actually use, before running that workflow.
It does not install packages, change the interpreter, claim a Lane or certify QA.

## Select the real interpreter

Run from the project where MUSE is installed. Use an absolute interpreter path,
including its virtual environment launcher when applicable:

```bash
MUSE_RUNTIME_PYTHON="/absolute/path/to/venv/bin/python"
"$MUSE_RUNTIME_PYTHON" -I .agent/skills/muse-commands/scripts/muse-runtime-dependencies.py \
  --python "$MUSE_RUNTIME_PYTHON"
```

The probe launches that exact path with `-I -B`, then reports `sys.executable`,
version, environment prefixes and isolation flags. Do not resolve a virtualenv
launcher to its base Python: that can select a different package environment.
The shell doctor uses `MUSE_PYTHON` when set; an explicit Python command must use
the same selected path. Preserve the actual workflow arguments and native identity.

Python's [isolated mode](https://docs.python.org/3/using/cmdline.html#cmdoption-I)
ignores `PYTHON*` variables and excludes the working directory and user site from
imports. A successful ordinary-shell import does not prove an isolated import.
MUSE helpers do not automatically enable isolation; match the launch conditions
of the workflow being diagnosed.

## Optional image decoder check

Only workflows that explicitly require image decoding need this check. The
public continuity runtime does not include a native image-attachment adapter,
and installing MUSE does not install or require Pillow.

```bash
"$MUSE_RUNTIME_PYTHON" -I .agent/skills/muse-commands/scripts/muse-runtime-dependencies.py \
  --python "$MUSE_RUNTIME_PYTHON" --require-image-decoder
```

This imports Pillow, verifies fixed PNG and JPEG fixtures, reopens and fully
decodes each, then checks its format and dimensions. Both formats must pass.
The report includes the Pillow version and module path. It proves those fixtures
decode in that environment; it does not prove an actual attachment was processed.

If the dependency is absent, select an existing suitable environment or follow
[Pillow's installation instructions](https://pillow.readthedocs.io/en/stable/installation/basic-installation.html)
for the intended environment. The probe never installs packages automatically.
After correcting the environment, rerun both the probe and the affected real
workflow with the same interpreter, identity and guarded inputs.

## Results and release evidence

- Exit `0`, `status: PASS`: the requested preflight passed. Without the image
  option, `image_decoder.status` is `NOT_REQUESTED`.
- Exit `2`, `status: FAIL`: inspect `error`. Missing packages produce
  `IMAGE_DECODER_UNAVAILABLE`; broken decoding produces `IMAGE_DECODER_FAILED`.
  Missing executables, unsupported Python, isolation failures, timeouts,
  oversized output and malformed responses have separate named errors.
- Startup output that is not valid text/JSON is a failed probe, including invalid
  encoding on stdout or stderr. It must not become a traceback or a success.

For a release, keep the exact invocation, JSON report and affected workflow
result. Exercise the installed copy after upgrade and verify rollback restores
the previous files. Keep interpreter paths and installation receipts private.
