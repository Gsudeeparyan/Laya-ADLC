---
applyTo: "**/*member*,**/*claim*,**/*policy*,**/*policyholder*,**/*patient*"
---

This code may handle personal or health data. Follow the `member-data-safety` skill before changing it.

- Claims and medical details are special category data under the GDPR.
- Name the columns you need. Log internal IDs or tokens, never names, PPSNs, dates of birth, contact details, health details or free-text notes.
- Say `member` or `policyholder`, not `customer`. Say `pseudonymised` when a key exists.
