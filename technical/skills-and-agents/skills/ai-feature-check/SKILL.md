---
name: ai-feature-check
description: Check a feature that uses AI before it's built. Use when a product, service, report or internal tool will call an AI model, make or support decisions about people, use machine learning, or add a chatbot or generated content, or when someone asks whether an AI use is allowed or needs sign-off.
license: Proprietary - Laya Healthcare internal use
---

# AI Feature Check

This is for features **Laya builds or buys that contain AI**. Using GitHub Copilot to write ordinary code doesn't need it. You sort out the facts and flag what's needed; Compliance, the DPO and the AI owner make the calls. Everything here goes to them as a recommendation, not a ruling.

## 1. Describe it plainly

Write down: what decision or output the AI produces, who it affects (members, staff, the public), what data goes in, who built the model, and what a person does with the output. Done when someone outside the team could say what the AI does and who it could harm.

## 2. Set the risk tier

Use `roles-and-lifecycle/risk-tiers.md`. **T3 applies, and work stops here until sign-off, if the AI**:

- does **risk assessment or pricing for natural persons in life or health insurance**, which the EU AI Act lists as high-risk (Annex III, point 5(c));
- decides or materially influences a claim, cover, complaint or anything else with a significant effect on a person;
- profiles people, or infers health, ethnicity, religion or similar;
- affects hiring, promotion or staff evaluation (also listed in Annex III);
- could be a prohibited practice, such as manipulation or emotion recognition at work.

**STOP** at T3. Tell the user to bring in the AI owner, Compliance and the DPO, and the actuarial function if it touches pricing or reserving, before anything gets built.

## 3. Check the six areas

EIOPA's AI opinion expects proportionate measures in these. Answer each in a line, in more depth as the tier rises:

| Area | The question |
|---|---|
| Fairness and ethics | Could it treat a group worse? Could a harmless-looking field stand in for a protected one? How will you measure it? |
| Data governance | Is the data complete, accurate and appropriate? Do you have a lawful basis for this use? Does it need a DPIA? |
| Records | Could you reconstruct what it did and why, for an auditor, a year from now? |
| Transparency | Do people know they're dealing with AI? Can you explain an outcome in plain words? |
| Human oversight | Who checks the output, and do they have the time, skill and authority to overrule it? Is there a route to complain? |
| Accuracy, robustness, security | How will you measure quality and drift? What if the model is down, wrong or attacked? |

Use `security-review` (`../security-review/SKILL.md`) for the attack side, and `member-data-safety` (`../member-data-safety/SKILL.md`) for the data flow.

## 4. Check the supplier

If a third party supplies the model or service, Laya stays responsible for its use. Find out: where data goes, whether it's used for training, retention, sub-processors, exit plan, and what evidence the supplier gives about quality. Raise it with the vendor owner for the contract and the ICT third-party register.

## 5. Plan the evaluation

Before building, write what "good enough" means as measures with thresholds, the test set (synthetic or approved data), and who reviews results. Model updates change behaviour, so re-run the evaluation on every model change.

## 6. Record it

Add it to the AI use register (the template is in `non-technical/ready-to-use/templates/`): owner, purpose, tier, data, supplier, oversight, review date.

Done when the register entry is complete, every area in step 3 has an answer with a named owner, and any T2 or T3 sign-offs are requested or recorded.
