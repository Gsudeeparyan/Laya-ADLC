# Laya glossary

The shared language for Laya's agents, skills and code. Use these terms the same way in prompts, documents, code, tests and tickets. Format follows Matt Pocock's `GLOSSARY.md` convention: the term, what it means, and the words to avoid.

**Single source of truth.** Three things copy from this file, so update them when a term changes:
- the staff agents' preamble (the five everyday words)
- Laya Comms Writer's plain-English swaps
- each Laya repo's `GLOSSARY.md`, copied by `technical/harness/install_harness.py`

Items marked **[to confirm]** need checking by the business owner before they are relied on.

## People and policies

**Member**:
A person covered by a Laya health insurance policy.
_Avoid_: customer (when you mean a covered person), patient, client, insured

**Policyholder**:
The person, or the employer for a group scheme, who holds the policy and pays the premium. A policyholder is usually also a member.
_Avoid_: customer, account holder, payer

**Dependant**:
A member covered under someone else's policy, such as a partner or child.

**Plan**:
The set of benefits a member is covered for. **[to confirm]** whether Laya's customer-facing word is "plan", "scheme" or "product" in each channel.
_Avoid_: package, tier

**Group scheme**:
Cover arranged and usually paid for by an employer for its staff. **[to confirm]** Laya's internal term (corporate scheme / company scheme).

**Broker**:
An intermediary who sells or arranges policies on a policyholder's behalf.

## Cover and claims

**Benefit**:
Something a plan pays for, in full or in part.

**Premium**:
The price of cover, paid yearly or in instalments.

**Excess**:
The part of a bill the member pays themselves before Laya pays the rest.

**Claim**:
A request for Laya to pay for treatment, made by the member or directly by the provider.
_Avoid_: case (unless you mean a complaint or service case)

**Provider**:
A hospital, clinic, consultant or practitioner who treats members.

**In-patient**:
Treatment where the member stays in hospital overnight.

**Day case**:
Treatment where the member is admitted and goes home the same day.

**Outpatient**:
Care without a hospital admission: GP, consultant visits, physiotherapy and similar. Often called day-to-day benefits.

**Waiting period**:
The time after joining or upgrading before a member can claim for certain things.

**Pre-existing condition**:
A condition the member had signs or symptoms of before they joined.

**Renewal**:
The date a policy rolls over for another term, when price and benefits can change.

## The Irish market

**Community rating**:
The principle that people pay the same price for the same plan regardless of their health, with set exceptions.

**Lifetime Community Rating (LCR) loading**:
An extra charge on the premium for people who first take out health insurance aged 35 or over.

**Open enrolment**:
The principle that insurers must accept anyone who applies, subject to the rules.

**Health Insurance Authority (HIA)**:
The regulator of the Irish private health insurance market.

**Central Bank of Ireland**:
Regulates how insurers treat customers, including the Consumer Protection Code. **[to confirm]** current complaint-handling timelines with Compliance before any agent or code relies on them.

**Data Protection Commission (DPC)**:
Ireland's data protection regulator under the GDPR.

## Personal data

**Personal data**:
Any information about an identifiable person.

**Special category data**:
Personal data needing extra protection under the GDPR. At Laya this is mainly health information: diagnosis, condition, treatment, medication.

**PPSN**:
Personal Public Service Number. 7 digits plus 1 or 2 letters, with a check letter.

**Eircode**:
The Irish postcode, such as D02 X285. The first three characters are the routing key.

**Token**:
A stand-in value such as PERSON_001 that replaces a real value consistently, so AI can work on the data without seeing it.

**Pseudonymised**:
Real values are replaced with tokens and can be put back with a key file. It is still personal data under the GDPR.
_Avoid_: anonymised (when a key exists)

**Anonymised**:
Identifiers are removed for good and the remaining data is generalised, so that no one can be picked out. No key exists.

**Key file**:
The private file (`<name>.pii-vault.json`) mapping tokens back to real values.
_Avoid_: vault (in staff-facing text; fine in code)

**DPO**:
Laya's Data Protection Officer. Advises on and approves uses of personal data.

**DPIA**:
Data Protection Impact Assessment, required before high-risk uses of personal data.

## ADLC terms

**AI-safe workbook**:
An Excel workbook that carries its own structure: a hidden `_ADLC` sheet (the spec), a README and a Change Log.
_Avoid_: smart workbook, ADLC file

**`_ADLC` sheet**:
The hidden sheet holding the workbook's spec, version and integrity hash.

**Change Log**:
The `tblChangeLog` table recording every change: when it was made, who asked, and what changed.

**ADLC Record**:
The status line at the end of an ADLC document: Document | Version | Status | Owner | Last updated | Decisions so far | Open questions | Next step. It is the document's memory between chats.

**Clean copy**:
A pseudonymised copy of a file, safe to use with any AI tool, with a key file.

**Agent**:
A Microsoft 365 Copilot agent built from one skill plus the shared preamble.
_Avoid_: bot, assistant

**Skill**:
A `SKILL.md` in the Agent Skills format: the instructions an agent or coding tool loads for one job.

## Relationships

- A **Policyholder** holds one or more policies; each policy covers one or more **Members**. A **Dependant** is a member who is not the policyholder.
- A **Member** is covered by one **Plan** at a time; the plan defines its **Benefits**, **Excess** and **Waiting periods**.
- A **Claim** belongs to one **Member** and one **Provider**.
- A **Clean copy** pairs with exactly one **Key file**.

## Flagged ambiguities

- "Customer" is used for both members and policyholders. Resolved: say **member** for the covered person and **policyholder** for the payer. Use "customer" only when quoting another system.
- "Anonymised" is often used for data that still has a key. Resolved: that data is **pseudonymised**.
