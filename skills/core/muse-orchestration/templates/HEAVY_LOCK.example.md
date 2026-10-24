# Heavy task lock (one per machine). Format: lane<TAB>task<TAB>started<TAB>expected end. No rows = free.
# Only heavy jobs take the lock: full test suites, production builds, timing-sensitive tests,
# virtual machines and simulators. Small targeted tests run outside the lock under a shared cap.
# Take the lock in the same process that runs the job, so a crash releases it; write the end time
# you expect, and remove your row (or append "released HH:MM") when done.
# Before starting, check: lock free, enough free disk and swap, load below your threshold.
