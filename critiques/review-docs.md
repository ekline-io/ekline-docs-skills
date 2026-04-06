# Critique: review-docs

**Script:** `skills/review-docs/scripts/run_review.py`
**Tests:** None
**Overall:** Thin wrapper around external tool. The skill with the highest friction and lowest self-sufficiency.

---

## Critical

### External dependency breaks the "zero config" promise

This is the only skill requiring:
1. A binary download (`ekline-cli`)
2. An API token (`EKLINE_EK_TOKEN`)
3. Network access to EkLine's servers

All other 11 skills are Python stdlib only. The README says "11 of 12 work out of the box" which is accurate, but the setup friction for this one skill is high.

**Action:** Ensure the skill fails gracefully with a clear message pointing to setup docs. Don't let a missing `ekline-cli` crash the agent workflow.

---

## Medium

### Token in environment variable can leak

Setting `EKLINE_EK_TOKEN` via `export` in shell can leak in:
- Shell history (`~/.zsh_history`, `~/.bash_history`)
- Process lists (`ps aux`)
- CI logs if echoed

**Action:** Recommend using a `.env` file or secret manager instead of `export`. Add a note about not setting it inline.

### No fallback when CLI unavailable

If `ekline-cli` is not installed, the skill fails completely. There's no subset of checks that can run without it.

**Action:** Consider a degraded mode that runs the other 11 skills' checks as a substitute when `ekline-cli` is unavailable. Or at minimum, suggest: "ekline-cli not found — try /docs-health for a similar check."

### No version pinning for ekline-cli

The install command downloads "latest" release. If a breaking change ships in ekline-cli, the skill breaks without warning.

**Action:** Pin to a specific version or at minimum check the installed version and warn if it's outside the tested range.

---

## Low

### SKILL.md is minimal compared to other skills

Other skills have detailed workflows, scoring, and fix suggestions. review-docs is essentially "run the CLI, show results, apply fixes."

**Action:** Add more detail about what EkLine checks for and how to interpret results, so users understand the value before investing in setup.

### No integration with docs-health

docs-health doesn't include review-docs in its report card (makes sense since it requires external tooling), but there's no mention of this in either skill's docs.

**Action:** Add a note in docs-health: "For a full AI-powered review, also try `/review-docs`."
