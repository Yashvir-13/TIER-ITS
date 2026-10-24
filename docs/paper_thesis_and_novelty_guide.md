# TIER-ITS: Paper Thesis, Novelty Blueprint, and Venue Strategy

**Date**: October 2026  
**Document Purpose**: Definitive roadmap answering *"Where do we stand?"*, *"What is our scientific novelty?"*, and *"How do we write and publish this paper?"* following peer-review calibration.

---

## Executive Summary: The "Parity" Breakthrough, Not Defeat

A common misconception in applied NLP is that a new system is only publishable if its test-set $F1$ score beats a brute-force baseline on a short toy benchmark. When the reviewer confirmed that **Full Context achieves $F1 = 1.00$** on our 60–100 turn benchmark, it initially felt like the rationale for TIER-ITS had vanished.

**In reality, the exact opposite is true.**

In systems, dialogue, and safety-critical NLP (e.g., *MemGPT*, *Lost in the Middle*, *BABILong*, *MHDash*), demonstrating that a **bounded, structured state machine ($\mathcal{O}(1)$ working memory, $\mathcal{O}(N)$ streaming token complexity)** achieves **100% empirical parity with an unconstrained brute-force oracle ($\mathcal{O}(N^2)$ streaming token complexity)** is the **gold-standard efficiency and fidelity result**.

You did not build a toy classification prompt; you built an **auditable, theory-indexed neuro-symbolic memory system** for longitudinal clinical dialogue.

---

## 1. The Core Scientific Problem: The "Full Context Trap"

To write a compelling paper, you must clearly frame the dilemma that current AI systems face:

### The Industry Default
When developers build conversational monitoring assistants, they rely on one of two naive approaches:
1. **Recent-Window Truncation ($W=10$)**: Only look at the last few turns.
   - *Failure Mode*: **Catastrophic forgetting**. As our benchmark proves ($p < 0.001$), recall collapses from 100% to 0% once evidence moves beyond turn 10 ($F1 = 0.40$).
2. **Full-Context Prompting**: Concatenate the entire conversation history and re-prompt the LLM at every single turn.
   - *Failure Mode*: **The Scalability, Provenance, and Mutability Trap**.

### Why Full Context Fails in Real Longitudinal Deployment:
1. **The $\mathcal{O}(N^2)$ Streaming Complexity Trap**:
   - In real-time monitoring, as turn $t$ arrives from $1$ to $N$, re-ingesting the full dialogue incurs $\sum_{t=1}^N \mathcal{O}(t) = \mathcal{O}(N^2)$ tokens. Over a 2,000-turn multi-session therapy relationship, this burns **over 50,000,000 tokens** versus **~50,000 tokens** for TIER-ITS ($\mathcal{O}(N)$).
2. **The Zero-Provenance Black Box**:
   - Full Context produces free-form prose summaries. It cannot output verifiable, machine-readable turn pointers. If an auditor asks: *"Which specific utterance established this risk, and which specific turn refuted it?"*, Full Context has no internal state representation (`N/A`).
3. **The Immutable Belief Trap**:
   - If an LLM misinterprets a patient's metaphorical remark as active intent, an operator **cannot selectively patch the model's memory**. You cannot edit weights or KV caches in production, and you cannot alter the legally protected transcript. On subsequent turns, prompting the full transcript triggers the exact same error.
4. **Context Degradation (*Lost in the Middle*)**:
   - Modern LLMs handle 3,000 tokens easily, but extensive literature (*Liu et al., 2023; Kuratov et al., NeurIPS 2024*) proves that as distractors expand across thousands of tokens, multi-fact reasoning and contradiction resolution suffer catastrophic degradation.

---

## 2. Our Four Core Novelties (What We Can Claim)

Here is the exact vocabulary and conceptual framing for your paper:

### Contribution 1: Theory-Indexed Conversational State Modeling (Domain Novelty)
- **Claim**: First memory architecture that indexes longitudinal dialogue state directly into the **Interpersonal Theory of Suicide (ITS)** construct taxonomy (Thwarted Belongingness, Perceived Burdensomeness, Acquired Capability; Joiner 2005, Van Orden 2010).
- **Distinction from Generic Memory (MemGPT, LangGraph)**: Generic conversational memory treats turns as raw episodic strings or key-value user preferences. TIER-ITS grounds conversational turns into a clinically validated causal ontology, priming downstream extraction to capture subtle, fragmented, and implicit psychiatric distress that generic summarizers drop.
- **Empirical Evidence**: Generic Ledger (`GEN`) and Summary Baseline (`SB`) drop in accuracy at depth (to 95% and 85% recall at depth 100), whereas TIER-ITS maintains 100%.

