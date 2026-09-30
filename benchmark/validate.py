import json
import sys
from pathlib import Path

def validate_benchmark(filepath: Path):
    if not filepath.exists():
        print(f"Error: {filepath} not found.")
        sys.exit(1)

    cases = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))

    print(f"Validating {len(cases)} cases...")

    errors = 0
    case_ids = set()

    for idx, case in enumerate(cases):
        # 1. Structural checks
        if "case_id" not in case:
            print(f"Case {idx} missing case_id")
            errors += 1
            continue
            
        case_id = case["case_id"]
        
        # 2. Duplicate ID check
        if case_id in case_ids:
            print(f"Duplicate case_id found: {case_id}")
            errors += 1
        case_ids.add(case_id)
        
        # 3. Check fields
        required_fields = ["conversation", "target_statement", "target_depth", "expected_concept"]
        for field in required_fields:
            if field not in case:
                print(f"[{case_id}] Missing required field: {field}")
                errors += 1
                
        # 4. Check depth logic
        conv = case.get("conversation", {})
        turns = conv.get("turns", [])
        target = case.get("target_statement", {})
        depth = case.get("target_depth", 0)
        
        target_idx = target.get("turn_index", -1)
        expected_idx = len(turns) - depth - 1
        
        if target_idx != expected_idx:
            print(f"[{case_id}] Depth mismatch: target is at {target_idx}, but len={len(turns)} and depth={depth} (expected {expected_idx})")
            errors += 1
            
        # 5. Check text matches
        if target_idx >= 0 and target_idx < len(turns):
            if turns[target_idx]["text"] != target["text"]:
                print(f"[{case_id}] Text mismatch between target statement and turn {target_idx} in conversation.")
                errors += 1

    if errors == 0:
        print("✅ Validation passed. All cases are structurally sound and depth placements are correct.")
    else:
        print(f"❌ Validation failed with {errors} errors.")
        sys.exit(1)

if __name__ == "__main__":
    benchmark_file = Path(__file__).parent.parent / "data" / "benchmark" / "benchmark_cases.jsonl"
    validate_benchmark(benchmark_file)
