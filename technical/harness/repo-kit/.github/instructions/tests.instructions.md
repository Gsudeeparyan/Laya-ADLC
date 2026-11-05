---
applyTo: "**/test*/**,**/*test*.*,**/*.spec.*"
---

Follow the `test-strategy` skill.

- Expected values come from the spec or a worked example, not from the code under test.
- All data is synthetic and obviously fake, built at test time where possible.
- Don't delete, skip or loosen a test to get green. If a test is wrong, say so and explain.