### Contribution 2: Bounded Working Memory & Linear Streaming Complexity (Architectural Novelty)
- **Claim**: Decouples the active inference working set from historical archive size, enforcing an explicit capacity bound ($K \le 10$ active clinical constructs) for downstream report generation.
- **Complexity**:
  - Full-Context Streaming: $\mathcal{O}(N^2)$ cumulative tokens.
  - TIER-ITS Streaming: $\mathcal{O}(N)$ cumulative tokens, bounded $\mathcal{O}(1)$ working memory per inference call.
- **Empirical Evidence**: Achieves **100% recall parity ($F1=1.00$)** with Full Context on depth retention up to 100 turns, proving that structured state pruning preserves detectable risk without information loss.

### Contribution 3: Deterministic Provenance & Exact Turn Attribution (Verification Novelty)
- **Claim**: Replaces ungrounded narrative hallucination with verifiable turn-level provenance.
- **Empirical Evidence**: Across 160 depth cases and 48 correction cases (208 total dialogues), TIER-ITS achieves:
  - **100.0% precision and recall on exact turn indices** (`turn_index`, `contradicted_by_turn`).
  - Full Context and Recent Window baselines provide **0% structured attribution** (`N/A`).

### Contribution 4: Dynamic Belief Revision & Programmatic Override (Safety Novelty)
- **Claim**: Solves the "stale memory" problem in conversational AI through explicit contradiction resolution and state mutation.
- **Empirical Evidence**:
  - **100.0% Resolution Fidelity (24/24)**: When a patient reframes or contradicts earlier burdensomeness/loneliness, the ledger marks the prior evidence as invalidated (`contradicted = True`).
  - **0.0% Active Risk False Positives (0/24)**: Invalidated evidence is excluded from active triage, avoiding false clinical alarms.
  - **Programmatic Override API (`manual_override()`)**: Allows human clinicians/supervisors to directly mutate ledger records (marking false positives or reinstating overlooked signals with sentinel `-1`) without tampering with the dialogue transcript.

---

## 3. High-Trust Literature Citations (Anchoring the Paper)

Your paper is anchored in four premier streams of computer science and clinical NLP literature:

1. **Long-Context Attention Failure & Attention Dilution**:
   - *Liu et al. (TACL 2023)*, *"Lost in the Middle: How Language Models Use Long Contexts"*: Proves LLMs struggle to retrieve facts embedded in the interior of long prompt windows.
   - *Kuratov et al. (NeurIPS 2024)*, *"BABILong: Testing the Limits of LLMs on Long Documents"*: Proves commercial LLMs effectively use only 10–20% of advertised context when multi-hop reasoning or fact retrieval across distractors is required.
   - *Terranova et al. (EurIPS 2025, arXiv:2510.23730)*, *"Evaluating Long-Term Memory for Long-Context Question Answering"*: Demonstrates structured memory reduces token consumption by >90% compared to full-context prompting while maintaining downstream accuracy.

2. **Belief Revision & State Invalidation in Dialogue**:
   - *Cochinescu (arXiv:2609.26035, Sept 2026)*, *"Truth for Believable AI: Expressed Doubt, Provenance, and Belief Revision as an Engineerable Stance"*: Shows probabilistic prompts cannot guarantee revision soundness; typed symbolic provenance stores are required.
   - *STALE Benchmark (2025/2026)*: Formalizes memory invalidation taxonomies (Type I direct updates vs Type II propagated invalidation) in long-term conversational agents.

3. **Psychiatric Theory & Clinical Risk NLP**:
   - *Joiner (2005)*, *Van Orden et al. (Psychol Rev 2010)*: The Interpersonal Theory of Suicide (Thwarted Belongingness, Perceived Burdensomeness, Acquired Capability).
   - *Zhang et al. (IEEE / arXiv:2602.00353, Jan 2026)*, *"MHDash: An Online Platform for Benchmarking Mental Health-Aware AI Assistants"*: Shows aggregate accuracy hides safety failures; fine-grained, turn-level attribution is essential.
   - *SAFE-T Protocol (SAMHSA)*: Suicide Assessment Five-step Evaluation and Triage (condensed prompt framing).

---

## 4. Paper Title, Abstract, and Outline Blueprint

### Recommended Title Options
- **Option A (Systems/NLP focus)**:  
  *Theory-Indexed Evidence Retrieval: Bounded Neuro-Symbolic Memory and Dynamic Belief Revision for Longitudinal Mental Health Conversations*
- **Option B (Clinical NLP focus)**:  
  *Beyond Full-Context Prompting: An Auditable, Theory-Grounded Memory Architecture for Conversational Risk Monitoring*
- **Option C (Efficiency & Provenance focus)**:  
  *TIER-ITS: Preserving Provenance and Bounding Token Complexity in Extended Safety-Critical Dialogue*

