"""
Script to generate publication-grade figures for TIER-ITS paper and repository.
Generates:
1. figures/depth_retention_curves.pdf & .png
2. figures/streaming_token_complexity.pdf & .png
3. figures/belief_revision_timeline.pdf & .png
"""

import os
os.environ["MPLCONFIGDIR"] = os.path.abspath("data/cache/matplotlib")
os.makedirs("data/cache/matplotlib", exist_ok=True)
os.makedirs("figures", exist_ok=True)

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# Set publication style
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "lines.linewidth": 2.2,
    "lines.markersize": 7,
    "grid.alpha": 0.35,
    "grid.linestyle": "--",
    "axes.edgecolor": "#333333",
    "axes.linewidth": 1.0,
})

PRIMARY_COLOR = "#1F3A5F"  # Navy matching main.tex
ACCENT_GREEN = "#2A7B4C"
ACCENT_RED = "#B22222"
ACCENT_PURPLE = "#6A3D9A"
ACCENT_ORANGE = "#D95F02"
COLOR_GRAY = "#777777"


def plot_depth_retention_curves():
    """Generates Figure 2: Recall / Sensitivity vs. Distractor Depth."""
    depths = [0, 20, 50, 100]

    # Data from Table 2 in paper (N=20 positive cases per depth)
    tier_recall = [100.0, 100.0, 100.0, 100.0]
    fc_recall = [100.0, 100.0, 100.0, 100.0]
    rw_recall = [100.0, 0.0, 0.0, 0.0]
    sb_recall = [100.0, 100.0, 95.0, 85.0]
    gen_recall = [95.0, 95.0, 90.0, 95.0]

    fig, ax = plt.subplots(figsize=(7.5, 4.6), dpi=300)

    # Plot baselines
    ax.plot(depths, fc_recall, label="Full Context (monolithic oracle)", color="#4A90E2", linestyle=":", marker="o", alpha=0.85)
    ax.plot(depths, rw_recall, label="Recent Window ($W=10$)", color=ACCENT_RED, linestyle="-.", marker="x", alpha=0.9)
    ax.plot(depths, sb_recall, label="Summary Baseline (rolling prose)", color=ACCENT_ORANGE, linestyle="--", marker="s", alpha=0.9)
    ax.plot(depths, gen_recall, label="Generic Quote Ledger (unindexed)", color=ACCENT_PURPLE, linestyle="-.", marker="^", alpha=0.85)
    
    # Plot TIER-ITS with thick line
    ax.plot(depths, tier_recall, label=r"TIER-ITS (Ours, bounded $K \leq 10$)", color=PRIMARY_COLOR, linestyle="-", marker="D", linewidth=3.0, markersize=8)

    # Annotations highlighting critical findings
    ax.annotate("Catastrophic Forgetting\n(0.0% at D >= 20)",
                xy=(20, 0), xytext=(24, 18),
                arrowprops=dict(facecolor=ACCENT_RED, shrink=0.08, width=1.2, headwidth=6),
                fontsize=9.5, fontweight="bold", color=ACCENT_RED)

    ax.annotate("Compression Decay\n(85.0% at D=100)",
                xy=(100, 85), xytext=(68, 68),
                arrowprops=dict(facecolor=ACCENT_ORANGE, shrink=0.08, width=1.2, headwidth=6),
                fontsize=9.5, fontweight="bold", color=ACCENT_ORANGE)

    ax.annotate("TIER-ITS & Full Context\n(100.0% across all depths)",
                xy=(50, 100), xytext=(30, 86),
                arrowprops=dict(facecolor=PRIMARY_COLOR, shrink=0.08, width=1.2, headwidth=6),
                fontsize=9.5, fontweight="bold", color=PRIMARY_COLOR)

    ax.set_xlabel("Distractor Depth $D$ (Intervening Conversational Turns)", labelpad=8)
    ax.set_ylabel("Positive Risk Sensitivity / Recall (%)", labelpad=8)
    ax.set_title("Clinical Risk Evidence Retention Across Conversational Depth", pad=12, fontweight="bold")
    ax.set_xticks(depths)
    ax.set_ylim(-5, 108)
    ax.grid(True)
    ax.legend(loc="lower left", frameon=True, framealpha=0.92, facecolor="#FDFDFD")

    plt.tight_layout()
    fig.savefig("figures/depth_retention_curves.pdf", bbox_inches="tight")
    fig.savefig("figures/depth_retention_curves.png", bbox_inches="tight")
    plt.close(fig)
    print("Saved figures/depth_retention_curves.pdf and .png")


