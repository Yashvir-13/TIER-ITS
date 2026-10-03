import json
from typing import List, Dict
from pathlib import Path
from src.schemas import Conversation, ConversationTurn

class BenchmarkGenerator:
    """
    Deep module to generate the synthetic controlled benchmark conversations.
    It takes target statements (evidence) and distractors (noise) and places 
    the target at precise depths (0, 20, 50, 100 turns from the end).
    """
    
    def __init__(self, templates_dir: str = "benchmark/templates/"):
        self.templates_dir = Path(templates_dir)
        
    def load_jsonl(self, filename: str) -> List[Dict]:
        file_path = self.templates_dir / filename
        if not file_path.exists():
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f]
            
    def generate_case(self, case_id: str, target_statement: Dict, distractors: List[Dict], depth: int) -> Conversation:
        """
        Generates a conversation where the target_statement is exactly `depth` turns from the end.
        
        Args:
            case_id: Unique identifier for this case.
            target_statement: The specific turn containing the ITS evidence.
            distractors: A pool of unrelated turns to use as padding.
            depth: How many turns *after* the target statement should exist.
            
        Returns:
            A Conversation object.
        """
        turns = []
        turn_index = 0
        
        # 1. Add some initial context (e.g. 5 turns of greeting/setup)
        for i in range(5):
            turns.append(ConversationTurn(
                turn_index=turn_index,
                speaker=distractors[i]["speaker"],
                text=distractors[i]["text"]
            ))
            turn_index += 1
            
        # 2. Add the target statement
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker=target_statement["speaker"],
            text=target_statement["text"]
        ))
        target_turn_index = turn_index
        turn_index += 1
        
        # 3. Add exactly `depth` number of distractor turns after the target
        distractor_offset = 5 # we used 5 already
        for i in range(depth):
            # cycle through distractors if we run out
            d_idx = (distractor_offset + i) % len(distractors)
            turns.append(ConversationTurn(
                turn_index=turn_index,
                speaker=distractors[d_idx]["speaker"],
                text=distractors[d_idx]["text"]
            ))
            turn_index += 1
            
        return Conversation(case_id=f"{case_id}_depth_{depth}", turns=turns)
        
    def build_pilot_benchmark(self, output_dir: str = "benchmark/pilot/"):
        """
        Builds the entire pilot benchmark of ~160 cases.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        
        tb_targets = self.load_jsonl("tb_evidence.jsonl")
        pb_targets = self.load_jsonl("pb_evidence.jsonl")
        distractors = self.load_jsonl("distractors.jsonl")
        
        if not tb_targets or not distractors:
            print("Templates missing. Please populate benchmark/templates/*.jsonl")
            return
            
        depths = [0, 20, 50, 100]
        
        # Simple loop for the pilot: place each target at each depth
        for targets, prefix in [(tb_targets, "tb"), (pb_targets, "pb")]:
            for i, target in enumerate(targets):
                nuance = target.get("nuance_level", "unknown")
                for depth in depths:
                    case_id = f"{prefix}_{nuance}_{i}_depth_{depth}"
                    case = self.generate_case(case_id, target, distractors, depth)
                    
                    # Save the generated case
                    # The case object might have its id appended with _depth_X internally 
                    # from generate_case, but let's just use what generate_case returned.
                    case_file = out_path / f"{case.case_id}.json"
                    with open(case_file, "w", encoding="utf-8") as f:
                        f.write(case.model_dump_json(indent=2))
                        
        print(f"Pilot benchmark generated at {output_dir}")
