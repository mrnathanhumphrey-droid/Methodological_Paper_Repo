# Pre-Registration v1.0 — Evidence Discipline for the Solar Substrate

**Locked at commit:** `fc32be4` on `main`.
**Status:** First lock. All downstream work in D:/Renewables/Solar/ inherits these rules.
**Scope:** This is a META pre-reg. It does NOT lock a scientific hypothesis. It locks the DISCIPLINE under which scientific hypotheses get pre-registered, evidence is admitted, and claims are labeled.

Per user direction 2026-05-27: *"pre reg everything. all that stuff was nonsense underneath. it was all code. reask"*. The v0 landscape doc (`00_LANDSCAPE_v0.md`) contained confident-sounding numeric claims with no primary citations — exactly the failure mode that pre-reg discipline is designed to prevent. This pre-reg fixes the loophole at the source.

---

## 0. What this pre-reg LOCKS

1. The definition of a **primary source** (admission list in §1).
2. The definition of what is **NOT** a primary source (§2).
3. The **verification protocol** that turns a NEEDS-VERIFICATION claim into a VERIFIED claim (§3).
4. The five **knowledge state labels** (§4) that every claim in this substrate carries.
5. The treatment of `00_LANDSCAPE_v0.md` (§5): every numeric claim moves to NEEDS-VERIFICATION pool effective immediately.
6. The **citation format** (§6).
7. **Conflict + disagreement resolution** (§7).
8. **Anti-LLM provisions** (§8): explicit ban on LLM outputs as primary evidence; LLM-written text inherits NEEDS-VERIFICATION on every numeric claim.
9. **Deviation log** structure (§9).
10. **Amendment process** (§10).

