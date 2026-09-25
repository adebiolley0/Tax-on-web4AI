#!/usr/bin/env python3
"""Store the citation graph in kuzu (embedded graph DB) and express neighbour expansion as Cypher.

Assesses build time, query time and ergonomics of kuzu for this use case; the retrieval
metrics themselves are computed in numpy (run_graph.py). The Cypher 1-hop boost is checked
against the numpy operator ('sum' normalisation) on the same seeds.

  uv run python kuzu_graph.py --tag B_raw
  uv run python kuzu_graph.py --tag C --max_group 200
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import time

import numpy as np

from common11 import CACHE, FirstStage, minmax
from propagate import PropGraph, top_k_seeds


def build_db(tag: str, db_dir, max_group: int) -> dict:
    import kuzu
    g = json.loads((CACHE / f"{tag}_graph.json").read_text())
    if tag.startswith("B"):
        docs = json.loads((CACHE / f"{tag}_docs.json").read_text())
        title = {d["id"]: d["title"] for d in docs}
        kind = {d["id"]: d["meta"]["code"] for d in docs}
    else:
        meta = json.loads((CACHE / "C_docs_meta.json").read_text())
        title = {d: m["title"] for d, m in meta.items()}
        kind = {d: m["folder"] for d, m in meta.items()}
    t0 = time.perf_counter()
    tmp = CACHE / f"{tag}_kuzu_csv"
    tmp.mkdir(exist_ok=True)
    with (tmp / "docs.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, quoting=csv.QUOTE_ALL)
        w.writerow(["id", "title", "kind"])
        for d in g["nodes"]:
            w.writerow([d, title.get(d, "")[:200].replace("\n", " "), kind.get(d, "")])
    with (tmp / "cites.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, quoting=csv.QUOTE_ALL)
        w.writerow(["from", "to", "type", "w"])
        for s, t, ty, wt in g["edges"]:
            w.writerow([s, t, ty, wt])
    n_groups = 0
    with (tmp / "groups.csv").open("w", newline="", encoding="utf-8") as ff, (tmp / "member.csv").open("w", newline="", encoding="utf-8") as fm:
        wg, wm = csv.writer(ff, quoting=csv.QUOTE_ALL), csv.writer(fm, quoting=csv.QUOTE_ALL)
        wg.writerow(["id", "kind", "size"]); wm.writerow(["from", "to"])
        for name, gs in g["groups"].items():
            for i, members in enumerate(gs):
                if len(members) > max_group:
                    continue
                gid = f"{name}:{i}"
                wg.writerow([gid, name, len(members)]); n_groups += 1
                for m in members:
                    wm.writerow([m, gid])
    csv_s = time.perf_counter() - t0

    if db_dir.is_dir():
        shutil.rmtree(db_dir)
    elif db_dir.exists():          # kuzu >= 0.10 writes a single database file
        db_dir.unlink()
    for extra in (db_dir.with_name(db_dir.name + ".wal"), db_dir.with_name(db_dir.name + ".lock")):
        if extra.exists():
            extra.unlink()
    t0 = time.perf_counter()
    db = kuzu.Database(str(db_dir))
    conn = kuzu.Connection(db)
    conn.execute("CREATE NODE TABLE Doc(id STRING, title STRING, kind STRING, PRIMARY KEY(id))")
    conn.execute("CREATE NODE TABLE Grp(id STRING, kind STRING, size INT64, PRIMARY KEY(id))")
    conn.execute("CREATE REL TABLE Cites(FROM Doc TO Doc, type STRING, w DOUBLE)")
    conn.execute("CREATE REL TABLE MemberOf(FROM Doc TO Grp)")
    conn.execute(f'COPY Doc FROM "{tmp / "docs.csv"}" (HEADER=true, ESCAPE=\'"\')')
    conn.execute(f'COPY Grp FROM "{tmp / "groups.csv"}" (HEADER=true, ESCAPE=\'"\')')
    conn.execute(f'COPY Cites FROM "{tmp / "cites.csv"}" (HEADER=true, ESCAPE=\'"\')')
    conn.execute(f'COPY MemberOf FROM "{tmp / "member.csv"}" (HEADER=true, ESCAPE=\'"\')')
    load_s = time.perf_counter() - t0
    size_mb = sum(p.stat().st_size for p in db_dir.rglob("*") if p.is_file()) / 1e6 if db_dir.is_dir() else db_dir.stat().st_size / 1e6
    counts = {}
    for q in ("MATCH (d:Doc) RETURN count(d)", "MATCH ()-[r:Cites]->() RETURN count(r)", "MATCH (g:Grp) RETURN count(g)", "MATCH ()-[m:MemberOf]->() RETURN count(m)"):
        counts[q.split("RETURN")[0].strip()] = conn.execute(q).get_next()[0]
    return {"conn": conn, "db": db, "csv_s": round(csv_s, 1), "load_s": round(load_s, 1), "db_mb": round(size_mb, 1), "counts": counts, "n_groups": n_groups}


Q_1HOP = """
WITH $ids AS ids, $scores AS scs
UNWIND range(1, size(ids)) AS i
MATCH (a:Doc {id: ids[i]})-[r:Cites]-(b:Doc)
RETURN b.id AS id, sum(scs[i] * r.w) AS boost
"""
Q_1HOP_BINARY = """
WITH $ids AS ids, $scores AS scs
UNWIND range(1, size(ids)) AS i
MATCH (a:Doc {id: ids[i]})-[r:Cites]-(b:Doc)
WITH b.id AS id, ids[i] AS src, r.type AS ty, scs[i] AS sc
WITH id, src, ty, max(sc) AS sc
RETURN id, sum(sc) AS boost
"""
Q_2HOP = """
WITH $ids AS ids, $scores AS scs
UNWIND range(1, size(ids)) AS i
MATCH (a:Doc {id: ids[i]})-[:Cites*1..2]-(b:Doc)
WHERE a.id <> b.id
RETURN b.id AS id, sum(scs[i]) AS boost
"""
Q_GROUP = """
WITH $ids AS ids, $scores AS scs
UNWIND range(1, size(ids)) AS i
MATCH (a:Doc {id: ids[i]})-[:MemberOf]->(g:Grp)<-[:MemberOf]-(b:Doc)
WHERE g.size <= 60
RETURN b.id AS id, sum(scs[i] / (g.size - 1)) AS boost
"""


def fetch(conn, query: str, params: dict) -> dict[str, float]:
    res = conn.execute(query, parameters=params)
    out: dict[str, float] = {}
    while res.has_next():
        k, v = res.get_next()
        out[k] = out.get(k, 0.0) + float(v)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="B_raw")
    ap.add_argument("--k", type=int, default=30)
    ap.add_argument("--max_group", type=int, default=200)
    ap.add_argument("--skip_2hop", action="store_true", help="the variable-length 2-hop query is slow on hubs")
    a = ap.parse_args()
    db_dir = CACHE / f"{a.tag}_kuzu_db"
    info = build_db(a.tag, db_dir, a.max_group)
    conn = info.pop("conn"); db = info.pop("db")
    print(json.dumps(info, indent=1), flush=True)

    fs = FirstStage(a.tag)
    g = json.loads((CACHE / f"{a.tag}_graph.json").read_text())
    G = PropGraph(fs.doc_ids, g["edges"], g["groups"])
    S = np.stack([minmax(r) for r in fs.doc_scores("bm25")]).astype(np.float32)
    seeds = top_k_seeds(S, a.k)
    cite_types = {t: 1.0 for t in G.adj}
    num_1hop = G.expand(seeds, cite_types, "sum", 1)
    timings = {"1hop_binary": [], "1hop_weighted": [], "2hop": [], "group": []}
    max_abs_diff = 0.0
    n_checked = 0
    for qi in range(len(fs.qids)):
        idx = np.flatnonzero(seeds[qi] > 0)
        ids = [fs.doc_ids[j] for j in idx]
        scs = [float(seeds[qi, j]) for j in idx]
        params = {"ids": ids, "scores": scs}
        t0 = time.perf_counter(); b1 = fetch(conn, Q_1HOP_BINARY, params); timings["1hop_binary"].append(time.perf_counter() - t0)
        t0 = time.perf_counter(); fetch(conn, Q_1HOP, params); timings["1hop_weighted"].append(time.perf_counter() - t0)
        if not a.skip_2hop:
            t0 = time.perf_counter(); fetch(conn, Q_2HOP, params); timings["2hop"].append(time.perf_counter() - t0)
        t0 = time.perf_counter(); fetch(conn, Q_GROUP, params); timings["group"].append(time.perf_counter() - t0)
        # correctness: binary 1-hop boost vs numpy 'sum' operator over the cite edge types
        for did, v in b1.items():
            j = fs.doc_ids.index(did) if n_checked < 2000 else None
            if j is not None:
                max_abs_diff = max(max_abs_diff, abs(v - float(num_1hop[qi, j])))
                n_checked += 1
    rep = {"tag": a.tag, "k": a.k, **info,
           "query_ms": {k: round(1000 * float(np.mean(v)), 1) for k, v in timings.items() if v},
           "query_ms_max": {k: round(1000 * float(np.max(v)), 1) for k, v in timings.items() if v},
           "numpy_vs_cypher_1hop_max_abs_diff": round(max_abs_diff, 6), "n_checked": n_checked,
           "kuzu_version": __import__("kuzu").__version__}
    print(json.dumps(rep, indent=1))
    (CACHE.parent / f"kuzu_{a.tag}.json").write_text(json.dumps(rep, indent=1))
    del conn, db


if __name__ == "__main__":
    main()