def plot_token_complexity():
    """Generates Figure: Cumulative Streaming Token Scaling."""
    N = np.linspace(1, 2000, 200)
    L = 25  # average tokens per turn

    # Full context: sum_{t=1}^N t * L = N(N+1)/2 * L
    tokens_fc = (N * (N + 1) / 2) * L

    # Summary baseline: N/W * (K + W*L) where W=10, K=150 tokens summary
    tokens_sb = (N / 10.0) * (150 + 10 * L)

    # TIER-ITS: N * (2*L + K_active*L_quote) where local extract is ~2 turns, check is K active
    tokens_tier = N * (2 * L * 2 + 5 * 15)  # bounded constant per turn

    fig, ax = plt.subplots(figsize=(7.5, 4.6), dpi=300)

    ax.plot(N, tokens_fc / 1e6, label="Full-Context Prompting $\\mathcal{O}(N^2)$", color=ACCENT_RED, linestyle="-", linewidth=2.8)
    ax.plot(N, tokens_sb / 1e6, label="Summary Baseline $\\mathcal{O}(N)$", color=ACCENT_ORANGE, linestyle="--", linewidth=2.4)
    ax.plot(N, tokens_tier / 1e6, label="TIER-ITS Online Stream $\\mathcal{O}(N)$", color=PRIMARY_COLOR, linestyle="-", linewidth=3.0)

    # Annotate end points
    ax.scatter([2000], [tokens_fc[-1] / 1e6], color=ACCENT_RED, s=60, zorder=5)
    ax.scatter([2000], [tokens_tier[-1] / 1e6], color=PRIMARY_COLOR, s=60, zorder=5)

    ax.annotate("Quadratic Explosion\n(>50 Million tokens)",
                xy=(2000, tokens_fc[-1] / 1e6), xytext=(1450, 40),
                arrowprops=dict(facecolor=ACCENT_RED, shrink=0.08, width=1.2, headwidth=6),
                fontsize=9.5, fontweight="bold", color=ACCENT_RED)

    ax.annotate("Bounded Linear Scaling\n(<0.4 Million tokens; >99% reduction)",
                xy=(2000, tokens_tier[-1] / 1e6), xytext=(1150, 8),
                arrowprops=dict(facecolor=PRIMARY_COLOR, shrink=0.08, width=1.2, headwidth=6),
                fontsize=9.5, fontweight="bold", color=PRIMARY_COLOR)

    ax.set_xlabel("Total Conversational Turns ($N$)", labelpad=8)
    ax.set_ylabel("Cumulative Streaming Tokens (Millions)", labelpad=8)
    ax.set_title("Real-Time Streaming Token Complexity Scaling", pad=12, fontweight="bold")
    ax.set_xlim(0, 2100)
    ax.set_ylim(-1, 55)
    ax.grid(True)
    ax.legend(loc="upper left", frameon=True, framealpha=0.92, facecolor="#FDFDFD")

    plt.tight_layout()
    fig.savefig("figures/streaming_token_complexity.pdf", bbox_inches="tight")
    fig.savefig("figures/streaming_token_complexity.png", bbox_inches="tight")
    plt.close(fig)
    print("Saved figures/streaming_token_complexity.pdf and .png")


