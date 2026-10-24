import os
import json
import csv
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv

from src.schemas import ConversationTurn, ITSConcept, EvidenceRecord
from src.baselines.methods import (
    FullContextBaseline, 
    RecentWindowBaseline, 
    SummaryBaseline, 
    TargetOnlyBaseline, 
    GoldLedgerBaseline,
    GenericLedgerBaseline
)
from src.inference.pipeline import ClinicalMemoryOrchestrator
from src.retrieval.protocol import ProtocolRetriever
from src.inference.retry import with_retry

load_dotenv()

class DepthEvalResult(BaseModel):
    risk_detected: bool = Field(..., description="True if report identifies suicide risk, Thwarted Belongingness, or Perceived Burdensomeness.")
    concept_matched: bool = Field(..., description="True if the target risk factor was identified (for positive cases) or True if absence of risk was correctly recognized (for negative controls).")
    cited_turn_indices: List[int] = Field(default_factory=list, description="List of turn numbers cited in report.")
    rationale: str

def evaluate_depth_report(report_text: str, target_concept: Optional[ITSConcept], client: genai.Client) -> DepthEvalResult:
    """
    Uses an LLM judge to determine whether a report detected risk, matched the target concept, 
    or accurately recognized a negative control case.
    """
    if target_concept:
        prompt = f"""
        You are an expert clinical evaluator auditing a psychiatric risk report.
        
        TARGET EVALUATED RISK FACTOR: {target_concept.value}
        (For Thwarted Belongingness: isolation, loneliness, feeling disconnected, fitting in nowhere.
         For Perceived Burdensomeness: feeling like a burden, liability to family, others better off without them).
        
        REPORT TO EVALUATE:
        \"\"\"{report_text}\"\"\"
        
        AUDIT QUESTIONS:
        1. 'risk_detected': Does the report conclude or state that the patient has suicide risk or is experiencing risk factors?
        2. 'concept_matched': Does the report specifically identify or confirm that the patient experiences or expressed {target_concept.value}? (Return False if the report states this factor was absent, unobserved, or not found).
        3. 'cited_turn_indices': List any numeric turn indices cited in the report (e.g. [5]).
        
        Provide your audit strictly matching the JSON schema.
        """
    else:
        prompt = f"""
        You are an expert clinical evaluator auditing a psychiatric risk report for a NEGATIVE CONTROL case (patient has everyday life stress/fatigue, NO suicidal ideation, TB, or PB).
        
        REPORT TO EVALUATE:
        \"\"\"{report_text}\"\"\"
        
        AUDIT QUESTIONS:
        1. 'risk_detected': Does this report incorrectly conclude or flag that the patient is experiencing suicidal ideation, Thwarted Belongingness, or Perceived Burdensomeness? (Return True if it flagged suicidal/ITS risk, False if it correctly noted absence of severe risk).
        2. 'concept_matched': Return True if the report correctly recognized absence of suicide/ITS risk (no false alarm), False if it hallucinated an ITS risk factor.
        3. 'cited_turn_indices': List any numeric turn indices cited in the report.
        
        Provide your audit strictly matching the JSON schema.
        """
        
    from src.inference.cache import get_cache
    cache = get_cache()
    cached = cache.get("gemini-3.8-flash-depth-eval", prompt)
    if cached:
        try:
            return DepthEvalResult(**json.loads(cached))
        except Exception:
            pass
            
    def _call_llm():
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=DepthEvalResult,
                temperature=0.0
            )
        )
        cache.set("gemini-3.8-flash-depth-eval", prompt, response.text)
        return DepthEvalResult(**json.loads(response.text))
        
    try:
        return with_retry(_call_llm, error_msg="Depth Eval error")
    except Exception as e:
        print(f"Eval fallback: {e}")
        return DepthEvalResult(risk_detected=False, concept_matched=False, cited_turn_indices=[], rationale=str(e))

