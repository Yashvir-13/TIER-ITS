import os
import json
import csv
from pathlib import Path
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv

from src.schemas import ConversationTurn, ITSConcept
from src.baselines.methods import FullContextBaseline, RecentWindowBaseline
from src.extractor.gemini import GeminiExtractor
from src.ledger.store import EvidenceLedger
from src.ledger.assessor import GeminiContradictionAssessor
from src.retrieval.conversation import ConversationRetriever
from src.report.generator import ReportGenerator

load_dotenv()

class EvalResult(BaseModel):
    detected: bool
    rationale: str

def evaluate_report(report_text: str, target_concept: ITSConcept, client: genai.Client) -> bool:
    """
    Uses an LLM judge to determine if the generated report correctly identified the target risk factor.
    """
    prompt = f"""
    You are an expert clinical evaluator.
    Read the following clinical risk report and determine if it explicitly mentions or captures the essence of the risk factor: {target_concept.value}.
    
    If it's Thwarted Belongingness, look for isolation, loneliness, not fitting in, or no one caring.
    If it's Perceived Burdensomeness, look for feeling like a burden, feeling others are better off without them.
    
    REPORT:
    {report_text}
    
    Respond strictly with the provided JSON schema.
    """
    
    import time
    max_retries = 10
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-3.8-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=EvalResult,
                    temperature=0.0
                )
            )
            res = EvalResult(**json.loads(response.text))
            return res.detected
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Eval error after {max_retries} attempts: {e}")
                return False
            print(f"Network error in Eval (attempt {attempt+1}/{max_retries}): {e}. Waiting 10s...")
            time.sleep(10)

def run_experiment():
    benchmark_dir = Path("benchmark/pilot")
    results_file = Path("results/depth_experiment_results.csv")
    
    # Ensure directories exist
    results_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Setup CSV
    file_exists = results_file.exists()
    
    processed_cases = set()
    if file_exists:
        with open(results_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed_cases.add(row["case_id"])
    else:
        with open(results_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["case_id", "target_concept", "nuance", "depth", "full_context_detected", "recent_window_detected", "tier_its_detected"])

    client = genai.Client(http_options={'timeout': 120000})
    
    # Initialize baselines
    full_baseline = FullContextBaseline(client=client)
    recent_baseline = RecentWindowBaseline(client=client, window_size=10)
    
    case_files = list(benchmark_dir.glob("*.json"))
    print(f"Found {len(case_files)} benchmark cases.")
    
    for case_file in case_files:
        case_id = case_file.stem
        if case_id in processed_cases:
            print(f"Skipping {case_id}, already processed.")
            continue
            
        print(f"Processing {case_id}...")
        
        with open(case_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        turns = [ConversationTurn(**t) for t in data["turns"]]
        
        # Parse metadata from filename: tb_explicit_0_depth_20_depth_20
        # format is generally {concept}_{nuance}_{id}_depth_{depth}
        parts = case_id.split("_")
        concept_str = parts[0]
        if concept_str == "tb":
            target_concept = ITSConcept.THWARTED_BELONGINGNESS
        else:
            target_concept = ITSConcept.PERCEIVED_BURDENSOMENESS
            
        # some files are tb_case_0_depth_20, some are tb_explicit_0_depth_20
        nuance = parts[1] if parts[1] in ["explicit", "implicit", "fragmented"] else "explicit"
        
        # find depth index
        try:
            depth_idx = parts.index("depth")
            depth = int(parts[depth_idx + 1])
        except ValueError:
            depth = 0
            
        import time
        reports_dir = Path("results/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Full Context Baseline
        print("  Running Full Context...")
        fc_report = full_baseline.generate_report(turns, "SAFE-T")
        with open(reports_dir / f"{case_id}_fc.txt", "w", encoding="utf-8") as f:
            f.write(fc_report)
        fc_detected = evaluate_report(fc_report, target_concept, client)
        
        # 2. Recent Window Baseline
        print("  Running Recent Window...")
        rw_report = recent_baseline.generate_report(turns, "SAFE-T")
        with open(reports_dir / f"{case_id}_rw.txt", "w", encoding="utf-8") as f:
            f.write(rw_report)
        rw_detected = evaluate_report(rw_report, target_concept, client)
        
        # 3. TIER-ITS
        print("  Running TIER-ITS...")
        # We need a fresh state for each case
        extractor = GeminiExtractor()
        assessor = GeminiContradictionAssessor(client=client)
        ledger = EvidenceLedger(assessor=assessor)
        
        # Use an in-memory chroma for fast testing if possible, or fresh persist directory
        retriever = ConversationRetriever(in_memory=True)
        
        # Batch extract evidence from all patient turns at once to avoid API rate limits
        extracted_records = extractor.batch_extract(turns)
        for record in extracted_records:
            ledger.add_evidence(record)
            
        # Add all turns to the retriever context
        retriever.add_turns(turns)
            
        active_evidence = ledger.get_active_evidence()
        # Retrieve context around the active evidence concepts
        query_str = " ".join([e.concept.value for e in active_evidence]) if active_evidence else "suicide risk factors"
        relevant_turns = retriever.retrieve_relevant_turns(query_str, top_k=3)
        
        report_generator = ReportGenerator(client=client)
        tier_report = report_generator.generate_report(active_evidence, relevant_turns, "SAFE-T")
        with open(reports_dir / f"{case_id}_tier.txt", "w", encoding="utf-8") as f:
            f.write(tier_report)
        tier_detected = evaluate_report(tier_report, target_concept, client)
        
        # Save results
        with open(results_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([case_id, target_concept.value, nuance, depth, fc_detected, rw_detected, tier_detected])
            
        print(f"  Result: FC={fc_detected}, RW={rw_detected}, TIER={tier_detected}")

if __name__ == "__main__":
    run_experiment()
