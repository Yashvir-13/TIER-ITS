import json
import uuid
import random
from typing import List, Dict, Any
from pathlib import Path

# Paths
TEMPLATES_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "benchmark"
OUTPUT_FILE = OUTPUT_DIR / "benchmark_cases.jsonl"

def load_jsonl(filepath: Path) -> List[Dict[str, Any]]:
    if not filepath.exists():
        return []
    with open(filepath, 'r') as f:
        return [json.loads(line) for line in f if line.strip()]

def generate_conversation(
    case_id: str,
    target_turn: Dict[str, Any],
    distractors: List[Dict[str, Any]],
    depth: int
) -> Dict[str, Any]:
    """
    Generates a conversation of roughly 'depth' length, placing the target_turn
    at the appropriate distance from the end.
    """
    # Simply generate dummy context using distractors
    turns = []
    
    # We need to place the target turn 'depth' turns before the end.
    # Total length = depth + some random prefix.
    total_length = depth + random.randint(5, 15)
    target_idx = total_length - depth - 1
    if target_idx < 0:
        target_idx = 0
        total_length = depth + 1
        
    speaker_cycle = ["Patient", "Therapist"]
    
    for i in range(total_length):
        speaker = speaker_cycle[i % 2]
        
        if i == target_idx:
            # Insert target
            turns.append({
                "turn_index": i,
                "speaker": speaker,
                "text": target_turn["text"]
            })
        else:
            # Pick a random distractor that matches the speaker if possible, else generic
            dist = random.choice(distractors)
            turns.append({
                "turn_index": i,
                "speaker": speaker,
                "text": dist["text"]
            })
            
    return {
        "id": case_id,
        "turns": turns
    }

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    tb_cases = load_jsonl(TEMPLATES_DIR / "tb_evidence.jsonl")
    pb_cases = load_jsonl(TEMPLATES_DIR / "pb_evidence.jsonl")
    distractors = load_jsonl(TEMPLATES_DIR / "distractors.jsonl")
    
    if not tb_cases and not pb_cases:
        print("No target cases found in templates. Please add some!")
        return

    if not distractors:
        print("No distractors found. Using fallback distractor.")
        distractors = [{"text": "Can you tell me more about that?"}, {"text": "I see. And how did that make you feel?"}, {"text": "Just been busy with work lately."}]

    depths = [0, 20, 50, 100]
    all_targets = tb_cases + pb_cases
    generated_cases = []
    
    for target in all_targets:
        for depth in depths:
            case_id = f"case_{uuid.uuid4().hex[:8]}_d{depth}"
            conv = generate_conversation(case_id, target, distractors, depth)
            
            benchmark_case = {
                "case_id": case_id,
                "conversation": conv,
                "target_statement": {
                    "turn_index": len(conv["turns"]) - depth - 1,
                    "speaker": conv["turns"][-depth-1]["speaker"] if depth < len(conv["turns"]) else "Unknown",
                    "text": target["text"]
                },
                "target_depth": depth,
                "expected_concept": target.get("concept", "unknown")
            }
            generated_cases.append(benchmark_case)
            
    with open(OUTPUT_FILE, 'w') as f:
        for case in generated_cases:
            f.write(json.dumps(case) + "\n")
            
    print(f"Generated {len(generated_cases)} benchmark cases at {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
