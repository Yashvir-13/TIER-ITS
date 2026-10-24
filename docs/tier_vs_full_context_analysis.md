# Architectural & Empirical Analysis: TIER-ITS vs. Full-Context Prompting

**Target Venue**: ACL / EMNLP / JAMIA / CHIL  
**Topic**: Comparing Structured Evidence Ledgers and Full-Context Prompting in Longitudinal Mental Health Conversations  
**Date**: October 2026  

---

## Executive Summary: Addressing the "Full Context Parity" Dilemma

When evaluating TIER-ITS against baseline architectures on a 60–100 turn single-session benchmark, a superficial glance at raw classification accuracy might suggest parity:
- **Depth Retention (RQ1/RQ2)**: TIER-ITS (100.0%) vs. Full Context (100.0%)
- **Active Risk False Positives (RQ4)**: TIER-ITS (0.0%) vs. Full Context (0.0%)
- **Ledger Invalidation Fidelity (RQ4)**: TIER-ITS (100.0%, 24/24) vs. Full Context (N/A)
*(Note on Resolution Acknowledgment: On the final 48-case correction benchmark, TIER-ITS achieves 100% (24/24) structured ledger invalidation and 0.0% active risk false positives, matching Full Context's narrative resolution score (100.0%, 24/24). An earlier pilot report-level LLM-judge narrative evaluation on free-form summary text scored 95.8% (23/24); that free-form narrative metric is distinct from the exact structured ledger state invalidation evaluated in the benchmark).*

This raises an essential scientific and peer-review question:
> *"If Full-Context prompting achieves 100% on raw narrative acknowledgment without an external memory system, why is TIER-ITS necessary? How can we claim TIER-ITS is fundamentally better in an academic paper?"*

The answer lies in understanding that **raw single-session classification accuracy within short contexts (<4,000 tokens) is an evaluation artifact**. Testing Full Context on a 60-turn conversation uses less than **0.3%** of a modern LLM's context window. 

In longitudinal clinical settings, psychiatric care spans **multiple multi-hour sessions across months (1,000–5,000+ turns)**. In this real-world deployment regime, re-prompting the full conversation at every turn introduces compounding latency and costs, while lacking verifiable provenance.

Rather than claiming categorical superiority on raw synthetic accuracy—where Full Context and TIER-ITS perform at parity ($F1=1.00$) on the current single-session benchmark—TIER-ITS introduces distinct **architectural and clinical trade-offs**:
1. **Bounded Working State & Operational Token Scaling (Theoretical $\mathcal{O}(N)$ vs $\mathcal{O}(N^2)$ Streaming Complexity)**
2. **Deterministic Provenance & Auditability (Direct Turn Attribution)**
3. **Clinician-in-the-Loop Inspectability & Mutable Override (Explicit Ledger Operations)**
4. **Protocol-Grounded Prompt Structuring (Condensed SAFE-T Framing)**
5. **Mitigation of Long-Context Needle Degradation (*Lost in the Middle*)**

---

## 1. Operational Complexity & Token Scaling (Streaming Deployment Analysis)

### Operational Formulation (Online vs. Offline)
*Important Evaluation Clarification:* In our offline benchmark experiments, all baselines (including Full Context) were evaluated once at the conclusion of the conversation. The following analysis characterizes **real-time streaming deployment** where a clinical assistant monitors patient risk sequentially at each turn $t \in [1, N]$.

- **Full-Context Prompting in Real-Time Streaming**:
  If the full conversation history must be re-sent to the LLM at each turn $t$ to assess emerging risk:
  $$\text{Cumulative Streaming Tokens}_{\text{FullContext}} = \sum_{t=1}^N \mathcal{O}(t) = \mathcal{O}(N^2)$$
  For an extended therapeutic dialogue with $N = 2,000$ turns:
  $$\text{Total Tokens} \approx 25 \times \frac{2000 \times 2001}{2} \approx 50,025,000 \text{ tokens}$$
  This leads to compounding latency (TTFT), high deployment costs, and eventual prompt limit exhaustion.

- **TIER-ITS (Online Stream State Machine)**:
  Each turn $t$ is evaluated online with a bounded local context window $(t-1, t)$:
  $$\text{Turn Extraction Prompt} = \mathcal{O}(1)$$
  The active clinical state is maintained in an external **Evidence Ledger** capped at $K \le 10$ active records.
  At report generation time, the prompt ingests only active ledger items ($K \le 10$) and top-$k$ retrieved protocol guidelines:
  $$\text{Report Generation Prompt Tokens} = |\mathcal{L}_{\text{active}}| + k = \mathcal{O}(1) \text{ bounded working set}$$
  $$\text{Cumulative Streaming Tokens}_{\text{TIER-ITS}} = \mathcal{O}(N)$$
  *Note on System Memory:* While the active working set for report synthesis is bounded ($K \le 10$), total system memory scales linearly ($\mathcal{O}(N)$) because historical records are retained for regulatory auditability and turns are indexed in the episodic vector store (ChromaDB).

### Literature Context
- **Terranova et al. (EurIPS 2025, arXiv:2510.23730)**, *"Evaluating Long-Term Memory for Long-Context Question Answering"*:
  Empirically established that structured, memory-augmented architectures reduce token consumption by **over 90%** compared to repeated full-context prompting while maintaining competitive downstream task accuracy.
- **Packer et al. (arXiv:2310.08560)**, *"MemGPT: Towards LLMs as Operating Systems"*:
  Demonstrated that virtual context management and tiered paging are mandatory prerequisites for multi-session conversational continuity beyond toy context windows.

---

## 2. Symbolic Provenance vs. Black-Box Paraphrase (The "N/A" Deficit)

Examining the experimental results table reveals the core architectural difference:

| Metric | TIER-ITS | Full Context | Research & Traceability Implication |
|:---|:---:|:---:|:---|
| **Ledger Invalidation Rate** | **100.0%** (24/24) | **N/A (No Ledger)** | Full context has no internal state representation |
| **Exact Turn Identification** | **100.0%** (24/24) | **N/A** | Compared baseline does not maintain structured turn pointers |
| **Auditable Evidence Graph** | **Yes** (Structured records) | **No** (Unstructured text) | Enables verifiable turn-level provenance |

### Why Structured State Tracking Matters
In longitudinal conversational systems, an AI that produces unstructured narrative summaries like:
> *"The patient previously felt like a burden, but is feeling better now after speaking with family."*

leaves the exact origins of risk statements opaque and difficult to verify independently.

For rigorous conversational evaluation and auditability:
1. **Which turn originated the risk?** Full Context does not maintain a machine-readable pointer to the turn index. TIER-ITS points to `turn_index: 8`, linking to the verbatim utterance: `"They'd be better off if I was gone"`.
2. **Which turn resolved it?** Full Context blends historical information in the prompt. TIER-ITS explicitly records `contradicted_by_turn: 38`, capturing the specific dialogue turn that contextualized the earlier disclosure.
3. **Auditability**: For retrospective qualitative evaluation, TIER-ITS provides a structured log of every state transition, whereas unstructured prompt generation can vary across runs.

### Literature Support
- **Cochinescu (arXiv:2609.26035, Sept 2026)**, *"Truth for Believable AI: Expressed Doubt, Provenance, and Belief Revision as an Engineerable Stance"*:
  Proves that persistent revision stores with typed provenance and explicit belief state tracking achieve a **by-construction guarantee of acknowledgment soundness (100%)**, which probabilistic language model prompts cannot guarantee without an externalized symbolic layer.
- **Zhang et al. (IEEE / arXiv:2602.00353, Jan 2026)**, *"MHDash: An Online Platform for Benchmarking Mental Health-Aware AI Assistants"*:
  Showed that conventional aggregate evaluation metrics obscure risk-specific failure modes, and that clinical reliability mandates fine-grained, turn-level auditable attribution.

---

## 3. Programmatic Inspectability & Manual Ledger Override (RQ4b)

In structured safety-critical dialogue systems, externalized state allows **human-in-the-loop inspection and deterministic override capability**.

### The Full-Context "Immutable Black Box" Problem
Suppose an LLM operating under Full Context misinterprets an ironic remark or patient metaphor as active suicidal intent, or conversely, dismisses genuine veiled intent as resolved.
- **How does a supervisor correct Full Context?**
  They cannot directly intervene at the state level. An operator cannot modify neural network weights, clear the KV-cache selectively, or alter the raw historical dialogue transcript (which is legally protected). On subsequent turns or future reports, prompting the full context will re-expose the unguided model to the exact same transcript ambiguities.

### The TIER-ITS Architecture
In TIER-ITS, memory is decoupled from the model into a symbolic **Evidence Ledger**:
- The ledger state can be programmatically inspected at any turn:
  - `EvidenceRecord(turn_index=8, concept=ITSConcept.PERCEIVED_BURDENSOMENESS, evidence_text="...", contradicted=False)`
- An operator can invoke the explicit override method:
  - `ledger.manual_override(record_turn_index=8, active=False, concept=ITSConcept.PERCEIVED_BURDENSOMENESS)`
  - This marks `contradicted = True` and records `contradicted_by_turn = -1` (sentinel indicating manual override)
  - It immediately resynchronizes the bounded active working set (`_active_records`)
- When subsequent reports or summaries are generated, the prompt builder queries `get_active_evidence()`, excluding invalidated records from active risk sections.

---

## 4. Protocol-Grounded Structuring: SAFE-T Summary Framing

Full Context treats dialogue summarization as a generic text synthesis problem. In our experiment, Full Context achieved high resolution acknowledgment by noting that the patient seemed reassured.

However, psychiatric triage frameworks emphasize structured categorization of both risks and protective factors.
Using the **SAFE-T (Suicide Assessment Five-step Evaluation and Triage)** framework:
- **Step 1: Identify Risk Factors** (Suicidal ideation, burdensomeness, hopelessness).
- **Step 2: Identify Protective Factors** (Internal coping, family bonds, reasons for living).
- **Step 3: Conduct Suicide Inquiry**.
- **Step 4: Determine Risk Level**.
- **Step 5: Document and Intervene**.

### How TIER-ITS Structures Reporting with Protocol Guidance
When an initial disclosure of Perceived Burdensomeness (Turn 8) is contradicted at Turn 38:
1. TIER-ITS marks the evidence as `contradicted = True` in the ledger.
2. The report generator explicitly moves the resolution out of active danger and synthesizes it under **Step 2 (Protective Factors)** using the bundled condensed protocol summary:
   > *"Under Step 2, the patient demonstrates an emergent protective factor via the resolution of perceived burdensomeness, recognizing that cognitive distortions clouded their perception of family support and expressing genuine connection."*
3. This provides structured documentation grounded in the condensed guideline summary (without claiming clinical protocol certification or diagnostic compliance).

---

## 5. Robustness Against Long-Context Attention Degradation

Why did Full Context appear to perform so well on our Phase 6 and Phase 7 benchmarks?
Because our benchmark evaluated conversations up to 106 turns (~3,000–4,000 tokens).

In literature, modern LLMs with 1M token windows easily handle a single "needle" inside 3,000 tokens. However, extensive academic literature documents what happens as conversation length and distractor density scale to realistic clinical dimensions:

### Literature Evidence
1. **Liu et al. (TACL 2023, arXiv:2307.03172) - *Lost in the Middle***:
   - Evaluated language models across long input contexts and discovered severe "U-shaped" performance degradation: information located in the middle of input context suffers substantial retrieval and reasoning failure compared to information placed at the immediate start or end.
   - In longitudinal therapy transcripts, critical disclosures made in Session 4 of 16 reside precisely in this vulnerable middle zone.

2. **Kuratov et al. (NeurIPS 2024, arXiv:2406.10149) - *BABILong Benchmark***:
   - Tested LLMs on reasoning across scattered facts in long documents (up to millions of tokens).
   - **Key Finding**: Popular commercial LLMs effectively utilize only **10–20% of their advertised context window** when multi-fact reasoning or contradiction resolution is required, suffering catastrophic drops in accuracy as distractor volume expands.

3. **Maharana et al. (Snap Research / UNC, arXiv:2402.17753) - *LoCoMo: Long-Context Conversation Modeling***:
   - Evaluated LLMs on 300+ turn, 35-session dialogues.
   - **Key Finding**: Long-context LLMs struggle significantly to track temporal dynamics, belief revisions, and causal event transitions over extended dialogue turns.

4. **Wang et al. (arXiv:2504.04150) - *Reasoning on Multiple Needles in a Haystack***:
   - Found that as input context grows, LLMs systematically shorten their internal reasoning steps and suffer from attention dilution across distracting dialogue.

TIER-ITS is designed to mitigate this degradation: because dialogue turns are processed sequentially and tracked in structured ledger records, downstream summary generation does not rely solely on long-range in-context search over large raw transcripts.

---

## 6. How to Frame this in the Research Paper (Paper Writing Strategy)

When writing the paper, the experimental section should be framed as follows:

### Suggested Table & Framing for Paper Results Section

#### Table 1: Multi-Dimensional Evaluation of Conversational Risk Architectures
| Evaluation Dimension | Full Context | Recent Window ($N=10$) | TIER-ITS (Ours) |
|:---|:---:|:---:|:---:|
| **Depth Recall (Depth 100)** | 100.0% | 0.0% | **100.0%** (Parity) |
| **Active Risk Hallucination (FP)** | 0.0% | 0.0% | **0.0%** |
| **Exact Turn Provenance** | $\times$ (None) | $\times$ (None) | **100.0%** (Structured Ledger) |
| **Auditable Belief Revision** | $\times$ (Implicit) | $\times$ (Lossy) | **100.0%** (State Transitions) |
| **External State Mutation / Override** | $\times$ (Unstructured prompt edits) | $\times$ (Unstructured prompt edits) | **Supported** (Explicit Ledger CRUD API) |
| **Report Working Memory** | $\mathcal{O}(N)$ (Full dialogue) | $\mathcal{O}(W)$ (Local window) | $\mathcal{O}(1)$ (Bounded working set $K \le 10$) |
| **Streaming Tokens per Turn (Theoretical)** | $\mathcal{O}(t)$ | $\mathcal{O}(W)$ (lossy) | $\mathcal{O}(1)$ (bounded window) |
| **Cumulative Streaming Tokens (Theoretical)** | $\mathcal{O}(N^2)$ | $\mathcal{O}(N \cdot W)$ | $\mathcal{O}(N)$ |
| **Protocol Structuring (SAFE-T Summary)** | Unstructured | Fragmented | **Structured (Step 1–5 Grounding)** |

*Note on Evaluation:* In the offline empirical benchmark, all methods were executed once at session end. The token complexities above model real-time turn-by-turn streaming monitoring. Total system storage for TIER-ITS is $\mathcal{O}(N)$ due to archival audit logs and episodic vector retrieval. Provenance metrics evaluate structured ledger record turn indices (`tier_evidence_turns`), not inline citations in free-form narrative reports.

### Core Narrative for the Paper
1. **"Parity on Synthetic Accuracy, Structural Advantages in Architecture"**:
   Matching Full Context ($F1=1.00$) demonstrates that structured extraction accurately preserves detectable risk signals on this synthetic benchmark, while constraining the active working set ($K \le 10$) and theoretical streaming token scaling ($\mathcal{O}(N)$).
2. **"Auditability and Provenance in Conversational AI"**:
   Highlight that in high-stakes dialogue domains, an ungrounded classification score from a black-box model lacks verifiable provenance and explicit state control; TIER-ITS grounds decisions in verifiable turn indices.
3. **"State Grounding vs In-Context Drift"**:
   Drawing on the literature (*Lost in the Middle*, *BABILong*), an explicit Interpersonal Theory of Suicide (ITS) ledger provides structured state tracking to help guard against prompt degradation over long dialogues.
4. **"Research Scope & Synthetic Evaluation"**:
   Acknowledge that all evaluations are synthetic and LLM-judged without independent human clinical review; this study establishes structural and computational feasibility rather than clinical efficacy.
