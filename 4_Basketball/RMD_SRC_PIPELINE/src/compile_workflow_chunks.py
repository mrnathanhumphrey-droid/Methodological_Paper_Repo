"""Compile per-league per-chunk workflow scripts with candidates inlined.

For each (league, chunk_idx) tuple, produces a standalone workflow script at
RMD_SRC_PIPELINE/src/wf_<league>_<chunk_idx>.wf.js that contains the chunk's
candidate profiles inlined as a const. Workflow tool's script-size limit is
524288 chars; we chunk to stay safely under.

WNBA: 1 chunk (112 candidates).
NCAA M: 3 chunks (~712 candidates each).
NCAA W: 2 chunks (~575 candidates each).
"""
import json
from pathlib import Path

ROOT_SCRIPTS = Path("D:/NBA Projections/RMD_SRC_PIPELINE/src")
TEMPLATE_PATH = ROOT_SCRIPTS / "sloan_cross_league_adjudication.wf.js"

LEAGUES = {
    "WNBA": {
        "profiles_path": Path("C:/WNBA Projections/audit_runs/test_1_replication/sloan_adjudicated/wnba_candidate_profiles.json"),
        "chunk_size": 1000,  # all in one
    },
    "NCAA_M": {
        "profiles_path": Path("C:/NCAA D1 Mens/audit_runs/test_1_replication/sloan_adjudicated/ncaa_m_candidate_profiles.json"),
        "chunk_size": 750,  # 3 chunks of ~712
    },
    "NCAA_W": {
        "profiles_path": Path("C:/NCAA D1 Womens/audit_runs/test_1_replication/sloan_adjudicated/ncaa_w_candidate_profiles.json"),
        "chunk_size": 600,  # 2 chunks of ~575
    },
}


def build_chunk_script(template: str, league: str, candidates: list, chunk_idx: int, chunk_total: int) -> str:
    """Strip the `const { league, profiles, chunk_idx, chunk_total } = args` line
    and replace with inlined constants."""
    inlined_constants = (
        f"const league = {json.dumps(league)}\n"
        f"const chunk_idx = {chunk_idx}\n"
        f"const chunk_total = {chunk_total}\n"
        f"const profiles = {json.dumps(candidates, ensure_ascii=False, separators=(',', ':'))}\n"
    )
    args_line = "const { league, profiles, chunk_idx, chunk_total } = args"
    if args_line not in template:
        raise RuntimeError("Template missing args destructure line")
    return template.replace(args_line, inlined_constants)


def main():
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    for league, cfg in LEAGUES.items():
        with open(cfg["profiles_path"], encoding="utf-8") as f:
            data = json.load(f)
        candidates = data["candidates"]
        n = len(candidates)
        chunk_size = cfg["chunk_size"]
        chunks = [candidates[i:i + chunk_size] for i in range(0, n, chunk_size)]
        chunk_total = len(chunks)
        print(f"{league}: {n} candidates -> {chunk_total} chunk(s) of up to {chunk_size}")

        for i, chunk in enumerate(chunks):
            script = build_chunk_script(template, league, chunk, i, chunk_total)
            out_path = ROOT_SCRIPTS / f"wf_{league.lower()}_chunk{i}.wf.js"
            out_path.write_text(script, encoding="utf-8")
            print(f"  chunk {i}: {len(chunk)} candidates -> {out_path.name} "
                  f"({len(script):,} chars)")


if __name__ == "__main__":
    main()
