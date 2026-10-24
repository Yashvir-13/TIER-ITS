import os
import json
import csv
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv

from src.schemas import ConversationTurn, ITSConcept
from src.baselines.methods import (
    FullContextBaseline, 
    RecentWindowBaseline, 
    SummaryBaseline, 
    GenericLedgerBaseline
)
from src.inference.pipeline import ClinicalMemoryOrchestrator
from src.inference.retry import with_retry
from src.retrieval.protocol import ProtocolRetriever

load_dotenv()

class CorrectionEvalResult(BaseModel):
    active_risk_reported: bool = Field(
        ..., 
        description="True if the report concludes the patient is CURRENTLY experiencing active risk from this concept. False if resolved, absent, or explicitly marked inactive."
    )
    resolution_acknowledged: bool = Field(
        ..., 
        description="True if the report notes that the prior risk disclosure was contradicted, resolved, or proved unfounded by later events."
    )
    rationale: str

def evaluate_correction_report(report_text: str, target_concept: ITSConcept, client: genai.Client) -> CorrectionEvalResult:
    """
    Uses an LLM judge to determine whether a clinical report:
    1. Reports the risk as currently active (active_risk_reported).
    2. Acknowledges the contradiction/resolution (resolution_acknowledged).
    """
    prompt = f"""
    You are an expert clinical evaluator auditing a psychiatric risk summary.
    
    EVALUATED RISK FACTOR: {target_concept.value}
    
    CLINICAL REPORT TO AUDIT:
    \"\"\"
    {report_text}
    \"\"\"
    
    AUDIT QUESTIONS:
    1. 'active_risk_reported': Does this report conclude that the patient is CURRENTLY suffering from or presenting active, unmitigated danger regarding {target_concept.value}? (Return False if the report states the patient is NOT currently at risk, or that the factor is absent/resolved).
    2. 'resolution_acknowledged': Does this report acknowledge that an earlier expression of this factor was resolved, contradicted, or softened by subsequent disclosures or family connection?
    
    Provide your evaluation strictly matching the JSON schema.
    """
    
    from src.inference.cache import get_cache
    cache = get_cache()
    cached = cache.get("gemini-3.8-flash-corr-eval", prompt)
    if cached:
        try:
            return CorrectionEvalResult(**json.loads(cached))
        except Exception:
            pass
            
    def _call_llm():
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CorrectionEvalResult,
                temperature=0.0
            )
        )
        cache.set("gemini-3.8-flash-corr-eval", prompt, response.text)
        return CorrectionEvalResult(**json.loads(response.text))
        
    try:
        return with_retry(_call_llm, error_msg="Correction Eval error")
    except Exception as e:
        print(f"Eval fallback due to error: {e}")
        return CorrectionEvalResult(active_risk_reported=True, resolution_acknowledged=False, rationale=f"Error: {e}")

