# Research Audit, Literature Grounding, and Scientific Remediation for TIER-ITS

**Date**: October 2026  
**Status**: Approved Research Analysis  
**Repository**: `TIER-ITS` (Theory-Indexed Evidence Retrieval for Mental Health Conversations)

---

## 1. Executive Summary & Review Audit

An external scientific review of the TIER-ITS pilot codebase and experimental results concluded:
> *"Worth pursuing, but I would not submit a full efficacy paper from these results as they stand. They support a feasibility pilot: TIER-ITS runs on controlled examples, but the experiments don't show that it improves on full-context prompting or establish clinical risk-detection performance."*

### Key Deficits Identified by the Reviewer:
1. **Uninformative Performance Tied with Full Context**:
   - In 56 depth cases, Full Context and TIER-ITS both scored 56/56 (100%), while Recent Window scored 14/56 (only at depth 0).
   - In 24 correction cases, Full Context scored 24/24, TIER-ITS 23/24, Recent Window 22/24 on report acknowledgment; all three reported 0 active risk.
   - Crucially, **all cases were positive cases** (targets present, or corrections present). Without negative controls, these numbers represent positive-case detection rates—not accuracy, precision, or F1.
2. **Implementation vs. Architectural Claims**:
   - The paper/docs claim $O(1)$ memory scaling and infinite conversational horizon.
   - However, the code (`src/extractor/gemini.py:58`, `src/inference/pipeline.py:28`) sent all patient turns in one monolithic batch API call, passed all turns to a batch contradiction assessor, and dumped all turns into ChromaDB. It was **not** an incremental, bounded-memory streaming state machine.
3. **Severe Experimental Asymmetry**:
   - `SummaryBaseline` (`src/baselines/methods.py:100`) was an empty stub returning `"Summary Baseline not fully implemented yet."`
   - Prompt/Protocol asymmetry: TIER-ITS retrieved full markdown protocol documents (`ProtocolRetriever().get_protocol("SAFE-T")`), whereas Full-Context and Recent-Window baselines were passed only the literal string `"SAFE-T"`.
   - Correction validation checked if *any* ledger record was contradicted (`if r.contradicted:`), rather than confirming that the *target concept* at `initial_turn_index` was specifically updated.
4. **Missing Theoretical & Literature Grounding**:
   - Long-context conversational degradation in suicidal ideation is already established by a July 2026 medRxiv preregistered study (Kalinich et al.). Treating degradation itself as novel is untenable.
   - "Memory for mental-health assessment" is already addressed by AAAI 2026's AgentMental (Hu et al.).
   - The defensible contribution must be **Theory-Indexed Evidence Provenance, Contradiction/Correction, and Inspectable Concept Bottlenecks**, tested against strictly matched baselines under token budget constraints.
5. **Missing Proposal Artifacts & Packaging**:
   - Proposal planned ~160 balanced targets (positive/negative), non-correction controls, genuinely multi-turn evidence, turn-level evidence precision/recall, paired bootstrap confidence intervals (Efron & Tibshirani 1993), and token/latency analysis. None of these were implemented.
   - `requirements.txt` lacked `google-genai`.
   - Missing 3 report files (237 vs 240) due to a filename double-suffix bug (`pb_explicit_0_depth_0_depth_0`).

---

## 2. Primary Literature Positioning & Novelty Defense

To elevate TIER-ITS from a toy pilot to a publishable conference paper (e.g., ACL, EMNLP, CHIL, JAMIA), the project must be positioned rigorously against primary literature.

### 2.1 The Degradation Baseline: Kalinich et al. (medRxiv, July 2026)
- **Primary Source**: Kalinich, M., Luccarelli, J., Santa Maria, J. P., et al. *"Conversational trajectory degrades large language model detection of suicidal ideation relative to clinicians: A preregistered study."* medRxiv, 2026. doi:10.64898/2026.07.10.26357132.
- **Key Findings**: Evaluated 49 LLMs against board-certified clinical psychologists using 400 clinician-validated statements embedded in real psychotherapy trajectories up to 200 turns. While human clinician sensitivity remained stable across trajectory depth, LLM sensitivity steadily degraded due to preceding dialogue distraction and context dispersion. Top proprietary LLMs still achieved high absolute detection in short contexts.
- **Strategic Implication for TIER-ITS**: TIER-ITS must **not** claim the discovery of trajectory degradation. Instead, TIER-ITS takes Kalinich et al.'s empirical finding as an established premise and tests a concrete architectural remedy: **Can an online, theory-indexed symbolic evidence ledger prevent this trajectory degradation, especially when constrained to a realistic token budget?**

