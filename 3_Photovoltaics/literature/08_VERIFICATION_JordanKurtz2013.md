# Verification: Jordan & Kurtz 2013

**Target citation under review:**
Jordan, D.C., Kurtz, S.R., 2013. "Photovoltaic Degradation Rates — an Analytical Review." *Progress in Photovoltaics: Research and Applications*, 21(1), 12-29. DOI: 10.1002/pip.1182.

**Date of verification:** 2026-05-27.
**Verifier access level:** WebFetch DENIED by harness for Wiley, NREL docs (docs.nrel.gov), OSTI, UNT digital library, ResearchGate, and research-hub.nrel.gov. Bash `curl` and PowerShell `Invoke-WebRequest` also denied for the same hosts. **Verification is therefore limited to DOI-redirect metadata + WebSearch result snippets.** No primary full-text was read.

## DOI resolution

- **VERIFIED.** `https://doi.org/10.1002/pip.1182` issued a 302 redirect to `https://onlinelibrary.wiley.com/doi/10.1002/pip.1182`. The DOI resolves to a live Wiley Online Library record. The Wiley landing page itself could not be fetched (permission denied), but WebSearch returned the Wiley page title verbatim: *"Photovoltaic Degradation Rates—an Analytical Review - Jordan - 2013 - Progress in Photovoltaics: Research and Applications - Wiley Online Library."*
- Authors, journal, year, volume, page range as listed in independent third-party reference snippets (SciRP, ScispaceAI, research-hub.nrel.gov, OSTI.gov bibliographic listings): **Jordan, D.C.; Kurtz, S.R.; 2013; Progress in Photovoltaics: Research and Applications; vol. 21; pp. 12-29.** Issue "(1)" is consistent with vol. 21 pp. 12-29 (issue 1 is the standard early-year issue). All metadata fields **MATCH** the citation as written in our landscape docs.

## Access

