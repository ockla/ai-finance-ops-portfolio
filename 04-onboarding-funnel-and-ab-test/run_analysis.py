"""
Onboarding funnel, retention and an A/B test for a B2B SaaS product (SYNTHETIC data).

Product question: new finance teams sign up, but many never get value. Where do we lose them, and
does a one-click ERP connection flow (variant) actually improve activation without hurting support load?

What a PM does here, step by step
  1. Funnel: signup -> connected ERP -> processed first invoice -> activated (3+ invoices in 7 days) -> still active in week 4.
  2. Find the biggest drop-off and segment it (company size, acquisition channel).
  3. Design the experiment BEFORE running it: sample size from baseline + minimum detectable effect.
  4. Analyse it properly: sample-ratio check, two-proportion z-test, confidence interval, guardrail metric.
  5. Make a decision and state what you would not conclude.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 11
rng = np.random.default_rng(SEED)
OUT = Path(__file__).parent / "results"; OUT.mkdir(exist_ok=True)
STAGES = ["signed_up", "connected_erp", "first_invoice", "activated", "active_week4"]


def simulate_users(n=20000):
    size = rng.choice(["SMB", "Mid-market", "Enterprise"], n, p=[.55, .33, .12])
    channel = rng.choice(["Organic", "Paid", "Partner"], n, p=[.45, .35, .20])
    base_connect = np.where(size == "SMB", .52, np.where(size == "Mid-market", .44, .31))   # enterprises struggle most with ERP setup
    connect_adj = np.where(channel == "Partner", 1.18, np.where(channel == "Paid", .92, 1.0))
    connected = rng.random(n) < np.clip(base_connect * connect_adj, 0, 1)
    first_inv = connected & (rng.random(n) < .78)
    activated = first_inv & (rng.random(n) < .60)
    week4 = activated & (rng.random(n) < .72)
    return pd.DataFrame(dict(size=size, channel=channel, signed_up=True, connected_erp=connected,
                             first_invoice=first_inv, activated=activated, active_week4=week4))


def funnel_table(df):
    rows, prev = [], len(df)
    for s in STAGES:
        n = int(df[s].sum())
        rows.append(dict(stage=s, users=n, pct_of_signups=round(n / len(df), 4), step_conversion=round(n / prev, 4)))
        prev = n
    return pd.DataFrame(rows)


def sample_size_per_arm(p_base, mde_abs, alpha=0.05, power=0.80):
    p1, p2 = p_base, p_base + mde_abs
    z_a, z_b = stats.norm.ppf(1 - alpha / 2), stats.norm.ppf(power)
    pbar = (p1 + p2) / 2
    n = ((z_a * np.sqrt(2 * pbar * (1 - pbar)) + z_b * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2) / (mde_abs ** 2)
    return int(np.ceil(n))


def run_experiment(p_control, true_lift, n_per_arm):
    """Variant = one-click ERP connect. Primary metric: connected_erp rate. Guardrail: support tickets per user."""
    users = n_per_arm * 2
    arm = rng.permutation(np.array(["control"] * n_per_arm + ["variant"] * n_per_arm))
    p = np.where(arm == "variant", p_control + true_lift, p_control)
    connected = rng.random(users) < p
    tickets = rng.poisson(np.where(arm == "variant", 0.34, 0.31), users)   # slight, non-significant extra support load
    return pd.DataFrame(dict(arm=arm, connected=connected, tickets=tickets))


def analyse(exp):
    c, v = exp[exp.arm == "control"], exp[exp.arm == "variant"]
    # 1) sample ratio mismatch check (should be ~50/50)
    chi = stats.chisquare([len(c), len(v)])
    # 2) primary metric: two-proportion z-test
    x1, n1, x2, n2 = c.connected.sum(), len(c), v.connected.sum(), len(v)
    p1, p2 = x1 / n1, x2 / n2
    pp = (x1 + x2) / (n1 + n2)
    z = (p2 - p1) / np.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2))
    pval = 2 * (1 - stats.norm.cdf(abs(z)))
    se = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    ci = (p2 - p1 - 1.96 * se, p2 - p1 + 1.96 * se)
    # 3) guardrail: tickets per user (Welch t-test)
    t = stats.ttest_ind(v.tickets, c.tickets, equal_var=False)
    return dict(n_control=n1, n_variant=n2, srm_p=float(chi.pvalue), control_rate=float(p1), variant_rate=float(p2),
                abs_lift=float(p2 - p1), rel_lift=float((p2 - p1) / p1), ci95_abs=[float(ci[0]), float(ci[1])], z=float(z), p_value=float(pval),
                tickets_control=float(c.tickets.mean()), tickets_variant=float(v.tickets.mean()), tickets_p_value=float(t.pvalue))


def main():
    df = simulate_users()
    ft = funnel_table(df)
    worst = ft.iloc[1:].sort_values("step_conversion").iloc[0]
    seg_size = df.groupby("size")["connected_erp"].mean().round(3).to_dict()
    seg_channel = df.groupby("channel")["connected_erp"].mean().round(3).to_dict()
    p_base = float(df.connected_erp.mean())
    mde = 0.02
    n_needed = sample_size_per_arm(p_base, mde)
    exp = run_experiment(p_base, true_lift=0.03, n_per_arm=n_needed)
    res = analyse(exp)
    decision = ("SHIP: statistically significant improvement in ERP connection with no significant increase in support tickets."
                if res["p_value"] < 0.05 and res["ci95_abs"][0] > 0 and res["tickets_p_value"] > 0.05 else "DO NOT SHIP YET: see results.")
    out = dict(users_simulated=len(df), funnel=ft.to_dict("records"), biggest_drop_stage=worst["stage"],
               erp_connect_rate_by_company_size=seg_size, erp_connect_rate_by_channel=seg_channel,
               baseline_connect_rate=round(p_base, 4), design=dict(mde_abs=mde, alpha=0.05, power=0.8, n_per_arm=n_needed),
               experiment=res, decision=decision)
    (OUT / "metrics.json").write_text(json.dumps(out, indent=2, default=float))

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.4))
    ax[0].barh(ft.stage[::-1], ft.pct_of_signups[::-1] * 100, color="#0e9f8e")
    for i, (s, v) in enumerate(zip(ft.stage[::-1], ft.pct_of_signups[::-1] * 100)): ax[0].text(v + 1, i, f"{v:.1f}%", va="center", fontsize=9)
    ax[0].set_xlim(0, 115); ax[0].set_title("Onboarding funnel (% of signups)")
    ax[1].bar(["Control", "Variant"], [res["control_rate"] * 100, res["variant_rate"] * 100], color=["#9aa5b1", "#0e9f8e"])
    lo, hi = res["ci95_abs"]
    ax[1].set_title(f"ERP connection rate (lift {res['abs_lift']*100:+.1f} pp, 95% CI {lo*100:+.1f} to {hi*100:+.1f}, p={res['p_value']:.4f})", fontsize=9)
    ax[1].set_ylabel("% connected"); plt.tight_layout(); plt.savefig(OUT / "funnel_and_experiment.png", dpi=140)
    print(json.dumps({k: out[k] for k in ["funnel", "biggest_drop_stage", "erp_connect_rate_by_company_size", "erp_connect_rate_by_channel", "design", "experiment", "decision"]}, indent=2, default=float))


if __name__ == "__main__":
    main()