### 2.2 Mental Health Dialogue Systems: AgentMental (AAAI 2026)
- **Primary Source**: Hu, J., Wang, A., Xie, Q., Li, Z., Ma, H., Guo, D. *"AgentMental: An interactive multi-agent framework for explainable and adaptive mental health assessment."* Proceedings of the AAAI Conference on Artificial Intelligence, 2026. doi:10.1609/aaai.v40i37.40365.
- **Key Findings**: Multi-agent conversational system using 4 specialized agents (Questioning, Adequacy Evaluation, Scoring, Updating) and a dynamic tree-structured memory for DSM symptom hierarchy tracking across interactive clinical interviews.
- **Strategic Differentiation for TIER-ITS**:
  - AgentMental focuses on *active interviewing* and symptom categorization (DAIC-WOZ).
  - TIER-ITS focuses on *passive longitudinal monitoring and clinical risk triage* under the **Interpersonal Theory of Suicide (ITS)** (Joiner, 2005; Van Orden et al., 2010).
  - TIER-ITS's core novelty is **Symbolic Provenance and Deterministic Belief Revision**:
    1. Turn-anchored verbatim evidence extraction (exact span + speaker attribution + temporality).
    2. Dynamic contradiction resolution (invalidating obsolete risk factors when patients disclose genuine connection or resolution).
    3. Clinician-in-the-loop inspectability & override (Concept Bottleneck Model paradigm, Koh et al., 2020).
    4. Deterministic auditability: An immutable timeline of belief transitions for medico-legal accountability, which probabilistic full-context generation cannot provide (Cochinescu, 2026).

### 2.3 Belief Revision and Verifiable Provenance: Cochinescu (arXiv, Sept 2026)
- **Primary Source**: Cochinescu, C. *"Truth for Believable AI: Expressed Doubt, Provenance, and Belief Revision as an Engineerable Stance."* arXiv:2609.26035, 2026.
- **Key Findings**: Neural language models exhibit probabilistic drift and cannot guarantee acknowledgment soundness across long sequences. Persistent revision stores with typed provenance and explicit belief-state tracking provide a mathematical and structural guarantee of update fidelity.
- **Application to TIER-ITS**: Validates the necessity of the Evidence Ledger. When a patient says at turn 8: *"They'd be better off if I were gone,"* and at turn 38: *"My daughter told me how much she needs me,"* Full Context outputs a narrative blur without machine-readable pointers. TIER-ITS provides an explicit, auditable state transition: `Record(ID=1, Concept=PB, Turn=8, Contradicted=True, ContradictedBy=38)`.

---

## 3. Mathematical Formulation of Online Bounded Memory

To substantiate the asymptotic complexity claims in the paper, TIER-ITS must be implemented as a genuine online stream state machine:

### 3.1 Asymptotic Token Complexity
Let $N$ be the total conversation turns, with average turn length $L$ tokens.
- **Full-Context Baseline**:
  At each assessment step $t$, the full conversation prefix $1 \dots t$ is ingested:
  $$\text{Cumulative Tokens}_{\text{FullContext}} = \sum_{t=1}^N t \cdot L = \frac{N(N+1)}{2} L = \mathcal{O}(N^2)$$
- **Summary Baseline**:
  Maintains a running summary $\mathcal{S}_t$ of size $|\mathcal{S}| \le K$. At each update interval $W$, ingests $\mathcal{S}_{t-W}$ plus recent $W$ turns:
  $$\text{Tokens per update} = K + W \cdot L = \mathcal{O}(1)$$
  $$\text{Cumulative Tokens}_{\text{Summary}} = \frac{N}{W} (K + W \cdot L) = \mathcal{O}(N)$$