def run_correction_experiment():
    benchmark_dir = Path("benchmark/correction")
    results_file = Path("results/correction_experiment_results.csv")
    reports_dir = Path("results/reports")
    
    results_file.parent.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    new_headers = [
        "case_id",
        "scenario_id",
        "target_concept",
        "nuance",
        "gap",
        "initial_turn_idx",
        "correction_turn_idx",
        "is_non_correction_control",
        "tier_ledger_invalidated",
        "tier_invalidated_by_turn",
        "tier_active_risk",
        "tier_resolved_ack",
        "fc_active_risk",
        "fc_resolved_ack",
        "rw_active_risk",
        "rw_resolved_ack",
        "sb_active_risk",
        "sb_resolved_ack",
        "gen_active_risk",
        "gen_resolved_ack"
    ]
    file_exists = results_file.exists()
    processed_cases = set()

    if file_exists:
        with open(results_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            if "scenario_id" not in fieldnames or "gen_active_risk" not in fieldnames:
                print("Old schema detected in results file. Re-initializing with new schema.")
                file_exists = False
            else:
                for row in reader:
                    processed_cases.add(row["case_id"])
                print(f"Resuming experiment. Found {len(processed_cases)} already-completed cases in {results_file}.")
                
    if not file_exists:
        with open(results_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(new_headers)
            
    client = genai.Client(http_options={'timeout': 120000})
    full_baseline = FullContextBaseline(client=client)
    recent_baseline = RecentWindowBaseline(client=client, window_size=10)
    summary_baseline = SummaryBaseline(client=client, chunk_size=10)
    generic_baseline = GenericLedgerBaseline(client=client)
    protocol_retriever = ProtocolRetriever()
    protocol_text = protocol_retriever.get_protocol("SAFE-T")
    
    case_files = sorted(list(benchmark_dir.glob("*.json")))
    print(f"Found {len(case_files)} correction benchmark cases to run.")
    
    for case_file in case_files:
        case_id = case_file.stem
        if case_id in processed_cases:
            print(f"Skipping {case_id} (already completed).")
            continue
            
        print(f"\nProcessing {case_id}...")
        with open(case_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        turns = [ConversationTurn(**t) for t in data["turns"]]
        concept_raw = data.get("concept", "perceived_burdensomeness")
        target_concept = ITSConcept.THWARTED_BELONGINGNESS if "belongingness" in concept_raw else ITSConcept.PERCEIVED_BURDENSOMENESS
        nuance = data.get("nuance_level", "explicit")
        gap = data.get("gap", 10)
        initial_turn_idx = data.get("initial_turn_index", 3)
        correction_turn_idx = data.get("correction_turn_index", None)
        is_non_correction_control = data.get("is_non_correction_control", False)
        scenario_id = case_id.rsplit("_gap_", 1)[0] if "_gap_" in case_id else case_id
        
        # 1. Full Context Baseline
        print("  Running Full Context Baseline...")
        fc_report = full_baseline.generate_report(turns, protocol_text)
        with open(reports_dir / f"{case_id}_fc.txt", "w", encoding="utf-8") as f:
            f.write(fc_report)
        fc_eval = evaluate_correction_report(fc_report, target_concept, client)
        
        # 2. Recent Window Baseline
        print("  Running Recent Window Baseline...")
        rw_report = recent_baseline.generate_report(turns, protocol_text)
        with open(reports_dir / f"{case_id}_rw.txt", "w", encoding="utf-8") as f:
            f.write(rw_report)
        rw_eval = evaluate_correction_report(rw_report, target_concept, client)
        
        # 3. Summary Baseline
        print("  Running Summary Baseline...")
        sb_report = summary_baseline.generate_report(turns, protocol_text)
        with open(reports_dir / f"{case_id}_sb.txt", "w", encoding="utf-8") as f:
            f.write(sb_report)
        sb_eval = evaluate_correction_report(sb_report, target_concept, client)
        
        # 4. Generic Ledger Baseline (Ablation: Unindexed Memory)
        print("  Running Generic Ledger Baseline...")
        gen_report = generic_baseline.generate_report(turns, protocol_text)
        with open(reports_dir / f"{case_id}_gen.txt", "w", encoding="utf-8") as f:
            f.write(gen_report)
        gen_eval = evaluate_correction_report(gen_report, target_concept, client)
        
        # 5. TIER-ITS Online Streaming Orchestrator
        print("  Running TIER-ITS (Streaming)...")
        orchestrator = ClinicalMemoryOrchestrator(client=client)
        tier_res = orchestrator.process_stream(turns, "SAFE-T")
        tier_report = tier_res.report
        with open(reports_dir / f"{case_id}_tier.txt", "w", encoding="utf-8") as f:
            f.write(tier_report)
        tier_eval = evaluate_correction_report(tier_report, target_concept, client)
        
        # Target-specific ledger verification
        all_records = orchestrator.ledger.get_all_evidence()
        tier_ledger_invalidated = False
        tier_invalidated_by_turn = None
        for r in all_records:
            if r.concept == target_concept and r.turn_index == initial_turn_idx:
                if r.contradicted:
                    tier_ledger_invalidated = True
                    tier_invalidated_by_turn = r.contradicted_by_turn
                    break
                    
        # Checkpoint to CSV
        with open(results_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                case_id,
                scenario_id,
                target_concept.value,
                nuance,
                gap,
                initial_turn_idx,
                correction_turn_idx,
                is_non_correction_control,
                tier_ledger_invalidated,
                tier_invalidated_by_turn,
                tier_eval.active_risk_reported,
                tier_eval.resolution_acknowledged,
                fc_eval.active_risk_reported,
                fc_eval.resolution_acknowledged,
                rw_eval.active_risk_reported,
                rw_eval.resolution_acknowledged,
                sb_eval.active_risk_reported,
                sb_eval.resolution_acknowledged,
                gen_eval.active_risk_reported,
                gen_eval.resolution_acknowledged
            ])
            
        print(f"  Summary for {case_id} (Scenario={scenario_id}, Ctrl={is_non_correction_control}):")
        print(f"    TIER: Ledger Inval={tier_ledger_invalidated} (turn {tier_invalidated_by_turn}), ActiveRisk={tier_eval.active_risk_reported}, ResAck={tier_eval.resolution_acknowledged}")
        print(f"    GEN:  ActiveRisk={gen_eval.active_risk_reported}, ResAck={gen_eval.resolution_acknowledged}")
        print(f"    FC:   ActiveRisk={fc_eval.active_risk_reported}, ResAck={fc_eval.resolution_acknowledged}")
        print(f"    RW:   ActiveRisk={rw_eval.active_risk_reported}, ResAck={rw_eval.resolution_acknowledged}")
        print(f"    SB:   ActiveRisk={sb_eval.active_risk_reported}, ResAck={sb_eval.resolution_acknowledged}")

if __name__ == "__main__":
    run_correction_experiment()
