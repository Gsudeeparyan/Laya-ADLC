---
applyTo: "**/*.sql,**/*.pls,**/*.pkb,**/*.pks,**/*.plsql"
---

Follow the `data-design` skill. For old PL/SQL without tests, follow `legacy-change` first.

- Name your columns; no `SELECT *` on member, policy or claim tables.
- Use bind variables in dynamic SQL.
- Jobs and migrations are safe to run twice. Migrations are expand, migrate, contract.
- Reports suppress groups smaller than 5.
