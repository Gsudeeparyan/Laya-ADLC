---
name: adlc-agent-author
description: Write or change a Laya staff agent in the Laya-ADLC library. Use when editing anything under non-technical/everyone or non-technical/paid-licence, the shared preamble or PII guard, an agent.yaml, or when adding a new staff agent.
license: Proprietary - Laya Healthcare internal use
---

# ADLC Agent Author

A staff agent is the shared preamble + (the PII guard) + one `SKILL.md`. It runs on Microsoft Copilot: 8,000 characters, no memory between chats, users who aren't AI or Excel experts, and most of them on the free version. The house style is in `best-practices/04-writing-skills.md`; the shared language in `GLOSSARY.md`.

## Steps

1. **Read what's already said.** Read `non-technical/shared/laya-preamble.md`, `non-technical/shared/pii-guard.md` (if the skill sets `adlc-data-guard`), and the guide's seven levers. Anything the preamble or guard says, the skill leaves out.

2. **Check the tier.** Free unless it needs what only the paid licence has (`non-technical/admin/licences.md`). A paid agent must have a free route for the same job, named in the AI Helper.

3. **Make the change.** Steps end on "Done when..." where rushing would hurt. Reuse the guide's leading words. State the target behaviour rather than banning its opposite. Spend the budget on expertise the model lacks (formats, file internals, the order to test causes, Laya's words), not on etiquette. A new term goes into `GLOSSARY.md` first.

4. **Validate.** From `technical/platform`: `python tools/validate_skills.py`. Done when it passes, with the agent's total under 8,000.

5. **Role-play the agent.** Run `python tools/build_agents.py`, read `non-technical/ready-to-use/agents/<tier>/<agent>/appPackage/instruction.txt` as the agent's only instructions, and play three conversations against it:
   - its first conversation starter
   - a vague ask
   - a message with a member's name and PPSN pasted in

   Check each reply: it asks in rounds with suggested answers, acts on a clear request, STOPs before anything destructive, protects the personal data, and ends with **What next?**. Done when all three pass. A failure is fixed in the skill, then re-checked.

6. **Ripple.** Bump `adlc-version`. If staff will see the change, update `agent.yaml` (description, starters, `staff_guide`). If routing changed, update `everyone/skills/start-here/SKILL.md`, `staff-guide/getting-started.md` and any playbook that names it. Then run `python tools/build_guides.py`.

7. **Test.** `python -m pytest` and `python tools/check_library.py`. Done when both pass.

8. **Retro.** If you made a mistake the validator could have caught, add a check to `tools/validate_skills.py` (watch it go red on a broken copy first) rather than a sentence to the guide.

For Excel skills, the workbook format is a contract: `technical/platform/docs/excel-continuity-pattern.md`, `src/adlc_workbook/` and the Excel skills change together, with a test.
