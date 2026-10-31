# Heavy task lock (one per machine). Format: lane<TAB>task<TAB>started<TAB>expected end. No rows = free.
# Only heavy jobs that must run on this machine take the lock: production builds,
# timing-sensitive tests, virtual machines and simulators. Full test suites run in CI or on a
# remote runner, not here. Small targeted tests run outside the lock under a shared cap.
# Take the lock in the same process that runs the job, so a crash releases it; write the end time
# you expect, and remove your row (or append "released HH:MM") when done.
# Before starting, check: lock free, enough free disk, memory pressure and swap, load below your threshold.
