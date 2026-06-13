# 39 — Probe 12: V2 inverter-swap confound check — V2 NOT confounded

**Status:** Falsification check on V2's K=12-13 "operational" claim against publicly-known DKA inverter operations. Triggered by the DKA Notes-on-Data page (https://dkasolarcentre.com.au/download/notes-on-the-data) listing 4 specific operational events 2022-2024.
**Date:** 2026-05-31
**Substrate:** D:/Renewables/Solar/

---

## 1. Known operational events from DKA public docs

| Date | Event |
|---|---|
| 2023-02-03 | SMA Site 21 inverter replaced with Fronius (per-system) |
| 2023-01-24 | DKASC offline ~08:00 — network shutdown (site-wide) |
| 2022-12-15 | Original SMA inverters replaced (batch swap, multiple systems) |
| 2022-06-01 | Site 10 + 12 intermittent inverter issues (per-system) |

Inverter swaps cause sudden power-step changes that SRR could detect as recovery events. If V2's K=12-13 "operational" claims overlap these dates, the operational interpretation is contaminated.

---

## 2. Results

### 2.1 Per-event window (±7 days)

| Known event | K≥11 nearby | K≥12 nearby | K≥13 nearby | Random expectation |
|---|---|---|---|---|
| 2023-02-03 SMA → Fronius | 2 (both K=11) | 0 | 0 | 0.18 |
| 2023-01-24 network shutdown | 2 (both K=11) | 0 | 0 | 0.18 |
| 2022-12-15 SMA batch | 0 | 0 | 0 | 0.18 |
| 2022-06-01 Site 10/12 | 1 (K=11) | 0 | 0 | 0.18 |

**0 of 42 K=13 events fall within ±7 days of any known operational date.**
**0 of 51 K=12 events fall within ±7 days of any known operational date.**

Expected by chance (4 events × 15-day windows / 6190 substrate days): 1.0%. Observed: 0%. K=12-13 events do **not** cluster near publicly-known inverter operations.

### 2.2 2022-2023 confound period concentration

If K=12-13 events were driven by 2022-2023 inverter operations, that period should be over-represented.

| | Observed in 2022-2023 | Uniform expectation | Verdict |
|---|---|---|---|
| K≥11 (n=76) | 13.2% | 11.8% | Roughly uniform |
| K≥12 (n=51) | 5.9% | 11.8% | **Under**-represented |
| K≥13 (n=42) | 0.0% | 11.8% | **Strongly under**-represented |

K=13 events show ZERO events in the 2022-2023 confound period vs ~5 expected. Strong evidence that K=13 is NOT driven by inverter swaps.

---

## 3. Unexpected finding — 2019 concentration

Year-by-year K=13 event distribution:

```
2009-2015:  0 events
2016: 0  | 2017: 0  | 2018: 0
2019: 36 ← 86% of all 17-year K=13 events
2020: 0  | 2021: 6  | 2022: 0  | 2023: 0
2024: 0  | 2025: 0
```

**36 of 42 K=13 events fall in 2019.** This is a striking concentration that suggests one of:

- (a) A specific 2019 cleaning campaign at DKA (multiple cleanings clustered that year)
- (b) A 2019 weather event (e.g., big dust storms followed by cleanings)
- (c) A 2019 sensor recalibration or methodology change at DKA that affected all systems simultaneously
- (d) A pre-2018 issue where SRR couldn't detect events on earlier data (the 2018-2023 window is the substrate's Probe-2 NSRDB coverage)

The 2018-2025 distribution under (d) doesn't quite work — there are K=13 events in 2021 (n=6) and 2018 (n=0), so the 2019 spike isn't just a methodology artifact.

**This should be flagged for the DKA operator email** (pending reply). The 2019 concentration is the substrate's most informative outstanding question.

---

## 4. Verdict

- **V2's operational claim is NOT confounded by inverter swaps.** 0/42 K=13 events near any known operational date; 0% of K=13 events in 2022-2023 confound period.
- **V2 strengthens.** The publicly-noted inverter operations don't explain the high-K consensus events — these are a separate class of event (presumably annual cleanings or similar).
- **2019 anomaly is new outstanding question.** 86% of K=13 events fall in 2019; needs operator clarification.

---

## 5. CLM update

- **CLM-112 NEW:** V2 K=12-13 events not explained by publicly-known DKA inverter operations (0/42 K=13 within ±7d of any known op event). 2019 concentration of K=13 events (36/42) is unexplained and pending operator clarification

---

## 6. Artifacts

- `code/probe12_v2_inverter_swap_confound.py`
- `data/processed/probe12_inverter_swap_check.csv`

---

**END Probe 12** — V2 operational claim survives the inverter-swap confound check cleanly. 2019 concentration (86% of K=13 events) is the substrate's most informative outstanding question; flagged for operator follow-up.
