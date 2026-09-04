#!/usr/bin/env python3
"""Chapter 18 — two screens with the same AUC and opposite usefulness.

    python ch18_enrichment/scripts/enrichment.py

10,000 compounds, 100 actives, two rankings tuned to the *same* AUC. One puts
most of its actives in the first 1% of the list; the other puts none there. AUC
cannot tell them apart. Nothing you would actually do with a screen depends on
AUC and everything depends on the difference.

The construction lives in `ch18_make_screens.py` and is imported rather than
copied, so there is exactly one definition of what the two screens are. This
script measures them and writes the report.

Writes outputs/metrics.json, outputs/metrics.md and outputs/enrichment.png.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

CH = Path(__file__).resolve().parent.parent
OUT = CH / "outputs"

# The screens are defined once, next door. Copying the construction in here
# would let the two copies drift, and a chapter whose figure disagrees with its
# own table is worse than no figure.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch18_make_screens import N, SEED, make_screens, n as N_ACTIVES  # noqa: E402

ALPHA = 20.0

# Everything below is implemented independently of `ch18_make_screens`, which
# carries its own copies. Two implementations of BEDROC that agree to six
# decimals are worth more than one implementation that looks right, and RDKit
# makes a third.


def auc(labels_by_rank):
    """Probability a random active outranks a random decoy.

    From the rank sum (the Mann-Whitney form) rather than by trapezoid. The
    labels arrive already in rank order, so the rank of each active is its
    index + 1 and there are no ties to resolve.
    """
    labels = np.asarray(labels_by_rank)
    n_act = int(labels.sum())
    n_dec = len(labels) - n_act
    rank_sum = float((np.nonzero(labels)[0] + 1).sum())
    return float((n_act * (n_act + 1) / 2 + n_act * n_dec - rank_sum) / (n_act * n_dec))


def enrichment_factor(labels_by_rank, fraction):
    """Actives found in the top fraction, over what chance would give."""
    k = int(round(len(labels_by_rank) * fraction))
    hits = int(labels_by_rank[:k].sum())
    return float((hits / k) / (labels_by_rank.sum() / len(labels_by_rank)))


def bedroc(labels_by_rank, alpha=ALPHA):
    """Truchon & Bayly (2007), implemented from the paper."""
    n_act = int(labels_by_rank.sum())
    big_n = len(labels_by_rank)
    ra = n_act / big_n
    ranks = np.nonzero(labels_by_rank)[0] + 1
    rie_num = np.exp(-alpha * ranks / big_n).sum() / n_act
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
    for name, by_rank in screens.items():
        found = np.cumsum(by_rank) / by_rank.sum()
        fraction = np.arange(1, len(by_rank) + 1) / len(by_rank)
        left.plot(fraction, found, label="Screen %s" % name)
        right.plot(fraction[:500], found[:500], label="Screen %s" % name)
    for axis, title in ((left, "Whole list - identical AUC 0.758"),
                        (right, "First 5% - where the difference lives")):
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

    # The search is a single pass over one generator: the loop bounds and their
    # order are part of the specification, which is why they live in one file
    # and are imported rather than restated.
    gap, hi, lo, screen_a, screen_b = make_screens()
    screens = {"A": screen_a, "B": screen_b}

    results = {"n_compounds": N, "n_actives": N_ACTIVES,
               "alpha": int(ALPHA), "seed": SEED,
               "actives_in_top_one_percent_by_construction": hi,
               "screen_b_spread_upper_bound": lo,
               "auc_gap_between_screens": gap,
               "weight_in_top_8_percent": round(weight_in_top(0.08), 4),
               "screens": {}}

    print("%d compounds, %d actives, alpha %d, seed %d"
          % (N, N_ACTIVES, ALPHA, SEED))
    print("construction: %d actives in the top 1%%, screen B spread over ranks "
          "401-%d\n" % (hi, lo))
    print("%-8s %-7s %-7s %-7s %-8s %s" % ("screen", "AUC", "EF1%", "EF5%",
                                           "BEDROC", "RDKit BEDROC"))
    for name, by_rank in screens.items():
        ours = bedroc(by_rank)
        theirs = rdkit_bedroc(by_rank)
        results["screens"][name] = {
            "auc": round(auc(by_rank), 4),
            "ef1": round(enrichment_factor(by_rank, 0.01), 3),
            "ef5": round(enrichment_factor(by_rank, 0.05), 3),
            "bedroc": round(ours, 3),
            "bedroc_full_precision": ours,
            "bedroc_rdkit": theirs,
            "actives_in_top_1_percent": int(by_rank[:100].sum()),
            "actives_in_top_5_percent": int(by_rank[:500].sum()),
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

    # -- against the book ----------------------------------------------------
    # Compared, not assumed. Every published value is checked at the precision
    # the book prints it, and the number that matched is counted and printed
    # rather than claimed.
    book = {"A": {"auc": 0.758, "ef1": 56.0, "ef5": 11.6, "bedroc": 0.574},
            "B": {"auc": 0.758, "ef1": 0.0, "ef5": 0.6, "bedroc": 0.058}}
    results["book"] = book
    checked = []
    for name in ("A", "B"):
        r, b = results["screens"][name], book[name]
        for metric, places in (("auc", 3), ("ef1", 1), ("ef5", 1), ("bedroc", 3)):
            checked.append((name, metric, round(r[metric], places), b[metric]))
    matched = [c for c in checked if c[2] == c[3]]
    results["book_values_matched"] = "%d/%d" % (len(matched), len(checked))
    print("\n%-8s %-22s %s" % ("", "this construction", "the book"))
    for name in ("A", "B"):
        r, b = results["screens"][name], book[name]
        print("%-8s AUC %.3f EF1 %5.1f     AUC %.3f EF1 %5.1f"
              % ("screen " + name, r["auc"], r["ef1"], b["auc"], b["ef1"]))
        print("%-8s EF5 %5.1f BEDROC %.3f  EF5 %5.1f BEDROC %.3f"
              % ("", r["ef5"], r["bedroc"], b["ef5"], b["bedroc"]))
    print("\n%d of the %d published values reproduce exactly."
          % (len(matched), len(checked)))
    for name, metric, ours, theirs in checked:
        if ours != theirs:
            print("  screen %s %s: %s here, %s in the book"
                  % (name, metric, ours, theirs))

    write_report(results)
    (OUT / "metrics.json").write_text(json.dumps(results, indent=2) + "\n",
                                      encoding="utf-8")
    print("\nwrote %s" % (OUT / "metrics.json"))


def write_report(results):
    a, b = results["screens"]["A"], results["screens"]["B"]
    lines = [
        "# Chapter 18 — enrichment", "",
        "%d compounds, %d actives, α = %d, seed %d. The two rankings are found"
        % (results["n_compounds"], results["n_actives"], results["alpha"],
           results["seed"]),
        "by searching for the pair that lands on the *same* AUC: %d of screen A's"
        % results["actives_in_top_one_percent_by_construction"],
        "actives inside the top 1%%, screen B's spread over ranks 401–%d. The two"
        % results["screen_b_spread_upper_bound"],
        "AUCs differ by %.2e." % results["auc_gap_between_screens"],
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
        "**%s of the published values reproduce exactly**, at the precision the"
        % results["book_values_matched"],
        "book prints them. This is arithmetic on a fixed construction, so unlike",
        "Chapters 8 and 9 there is no build-level difference to absorb: a reader",
        "on any platform gets these numbers or has found a bug.",
        "",
    ]
    (OUT / "metrics.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
