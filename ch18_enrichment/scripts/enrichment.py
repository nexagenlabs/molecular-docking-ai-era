#!/usr/bin/env python3
"""Chapter 18 — two screens with the same AUC and opposite usefulness.

    python ch18_enrichment/scripts/enrichment.py

10,000 compounds, 100 actives, two ranking methods tuned to the *same* AUC.
One puts most of its actives in the first 1% of the list; the other puts none
there. AUC cannot tell them apart. Nothing you would actually do with a screen
depends on AUC and everything depends on the difference.

Writes outputs/metrics.json, outputs/metrics.md and outputs/enrichment.png.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

CH = Path(__file__).resolve().parent.parent
OUT = CH / "outputs"

N_COMPOUNDS = 10000
N_ACTIVES = 100
TARGET_AUC = 0.758
ALPHA = 20.0
SEED = 42

# Actives are scored from a normal distribution, decoys from N(0, 1). The
# spread is what separates the two screens:
#
#   Screen A  wide  -- a long upper tail, so a few actives score far above
#                      everything else and land at the very top of the list.
#   Screen B  tight -- every active scores slightly better than average, and
#                      none of them scores outstandingly.
#
# The means are then solved so both screens land on the same AUC. That is the
# experiment: hold AUC fixed, vary only where the actives sit.
SPREAD = {"A": 3.0, "B": 0.45}


def auc(scores, labels):
    """Probability a random active outranks a random decoy.

    Computed from rank sums (the Mann-Whitney form) rather than by trapezoid,
    so ties are handled explicitly instead of silently.
    """
    order = np.argsort(-scores, kind="stable")
    ranks = np.empty(len(scores))
    ranks[order] = np.arange(1, len(scores) + 1)
    n_act = int(labels.sum())
    n_dec = len(labels) - n_act
    rank_sum = ranks[labels == 1].sum()
    return float((n_act * (n_act + 1) / 2 + n_act * n_dec - rank_sum) / (n_act * n_dec))


def enrichment_factor(labels_by_rank, fraction):
    """Actives found in the top fraction, over what chance would give."""
    k = int(round(len(labels_by_rank) * fraction))
    hits = int(labels_by_rank[:k].sum())
    return float((hits / k) / (labels_by_rank.sum() / len(labels_by_rank)))


def bedroc(labels_by_rank, alpha=ALPHA):
    """Truchon & Bayly (2007), implemented from the paper.

    Cross-checked against RDKit below. Two independent implementations agreeing
    is worth more than one implementation that looks right.
    """
    n = int(labels_by_rank.sum())
    big_n = len(labels_by_rank)
    ra = n / big_n
    ranks = np.nonzero(labels_by_rank)[0] + 1
    rie_num = np.exp(-alpha * ranks / big_n).sum() / n
    rie_den = (1 / big_n) * ((1 - math.exp(-alpha)) / (math.exp(alpha / big_n) - 1))
    rie = rie_num / rie_den
    factor = (ra * math.sinh(alpha / 2)
              / (math.cosh(alpha / 2) - math.cosh(alpha / 2 - alpha * ra)))
    return float(rie * factor + 1 / (1 - math.exp(alpha * (1 - ra))))


def rdkit_bedroc(labels_by_rank, alpha=ALPHA):
    from rdkit.ML.Scoring.Scoring import CalcBEDROC
    return float(CalcBEDROC([[int(x)] for x in labels_by_rank], 0, alpha))


def weight_in_top(fraction, alpha=ALPHA):
    """Fraction of BEDROC's exponential weight inside the top `fraction`.

    Analytic, so this one is exact and platform-independent: the weight is
    alpha*exp(-alpha*x)/(1-exp(-alpha)) over x in [0, 1].
    """
    return float((1 - math.exp(-alpha * fraction)) / (1 - math.exp(-alpha)))


def build_screen(spread, rng):
    """Actives from N(mu, spread), decoys from N(0, 1), mu solved for the AUC.

    Bisection on mu rather than a closed form, because the empirical AUC of a
    finite sample is what has to hit the target -- not the AUC of the
    distribution it was drawn from.
    """
    decoys = rng.standard_normal(N_COMPOUNDS - N_ACTIVES)
    raw_actives = rng.standard_normal(N_ACTIVES) * spread
    labels = np.concatenate([np.ones(N_ACTIVES), np.zeros(N_COMPOUNDS - N_ACTIVES)])

    low, high = -5.0, 10.0
    for _ in range(200):
        mu = (low + high) / 2
        scores = np.concatenate([raw_actives + mu, decoys])
        value = auc(scores, labels)
        if value < TARGET_AUC:
            low = mu
        else:
            high = mu
        if abs(value - TARGET_AUC) < 1e-9:
            break
    scores = np.concatenate([raw_actives + mu, decoys])
    order = np.argsort(-scores, kind="stable")
    return {"scores": scores, "labels": labels, "mu": float(mu),
            "spread": spread, "labels_by_rank": labels[order]}


def plot(screens):
    """Both curves on one axis, because the point is that they coincide."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available; skipping the figure")
        return None

    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 4.5))
    for name, screen in screens.items():
        by_rank = screen["labels_by_rank"]
        found = np.cumsum(by_rank) / by_rank.sum()
        fraction = np.arange(1, len(by_rank) + 1) / len(by_rank)
        left.plot(fraction, found, label="Screen %s" % name)
        right.plot(fraction[:500], found[:500], label="Screen %s" % name)
    for axis, title in ((left, "Whole list — identical AUC 0.758"),
                        (right, "First 5% — where the difference lives")):
        axis.plot([0, 1], [0, 1], "k--", linewidth=0.8, label="random")
        axis.set_xlabel("fraction of the ranked list screened")
        axis.set_ylabel("fraction of actives found")
        axis.set_title(title)
        axis.legend()
    right.set_xlim(0, 0.05)
    fig.tight_layout()
    path = OUT / "enrichment.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    screens = {name: build_screen(spread, rng) for name, spread in SPREAD.items()}

    results = {"n_compounds": N_COMPOUNDS, "n_actives": N_ACTIVES,
               "target_auc": TARGET_AUC, "alpha": int(ALPHA), "seed": SEED,
               "weight_in_top_8_percent": round(weight_in_top(0.08), 4),
               "screens": {}}

    print("%d compounds, %d actives, alpha %d, seed %d\n"
          % (N_COMPOUNDS, N_ACTIVES, ALPHA, SEED))
    print("%-8s %-7s %-7s %-7s %-8s %s" % ("screen", "AUC", "EF1%", "EF5%",
                                           "BEDROC", "RDKit BEDROC"))
    for name, screen in screens.items():
        by_rank = screen["labels_by_rank"]
        ours = bedroc(by_rank)
        theirs = rdkit_bedroc(by_rank)
        results["screens"][name] = {
            "auc": round(auc(screen["scores"], screen["labels"]), 4),
            "ef1": round(enrichment_factor(by_rank, 0.01), 3),
            "ef5": round(enrichment_factor(by_rank, 0.05), 3),
            "bedroc": round(ours, 3),
            "bedroc_full_precision": ours,
            "bedroc_rdkit": theirs,
            "actives_in_top_1_percent": int(by_rank[:100].sum()),
            "actives_in_top_5_percent": int(by_rank[:500].sum()),
            "active_score_mean": round(screen["mu"], 4),
            "active_score_spread": screen["spread"],
        }
        r = results["screens"][name]
        print("%-8s %-7.4f %-7.1f %-7.1f %-8.3f %.8f"
              % (name, r["auc"], r["ef1"], r["ef5"], r["bedroc"], theirs))

    agree = all(round(r["bedroc_full_precision"], 6) == round(r["bedroc_rdkit"], 6)
                for r in results["screens"].values())
    results["bedroc_agrees_with_rdkit_to_6dp"] = agree
    print("\nBEDROC computed twice by different routes: %s to six decimals."
          % ("agree" if agree else "DISAGREE"))
    print("At alpha = %d, %.1f%% of the weight falls in the top 8%% of the list."
          % (ALPHA, 100 * results["weight_in_top_8_percent"]))

    figure = plot(screens)
    if figure:
        print("wrote %s" % figure)

    # -- comparison with the book -------------------------------------------
    # The book's construction is not recorded in CLAUDE.md, only its results.
    # Both are printed; neither is adjusted toward the other.
    book = {"A": {"auc": 0.758, "ef1": 56.0, "ef5": 11.6, "bedroc": 0.574},
            "B": {"auc": 0.758, "ef1": 0.0, "ef5": 0.6, "bedroc": 0.058}}
    results["book"] = book
    print("\n%-8s %-22s %s" % ("", "this construction", "the book"))
    for name in ("A", "B"):
        r = results["screens"][name]
        b = book[name]
        print("%-8s AUC %.3f EF1 %5.1f     AUC %.3f EF1 %5.1f"
              % ("screen " + name, r["auc"], r["ef1"], b["auc"], b["ef1"]))
        print("%-8s EF5 %5.1f BEDROC %.3f  EF5 %5.1f BEDROC %.3f"
              % ("", r["ef5"], r["bedroc"], b["ef5"], b["bedroc"]))

    write_report(results)
    (OUT / "metrics.json").write_text(json.dumps(results, indent=2) + "\n",
                                      encoding="utf-8")
    print("\nwrote %s" % (OUT / "metrics.json"))


