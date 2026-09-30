# TIER-ITS Glossary

Domain vocabulary for the TIER-ITS project. Read this before working in the codebase.

## ITS Concepts

| Term | Full Name | Definition |
|:-----|:----------|:-----------|
| **ITS** | Interpersonal Theory of Suicide | Framework describing psychological states that may contribute to suicidal desire or dangerous behaviour (Van Orden et al. 2010). |
| **TB** | Thwarted Belongingness | Feeling disconnected from others, isolated, not part of a group. An ITS concept. |
| **PB** | Perceived Burdensomeness | Feeling like a burden to others, that others would be better off without you. An ITS concept. |
| **AC** | Acquired Capability | Fearlessness about death and elevated pain tolerance, often through habituation. An ITS concept. |
| **Hopelessness** | — | Belief that the states of TB/PB will not change. Amplifies suicidal desire in ITS. |

## Clinical Instruments

| Term | Full Name | Definition |
|:-----|:----------|:-----------|
| **C-SSRS** | Columbia Suicide Severity Rating Scale | Structured clinical instrument for assessing suicidal thoughts and behaviour. Used as a reference protocol in this project (Posner et al. 2011). |
| **SAFE-T** | Suicide Assessment Five-Step Evaluation and Triage | SAMHSA framework combining inquiry, risk/protective factors, and professional judgement (SAMHSA 2024). |

## Datasets

| Term | Definition |
|:-----|:-----------|
| **IRF dataset** | Interpersonal Risk Factors dataset (Garg et al. 2023). 3,522 Reddit posts with human labels and explanations for TB and PB. Split: 1,972 train / 493 val / 1,057 test. Public. |
| **CLPsych** | Computational Linguistics and Psychology workshop. Source of shared tasks on suicide risk detection. Data access may be restricted. |
| **Controlled benchmark** | The project's main test set. ~160 target statements placed at depths 0, 20, 50, 100 turns. Generated and labelled by construction. |

## System Components

| Term | Definition |
|:-----|:-----------|
| **Evidence ledger** | Structured JSON store recording ITS concepts extracted from conversation turns. Each record contains: concept, direction (supports/rejects/uncertain), turn index, text span, subject, temporality, confidence, and contradiction links. |
| **Evidence record** | A single entry in the ledger. One ITS concept extracted from one turn, with all metadata fields. Defined in `src/schemas/evidence.py`. |
| **Gold ledger** | A ledger filled with correct human labels (not model-extracted). Used as an upper bound to isolate extraction errors from memory design errors. |
| **Concept bottleneck** | Architecture pattern: raw text → human-readable concepts → final output. Enables inspection and correction of intermediate concepts before producing the report (Koh et al. 2020). |
| **Depth** | Number of conversation turns between the target statement and the report query point. The main independent variable in the experiments. |
| **Evidence precision** | How often a cited turn is actually relevant to the ITS concept. |
| **Evidence recall** | How much of the labelled evidence was found by the system. |

## Methods Compared

| Method | Description |
|:-------|:-----------|
| **Target only** | Model sees only the target statement. Easiest possible condition. |
| **Full conversation** | Model receives all turns at once. |
| **Recent window** | Model sees only the latest N turns. |
| **General summary** | An LLM maintains a prose summary of the conversation. |
| **TIER-ITS** | Structured ITS evidence ledger + conversation retrieval + protocol retrieval. |
| **Gold ledger** | TIER-ITS with human-labelled ledger entries instead of model-extracted ones. |