What this pre-reg does NOT lock:
- Specific scientific hypotheses about solar panels (those come in subsequent pre-regs, each numbered).
- Lab spec details (that's a downstream pre-reg).
- Specific experiments (downstream).
- Funding / personnel / IP structure (out of scope for evidence discipline).

---

## 1. Primary sources — admission list (LOCKED)

A claim is supported by a **primary source** only if the source belongs to one of these categories:

- **Peer-reviewed journals:** Progress in Photovoltaics, IEEE Journal of Photovoltaics, Solar Energy Materials and Solar Cells, Solar Energy, Renewable Energy, Journal of Applied Physics (for cell physics), Nature / Nature Energy / Nature Photonics, Joule, ACS Energy Letters. Other journals admissible if peer-reviewed with stated review process.
- **National lab technical reports:** NREL (publications.nrel.gov), Fraunhofer ISE, Sandia, Argonne, LBNL. Must be a published technical report with a report number or DOI; conference proceedings count if archived.
- **International standards body publications:** IEC (61215, 61730, 60904, 62804, 62788, etc.), IEEE (1547, 929, 1262, etc.), UL (1703, 61730), ISO (where applicable). Standards version + revision year must be cited.
- **Government program reports:** DOE / SETO, EU Horizon programs, IEA-PVPS Task series (Task 13 reliability, Task 16 forecasting, etc.).
- **Manufacturer technical specifications:** Datasheets, IEC 61853 power-rating reports, performance test certificates — ONLY when cited as evidence of a SPECIFIC PRODUCT'S claimed spec, NOT as evidence of generic product-class behavior. Model + revision + date required.
- **Field-monitoring databases with documented methodology:** NREL PVDAQ, NSRDB, Sandia PV systems database, IEA-PVPS field surveys. Citation must include access date + dataset version.
- **Pre-print servers (arXiv, etc.):** Admissible ONLY for claims that would be peer-reviewable; flag as PREPRINT in the citation; downgrade verdict to TENTATIVELY-VERIFIED until peer-reviewed version is found.

Default citation requirement: author(s), year, title, outlet, DOI or report number, page/section, retrieval date (see §6).

---

## 2. NOT primary sources (LOCKED)

These categories are **not citable as evidence** of fact in this substrate:

- **LLM outputs** — Claude, GPT, Gemini, Llama, any generative model. See §8 for full provisions.
- **Wikipedia** — admissible as an ENTRY POINT to find primary sources; the Wikipedia article itself is not citable.
- **Blog posts, Medium articles, Substack** — not citable. May surface a primary source that becomes citable.
- **Industry press releases** — citable ONLY as evidence of "Company X claimed Y on date Z" (a sociological fact), NEVER as evidence that Y is true.
- **Reddit, forums, Twitter/X, YouTube** — never citable.
- **Marketing materials from solar vendors** — same as press releases: documentation of claim, not evidence of fact.
- **Trade press articles** (PV Magazine, pv-tech.org, GreentechMedia, etc.) — admissible only when they cite a primary source we can independently retrieve; the trade-press article itself is not citable.
- **Personal communication / interviews** — only if logged with date, person, position, contact and explicitly flagged as PERSONAL-COMMUNICATION; never as standalone evidence for a quantitative claim.

When a non-citable source surfaces a claim, the workflow is: follow the trail to the primary source, retrieve it, cite the primary. If no primary source can be reached, the claim stays in NEEDS-VERIFICATION.

---

## 3. Verification protocol (LOCKED)

For every numeric or factual claim that enters the substrate:

1. **Locate** the primary source(s) supporting the claim. If none found in 30 minutes of reasonable search effort, log the claim as NEEDS-VERIFICATION and move on.
2. **Retrieve** the primary source (PDF, dataset, standard text).
3. **Check** the claim against the source: does the source explicitly state the claim, with the same scope/qualifiers? Note the page/section/figure where the claim appears.
4. **Log** the verification in `02_CLAIMS_LEDGER.md`: claim text, citation, page/section reference, scope of the claim (population/condition the claim covers), retrieval date, verifier (initials or session ID).
5. **Assign verdict** per §4.
6. **If multiple sources** support the claim, log all of them. If they disagree, default verdict is INDETERMINATE (§7).

Verification effort budget: **30 minutes per claim** as the soft default. Claims requiring more than 30 min stay NEEDS-VERIFICATION until a dedicated deep-dive session. This bounds the time cost and prevents rabbit-holing.

---

## 4. Knowledge state labels (LOCKED)

Every numeric or factual claim in this substrate carries exactly one of these labels:

| Label | Definition |
|---|---|
| **VERIFIED** | ≥1 primary source retrieved + checked + cited per §3. Sample/scope qualifier present. |
| **TENTATIVELY-VERIFIED** | Secondary source (review article, summary) only, OR preprint only; primary not yet retrieved. |
| **NEEDS-VERIFICATION** | Hypothesis pool. Claim exists; primary source not yet found. Default for new claims. |
| **REFUTED** | Primary source(s) contradict the claim. Original claim text retained for audit. |
| **INDETERMINATE** | Sources disagree, OR insufficient data exists in the field. Specific reason logged. |

Labels are **assigned at the claim level**, not the document level. A single document can contain claims at multiple labels.

A claim can be **demoted** from VERIFIED back to NEEDS-VERIFICATION if (a) the cited source is later retracted, (b) the citation is found to mis-state the source, or (c) a newer primary source supersedes the original with conflicting evidence. Demotion requires a §10 deviation entry.

---

## 5. v0 landscape doc handling (LOCKED)

Effective at commit of this pre-reg:

- `00_LANDSCAPE_v0.md` is **demoted in entirety**. Every numeric claim in it is labeled NEEDS-VERIFICATION.
- A **banner** is added to the top of `00_LANDSCAPE_v0.md` stating this explicitly.
- A new ledger `02_CLAIMS_LEDGER.md` is created listing every numeric claim from the v0 doc with NEEDS-VERIFICATION status.
- Subsequent verification passes (v0.1, v0.2, ...) move individual claims out of NEEDS-VERIFICATION as primary sources are retrieved and checked.
- `00_LANDSCAPE_v0.md` is NOT deleted. It remains as a record of the LLM's initial hypothesis pool that the substrate is now systematically replacing with verified knowledge.

Any document written BEFORE this pre-reg commit follows the same rule: numeric claims are NEEDS-VERIFICATION until processed through §3.

---

## 6. Citation format (LOCKED)

```
Author(s), Year. "Title." Outlet, vol/issue. DOI or URL. Page/section. Retrieved YYYY-MM-DD.
```

Example (verified-format):
```
Jordan, D.C., Kurtz, S.R., 2013. "Photovoltaic Degradation Rates—an Analytical Review."
Progress in Photovoltaics, 21(1), 12-29. DOI: 10.1002/pip.1182. p.18 Fig.3. Retrieved 2026-05-27.
```

Standards example:
```
IEC, 2021. IEC 61215-1:2021, "Terrestrial photovoltaic (PV) modules — Design qualification
and type approval — Part 1: Test requirements." Edition 2.0. Section 11.10 damp-heat test.
Retrieved 2026-05-27.
```

The retrieval date is REQUIRED so downstream verification can re-check the source version.

---

## 7. Conflict + disagreement resolution (LOCKED)

When two primary sources support different values or directions for the same claim:

1. Log both with full citations.
2. Default verdict: **INDETERMINATE** with both citations.
3. **Tiebreakers, in order:**
   a. A peer-reviewed systematic review or meta-analysis covering both sources → defer to it.
   b. A newer, larger-sample primary source → tentatively prefer; log both.
   c. If the disagreement is about a population-level number vs a site-specific number, log both with their scope qualifiers; this is not a true conflict.
   d. If still unresolvable: stays INDETERMINATE; logged as an OPEN QUESTION for the lab to address.
4. Open questions become candidate hypotheses for future scientific pre-regs (see §10 amendment process for downstream pre-reg numbering).

A claim is NEVER marked VERIFIED when sources disagree without a tiebreaker being applied. Mid-disagreement claims live in INDETERMINATE.

---

## 8. Anti-LLM provisions (LOCKED) — load-bearing

**LLM outputs are explicitly disallowed as primary or secondary evidence.** This includes:

- Claude (any version), GPT-x, Gemini, Llama, Mistral, any other generative model.
- LLM-aggregated "consensus" summaries.
- LLM-translated or LLM-summarized primary sources where the LLM summary is what's cited.

Operational rules:

- **Any document an LLM writes in this substrate inherits NEEDS-VERIFICATION on every numeric and factual claim.** Including this pre-reg's §1 admission list categories, IF those category names came from LLM training data and are themselves debatable. (They are reasonable but not infallible.)
- **LLM-stated numbers are TIPS to verify, never verifications themselves.** A Claude statement of "Si modules degrade at 0.5%/yr" is a hypothesis to check, not a fact.
- **LLM citations are LEADS, not verifications.** If Claude says "Jordan & Kurtz 2013 reports X," the operator must independently retrieve Jordan & Kurtz 2013 and confirm X is stated there. LLMs hallucinate citations.
- **Bibliographic claims from LLMs require double-verification:** confirm both (a) the source exists at the cited venue and (b) the claim appears in the source. LLM-fabricated citations to real authors are a documented failure mode.
- **For any document Claude (or any LLM) writes in this substrate, the operator runs through §3 verification on every numeric claim before the doc moves out of NEEDS-VERIFICATION status.**

This pre-reg's own content is subject to the same rules: §1 admission list of journals, §3 30-minute budget — these are *defaults proposed by Claude* and themselves require independent operator endorsement before they harden. The pre-reg locks the PROCESS; the operator (human) holds the final say on the categories.

---

## 9. Deviation log

Format: same as Battery + DNC pre-reg deviation logs.

| Date | Deviation | Rationale |
|---|---|---|

(Empty at lock. Entries added as edge cases surface.)

---

## 10. Amendment process (LOCKED)

This pre-reg is a **living document with versioned amendments**:

- Amendments are filed as `01_METAPREREG_v1.X_amendment_YYYY-MM-DD.md` in literature/.
- Each amendment requires a §9 deviation entry explaining the trigger and the revision.
- v1.0 is locked at the commit referenced in the header; subsequent versions cite their amendment commits.

Downstream scientific pre-regs follow their own numbering:
- `03_PREREG_v1.0_<topic>.md`, `04_PREREG_v1.0_<topic>.md`, etc.
- Each scientific pre-reg cites this meta-pre-reg as its discipline foundation.
- Each scientific pre-reg has its own §-deviation log scoped to that pre-reg.

---

## 11. Operational immediate next steps (LOCKED order)

1. Commit this meta-pre-reg.
2. Add the banner to `00_LANDSCAPE_v0.md` demoting all claims to NEEDS-VERIFICATION.
3. Create `02_CLAIMS_LEDGER.md` listing every numeric claim from `00_LANDSCAPE_v0.md` with NEEDS-VERIFICATION status, awaiting verification passes.
4. Update `D:/Renewables/Solar/README.md` to reflect the new discipline.
5. User direction selects the FIRST scientific pre-reg topic (the v0 landscape's 3 axes — degradation, reliability, siting — are candidates) and the FIRST claim from the ledger to verify.

No additional content claims may be added to this substrate without entering through `02_CLAIMS_LEDGER.md` with at minimum a NEEDS-VERIFICATION label.

---

**Locked at commit:** `fc32be4` on `main` of `D:/Renewables/`.
**Repository scope:** D:/Renewables/Solar/.
**Author of v1.0 draft:** Claude (LLM) under §8 — every claim in this document is itself subject to §3 verification when the operator endorses or amends.