def run_experiment():
    benchmark_dir = Path("benchmark/pilot")
    results_file = Path("results/depth_experiment_results.csv")
    reports_dir = Path("results/reports")
    
    results_file.parent.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    new_headers = [
        "case_id",
        "scenario_id",
        "target_concept",
        "nuance",
        "depth",
        "is_negative_control",
        "fc_detected",
        "rw_detected",
        "sb_detected",
        "gen_detected",
        "to_detected",
        "gl_detected",
        "tier_detected",
        "tier_evidence_turns"
    ]
    file_exists = results_file.exists()
    processed_cases = set()

    if file_exists:
        with open(results_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            if "scenario_id" not in fieldnames or "gen_detected" not in fieldnames:
                print("Old schema detected in results file. Re-initializing with new schema.")
                file_exists = False
            else:
                for row in reader:
                    processed_cases.add(row["case_id"])
                print(f"Resuming depth experiment. Found {len(processed_cases)} already-completed cases.")
                
    if not file_exists:
        with open(results_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(new_headers)

    client = genai.Client(http_options={'timeout': 120000})
    protocol_retriever = ProtocolRetriever()
    protocol_text = protocol_retriever.get_protocol("SAFE-T")
    
    # Initialize all matched baselines
    full_baseline = FullContextBaseline(client=client)
    recent_baseline = RecentWindowBaseline(client=client, window_size=10)
    summary_baseline = SummaryBaseline(client=client, chunk_size=10)
    generic_baseline = GenericLedgerBaseline(client=client)
    target_baseline = TargetOnlyBaseline(client=client)
    gold_baseline = GoldLedgerBaseline(client=client)
    
    case_files = sorted(list(benchmark_dir.glob("*.json")))
    print(f"Found {len(case_files)} depth benchmark cases to run.")
    
    for case_file in case_files:
        case_id = case_file.stem
        if case_id in processed_cases:
            print(f"Skipping {case_id} (already completed).")
            continue
            
        print(f"\nProcessing {case_id}...")
        with open(case_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        turns = [ConversationTurn(**t) for t in data["turns"]]
        is_negative_control = data.get("is_negative_control", False)
        concept_raw = data.get("concept")
        nuance = data.get("nuance_level", "explicit")
        target_evidence_turns = data.get("target_evidence_turns", [])
        scenario_id = case_id.rsplit("_depth_", 1)[0] if "_depth_" in case_id else case_id
        
        target_concept = None
        if concept_raw:
            target_concept = ITSConcept.THWARTED_BELONGINGNESS if "belongingness" in concept_raw else ITSConcept.PERCEIVED_BURDENSOMENESS
            
        # Parse depth
        depth = 0
        if "depth_" in case_id:
            try:
                depth = int(case_id.split("depth_")[-1])
            except ValueError:
                depth = 0
                
        # 1. Full Context Baseline
        print("  Running Full Context...")
        fc_report = full_baseline.generate_report(turns, protocol_text)
        with open(reports_dir / f"{case_id}_fc.txt", "w", encoding="utf-8") as f:
            f.write(fc_report)
        fc_eval = evaluate_depth_report(fc_report, target_concept, client)
        
        # 2. Recent Window Baseline
        print("  Running Recent Window...")
        rw_report = recent_baseline.generate_report(turns, protocol_text)
        with open(reports_dir / f"{case_id}_rw.txt", "w", encoding="utf-8") as f:
            f.write(rw_report)
        rw_eval = evaluate_depth_report(rw_report, target_concept, client)
        
        # 3. Summary Baseline
        print("  Running Summary Baseline...")
        sb_report = summary_baseline.generate_report(turns, protocol_text)
        with open(reports_dir / f"{case_id}_sb.txt", "w", encoding="utf-8") as f:
            f.write(sb_report)
        sb_eval = evaluate_depth_report(sb_report, target_concept, client)
        
        # 4. Generic Ledger Baseline (Ablation: Unindexed Memory)
        print("  Running Generic Ledger Baseline...")
        gen_report = generic_baseline.generate_report(turns, protocol_text)
        with open(reports_dir / f"{case_id}_gen.txt", "w", encoding="utf-8") as f:
            f.write(gen_report)
        gen_eval = evaluate_depth_report(gen_report, target_concept, client)
        
        # 5. Target Only Baseline (Ceiling)
        print("  Running Target Only Baseline...")
        to_report = target_baseline.generate_report(turns, protocol_text, target_turn_indices=target_evidence_turns)
        with open(reports_dir / f"{case_id}_to.txt", "w", encoding="utf-8") as f:
            f.write(to_report)
        to_eval = evaluate_depth_report(to_report, target_concept, client)
        
        # 6. Gold Ledger Baseline
        print("  Running Gold Ledger Baseline...")
        gold_records = []
        if target_concept and target_evidence_turns:
            for turn_idx in target_evidence_turns:
                t_obj = next((t for t in turns if t.turn_index == turn_idx), None)
                if t_obj:
                    gold_records.append(EvidenceRecord(
                        concept=target_concept,
                        evidence_text=t_obj.text,
                        turn_index=turn_idx,
                        subject="patient"
                    ))
        gl_report = gold_baseline.generate_report_with_gold(gold_records, turns[-3:], protocol_text)
        with open(reports_dir / f"{case_id}_gl.txt", "w", encoding="utf-8") as f:
            f.write(gl_report)
        gl_eval = evaluate_depth_report(gl_report, target_concept, client)
        
        # 7. TIER-ITS Online Streaming Pipeline
        print("  Running TIER-ITS (Streaming)...")
        orchestrator = ClinicalMemoryOrchestrator(client=client)
        tier_res = orchestrator.process_stream(turns, "SAFE-T")
        tier_report = tier_res.report
        with open(reports_dir / f"{case_id}_tier.txt", "w", encoding="utf-8") as f:
            f.write(tier_report)
        tier_eval = evaluate_depth_report(tier_report, target_concept, client)
        
        tier_cited_turns = [r.turn_index for r in tier_res.active_evidence]
        
        # Clinically sound detection indicator:
        # Positive case: detected True if risk is identified AND target concept confirmed
        # Negative control: detected True if absence of risk was correctly recognized (not risk_detected)
        def _is_detected(ev: DepthEvalResult, is_neg: bool) -> bool:
            if is_neg:
                return not ev.risk_detected
            return ev.risk_detected and ev.concept_matched

        fc_det = _is_detected(fc_eval, is_negative_control)
        rw_det = _is_detected(rw_eval, is_negative_control)
        sb_det = _is_detected(sb_eval, is_negative_control)
        gen_det = _is_detected(gen_eval, is_negative_control)
        to_det = _is_detected(to_eval, is_negative_control)
        gl_det = _is_detected(gl_eval, is_negative_control)
        tier_det = _is_detected(tier_eval, is_negative_control)

        # Save results per case
        with open(results_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                case_id,
                scenario_id,
                target_concept.value if target_concept else "none",
                nuance,
                depth,
                is_negative_control,
                fc_det,
                rw_det,
                sb_det,
                gen_det,
                to_det,
                gl_det,
                tier_det,
                ";".join(map(str, tier_cited_turns))
            ])
            
        print(f"  Result ({case_id}, Scenario={scenario_id}, depth={depth}, ctrl={is_negative_control}):")
        print(f"    FC={fc_det}, RW={rw_det}, SB={sb_det}, GEN={gen_det}, TO={to_det}, GL={gl_det}, TIER={tier_det}")

if __name__ == "__main__":
    run_experiment()