- **TIER-ITS (Online Stream State Machine)**:
  For each incoming turn $t$:
  1. **Turn Extraction**: Evaluates turn $t$ with local context (turn $t-1$, turn $t$):
     $$\text{Cost}_{\text{extract}}(t) = 2 L \cdot c_{\text{prompt}} = \mathcal{O}(1)$$
  2. **Contradiction Check**: Evaluates active ledger items $|\mathcal{L}_{\text{active}}|$ against turn $t$:
     $$\text{Cost}_{\text{contradict}}(t) \le |\mathcal{L}_{\text{active}}| \cdot L \cdot c_{\text{prompt}} = \mathcal{O}(1) \quad (\text{since } |\mathcal{L}_{\text{active}}| \le C_{\max} \ll N)$$
  3. **Report Generation**: At assessment point $t$, ingests only active ledger records $\mathcal{L}_{\text{active}}$, top-$k$ retrieved turns (where $k \le 5$), and protocol guidelines $\mathcal{P}$:
     $$\text{Cost}_{\text{report}} = (|\mathcal{L}_{\text{active}}| + k \cdot L + |\mathcal{P}|) = \mathcal{O}(1)$$
  4. **Total Cumulative Cost**:
     $$\text{Cumulative Tokens}_{\text{TIER-ITS}} = \sum_{t=1}^N \mathcal{O}(1) = \mathcal{O}(N)$$

By transitioning from $O(N^2)$ to $O(N)$, TIER-ITS achieves **constant marginal cost per turn** and **bounded context length**, making multi-session longitudinal monitoring computationally tractable.

---

## 4. Remediation Blueprint: Architecture, Benchmark, & Evaluation

To address every critique raised in the review, the following four pillars must be implemented:

```
+----------------------------------------------------------------------------------------------------+
|                                    TIER-ITS REMEDIATION BLUEPRINT                                   |
+------------------------------------+---------------------------------+-----------------------------+
| 1. ARCHITECTURE & INFERENCE        | 2. BENCHMARK ENRICHMENT         | 3. RIGOROUS EVALUATION      |
+------------------------------------+---------------------------------+-----------------------------+
| - Online Turn-by-Turn Orchestration| - 160 Balanced Depth Cases:     | - Metrics Suite:            |
|   (process_stream / stream_turn)   |   * 80 Positive (TB, PB)        |   * Concept P / R / F1      |
| - Implement SummaryBaseline        |   * 80 Negative Controls        |   * Evidence Turn P / R     |
|   (recursive rolling summary)      | - 48 Balanced Correction Cases: |   * Specificity / FPR       |
| - Implement TargetOnlyBaseline     |   * 24 Correction Cases         |   * False Resolution Rate   |
|   (upper-bound isolated ceiling)   |   * 24 Non-Correction Controls  | - Paired Bootstrap 95% CIs  |
| - Implement GoldLedgerBaseline     | - Genuinely Multi-Turn Evidence |   (1,000 resamples)         |
|   (disentangles extraction errors) |   (fragmented across 2-3 turns) | - Token Count & Latency     |
| - Symmetric Protocol Ingestion     | - Fix naming duplication bug    |   (empirical cost curves)   |
|   (identical SAFE-T prompt text)   |   (_depth_0_depth_0)            | - Concept Override Test     |
| - Target-Specific Contradiction    |                                 |   (RQ4b Clinician-in-loop)  |
|   (checks initial_turn_index & ID) |                                 |                             |
+------------------------------------+---------------------------------+-----------------------------+
```

### 4.1 Benchmark Construction: Balance & Controls
1. **Depth Experiment (160 cases)**:
   - Depths: $D \in [0, 20, 50, 100]$.
   - 80 Positive Cases: 40 Thwarted Belongingness (20 explicit, 10 implicit, 10 fragmented) + 40 Perceived Burdensomeness (20 explicit, 10 implicit, 10 fragmented) across the 4 depths.
   - 80 Negative Control Cases: Distress/everyday conversations without suicidal ideation, TB, or PB (e.g., job stress, somatic pain, grief without ideation, hobbies) across the 4 depths.
2. **Correction Experiment (48 cases)**:
   - Gaps: $G \in [10, 30, 50]$.
   - 24 Correction Cases: Initial risk at $t_{\text{init}}$, followed at $t_{\text{corr}}$ by genuine cognitive reframing, reconnection, or relief.
   - 24 Non-Correction Controls: Initial risk at $t_{\text{init}}$, followed at $t_{\text{ctrl}}$ by neutral dialogue or reinforcement of feelings (expected active risk = True, resolution acknowledged = False).
3. **Multi-Turn Fragmented Evidence**:
   - Construct targets spanning 2 to 3 consecutive turns rather than single isolated sentences.

