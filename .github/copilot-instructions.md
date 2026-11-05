# Laya-ADLC

Laya Healthcare's AI library, for Microsoft Copilot and GitHub Copilot. Read `AGENTS.md` for the rules and commands.

- Commands run from `technical/platform`. `python -m pytest` must pass before anything merges.
- Never edit `non-technical/ready-to-use/` by hand. Change the source and rebuild.
- Never put real member, customer or staff data anywhere in this repo.
- Changing a staff agent: follow the `adlc-agent-author` skill in `.github/skills/`.
