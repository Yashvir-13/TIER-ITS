import csv
from pathlib import Path
from collections import defaultdict

def analyze_correction_results(results_csv: str = "results/correction_experiment_results.csv"):
    csv_path = Path(results_csv)
    if not csv_path.exists():
        print(f"Results file {results_csv} does not exist yet.")
        return
        
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
            
    total = len(rows)
    if total == 0:
        print("No cases completed yet.")
        return
        
    print("=" * 70)
    print(f"TIER-ITS PHASE 7: CORRECTION EXPERIMENT ANALYSIS ({total} Cases)")
    print("=" * 70)
    
    # 1. State Machine Invalidation
    tier_invalidated = sum(1 for r in rows if r["tier_ledger_invalidated"].strip().lower() == "true")
    turn_matches = 0
    for r in rows:
        try:
            inv_turn = int(r["tier_invalidated_by_turn"])
            corr_turn = int(r["correction_turn_idx"])
            if inv_turn == corr_turn:
                turn_matches += 1
        except (ValueError, TypeError):
            pass
            
    print(f"\n[1] ITS EVIDENCE LEDGER ACCURACY:")
    print(f"  - Ledger Invalidation Rate:    {tier_invalidated}/{total} ({tier_invalidated/total*100:.1f}%)")
    print(f"  - Exact Turn Identification:   {turn_matches}/{total} ({turn_matches/total*100:.1f}%)")
    
    # 2. Risk Hallucination / False Positive Rate on Active Risk
    # (Since the risk was contradicted, reporting active risk is an erroneous False Positive)
    tier_fp = sum(1 for r in rows if r["tier_active_risk"].strip().lower() == "true")
    fc_fp = sum(1 for r in rows if r["fc_active_risk"].strip().lower() == "true")
    rw_fp = sum(1 for r in rows if r["rw_active_risk"].strip().lower() == "true")
    
    print(f"\n[2] ACTIVE RISK HALLUCINATION RATE (Lower is Better - Ground Truth = No Active Risk):")
    print(f"  - TIER-ITS:                  {tier_fp}/{total} ({tier_fp/total*100:.1f}%)")
    print(f"  - Full-Context Baseline:     {fc_fp}/{total} ({fc_fp/total*100:.1f}%)")
    print(f"  - Recent-Window Baseline:    {rw_fp}/{total} ({rw_fp/total*100:.1f}%)")
    
    # 3. Resolution Acknowledgment Rate
    tier_ack = sum(1 for r in rows if r["tier_resolved_ack"].strip().lower() == "true")
    fc_ack = sum(1 for r in rows if r["fc_resolved_ack"].strip().lower() == "true")
    rw_ack = sum(1 for r in rows if r["rw_resolved_ack"].strip().lower() == "true")
    
    print(f"\n[3] RESOLUTION ACKNOWLEDGMENT RATE (Sensitivity to Belief Revision):")
    print(f"  - TIER-ITS:                  {tier_ack}/{total} ({tier_ack/total*100:.1f}%)")
    print(f"  - Full-Context Baseline:     {fc_ack}/{total} ({fc_ack/total*100:.1f}%)")
    print(f"  - Recent-Window Baseline:    {rw_ack}/{total} ({rw_ack/total*100:.1f}%)")
    
    # 4. Breakdown by Intervening Gap Depth
    by_gap = defaultdict(list)
    for r in rows:
        by_gap[r["gap"]].append(r)
        
    print(f"\n[4] BREAKDOWN BY INTERVENING GAP DEPTH:")
    print(f"  {'Gap':<6} | {'N':<4} | {'TIER Invalidation':<18} | {'TIER FP':<9} | {'FC FP':<9} | {'RW FP':<9}")
    print("  " + "-" * 62)
    for gap in sorted(by_gap.keys(), key=lambda x: int(x)):
        g_rows = by_gap[gap]
        n = len(g_rows)
        t_inv = sum(1 for r in g_rows if r["tier_ledger_invalidated"].strip().lower() == "true") / n * 100
        t_fp = sum(1 for r in g_rows if r["tier_active_risk"].strip().lower() == "true") / n * 100
        f_fp = sum(1 for r in g_rows if r["fc_active_risk"].strip().lower() == "true") / n * 100
        r_fp = sum(1 for r in g_rows if r["rw_active_risk"].strip().lower() == "true") / n * 100
        print(f"  {gap:<6} | {n:<4} | {t_inv:>17.1f}% | {t_fp:>8.1f}% | {f_fp:>8.1f}% | {r_fp:>8.1f}%")
        
    # 5. Breakdown by Nuance Level
    by_nuance = defaultdict(list)
    for r in rows:
        by_nuance[r["nuance"]].append(r)
        
    print(f"\n[5] BREAKDOWN BY NUANCE LEVEL:")
    print(f"  {'Nuance':<12} | {'N':<4} | {'TIER Invalidation':<18} | {'TIER FP':<9} | {'FC FP':<9} | {'RW FP':<9}")
    print("  " + "-" * 68)
    for nu in sorted(by_nuance.keys()):
        nu_rows = by_nuance[nu]
        n = len(nu_rows)
        t_inv = sum(1 for r in nu_rows if r["tier_ledger_invalidated"].strip().lower() == "true") / n * 100
        t_fp = sum(1 for r in nu_rows if r["tier_active_risk"].strip().lower() == "true") / n * 100
        f_fp = sum(1 for r in nu_rows if r["fc_active_risk"].strip().lower() == "true") / n * 100
        r_fp = sum(1 for r in nu_rows if r["rw_active_risk"].strip().lower() == "true") / n * 100
        print(f"  {nu:<12} | {n:<4} | {t_inv:>17.1f}% | {t_fp:>8.1f}% | {f_fp:>8.1f}% | {r_fp:>8.1f}%")
    print("=" * 70)

if __name__ == "__main__":
    analyze_correction_results()
