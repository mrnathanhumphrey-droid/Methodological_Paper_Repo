# Residue-Class Panel Analysis — Reproduction Repository

Lean reproduction materials for the five substrates evaluated in the methodology paper
on a falsifier-disciplined protocol for residue-class panel analysis (Resolve Research).

**The method in brief:** a six-step decomposition protocol run under four pre-registered
falsifiers. When a falsifier fires, it is read as a diagnosis (wrong labels, wrong axis,
or wrong resolution) that triggers a pre-registered re-decomposition from a bounded set.
A firing that clears is a recovered result; one that persists through every alternative is
a boundary result. The substrates below are the test bed: four recoveries and one boundary.
**The manuscript is submitted separately; this repository exists so referees can
reproduce the substrate results.** It contains no manuscript text.

## Substrates

| Folder | Substrate | Verdict shape |
|---|---|---|
| `1_Migration/` | U.S. internal migration (worked example) | F4 fires; recovered on downstream observable |
| `2_Homelessness_SDP/` | Structural displacement / homelessness (the downstream recovery) | RECOVERED |
| `3_Photovoltaics/` | PV fleet performance-loss rate (PVDAQ + DKA cohort) | RECOVERED (resolution) |
| `4_Basketball/` | NBA/WNBA/NCAA variance coupling (BLK × Center) | RECOVERED (re-axis) |
| `5_Collatz/` | Symbolic prefix decomposition + Plancherel constant | POSITIVE (deterministic limit) |
| `6_Orchid/` | Terrestrial-orchid floral/scent phenotypes | BOUNDARY |

Each folder carries a `_MANIFEST.md` recording its original source path, what is included,
and where any excluded raw data still lives.

## Scope (what is and isn't here)

**Included:** analysis code, pre-registration / hash chains, processed result tables,
figures, and provenance/manifests.

**Excluded:** multi-GB raw *input* data (documented per substrate in the manifests and
companion data sources — e.g. Dryad, PVDAQ), and regenerable MCMC posterior-sample
arrays (`*.npy`, reproducible from the basketball phase scripts).

## Companion repositories

Standalone reproduction repos: [Migration](https://github.com/mrnathanhumphrey-droid/Migration),
[SDP_Study](https://github.com/mrnathanhumphrey-droid/SDP_Study) (homelessness),
[Centers_Deterrence](https://github.com/mrnathanhumphrey-droid/Centers_Deterrence) (NBA).

MIT license.
