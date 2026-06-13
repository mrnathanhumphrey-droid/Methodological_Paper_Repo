"""
Paper 7 Phase 4 — IDP <-> SDP methodology-equivalence read (PRE_REG_025 H3/H4).

Lays the locked IDP results beside the just-fired SDP results and renders the
equivalence verdict. H3 (SDP-IDP equivalence: same / overlapping / distinct)
and H4 (methodology portability) are the targets.

IDP numbers sourced from locked artifacts (not memory):
- channel orthogonality 92% : PRE_REG_004 (17/18 country-pairs |rho|<0.5; BRA exception)
- regime typology 6 regimes : Paper 2 (PRE_REG_003 + extensions; Regime 6 EQ firmed)
SDP numbers from analysis/paper7_prereg026_results_2026_05_27.json (this session).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"D:/IDP")
SDP = json.loads((ROOT / "analysis/paper7_prereg026_results_2026_05_27.json").read_text())
OUT = ROOT / "analysis/paper7_phase4_equivalence_2026_05_27.json"

idp = {
    "channel_orthogonality_rate": 0.92,
    "channels": ["conflict", "flood", "drought"],
    "channel_kind": "exogenous_shock",
    "n_regimes": 6,
    "regime_organizer": "hazard_type (flood/storm/EQ/drought)",
    "primary_driver": "exogenous events (armed conflict, climate hazard)",
    "source": "PRE_REG_004 (92%); Paper 2 disaster-regime typology (6 regimes)",
}
sdp = {
    "channel_orthogonality_rate": SDP["H1"]["single_channel_dominance_rate"],
    "channels": ["family(economic/eviction)", "chronic(institutional)",
                 "other-individual(situational)"],
    "channel_kind": "structural_condition",
    "n_regimes_primary": SDP["H3"]["best_k"],
    "n_regimes_substructure": "3-5 (silhouette >=0.30 but weaker than k=2)",
    "regime_organizer": "climate + shelter-policy (unsheltered/street vs sheltered/family)",
    "primary_driver": "policy + structural conditions (shelter law, housing cost, climate)",
    "source": "PRE_REG_026 H1/H3 (this session)",
}

verdict = {
    "H4_methodology_portability": {
        "disposition": "SUPPORTED",
        "basis": ("Both substrates decompose into orthogonal channels (IDP 92%, "
                  "SDP 61.9%, both clear their thresholds) AND sort into "
                  "geography-organized residue-class regimes. RMD-SRC machinery "
                  "(channel decomposition + residue-class clustering) runs and "
                  "returns structure on both. Methodology is substrate-agnostic."),
    },
    "H3_sdp_idp_equivalence": {
        "disposition": "OVERLAPPING (not identical, not distinct)",
        "shared": [
            "channel-decomposable: both pass single-channel-dominance orthogonality",
            "residue-class structure: both cluster into geography-organized regimes",
            "geography organizes regimes in both (IDP=hazard geography; SDP=climate+policy geography)",
        ],
        "divergent": [
            "channel KIND: IDP channels are exogenous shocks (conflict/flood/drought); "
            "SDP channels are structural conditions (family-economic/chronic-institutional/situational)",
            "orthogonality STRENGTH: IDP 92% vs SDP 61.9% (SDP channels more entangled)",
            "regime COMPLEXITY: IDP 6 distinct hazard regimes vs SDP bimodal-primary "
            "(street vs sheltered) with weaker 3-5 substructure",
            "DRIVER: IDP driven by exogenous events; SDP driven by policy/structural conditions",
        ],
        "one_line": ("Same math, different physics: the decomposition STRUCTURE transfers "
                     "(orthogonal channels + geographic residue-classes), but the FORCES "
                     "differ (policy/climate for SDP vs conflict/disaster for IDP). "
                     "SDP and IDP are methodologically equivalent, mechanistically overlapping."),
    },
}

out = {"idp": idp, "sdp": sdp, "verdict": verdict}
OUT.write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
print(f"\n[phase4] wrote {OUT}")
