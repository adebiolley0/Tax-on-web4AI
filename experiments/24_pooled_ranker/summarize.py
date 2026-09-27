import json, sys
c = sys.argv[1]
import os; s = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"runs/train24_{c}.json")))
KEY = ["lgbm-tiny__notype__pooled", "lgbm-tiny__withtype__pooled", "lgbm-tiny__notype-nogate__pooled", "lgbm-tiny__small__pooled",
       "lgbm-tiny__notype__pooled-scored", "lgbm-tiny__notype-nogate__pooled-scored", "lgbm-tiny__small__pooled-scored",
       "logreg__small__pooled", "logreg__notype__pooled", "lgbm-tiny__notype__mined", "lgbm-tiny__notype-nobge__pooled"]
REFS = ["vs bar_val", "vs bar_full", "vs convex05+bge@20", "vs exp22 gate T25", "vs exp17", "vs exp21-ranker cheap+bge", "vs exp24 mined-only (same features)", "vs convex05"]
def f(t): return f"{t['delta']:+.3f} [{t['ci'][0]:+.3f},{t['ci'][1]:+.3f}] p={t['p_t']:.3f} {t['wlt'][0]}/{t['wlt'][1]}/{t['wlt'][2]} ({t['mrr_a']:.3f}->{t['mrr_b']:.3f})"
for k in KEY:
    if k not in s["models"]: continue
    e = s["models"][k]; n = "ltr24__" + k
    print(f"\n## {k}  w={e['w_human']} C={e['C']}  human val {e['fitA']['human_val']['mrr']:.3f} oof {e['oof_human']['mrr']:.3f} allmined-oof {e.get('oof_human_allmined',{}).get('mrr',float('nan')):.3f} mined val {e['fitA']['mined_val']['mrr']:.3f}/sc {e['fitA']['mined_val_scored']['mrr']:.3f}")
    print("  imp:", ", ".join(f"{a} {b:+.3f}" for a, b in e["importance"][:12]))
    for sec in ("human_val", "human_all", "mined_val"):
        row = s["tests"][sec].get(n, {})
        for r in REFS:
            for kk, t in row.items():
                if kk == r or kk == f"[all-mined oof] {r}":
                    print(f"  {sec:9s} {kk:45s} n={t['n']:3d} {f(t)}")
    for b in e.get("gate", {}).get("bins", []):
        print(f"  gate {b['words']:8s} rows {b['n_rows']:5d} q {b['n_questions']:3d} |bge| {b['mean_abs_bge_contrib']:.3f} share {b['share_of_abs_contrib']:.3f} slope {b['slope_on_bge_norm']:+.3f} rho {b['spearman']:+.2f} PD {b['pd_bge_norm_0_to_1']} range {b['pd_range']:+.3f}")
