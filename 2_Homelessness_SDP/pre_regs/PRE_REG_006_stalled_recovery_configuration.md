# Pre-Registration 006 — Stalled-Recovery Configuration

**ID:** PRE_REG_006
**Locked:** 2026-05-25
**Substrate:** IDP broad-data corpus (D:/IDP/) — PATTERN_013 Bukelization
**Status:** LOCKED — predictions and falsifiers pre-committed; key holdout windows 2026-2028

---

## 1. Hypothesis

**H1 (stalled-recovery configuration):** After a Bukelization episode, recovery is STALLED (rather than durable) when the post-consolidation political configuration includes BOTH:
- **(a)** Captured Constitutional Court / supreme judicial body that survives parliamentary turnover (judges' terms protect them from immediate replacement)
- **(b)** Cohabitation with an old-regime-aligned presidency or veto-equivalent institution

**H2 (mechanism):** The captured court can invalidate restoration legislation while being itself reform-immune. The opposition presidency vetoes legislation that would restructure the court. Together they freeze the institutional capture in place while the post-Bukelization government can only operate AROUND captured institutions, not THROUGH them.

**H3 (predicted observable):** Stalled-recovery countries show an **initial libdem rebound followed by plateau or partial reversal** within 3-5 years of opposition winning parliamentary majority. Durable-recovery countries show **sustained rebound** because their captured institutions either weren't fully captured OR were structurally replaceable (constitutional amendment, fresh court).

---

## 2. In-sample evidence (NOT re-tested)

- **Carnegie Endowment 2025** (US Democratic Backsliding in Comparative Perspective): of 25 backsliding episodes since 1990, only 4 have FULLY recovered, only Sri Lanka >5 years sustained, and even SRI reversed in 2019.
- **Sri Lanka 2015-2019**: Sirisena reformist win 2015 produced ~+0.10 libdem; Rajapaksa returned 2019 and reversed it. Captured judiciary was not replaced.
- **Brazil 2003-2010** (Lula's first restoration era): semi-stalled; some backsliding under later PT.
- **South Korea 1987**: Constitutional amendment + captured court REPLACED. Recovery durable through 2025.
- **Indonesia post-1998**: Suharto resigned; Constitutional Court CREATED FRESH 2003. Recovery durable with some erosion 2010s+.

---

## 3. Pre-locked predictions (holdout — fires 2026-2028 as data arrives)

### Prediction set A — POL (Poland, the live test case)

**Configuration check 2025:**
- Tusk-led reformist coalition holds Sejm (won Oct 2023)
- PiS-captured Constitutional Tribunal still in place (judges with extended terms 2015-2023)
- **Karol Nawrocki (PiS-backed) won Polish presidential election June 2025** → opposition presidency in place
- BOTH stalled-config conditions (a)+(b) satisfied

**Libdem trajectory predictions:**

| V-Dem release | Covers year | POL libdem prediction (stalled-recovery) | POL libdem prediction (durable-recovery) |
|---|---|---|---|
| 2025 (already in v15) | 2024 | 0.613 (actual) | — |
| 2025 (already in v15) | 2025 | 0.645 (actual) | — |
| 2027 (v16) | 2026 | **0.55-0.65 (plateau)** | >0.70 |
| 2028 (v17) | 2027 | **0.50-0.60 (partial reversal)** | >0.70 |
| 2029 (v18) | 2028 | **0.45-0.60 (continued plateau or reversal)** | >0.70 |

**Constitutional Tribunal rulings prediction:**
- By end-2027, Constitutional Tribunal will rule AGAINST ≥3 major Tusk-coalition reform bills (predicted blocked: judicial restructuring, election law revision, media regulation reform)
- If Tribunal yields on ≥2 major rulings → durable-recovery side
- If Tribunal blocks ≥3 major rulings → stalled-recovery confirmed

**2027 parliamentary election prediction:**
- If Tusk coalition wins absolute majority + triggers Constitutional Tribunal restructuring → durable
- If PiS regains parliament → full reversal (libdem back below 0.50 by 2030)
- If Tusk loses majority but coalition holds → stalled-frozen partial recovery

### Prediction set B — BRA (Brazil, the comparison case with INDEPENDENT court)

**Configuration check 2025:**
- Lula PT coalition governing since Jan 2023
- **Brazilian Supreme Federal Tribunal (STF) was NOT captured under Bolsonaro** — independent throughout
- No cohabitation veto (Lula is president, no opposition president)
- BOTH stalled-config conditions FAIL → predicted DURABLE recovery

**Predictions:**
- BRA libdem 2026 (V-Dem v16): ≥0.70 (sustained)
- BRA libdem 2027 (V-Dem v17): ≥0.70 (sustained)
- **IF Bolsonaro returns in 2026 election**: STF independence should still constrain backsliding; predict libdem stays ≥0.55 even under Bolsonaro return, vs POL where it could collapse below 0.50

### Prediction set C — BGD (Bangladesh, the recent recovery case)

**Configuration check 2025:**
- Hasina ousted Aug 2024
- Yunus interim government, transitional
- Awami League-captured judiciary partly intact
- Configuration: captured judiciary present; no clear opposition-presidency (interim regime)
- AMBIGUOUS — stalled-config conditions partially satisfied

**Predictions:**
- BGD libdem 2025 (already in v15): 0.116 (actual — first reversal signal)
- BGD libdem 2026 (V-Dem v16): predict 0.20-0.35 (if institutional reset progresses)
- If Yunus interim leads to free election + judicial reform: durable recovery possible
- If captured judiciary blocks reform + Awami League returns electorally: stalled

### Prediction set D — Sri Lanka 2015-2019 retrospective validation

This is a closed historical case — the model should retro-fit it.

- Sirisena 2015 win configuration: captured judiciary partly intact + opposition president (Rajapaksa lost presidency but Constitutional Council was partial)
- Carnegie 2025 already classifies it as stalled-then-reversed
- **Predicted V-Dem libdem trajectory by our model**: Sri Lanka should show 2015-2018 partial rebound then 2019+ reversal. Pull V-Dem actual to verify.

### Prediction set E — Cross-corpus mass-test (when data arrives)

For any future country that satisfies BOTH stalled-config conditions (captured court + opposition presidency):
- Predict: libdem rebound peaks within 2 years of opposition parliamentary win
- Then plateau or partial reversal
- Net 5-year recovery Δ ≤ +0.10 libdem (vs durable-recovery cases that show Δ ≥ +0.20)

---

## 4. Falsifiers (pre-committed)

- **F1:** POL libdem 2027 ≥ 0.70 (sustained recovery despite stalled config) → mechanism falsified; captured-court-and-opposition-president configuration does NOT prevent recovery
- **F2:** POL Constitutional Tribunal YIELDS on ≥2 of the 3 expected blocking decisions by 2027 → captured-court-immunity assumption falsified
- **F3:** BRA libdem 2027 drops below 0.55 despite STF independence → independent-court-protects-recovery prediction falsified
- **F4:** BGD libdem 2027 jumps to ≥0.40 despite captured judiciary → either Yunus reform unexpectedly potent, or captured-court-blocks-recovery assumption wrong
- **F5:** A NEW country emerges showing durable recovery (>+0.20 sustained 5y) with BOTH stalled-config conditions present → mechanism falsified across cases

Any 2 of {F1, F2, F3, F4, F5} firing = HYPOTHESIS WALKED BACK; logged in patterns/ as such.

---

## 5. Methodology

### Data
- **V-Dem v15-v18** (libdem indicator + sub-indicators) — annual country-year
- **Constitutional Tribunal ruling tracking** (Poland Constitutional Tribunal database, official journal)
- **Polish electoral data** (2027 parliamentary election)
- **Brazilian Federal Tribunal independence indicators** (V-Dem v2juhcind, news monitoring)

### Test procedure (annual at each V-Dem release)
1. Pull V-Dem libdem for POL, BRA, BGD + reference cases (SRI retrospective, KOR durable comparator)
2. Score libdem against stalled-recovery vs durable-recovery prediction bands
3. Cross-check sub-indicators: judicial constraints, high court independence trajectory
4. Track political events: Constitutional Tribunal rulings, election outcomes
5. Update this pre-reg's Results section + cross-link in patterns/

### Decision rules
- **Supported:** POL fits stalled bands 2026-2028 AND BRA fits durable bands AND BGD trajectory matches prediction
- **Partial:** Mixed; refine the captured-court vs opposition-presidency contributions separately
- **Null:** F1 + F2 both fire → walk back the stalled-recovery mechanism

---

## 6. Theoretical hinterland (where this engages with the literature)

- Carnegie Endowment 2025 paper — primary motivating finding
- V-Dem WP #147 (52% reversal rate) — base rate against which stalled-config is the EXCEPTION
- Auer & Schaub 2024 ISQ (mass emigration feedback) — related but separate mechanism; possibly compound effect
- Sato et al. 2022 V-Dem WP #133 (sub-indicator sequencing) — recovery sub-indicator order also matters
- Levitsky & Way 2025 "New Competitive Authoritarianism"

**Novel contribution of this pre-reg:**
1. Operationalizes "stalled recovery" as a TESTABLE configuration (court + presidency) rather than a post-hoc descriptor
2. Pre-locks 3-year V-Dem predictions for live cases (POL, BRA, BGD)
3. Generates a falsifiable durability-prediction model

---

## 7. Cross-references

- [[PATTERN_013]] Bukelization — POL is one of 7 confirmed cases; recovery dynamics are the new wrinkle
- [[PATTERN_022]] BRA libdem recovery — BRA is the parallel-recovery comparator with INDEPENDENT court
- [[PATTERN_024]] POL PiS-era Bukelization — the consolidation that preceded this recovery test
- [[PRE_REG_005]] Bukelization pre-reg — collapse-side; this pre-reg is the recovery-side counterpart
- [[stalled_recovery_watch.md]] living tracker for events

---

## 8. Provenance

Locked 2026-05-25 (late session), substrate D:/IDP/, post-deep-extraction + lit-synthesis. Substrate motivation: Carnegie 2025 finding that only 4 of 25 backsliding episodes since 1990 have fully recovered. The POL configuration (captured Tribunal + Nawrocki presidency) was identified as the live test in real-time during the literature synthesis.

This pre-reg formalizes a hypothesis derived from literature + corpus observation, with predictions locked BEFORE the 2026-2028 V-Dem release window unfolds.

---

## 9. Standing forward-watch (will be updated annually)

| Date | Event | What it signals | Result (TBD) |
|---|---|---|---|
| Mar 2026 | V-Dem v16 release (covers 2025) | POL hold/reverse | TBD |
| Mid-2026 | Constitutional Tribunal first reform rulings | First test | TBD |
| Mar 2027 | V-Dem v17 release (covers 2026) | Year-2 stall signal | TBD |
| Autumn 2027 | Polish parliamentary election | Coalition durability | TBD |
| Mar 2028 | V-Dem v18 release (covers 2027) | Multi-year stall signal | TBD |
| 2028+ | BRA 2026 election outcome + STF behavior | Comparison case durability | TBD |
