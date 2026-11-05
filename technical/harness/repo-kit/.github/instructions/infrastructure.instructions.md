---
applyTo: "**/*.bicep,**/*.tf,**/infra/**,.github/workflows/**"
---

Follow the `production-ready` skill.

- Least privilege for every identity, and no public network access unless the ticket says so.
- No secrets in templates or pipeline YAML. GitHub Actions are pinned to a full commit SHA, with minimal `permissions`.
- Prepare changes as code for a person to run. Don't apply them to any shared environment.
