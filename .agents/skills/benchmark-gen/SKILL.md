---
name: benchmark-gen
description: Generate or extend the controlled conversation benchmark. Use when creating target statements, conversation templates, correction pairs, or distractor turns for the ITS evaluation benchmark.
---

# Benchmark Generation

The benchmark is the project's primary scientific instrument. Precision in construction determines whether the experiments measure what they claim. Every case must be:

- **Labelled by construction**: the target label and evidence span are known because we placed them deliberately.
- **Depth-controlled**: the same target statement placed at depths 0, 20, 50, and 100 turns.
- **Reviewed**: two independent checks that surrounding context hasn't changed the intended meaning of the target.

## Target: ~160 statements

Balanced between statements with and without relevant evidence, across the depth levels.

## Templates

Templates live in `benchmark/templates/`. Each is a JSONL file where one line = one case:

| File | Content |
|:--|:--|
| `tb_evidence.jsonl` | Thwarted belongingness cases |
| `pb_evidence.jsonl` | Perceived burdensomeness cases |
| `correction_pairs.jsonl` | Before/after correction cases (paired) |
| `distractors.jsonl` | Unrelated filler turns |

## Hard cases (from proposal §5.2)

The benchmark must include these realistic language cases:

1. Relevant evidence followed by a long unrelated discussion.
2. Historical evidence versus a current feeling.
3. A quotation or statement about another person (not the speaker).
4. Negation, uncertainty, and sarcasm.
5. An early statement that is later corrected.
6. Separate TB and PB evidence appearing far apart in the conversation.
7. Protective information introduced after concerning evidence.

## Ethics constraints

1. **No method or means details** in generated text — ever.
2. Examples must be paraphrased and stripped of identifying details.
3. Generated conversations must avoid graphic content.
4. If using real data (IRF dataset), respect the dataset agreement terms.

## After generation

Run `benchmark/validate.py` to check:
- Structural integrity (all required fields present).
- Depth placement is correct.
- No accidental duplicate targets.
- Distractor text doesn't contain unintended ITS signals.

Then have two reviewers independently check a sample of completed conversations.
