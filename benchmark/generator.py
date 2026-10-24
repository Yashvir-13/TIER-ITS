import json
from typing import List, Dict, Optional
from pathlib import Path
from src.schemas import Conversation, ConversationTurn

class BenchmarkGenerator:
    """
    Generates synthetic controlled benchmark conversations:
    1. Depth Benchmark (160 balanced cases):
       - 80 Positive cases (40 TB, 40 PB) across depths [0, 20, 50, 100].
       - 80 Negative control cases (distress/neutral without suicidal/ITS risk) across depths [0, 20, 50, 100].
    2. Correction Benchmark (48 balanced cases):
       - 24 Genuine resolution cases across gaps [10, 30, 50].
       - 24 Non-correction controls (risk persists) across gaps [10, 30, 50].
    """
    
    def __init__(self, templates_dir: str = "benchmark/templates/"):
        self.templates_dir = Path(templates_dir)
        
    def load_jsonl(self, filename: str) -> List[Dict]:
        file_path = self.templates_dir / filename
        if not file_path.exists():
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
            
    def generate_case(
        self, 
        base_id: str, 
        target_statement: Dict, 
        distractors: List[Dict], 
        depth: int,
        concept: str
    ) -> Conversation:
        """
        Generates a positive conversation where the target_statement is placed exactly `depth` turns from the end.
        """
        turns = []
        turn_index = 0
        
        # 1. Opening context (5 turns of greeting/setup)
        for i in range(5):
            turns.append(ConversationTurn(
                turn_index=turn_index,
                speaker=distractors[i % len(distractors)]["speaker"],
                text=distractors[i % len(distractors)]["text"]
            ))
            turn_index += 1
            
        # 2. Add target statement
        target_turn_index = turn_index
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker=target_statement.get("speaker", "patient"),
            text=target_statement["text"]
        ))
        turn_index += 1
        
        # 3. Add exactly `depth` distractor turns after target
        distractor_offset = 5
        for i in range(depth):
            d_idx = (distractor_offset + i) % len(distractors)
            turns.append(ConversationTurn(
                turn_index=turn_index,
                speaker=distractors[d_idx]["speaker"],
                text=distractors[d_idx]["text"]
            ))
            turn_index += 1
            
        case_id = f"{base_id}_depth_{depth}"
        return Conversation(
            case_id=case_id,
            turns=turns,
            concept=concept,
            nuance_level=target_statement.get("nuance_level", "explicit"),
            initial_turn_index=target_turn_index,
            expected_final_risk=True,
            is_negative_control=False,
            is_non_correction_control=False,
            target_evidence_turns=[target_turn_index]
        )

    def generate_negative_case(
        self,
        base_id: str,
        distress_statement: Dict,
        distractors: List[Dict],
        depth: int
    ) -> Conversation:
        """
        Generates a negative control conversation containing everyday distress/stress without suicidal/ITS risk.
        """
        turns = []
        turn_index = 0
        
        # 1. Opening context (5 turns)
        for i in range(5):
            turns.append(ConversationTurn(
                turn_index=turn_index,
                speaker=distractors[i % len(distractors)]["speaker"],
                text=distractors[i % len(distractors)]["text"]
            ))
            turn_index += 1
            
        # 2. Add distress control statement
        control_turn_index = turn_index
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker=distress_statement.get("speaker", "patient"),
            text=distress_statement["text"]
        ))
        turn_index += 1
        
        # 3. Add depth distractors
        distractor_offset = 5
        for i in range(depth):
            d_idx = (distractor_offset + i) % len(distractors)
            turns.append(ConversationTurn(
                turn_index=turn_index,
                speaker=distractors[d_idx]["speaker"],
                text=distractors[d_idx]["text"]
            ))
            turn_index += 1
            
        case_id = f"{base_id}_depth_{depth}"
        return Conversation(
            case_id=case_id,
            turns=turns,
            concept=None,
            nuance_level="control",
            initial_turn_index=control_turn_index,
            expected_final_risk=False,
            is_negative_control=True,
            is_non_correction_control=False,
            target_evidence_turns=[]
        )
        
    def build_pilot_benchmark(self, output_dir: str = "benchmark/pilot/"):
        """
        Builds the 160-case balanced depth benchmark (80 positive, 80 negative control).
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        
        tb_targets = self.load_jsonl("tb_evidence.jsonl")
        pb_targets = self.load_jsonl("pb_evidence.jsonl")
        distress_controls = self.load_jsonl("distress_controls.jsonl")
        distractors = self.load_jsonl("distractors.jsonl")
        
        if not tb_targets or not pb_targets or not distractors or not distress_controls:
            print("Templates missing. Please check benchmark/templates/")
            return
            
        depths = [0, 20, 50, 100]
        count = 0
        
        # 1. 80 Positive cases (40 TB, 40 PB)
        for targets, prefix, concept in [
            (tb_targets, "tb", "thwarted_belongingness"), 
            (pb_targets, "pb", "perceived_burdensomeness")
        ]:
            for i, target in enumerate(targets):
                nuance = target.get("nuance_level", "explicit")
                for depth in depths:
                    base_id = f"{prefix}_{nuance}_{i}"
                    case = self.generate_case(base_id, target, distractors, depth, concept)
                    case_file = out_path / f"{case.case_id}.json"
                    with open(case_file, "w", encoding="utf-8") as f:
                        f.write(case.model_dump_json(indent=2))
                    count += 1
                    
        # 2. 80 Negative control cases (20 distress statements x 4 depths)
        for i, control_stmt in enumerate(distress_controls):
            category = control_stmt.get("category", "distress")
            for depth in depths:
                base_id = f"ctrl_neg_{category}_{i}"
                case = self.generate_negative_case(base_id, control_stmt, distractors, depth)
                case_file = out_path / f"{case.case_id}.json"
                with open(case_file, "w", encoding="utf-8") as f:
                    f.write(case.model_dump_json(indent=2))
                count += 1
                
        print(f"Depth benchmark generated: {count} balanced cases (80 positive, 80 negative) at {output_dir}")

    def generate_correction_case(
        self,
        pair: Dict,
        distractors: List[Dict],
        gap: int
    ) -> Conversation:
        """
        Generates a realistic clinical conversation with strict turn alternation (Therapist / Patient):
        - Opening check-in
        - Initial risk disclosure & supportive therapist holding response
        - `gap` intervening therapeutic dialogue turns
        - Correction / resolution turn & therapist processing
        - Grounded closing
        """
        turns = []
        turn_index = 0
        
        # 1. Opening turns
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="therapist",
            text="Good morning, come in and have a seat. How has your week been feeling since we last spoke?"
        ))
        turn_index += 1
        
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="patient",
            text="A bit mixed, honestly. Some days were okay, but other times my mind has been in a pretty heavy place."
        ))
        turn_index += 1
        
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="therapist",
            text="What's been sitting with you the most over the past few days?"
        ))
        turn_index += 1
        
        # 2. Initial risk disclosure (Patient: turn 3) & Holding response (Therapist: turn 4)
        initial_turn_idx = turn_index
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="patient",
            text=pair["initial_turn"]["text"]
        ))
        turn_index += 1
        
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="therapist",
            text=pair["therapist_initial_response"]["text"]
        ))
        turn_index += 1
        
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="patient",
            text="Yeah, it's just been sitting heavily with me. Though I have been trying to stick to my day-to-day routine as best as I can."
        ))
        turn_index += 1
        
        # 3. Intervening therapeutic turns
        num_intervening = gap if gap % 2 == 0 else gap + 1
        d_idx = 0
        for _ in range(num_intervening // 2):
            t_turn = distractors[d_idx % len(distractors)]
            t_text = t_turn["text"] if t_turn["speaker"] == "therapist" else "How did that affect your daily routine?"
            turns.append(ConversationTurn(
                turn_index=turn_index,
                speaker="therapist",
                text=t_text
            ))
            turn_index += 1
            d_idx += 1
            
            p_turn = distractors[d_idx % len(distractors)]
            p_text = p_turn["text"] if p_turn["speaker"] == "patient" else "I just tried to take it one step at a time."
            turns.append(ConversationTurn(
                turn_index=turn_index,
                speaker="patient",
                text=p_text
            ))
            turn_index += 1
            d_idx += 1
            
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="therapist",
            text="It sounds like you've been navigating the daily grind as best as you can. How are you feeling right now in this room?"
        ))
        turn_index += 1
        
        # 4. Correction turn (Patient) & Therapist processing
        correction_turn_idx = turn_index
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="patient",
            text=pair["correction_turn"]["text"]
        ))
        turn_index += 1
        
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="therapist",
            text=pair["therapist_correction_response"]["text"]
        ))
        turn_index += 1
        
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="patient",
            text=pair["patient_reflection"]["text"]
        ))
        turn_index += 1
        
        # 5. Grounded closing
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="therapist",
            text="Holding onto that relief and connection is so valuable. As we wrap up today's session, what does the rest of your afternoon look like?"
        ))
        turn_index += 1
        
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="patient",
            text="I'm going to head home, make a warm cup of tea, and just give myself permission to relax."
        ))
        turn_index += 1
        
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="therapist",
            text="That sounds like a gentle, grounding way to close out today. Let's plan to meet same time next week."
        ))
        turn_index += 1
        
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="patient",
            text="Thank you, that sounds good. See you next week."
        ))
        turn_index += 1
        
        case_id = f"{pair['id']}_gap_{gap}"
        return Conversation(
            case_id=case_id,
            turns=turns,
            concept=pair["concept"],
            nuance_level=pair["nuance_level"],
            initial_turn_index=initial_turn_idx,
            correction_turn_index=correction_turn_idx,
            gap=gap,
            expected_final_risk=False,
            is_negative_control=False,
            is_non_correction_control=False,
            target_evidence_turns=[initial_turn_idx]
        )

    def generate_non_correction_case(
        self,
        pair: Dict,
        distractors: List[Dict],
        gap: int
    ) -> Conversation:
        """
        Generates a non-correction control case where the patient maintains and reinforces the initial risk factor.
        """
        turns = []
        turn_index = 0
        
        # 1. Opening turns
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="therapist",
            text="Good morning, come in and have a seat. How has your week been feeling since we last spoke?"
        ))
        turn_index += 1
        
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="patient",
            text="A bit mixed, honestly. Some days were okay, but other times my mind has been in a pretty heavy place."
        ))
        turn_index += 1
        
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="therapist",
            text="What's been sitting with you the most over the past few days?"
        ))
        turn_index += 1
        
        # 2. Initial disclosure
        initial_turn_idx = turn_index
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="patient",
            text=pair["initial_turn"]["text"]
        ))
        turn_index += 1
        
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="therapist",
            text=pair["therapist_initial_response"]["text"]
        ))
        turn_index += 1
        
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="patient",
            text="Yeah, it's just been sitting heavily with me. Though I have been trying to stick to my day-to-day routine as best as I can."
        ))
        turn_index += 1
        
        # 3. Intervening turns
        num_intervening = gap if gap % 2 == 0 else gap + 1
        d_idx = 0
        for _ in range(num_intervening // 2):
            t_turn = distractors[d_idx % len(distractors)]
            t_text = t_turn["text"] if t_turn["speaker"] == "therapist" else "How did that affect your daily routine?"
            turns.append(ConversationTurn(
                turn_index=turn_index,
                speaker="therapist",
                text=t_text
            ))
            turn_index += 1
            d_idx += 1
            
            p_turn = distractors[d_idx % len(distractors)]
            p_text = p_turn["text"] if p_turn["speaker"] == "patient" else "I just tried to take it one step at a time."
            turns.append(ConversationTurn(
                turn_index=turn_index,
                speaker="patient",
                text=p_text
            ))
            turn_index += 1
            d_idx += 1
            
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="therapist",
            text="It sounds like you've been navigating the daily grind as best as you can. How are you feeling right now in this room?"
        ))
        turn_index += 1
        
        # 4. Non-correction control turn (Patient reinforces initial risk)
        ctrl_turn_idx = turn_index
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="patient",
            text=pair["control_turn"]["text"]
        ))
        turn_index += 1
        
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="therapist",
            text=pair["therapist_control_response"]["text"]
        ))
        turn_index += 1
        
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="patient",
            text=pair["patient_reflection"]["text"]
        ))
        turn_index += 1
        
        # 5. Grounded closing
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="therapist",
            text="Thank you for being so honest about how deeply that pain is still present. Let's make sure you take gentle care of yourself this afternoon."
        ))
        turn_index += 1
        
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="patient",
            text="I'll try to just rest. Thank you for listening."
        ))
        turn_index += 1
        
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="therapist",
            text="You're very welcome. We will pick this right back up next week."
        ))
        turn_index += 1
        
        turns.append(ConversationTurn(
            turn_index=turn_index,
            speaker="patient",
            text="See you next week."
        ))
        turn_index += 1
        
        case_id = f"{pair['id']}_gap_{gap}"
        return Conversation(
            case_id=case_id,
            turns=turns,
            concept=pair["concept"],
            nuance_level=pair["nuance_level"],
            initial_turn_index=initial_turn_idx,
            correction_turn_index=None,
            gap=gap,
            expected_final_risk=True,  # Risk is active and NOT corrected
            is_negative_control=False,
            is_non_correction_control=True,
            target_evidence_turns=[initial_turn_idx, ctrl_turn_idx]
        )

    def build_correction_benchmark(self, output_dir: str = "benchmark/correction/"):
        """
        Builds the 48-case balanced correction benchmark:
        - 24 Genuine resolution cases (8 pairs x 3 gaps [10, 30, 50])
        - 24 Non-correction controls (8 pairs x 3 gaps [10, 30, 50])
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        
        pairs = self.load_jsonl("correction_pairs.jsonl")
        non_corr_pairs = self.load_jsonl("non_correction_controls.jsonl")
        distractors = self.load_jsonl("distractors.jsonl")
        
        if not pairs or not non_corr_pairs or not distractors:
            print("Templates missing. Please check benchmark/templates/")
            return
            
        gaps = [10, 30, 50]
        count = 0
        
        # 1. 24 Correction cases
        for pair in pairs:
            for gap in gaps:
                case = self.generate_correction_case(pair, distractors, gap=gap)
                case_file = out_path / f"{case.case_id}.json"
                with open(case_file, "w", encoding="utf-8") as f:
                    f.write(case.model_dump_json(indent=2))
                count += 1
                
        # 2. 24 Non-correction control cases
        for pair in non_corr_pairs:
            for gap in gaps:
                case = self.generate_non_correction_case(pair, distractors, gap=gap)
                case_file = out_path / f"{case.case_id}.json"
                with open(case_file, "w", encoding="utf-8") as f:
                    f.write(case.model_dump_json(indent=2))
                count += 1
                
        print(f"Correction benchmark generated: {count} balanced cases (24 correction, 24 non-correction) at {output_dir}")

if __name__ == "__main__":
    generator = BenchmarkGenerator()
    generator.build_pilot_benchmark()
    generator.build_correction_benchmark()
