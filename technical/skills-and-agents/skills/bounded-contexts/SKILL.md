---
name: bounded-contexts
description: Draw the boundaries between Laya's business areas and translate across them. Use when a change spans several business areas or systems (membership, sales, claims, providers, billing, pricing, complaints, group schemes, brokers), when one word means different things in different systems, or when designing an integration with a vendor or another team's system.
license: Proprietary - Laya Healthcare internal use
---

# Bounded Contexts

A **bounded context** is the area inside which a model, and its words, mean exactly one thing. "Member" in a membership system (who is covered, from when) is not "member" in a claims system (who was treated, under which plan). Sharing one class for both is how integrations rot. Full rule set (Vaughn Vernon, _Domain-Driven Design Distilled_): [RULES.md](RULES.md).

The language inside a context lives in its `GLOSSARY.md`. Sharpening that language is Matt Pocock's `domain-modeling` skill; this skill is about the **boundaries between** contexts.

## Steps

1. **Name the contexts** the change touches, and for each one its owning team and system. Done when every system the data passes through has a context name and an owner. Laya's likely candidates, to be confirmed with the teams **[to confirm]**:
   - membership and policy administration
   - sales and quotes
   - claims
   - provider network
   - billing and payments
   - pricing and underwriting
   - complaints and customer service
   - group schemes and brokers
   - data and analytics
2. **Classify each subdomain.** **Core** gives Laya its edge and gets the most modelling effort. **Supporting** is needed but not differentiating. **Generic** is bought or kept simple. Ask the user which is which rather than assuming.
3. **Map the relationships.** For each pair of contexts that integrate, pick the relationship deliberately:
   - **Customer/Supplier**: one team plans for the other's needs.
   - **Conformist**: we accept their model as-is.
   - **Anticorruption Layer**: we translate their model into ours, usually right for vendor and legacy systems.
   - **Open Host Service / Published Language**: we publish a stable contract for many consumers.
   - **Separate Ways**: no integration.
4. **Translate at the boundary.** Each term that crosses gets an explicit mapping in one place, with tests. Domain classes stay inside their own context.
5. **Spend modelling only where it pays.** Aggregates, value objects and domain events go into the Core, where invariants justify them. Supporting and Generic areas stay simple CRUD unless their own complexity says otherwise.

Done when every context is named with an owner, every integration has a chosen relationship, and every term that crosses a boundary has a tested translation. New or changed terms go into the right `GLOSSARY.md`: read and follow the `domain-modeling` skill (`../domain-modeling/SKILL.md`).