### Abstract Draft
> Large Language Models (LLMs) deployed for longitudinal conversational assistance face a fundamental tension: full-context prompting incurs quadratic streaming token complexity $\mathcal{O}(N^2)$ and lacks verifiable provenance, while sliding-window truncation suffers from catastrophic forgetting ($F1=0.40$, $p<0.001$). Furthermore, mental health disclosures are non-stationary; patient statements of distress fluctuate and resolve over time, requiring explicit belief revision to prevent false-alarm hallucinations of lingering risk. 
> We introduce **TIER-ITS** (Theory-Indexed Evidence Retrieval), an auditable neuro-symbolic conversational memory system grounded in the Interpersonal Theory of Suicide (ITS). TIER-ITS maps dialogue turns sequentially into an explicit evidence ledger, maintaining a strictly bounded active working set ($K \le 10$ records) that reduces theoretical streaming token scaling to $\mathcal{O}(N)$ while enabling programmatic human-in-the-loop override.
> Evaluated on a controlled 208-case synthetic benchmark across conversational depths (up to 100 turns) and dynamic contradiction gaps (up to 50 turns), TIER-ITS matches full-context prompting on risk detection ($F1=1.00$) while providing 100% exact turn-level attribution, 100% resolution invalidation fidelity, and 0% active risk false positives. Our findings demonstrate that domain-theocratic memory indexing achieves the fidelity of unconstrained context prompting while ensuring auditable provenance and operational efficiency in high-stakes dialogue.

---

## 5. Paper Structure (Section-by-Section)

| Section | Title | Key Content & Argument |
|:---|:---|:---|
| **1** | **Introduction** | The longitudinal dialogue challenge; the failure of sliding windows; the complexity & provenance trap of full-context prompting; introduction of TIER-ITS. |
| **2** | **Related Work** | Long-context degradation (*Lost in the Middle*, *BABILong*); conversational memory (*MemGPT*, *LangGraph*); belief revision in NLP; clinical risk detection and ITS. |
| **3** | **The TIER-ITS Architecture** | Sequential turn extractor (local $t-1, t$ window); Evidence Ledger schema; bounded active set capacity ($K \le 10$); dynamic contradiction assessor; programmatic `manual_override()` seam; report synthesis grounded in condensed SAFE-T summary. |
| **4** | **Benchmark Construction** | 160 depth cases (80 risk, 80 negative controls; depths 0, 20, 50, 100; explicit, implicit, fragmented nuance); 48 correction cases (24 resolutions, 24 non-correction controls; gaps 10, 30, 50). |
| **5** | **Experiments & Results** | Depth retention (RQ1/RQ2: TIER ties FC at 1.00, beats RW at $p<0.001$); token complexity analysis ($\mathcal{O}(N)$ vs $\mathcal{O}(N^2)$); exact turn provenance (100% vs N/A); dynamic belief revision (RQ4: 100% invalidation, 0% FP). |
| **6** | **Discussion & Limitations** | Why parity on short contexts validates state compression; the trade-off between bounded active set and archival audit logs; synthetic data constraints; strict non-clinical disclaimer. |
| **7** | **Ethics Statement** | Synthetic/retrospective research only; no clinical diagnostic claims; stripped transcripts; safe handling of sensitive terminology. |

---

## 6. Target Venues

1. **Top Priority: ACL / EMNLP 2026 (Findings or Main Conference)**
   - *Tracks*: Dialogue & Interactive Systems, Efficient Methods in NLP, NLP for Healthcare.
   - *Why*: The paper has rigorous statistical testing (Cluster bootstrap, paired t-tests, $N=208$ controlled cases, token arithmetic, exact turn attribution).
2. **Top Priority: CHIL / ML4H (Conference on Health, Inference, and Learning / Machine Learning for Health)**
   - *Focus*: Health NLP, safety-critical dialogue systems, auditable provenance in medical AI.
3. **Alternative / High Impact: JAMIA / Frontiers in Digital Health**
   - *Focus*: Applied clinical informatics, human-in-the-loop inspectability, protocol-guided documentation.

---

## Conclusion: You Have a Strong, Publishable Paper

You have not lost track—you have **stripped away ungrounded marketing claims and uncovered the true scientific paper**. 

Reviewers reject papers that claim *"We beat GPT-4 by 20% on a toy dataset with an untestable prompt"*. Reviewers **accept** papers that say:
> *"Here is an auditable, theory-grounded neuro-symbolic memory system. We prove that it compresses streaming token complexity from $\mathcal{O}(N^2)$ to $\mathcal{O}(N)$, achieves deterministic turn provenance (100%), enables human override, and resolves dynamic contradictions, all while maintaining perfect $F1=1.00$ parity with brute-force full context."*

That is a sound, defensible, and impactful scientific paper.