- **Paywalled at publisher (Wiley).** WebSearch identified at least four candidate open / preprint surfaces that I was unable to retrieve under current harness permissions:
  1. NREL preprint candidates: `docs.nrel.gov/docs/fy12osti/51664.pdf` and `docs.nrel.gov/docs/fy12osti/53712.pdf` (the latter's known title is "Photovoltaic Degradation Risk" — likely a sibling paper, not this one).
  2. OSTI bibliographic record: `osti.gov/biblio/1073525` ("Photovoltaic Degradation Rates — An Analytical Review") and `osti.gov/biblio/1045052`.
  3. UNT Digital Library: `digital.library.unt.edu/ark:/67531/metadc829954/` (32-page record — likely the full NREL preprint).
  4. ResearchGate publication page 230551090.
- Recommend re-running this verification with WebFetch permitted for `docs.nrel.gov`, `osti.gov`, and `digital.library.unt.edu`, or with `curl`/`Invoke-WebRequest` to those hosts allowed.

## Per-claim verdicts

- **C1: "Median c-Si module degradation rate in the field is ~0.5%/yr"** — **PARTIALLY VERIFIED FROM SNIPPETS.** Multiple search-result snippets attribute to this paper: *"nearly 2000 degradation rates, measured on individual modules or entire systems, have been assembled from the literature, showing a median value of 0.5%/year."* This **0.5%/yr is the overall (all-technology) median**, not c-Si specifically, in the snippet wording I could see. The c-Si-specific median was not isolated in any snippet. Source location in paper: NOT VERIFIED. **Caveat: our landscape ledger phrases this as "c-Si," which the snippet evidence does not directly support — the paper's 0.5%/yr appears to be the aggregate.**
- **C2: "Mean c-Si degradation rate is ~0.8-0.9%/yr"** — **CAN'T-VERIFY-FROM-ACCESS-LEVEL.** One search snippet returned the range "median 0.5-0.6 %/yr, mean 0.8-0.9 %/yr for x-Si" but the snippet attributed that range to **Jordan et al. 2016 "Compendium of photovoltaic degradation rates"** (DOI 10.1002/pip.2744), *not* the 2013 paper. This is a likely **MIS-ATTRIBUTION in our landscape ledger** — the 0.8-0.9%/yr mean for c-Si may belong to the 2016 *Compendium*, not the 2013 *Analytical Review*. Flag for re-check against the 2013 PDF.
- **C3: "Distribution is long-tailed"** — **CAN'T-VERIFY-FROM-ACCESS-LEVEL.** No snippet retrieved explicit "long-tailed" / "log-normal" / "skewed" language for the 2013 paper. Plausible but not confirmed from accessible sources.
- **C4: "Thin-film modules degrade at ~0.8-1.0%/yr median"** — **CAN'T-VERIFY-FROM-ACCESS-LEVEL.** No snippet returned thin-film (a-Si / CdTe / CIGS) breakdowns from the 2013 paper specifically. WebSearch directed thin-film questions toward the 2016 *Compendium* and a 2022 review.
- **C5: "Field median outperforms manufacturer warranty"** — **WEAKLY-INDICATED, NOT VERIFIED.** One snippet states the paper "discusses warranty considerations in relation to degradation risk analysis" and notes manufacturers "guarantee a maximum loss of about 20% of power after 25 years." That is ~0.8%/yr warranty implied vs. 0.5%/yr observed median, consistent with the claim, but no verbatim "outperforms warranty" sentence was retrieved.
- **C6: N of studies / datapoints reviewed** — **PARTIALLY VERIFIED.** Snippet: "**nearly 2000 degradation rates**, measured on individual modules or entire systems, have been assembled from the literature." So N ≈ 2000 individual rates (not 2000 studies). Number of source studies/papers reviewed: NOT VERIFIED. *(Contrast: 2016 Compendium snippet reported >11,000 rates from ~200 studies in 40 countries — useful distinguishing fingerprint.)*
- **C7: Geographic / climate scope** — **CAN'T-VERIFY-FROM-ACCESS-LEVEL.** Snippets describe scope as "field testing throughout the last 40 years" but do not enumerate countries or climate zones for the 2013 paper.

## Datasets referenced

- **CAN'T-VERIFY-FROM-ACCESS-LEVEL.** Not extractable from snippets. Paper structure described as "three parts: a brief historical outline, an analytical summary of degradation rates, and a detailed bibliography partitioned by technology" — the bibliography is the dataset surrogate. No external public dataset was identified in any snippet I could see.

## Follow-up citations worth verifying next

1. **Jordan, Kurtz, VanSant, Newmiller, 2016. "Compendium of photovoltaic degradation rates." *Prog. Photovolt.* 24(7), 978-989. DOI: 10.1002/pip.2744.** — The direct successor; likely the actual source of the "mean 0.8-0.9 %/yr" c-Si number our ledger attributes to 2013. **HIGH PRIORITY.**
2. **Jordan, Silverman, Wohlgemuth, Kurtz, VanSant, 2017. "PV degradation curves: non-linearities and failure modes." *Prog. Photovolt.* DOI: 10.1002/pip.2835.** — Already in our ledger; succeeds 2013/2016 and treats non-linear and accelerated-climate cases.
3. **Jordan, Deline, Kurtz et al., 2018. "Robust PV Degradation Methodology and Application." *IEEE J. Photovoltaics.* DOI: 10.1109/JPHOTOV.2017.2779779.** — Already in our ledger.
4. **Jordan et al., 2020/2022 PV Fleet Performance Data Initiative paper(s).** Currently UNVERIFIED-LEAD in our ledger; canonical 100,000-system follow-on.

## Notes / disagreements with our attribution

1. **C1 wording slip:** our ledger row 53 says median **c-Si** ≈ 0.5-0.8 %/yr citing Jordan & Kurtz 2013. The 2013 abstract-snippet evidence supports only **all-technology** median ≈ 0.5 %/yr from this paper. The c-Si-specific cut may exist inside the paper but is not what the 0.5 %/yr headline refers to. **Recommend tightening to "all-technology median ≈ 0.5 %/yr" when re-citing 2013.**
2. **C2 likely mis-attribution:** the "mean 0.8-0.9 %/yr for c-Si" range appears in snippet evidence to come from the **2016 Compendium (DOI 10.1002/pip.2744)**, not 2013. **Recommend re-attributing C2 to Jordan et al. 2016** pending full-text confirmation of both papers.
3. **N value:** N ≈ 2000 *rates* (not studies) in 2013; N > 11,000 *rates* from ~200 *studies* across 40 countries in 2016. Use the right N for the right paper.
4. **Access limitation is the binding constraint here.** Six of seven claims are CAN'T-VERIFY or only partially verified because I could not read the full PDF. The DOI itself, the metadata, the headline number (0.5 %/yr, ~2000 rates), and the paper's three-part structure are the only items I can confirm. **Re-run with PDF host access enabled to close C3, C4, C5, C7, and the dataset/follow-up questions properly.**
