# Data protection with AI

**For everyone, and in more depth for owners of a process or system.** The DPO advises on what the law requires at Laya. This is **draft guidance for the DPO to review [to confirm]**.

Laya holds health information about its members, which the GDPR treats as **special category data** needing extra protection. So the care here is higher than in most companies.

## For everyone

**Ask yourself three things before you put data into Copilot:**

1. **Does the job need it?** Usually not. "A member with a query about a waiting period" works as well as a name.
2. **Is this Laya's Copilot, with the green shield?** Nothing else is OK for work data.
3. **Can it be cleaned first?** The **Laya PII Guard** swaps personal details for tokens, and can put them back afterwards.

**Most sensitive first:**

| Data | Care |
|---|---|
| Health, claims, diagnosis, treatment; anything about children | The most care. Clean it first, or leave it out. Ask if unsure |
| PPS numbers, bank details, HR records | Very careful. Rarely needed in a chat |
| Names, contact details, policy numbers | Leave out unless needed |
| Figures with no way to identify a person | Generally fine. Watch for groups smaller than 5 |

**"Anonymised" is harder than it looks.** Removing names isn't enough if someone can still be identified, such as the only 80-year-old on a plan in a small town. If a key exists to put names back, the data is **pseudonymised**, and it's still personal data. See the [glossary](../GLOSSARY.md).

**Laya's tools protect you here:** Laya's agents never refuse if personal data appears. They protect it, using tokens like PERSON_001, and carry on. That's a safety net, not permission.

**If you make a mistake, tell someone the same day.** See [When something goes wrong](../non-technical/staff-guide/when-something-goes-wrong.md).

## What Microsoft's protections do and don't cover

From [Microsoft's Copilot Chat privacy page](https://learn.microsoft.com/en-us/copilot/plan/privacy-and-protections):

**They do:**
- Process prompts and responses inside the Microsoft 365 service boundary, with Microsoft as a data processor.
- Keep prompts and responses out of training for the underlying foundation models.
- Keep EU traffic within the EU Data Boundary for Copilot Chat.
- Log prompts and responses for audit and eDiscovery.

**They don't:**
- Make it lawful to use any data for any purpose. That's still for Laya to decide.
- Cover web searches: queries sent to Bing aren't within the EU Data Boundary.
- Cover every model: [Microsoft's enterprise data protection page](https://learn.microsoft.com/en-us/microsoft-365/copilot/enterprise-data-protection) lists models outside the EU Data Boundary, so check before allowing them.

**Files:** files uploaded to Copilot Chat are stored in that person's OneDrive for Business. Keep this in mind for retention.

## For anyone starting something new with AI

The [Irish Data Protection Commission](https://www.dataprotection.ie/en/dpc-guidance/blogs/AI-LLMs-and-Data-Protection) (July 2024) asks organisations to understand, before using an AI system:

- what personal data it uses, and how;
- where the data goes, and whether the provider keeps or reuses it;
- how staff input is protected;
- how to handle people's rights, such as access and deletion;
- a retention schedule;
- whether outputs could be inaccurate or biased, and what human review applies.

It also warns that purely automated decisions can cause harm, and that models can unintentionally reproduce training data.

**Use the Laya Privacy & AI Check** for a first screening. Go to the DPO for:

- a new purpose for existing data;
- a new kind of processing, such as profiling or automated decisions;
- large-scale health data;
- a new supplier, or data leaving the EU;
- children's data.

A **DPIA** (Data Protection Impact Assessment) may be required. The DPO decides.

## People's rights

If a person asks for their data, or to have it corrected or deleted, Laya needs to be able to do that, including where AI was involved. So:

- Know where AI-related data is stored: chats, uploaded files and outputs.
- Agree retention with the DPO **[to confirm]**.
- Be able to explain any AI-assisted decision about a person. See [regulation](07-regulation.md).

## For people who build things

Follow the `member-data-safety` skill. In short:

- **Classify** each field: none, personal or special category.
- **Trace** every place the data goes, including logs, errors, analytics, caches, test fixtures and prompts to an AI model.
- **Check each one:** name your columns, log IDs rather than details, use synthetic test data, encrypt it, set retention, keep a deletion path.
- **Pseudonymise before a prompt leaves Laya's tenant,** and keep the key inside. `technical/platform/src/adlc_pii` has a tested way to do this.
- **Treat logged prompts and responses as personal data.**
- **Suppress groups smaller than 5** in reports.

## Staff data

Using AI on staff data raises its own questions: monitoring, fairness, and what employees were told. Don't use Copilot to analyse individuals. HR and the DPO should agree what staff are told about logging **[to confirm]**.