def plot_architecture_schematic():
    """Generates Figure: High-resolution visual architecture schematic PNG/PDF."""
    fig, ax = plt.subplots(figsize=(10.5, 5.8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Box styles
    bbox_turn = dict(boxstyle="round,pad=0.6", facecolor="#EBF3FB", edgecolor="#4A90E2", linewidth=1.5)
    bbox_extract = dict(boxstyle="round,pad=0.6", facecolor="#FFF2E6", edgecolor="#D95F02", linewidth=1.5)
    bbox_active = dict(boxstyle="round,pad=0.7", facecolor="#E8F5E9", edgecolor="#2A7B4C", linewidth=2.0)
    bbox_archive = dict(boxstyle="round,pad=0.7", facecolor="#F3E5F5", edgecolor="#7B1FA2", linewidth=1.5)
    bbox_override = dict(boxstyle="round,pad=0.6", facecolor="#FFEBEE", edgecolor="#C62828", linewidth=1.5)
    bbox_report = dict(boxstyle="round,pad=0.7", facecolor="#E0F2F1", edgecolor="#00695C", linewidth=2.0)

    # 1. Incoming stream
    ax.text(12, 85, "Patient Turn t\n& Local Context (t-1, t)", ha="center", va="center", bbox=bbox_turn, fontsize=9.5, fontweight="bold")

    # Arrow to extractor
    ax.annotate("", xy=(12, 68), xytext=(12, 77), arrowprops=dict(facecolor="#333333", width=1.5, headwidth=6))

    # 2. Concept Extractor
    ax.text(12, 60, "ITS Concept Extractor\n(Thwarted Belongingness / PB / AC)\nO(1) local prompt", ha="center", va="center", bbox=bbox_extract, fontsize=9)

    # Arrow to Contradiction Assessor & Router
    ax.annotate("", xy=(28, 60), xytext=(22, 60), arrowprops=dict(facecolor="#333333", width=1.5, headwidth=6))

    # 3. Router / Contradiction Assessor
    ax.text(40, 60, "Contradiction Assessor\nChecks Turn t against\nActive Records (K <= 10)", ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.6", facecolor="#FFFDE7", edgecolor="#FBC02D", linewidth=1.5), fontsize=9, fontweight="bold")

    # Arrows to Two Tiers
    ax.annotate("", xy=(58, 75), xytext=(50, 65), arrowprops=dict(facecolor="#2A7B4C", width=1.5, headwidth=6))
    ax.annotate("", xy=(58, 45), xytext=(50, 55), arrowprops=dict(facecolor="#7B1FA2", width=1.5, headwidth=6))

    # 4. Tier 1: Active Working Set
    ax.text(70, 77, "Tier 1: Bounded Active Set (L_active)\nCapacity K <= 10 records\nUnrefuted active risk only\nO(1) prompt working set",
            ha="center", va="center", bbox=bbox_active, fontsize=9.5, fontweight="bold", color="#1B5E20")

    # 5. Tier 2: Archival Log
    ax.text(70, 43, "Tier 2: Archival Audit Log (L_archive)\nAppend-only historical store\nInvalidated & evicted records (t_refuted)\nFull medico-legal auditability O(N)",
            ha="center", va="center", bbox=bbox_archive, fontsize=9, color="#4A148C")

    # Invalidation arrow from Active to Archive
    ax.annotate("Refuted / Evicted\n(t_refuted = t_corr or -2)",
                xy=(70, 52), xytext=(70, 68),
                arrowprops=dict(facecolor=ACCENT_RED, width=1.5, headwidth=6),
                ha="center", fontsize=8.5, fontweight="bold", color=ACCENT_RED)

    # 6. Clinician Override Box
    ax.text(40, 20, "Clinician-in-the-Loop Override Seam\nmanual_override(turn_index, active)\nSets sentinel -1 without touching transcript",
            ha="center", va="center", bbox=bbox_override, fontsize=9, fontweight="bold", color="#B71C1C")
    ax.annotate("", xy=(60, 20), xytext=(53, 20), arrowprops=dict(facecolor="#C62828", width=1.5, headwidth=6))
    ax.annotate("", xy=(68, 35), xytext=(68, 25), arrowprops=dict(facecolor="#C62828", width=1.5, headwidth=6))

    # 7. Downstream Report Synthesis
    ax.text(92, 60, "SAFE-T Report\nSynthesis\n(Steps 1--5)\nO(1) Prompt Size",
            ha="center", va="center", bbox=bbox_report, fontsize=9.5, fontweight="bold", color="#004D40")
    ax.annotate("", xy=(84, 75), xytext=(80, 75), arrowprops=dict(facecolor="#00695C", width=1.5, headwidth=6))
    ax.annotate("", xy=(92, 68), xytext=(86, 75), arrowprops=dict(facecolor="#00695C", width=1.5, headwidth=6))

    # Title Banner
    ax.text(50, 95, "TIER-ITS: Two-Tier Neuro-Symbolic Conversational Memory Architecture",
            ha="center", va="center", fontsize=13, fontweight="bold", color=PRIMARY_COLOR)

    plt.tight_layout()
    fig.savefig("figures/architecture_diagram.pdf", bbox_inches="tight")
    fig.savefig("figures/architecture_diagram.png", bbox_inches="tight")
    plt.close(fig)
    print("Saved figures/architecture_diagram.pdf and .png")


def plot_belief_revision_timeline():
    """Generates Figure: Dynamic Belief Revision Timeline and Concept Bottleneck."""
    fig, ax = plt.subplots(figsize=(10.5, 5.0), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Timeline line
    ax.plot([10, 90], [50, 50], color="#999999", linewidth=3, zorder=1)

    # Key timeline points
    points = [18, 50, 82]
    for p in points:
        ax.scatter([p], [50], color=PRIMARY_COLOR, s=120, zorder=3)

    # Step 1: Disclosure
    bbox_d = dict(boxstyle="round,pad=0.5", facecolor="#FFEBEE", edgecolor="#C62828", linewidth=1.5)
    ax.text(18, 75, "Turn t = 8: Initial Risk Disclosure\n\"They'd be better off if I were dead\"\nConcept: Perceived Burdensomeness (PB)",
            ha="center", va="center", bbox=bbox_d, fontsize=8.5, fontweight="bold", color="#B71C1C")
    ax.annotate("", xy=(18, 53), xytext=(18, 65), arrowprops=dict(facecolor="#C62828", width=1.5, headwidth=6))

    # Ledger State 1
    bbox_s1 = dict(boxstyle="square,pad=0.4", facecolor="#FFFDE7", edgecolor="#FBC02D", linewidth=1.2)
    ax.text(18, 28, "Ledger State:\nRecord(ID=1, Concept=PB, Turn=8,\ncontradicted=False, active=True)\nIn L_active (Working Set)",
            ha="center", va="center", bbox=bbox_s1, fontsize=8.0, color="#333333")
    ax.annotate("", xy=(18, 38), xytext=(18, 47), arrowprops=dict(facecolor="#FBC02D", width=1.2, headwidth=5))

    # Step 2: Gap / Distractors
    ax.text(50, 58, "30 Intervening Distractor Turns (G = 30)\nEveryday topics, therapeutic holding\nPB Record safely preserved in L_active",
            ha="center", va="center", fontsize=8.5, style="italic", color="#555555")

    # Step 3: Reframing / Correction
    bbox_c = dict(boxstyle="round,pad=0.5", facecolor="#E8F5E9", edgecolor="#2A7B4C", linewidth=1.5)
    ax.text(82, 75, "Turn t = 38: Cognitive Reframing\n\"My daughter called today... made me\nrealize how much they need me around\"",
            ha="center", va="center", bbox=bbox_c, fontsize=8.5, fontweight="bold", color="#1B5E20")
    ax.annotate("", xy=(82, 53), xytext=(82, 65), arrowprops=dict(facecolor="#2A7B4C", width=1.5, headwidth=6))

    # Ledger State 2: Atomic Invalidation
    bbox_s2 = dict(boxstyle="square,pad=0.4", facecolor="#E0F2F1", edgecolor="#00695C", linewidth=1.2)
    ax.text(82, 28, "Atomic State Transition:\nRecord(ID=1, contradicted=True,\ncontradicted_by=38)\nEvicted from L_active -> L_archive\nReport: 0 Active Risk; 1 Protective Factor",
            ha="center", va="center", bbox=bbox_s2, fontsize=8.0, fontweight="bold", color="#004D40")
    ax.annotate("", xy=(82, 38), xytext=(82, 47), arrowprops=dict(facecolor="#00695C", width=1.2, headwidth=5))

    # Title
    ax.text(50, 94, "Dynamic Belief Revision: Turn-Anchored Evidence Invalidation & Triage",
            ha="center", va="center", fontsize=12.5, fontweight="bold", color=PRIMARY_COLOR)

    plt.tight_layout()
    fig.savefig("figures/belief_revision_timeline.pdf", bbox_inches="tight")
    fig.savefig("figures/belief_revision_timeline.png", bbox_inches="tight")
    plt.close(fig)
    print("Saved figures/belief_revision_timeline.pdf and .png")


if __name__ == "__main__":
    plot_depth_retention_curves()
    plot_token_complexity()
    plot_architecture_schematic()
    plot_belief_revision_timeline()
    print("All publication figures successfully generated in figures/ directory!")
