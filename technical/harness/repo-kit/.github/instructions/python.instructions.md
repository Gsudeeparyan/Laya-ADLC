---
applyTo: "**/*.py"
---

- Every outbound call has an explicit timeout. Retries are bounded and backed off, on safe operations only.
- Catch specific exceptions, and log the type and an ID, not the payload.
- Add a dependency only after looking it up on PyPI, and pin it in the lock file.