### 4.2 Matched Baselines & Evaluation Harness
1. **Full-Context Baseline**: Receives all turns up to the current turn + retrieved protocol text.
2. **Recent-Window Baseline**: Receives the last $W=10$ turns + retrieved protocol text.
3. **Summary Baseline**: Maintains a rolling clinical summary updated incrementally every $W=10$ turns + retrieved protocol text.
4. **Target-Only Baseline**: Evaluates only the target utterance + retrieved protocol text (empirical upper bound on extraction capabilities).
5. **Gold-Ledger Baseline**: Ingests ground-truth EvidenceRecords directly into the ledger, bypassing the extraction LLM to evaluate retrieval and report synthesis in isolation.
6. **TIER-ITS (Online Ledger)**: Runs incremental streaming extraction, updates the ledger, resolves contradictions, retrieves relevant turns via semantic search, and compiles the clinical report.

### 4.3 Metrics & Statistical Significance
- **Classification Performance**:
  $$\text{Precision} = \frac{TP}{TP + FP}, \quad \text{Recall} = \frac{TP}{TP + FN}, \quad F_1 = \frac{2 \cdot P \cdot R}{P + R}, \quad \text{Specificity} = \frac{TN}{TN + FP}$$
- **Evidence Provenance Performance**:
  $$\text{Evidence Precision} = \frac{|\text{Retrieved/Cited Turns} \cap \text{Ground Truth Evidence Turns}|}{|\text{Retrieved/Cited Turns}|}$$
  $$\text{Evidence Recall} = \frac{|\text{Retrieved/Cited Turns} \cap \text{Ground Truth Evidence Turns}|}{|\text{Ground Truth Evidence Turns}|}$$
- **Contradiction Soundness**:
  $$\text{Resolution Fidelity} = \frac{\text{Correctly Invalidated Cases}}{\text{Total Correction Cases}}$$
  $$\text{False Resolution Rate} = \frac{\text{Mistakenly Invalidated Cases}}{\text{Total Non-Correction Control Cases}}$$
- **Paired Bootstrap Confidence Intervals**:
  For metric difference $\Delta = M_{\text{TIER}} - M_{\text{baseline}}$, compute 95% percentile bootstrap intervals with $B = 1,000$ paired resamples clustered by base scenario.
- **Resource Profiling**: Track prompt tokens, completion tokens, API cost ($USD), and wall-clock latency per session.

---

## 5. Summary Table: Review Criticism vs. Concrete Remediation

| Review Criticism | Root Cause in Code | Scientific Remediation in This Plan |
|:---|:---|:---|
| **Tie with Full Context on depth (56/56)** | Only positive cases evaluated; 0 negative cases. | Add 80 negative control cases; compute true Precision, Recall, Specificity, and F1 across depths. |
| **No advantage in correction (23 vs 24)** | Only correction cases evaluated; no non-correction controls. | Add 24 non-correction controls; evaluate False Resolution Rate and Active Risk Specificity. |
| **Not incremental/bounded memory** | `batch_extract` and `check_contradictions_batch` run on all turns at once. | Implement true streaming online pipeline (`process_stream`), processing turn-by-turn with token accounting. |
| **Summary baseline is a stub** | `SummaryBaseline.generate_report` returns placeholder string. | Implement genuine rolling-summary baseline updating every $W$ turns. |
| **Prompt/Protocol asymmetry** | Baselines received literal `"SAFE-T"`, TIER-ITS retrieved full markdown protocol. | Standardize protocol injection: all methods receive identical retrieved protocol text. |
| **Correction checked *any* record** | Loop checked `if r.contradicted: break` without checking concept or turn index. | Match against target concept and `initial_turn_index` specifically. |
| **Missing Gold-Ledger & Target-Only** | Only FC, RW, and TIER were implemented. | Add `GoldLedgerBaseline` and `TargetOnlyBaseline` per proposal. |
| **Missing Evidence Metrics & CI** | Only binary judge used; no turn-level scoring or bootstrap CI. | Implement `evaluation/metrics.py` with turn P/R, paired bootstrap 95% CI, and cost logging. |
| **Missing `google-genai` in requirements** | Undeclared dependency causing external test collection failure. | Add `google-genai>=0.1.0` to `requirements.txt`. |
| **Report file count mismatch (237 vs 240)** | `_depth_0_depth_0` duplicate naming glitch skipped saving reports for 1 case. | Fix generator ID generation; verify 100% complete report artifact generation. |

