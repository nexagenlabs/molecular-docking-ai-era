# The build record

How this repository was built and checked. Kept because a repository claiming
to verify rather than assert should show its working. **None of it is required
to use the code** — start at the [root README](../README.md) instead.

| File | What it is |
|---|---|
| [`BUILD_REPORT.md`](BUILD_REPORT.md) | The defects the expected values caught while the chapters were written. Every one returned a plausible wrong answer rather than an error, which is why a human reviewer would have passed them. |
| [`STRESS_REPORT.md`](STRESS_REPORT.md) | An adversarial test of this repository against itself: mutate the code, see whether the suite notices. Two tests passed only on accumulated state, and one reported protection it was not providing. |
| [`STRESS_TEST.md`](STRESS_TEST.md) | The checks `STRESS_REPORT.md` answers — written before the results were known, so the report could not quietly become a list of things that happened to pass. |
| [`SESSION_PLAN.md`](SESSION_PLAN.md) | The plan the repository was built to. |
| [`PROGRESS.md`](PROGRESS.md) | A working log. It reads like one. |
| [`SITE_CONTENT.md`](SITE_CONTENT.md) | The draft the companion site at `dock.nexagenlabs.com` was written from, open questions and all. It lived in `site/` until the first deploy showed it publishing itself at `/SITE_CONTENT.md`. |

None of `SESSION_PLAN.md`, `STRESS_TEST.md` or `SITE_CONTENT.md` is instructions
to a reader.

Where this repository disagrees with the book, both numbers are recorded in
`PROGRESS.md` with a diagnosis, and neither is edited to match the other. The
exhaustiveness-ratio band is the worked example: it sat as a failing-by-design
test carrying its measurements until the book, not the script, turned out to be
the wrong side.
