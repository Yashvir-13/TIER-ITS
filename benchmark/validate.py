import json
import sys
from pathlib import Path

# Ensure project root is in sys.path so script works when executed directly
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.schemas import Conversation, ITSConcept

def validate_benchmark(pilot_dir: str = "benchmark/pilot", correction_dir: str = "benchmark/correction"):
    print("=" * 60)
    print("VALIDATING TIER-ITS BENCHMARK DATASETS")
    print("=" * 60)
    
    errors = []
    
    # 1. Validate Pilot (Depth Experiment) Cases
    pilot_path = Path(pilot_dir)
    if not pilot_path.exists():
        errors.append(f"Pilot directory {pilot_dir} does not exist.")
    else:
        pilot_files = list(pilot_path.glob("*.json"))
        print(f"\n[1] Checking Depth Pilot Cases: {len(pilot_files)} files found.")
        pos_count = 0
        neg_count = 0
        for f in pilot_files:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                case = Conversation(**data)
                
                if case.is_negative_control:
                    neg_count += 1
                else:
                    pos_count += 1
                
                # Check turn indices are strictly sequential
                for idx, turn in enumerate(case.turns):
                    if turn.turn_index != idx:
                        errors.append(f"File {f.name}: Turn index mismatch at position {idx} (found {turn.turn_index})")
                        
            except Exception as e:
                errors.append(f"File {f.name} failed validation: {e}")
                
        print(f"    -> Positive cases: {pos_count}, Negative controls: {neg_count} (Total: {len(pilot_files)})")
                
    # 2. Validate Correction Cases
    corr_path = Path(correction_dir)
    if not corr_path.exists():
        errors.append(f"Correction directory {correction_dir} does not exist.")
    else:
        corr_files = list(corr_path.glob("*.json"))
        print(f"\n[2] Checking Correction Cases: {len(corr_files)} files found.")
        corr_count = 0
        non_corr_count = 0
        for f in corr_files:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                case = Conversation(**data)
                
                if case.is_non_correction_control:
                    non_corr_count += 1
                else:
                    corr_count += 1
                
                # Check turn indices and strict speaker alternation
                prev_speaker = None
                for idx, turn in enumerate(case.turns):
                    if turn.turn_index != idx:
                        errors.append(f"File {f.name}: Turn index mismatch at position {idx} (found {turn.turn_index})")
                    if prev_speaker is not None and turn.speaker == prev_speaker:
                        errors.append(f"File {f.name}: Consecutive speaker collision at turn {idx} ({turn.speaker})")
                    prev_speaker = turn.speaker
                    
                # Check metadata integrity
                if case.is_non_correction_control:
                    if case.initial_turn_index is None:
                        errors.append(f"File {f.name}: Missing initial turn index in non-correction control.")
                    elif case.turns[case.initial_turn_index].speaker != "patient":
                        errors.append(f"File {f.name}: Initial turn {case.initial_turn_index} is not patient.")
                    if not case.expected_final_risk:
                        errors.append(f"File {f.name}: Non-correction control should have expected_final_risk=True.")
                else:
                    if case.initial_turn_index is None or case.correction_turn_index is None:
                        errors.append(f"File {f.name}: Missing initial or correction turn index metadata.")
                    else:
                        if case.turns[case.initial_turn_index].speaker != "patient":
                            errors.append(f"File {f.name}: Initial turn {case.initial_turn_index} is not patient.")
                        if case.turns[case.correction_turn_index].speaker != "patient":
                            errors.append(f"File {f.name}: Correction turn {case.correction_turn_index} is not patient.")
                        if case.initial_turn_index >= case.correction_turn_index:
                            errors.append(f"File {f.name}: Initial turn index >= correction turn index.")
                        if case.expected_final_risk:
                            errors.append(f"File {f.name}: Resolution case should have expected_final_risk=False.")
                        
            except Exception as e:
                errors.append(f"File {f.name} failed validation: {e}")
                
        print(f"    -> Resolution cases: {corr_count}, Non-correction controls: {non_corr_count} (Total: {len(corr_files)})")
                
    # Summary
    print("\n" + "=" * 60)
    if errors:
        print(f"FAILED: {len(errors)} validation errors detected:")
        for err in errors[:10]:
            print(f"  - {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors.")
        sys.exit(1)
    else:
        print("SUCCESS: All benchmark cases passed structural and conversational validation!")
        print("=" * 60)

if __name__ == "__main__":
    validate_benchmark()