def write_report(results):
    a, b = results["screens"]["A"], results["screens"]["B"]
    lines = [
        "# Chapter 18 — enrichment", "",
        "%d compounds, %d actives, α = %d, seed %d. Both screens are tuned to"
        % (results["n_compounds"], results["n_actives"], results["alpha"],
           results["seed"]),
        "the same AUC by solving for the active score mean; only the *spread* of",
        "the active scores differs.",
        "",
        "| | AUC | EF1% | EF5% | BEDROC (α=20) | Actives in top 1% |",
        "|---|---|---|---|---|---|",
        "| Screen A | %.3f | %.1f | %.1f | %.3f | %d |"
        % (a["auc"], a["ef1"], a["ef5"], a["bedroc"], a["actives_in_top_1_percent"]),
        "| Screen B | %.3f | %.1f | %.1f | %.3f | %d |"
        % (b["auc"], b["ef1"], b["ef5"], b["bedroc"], b["actives_in_top_1_percent"]),
        "",
        "**The same AUC, and one of these screens is useless.** Screen A puts %d"
        % a["actives_in_top_1_percent"],
        "of its %d actives in the first 1%% of the list. Screen B puts %d there."
        % (results["n_actives"], b["actives_in_top_1_percent"]),
        "Nobody screens the whole library, so AUC measures something nobody uses.",
        "",
        "## BEDROC, computed twice",
        "",
        "Once from Truchon & Bayly (2007) directly, once with",
        "`rdkit.ML.Scoring.Scoring.CalcBEDROC`. They %s to six decimals:"
        % ("agree" if results["bedroc_agrees_with_rdkit_to_6dp"] else "DISAGREE"),
        "",
        "| Screen | This implementation | RDKit |",
        "|---|---|---|",
        "| A | %.8f | %.8f |" % (a["bedroc_full_precision"], a["bedroc_rdkit"]),
        "| B | %.8f | %.8f |" % (b["bedroc_full_precision"], b["bedroc_rdkit"]),
        "",
        "At α = 20, **%.1f%% of BEDROC's weight falls in the top 8%%** of the"
        % (100 * results["weight_in_top_8_percent"]),
        "list — analytic, so that figure is exact. α is not a tuning knob; it is",
        "a statement about how much of the list you intend to look at.",
        "",
        "## Against the book",
        "",
        "| | AUC | EF1% | EF5% | BEDROC |",
        "|---|---|---|---|---|",
        "| Screen A, book | 0.758 | 56.0 | 11.6 | 0.574 |",
        "| Screen A, here | %.3f | %.1f | %.1f | %.3f |"
        % (a["auc"], a["ef1"], a["ef5"], a["bedroc"]),
        "| Screen B, book | 0.758 | 0.0 | 0.6 | 0.058 |",
        "| Screen B, here | %.3f | %.1f | %.1f | %.3f |"
        % (b["auc"], b["ef1"], b["ef5"], b["bedroc"]),
        "",
        "The AUCs match because both are solved for. The rest depends on how the",
        "screens were built, and `CLAUDE.md` records the book's results without",
        "recording its construction — so these are two different synthetic",
        "experiments that make the same point, not a disagreement about one.",
        "See `PROGRESS.md`.",
        "",
    ]
    (OUT / "metrics.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
