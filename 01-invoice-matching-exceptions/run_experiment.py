"""
Invoice 3-way matching: rules vs ML for exception detection (SYNTHETIC data).

Question a product manager would ask: "If we auto-approve invoices that look fine, how many
can we straight-through-process (STP) without letting bad invoices slip through?"

Pipeline
  1. Generate synthetic purchase orders (PO), goods receipts (GRN) and invoices with labelled
     problems: price mismatch, over-billed quantity, duplicate, missing PO, wrong vendor.
  2. Build matching features (price/quantity differences, fuzzy vendor-name similarity, duplicate key).
  3. Compare: strict rules (1% tolerance), tuned rules (3% tolerance), and a Random Forest.
  4. Report product metrics: STP rate, false-approve rate, exception precision, and an STP vs risk curve.

Everything is synthetic and seeded, so results are reproducible. It is a methodology demo, not a
claim about any company's real data.
"""
import json, difflib, re
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, f1_score

SEED = 42
rng = np.random.default_rng(SEED)
OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)

CLASSES = ["clean", "price_mismatch", "qty_mismatch", "duplicate", "missing_po", "vendor_mismatch"]
WORDS_A = ["Apex", "Bright", "Cobalt", "Delta", "Evergreen", "Falcon", "Granite", "Harbor", "Indigo", "Juniper"]
WORDS_B = ["Logistics", "Packaging", "Foods", "Metals", "Textiles", "Electric", "Supplies", "Chemicals"]
SUFFIX = ["Pvt Ltd", "Private Limited", "LLP", "Inc"]


def make_vendors(n=60):
    vendors = set()
    while len(vendors) < n:
        vendors.add(f"{rng.choice(WORDS_A)} {rng.choice(WORDS_B)} {rng.choice(SUFFIX)}")
    return sorted(vendors)


def norm(name: str) -> str:
    s = re.sub(r"[^a-z0-9 ]", "", str(name).lower())
    s = re.sub(r"\b(pvt|ltd|private|limited|llp|inc)\b", "", s)
    return re.sub(r"\s+", " ", s).strip()


def typo(name: str) -> str:
    """Harmless formatting differences that must NOT be flagged as vendor mismatch."""
    r = rng.random()
    if r < 0.3: return name.upper()
    if r < 0.6: return name.replace("Private Limited", "Pvt Ltd").replace("Pvt Ltd", "Pvt. Ltd.")
    if r < 0.8: return name.replace(" ", "  ")
    return name.lower()


def generate(n_po=4000):
    vendors = make_vendors()
    rows = []
    for i in range(n_po):
        vendor = rng.choice(vendors)
        qty = int(rng.integers(5, 300))
        price = float(np.round(rng.lognormal(3.2, 0.7), 2))
        grn_qty = qty if rng.random() < 0.82 else int(max(1, qty * rng.uniform(0.6, 0.95)))
        label = rng.choice(CLASSES, p=[0.76, 0.06, 0.06, 0.05, 0.03, 0.04])
        inv_vendor, inv_price, inv_qty, po_ref = vendor, price, grn_qty, f"PO-{i:05d}"
        if label == "clean":
            inv_price = price * (1 + np.clip(rng.normal(0, 0.008), -0.03, 0.03))  # rounding / tax noise
            if rng.random() < 0.18: inv_vendor = typo(vendor)
            if rng.random() < 0.10: inv_qty = max(1, int(round(grn_qty * (1 + rng.uniform(-0.01, 0.01)))))
        elif label == "price_mismatch":
            inv_price = price * (1 + rng.uniform(0.015, 0.20) * rng.choice([-1, 1], p=[0.3, 0.7]))
        elif label == "qty_mismatch":
            inv_qty = int(np.ceil(grn_qty * (1 + rng.uniform(0.04, 0.40))))
        elif label == "missing_po":
            po_ref = None if rng.random() < 0.6 else f"PO-{rng.integers(90000, 99999)}"
        elif label == "vendor_mismatch":
            inv_vendor = rng.choice([v for v in vendors if norm(v) != norm(vendor)])
        rows.append(dict(po_ref_true=f"PO-{i:05d}", vendor_po=vendor, po_qty=qty, po_price=price, grn_qty=grn_qty,
                         inv_vendor=inv_vendor, inv_price=round(inv_price, 2), inv_qty=inv_qty, po_ref=po_ref,
                         day=int(rng.integers(0, 120)), label=label, invoice_no=f"INV-{i:05d}"))
    df = pd.DataFrame(rows)
    # duplicates: re-send an existing invoice later, sometimes with a slightly different number
    base = df[df.label == "clean"].sample(frac=0.07, random_state=SEED).copy()
    base["label"] = "duplicate"
    base["day"] = base["day"] + rng.integers(1, 20, len(base))
    base["invoice_no"] = [s if rng.random() < 0.6 else s[:-1] + str(rng.integers(0, 9)) for s in base["invoice_no"]]
    df = df[df.label != "duplicate"]
    df = pd.concat([df, base], ignore_index=True).sort_values("day").reset_index(drop=True)
    return df


def features(df):
    d = pd.DataFrame(index=df.index)
    d["po_found"] = df["po_ref"].notna() & df["po_ref"].eq(df["po_ref_true"])
    d["price_diff_pct"] = (df.inv_price - df.po_price) / df.po_price
    d["qty_over_grn"] = (df.inv_qty - df.grn_qty) / df.grn_qty
    d["qty_over_po"] = (df.inv_qty - df.po_qty) / df.po_qty
    d["vendor_sim"] = [difflib.SequenceMatcher(None, norm(a), norm(b)).ratio() for a, b in zip(df.inv_vendor, df.vendor_po)]
    d["total_diff_pct"] = (df.inv_price * df.inv_qty - df.po_price * df.grn_qty) / (df.po_price * df.grn_qty)
    seen, dup = {}, []
    for ref, vend, tot in zip(df.po_ref_true, df.inv_vendor.map(norm), df.inv_price * df.inv_qty):
        key = (ref, vend)
        dup.append(key in seen and abs(seen[key] - tot) / max(tot, 1) < 0.01)
        seen.setdefault(key, tot)
    d["dup_flag"] = dup
    for c in ["po_found", "dup_flag"]: d[c] = d[c].astype(int)
    return d


def rule_predict(f, tol):
    out = []
    for _, r in f.iterrows():
        if not r.po_found: out.append("missing_po")
        elif r.dup_flag: out.append("duplicate")
        elif r.vendor_sim < 0.75: out.append("vendor_mismatch")
        elif abs(r.price_diff_pct) > tol: out.append("price_mismatch")
        elif r.qty_over_grn > tol: out.append("qty_mismatch")
        else: out.append("clean")
    return np.array(out)


def product_metrics(y_true, y_pred):
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    bad = y_true != "clean"
    approved = y_pred == "clean"
    flagged = ~approved
    return dict(
        stp_rate=float(approved.mean()),                              # share auto-approved
        false_approve_rate=float((approved & bad).sum() / bad.sum()),  # bad invoices that slipped through
        exception_precision=float((flagged & bad).sum() / max(flagged.sum(), 1)),  # flagged that were truly bad
        macro_f1=float(f1_score(y_true, y_pred, labels=CLASSES, average="macro", zero_division=0)),
    )


def main():
    df = generate()
    X = features(df)
    y = df["label"].values
    idx_train, idx_test = train_test_split(np.arange(len(df)), test_size=0.3, random_state=SEED, stratify=y)
    Xtr, Xte, ytr, yte = X.iloc[idx_train], X.iloc[idx_test], y[idx_train], y[idx_test]

    results = {"n_invoices": int(len(df)), "class_share": {k: round(float((y == k).mean()), 3) for k in CLASSES}}
    results["rules_strict_1pct"] = product_metrics(yte, rule_predict(Xte, 0.01))
    results["rules_tuned_3pct"] = product_metrics(yte, rule_predict(Xte, 0.03))

    rf = RandomForestClassifier(n_estimators=300, random_state=SEED, class_weight="balanced", min_samples_leaf=2)
    rf.fit(Xtr, ytr)
    proba = rf.predict_proba(Xte)
    pred_rf = rf.classes_[proba.argmax(1)]
    results["random_forest"] = product_metrics(yte, pred_rf)
    results["feature_importance"] = {c: round(float(v), 3) for c, v in sorted(zip(X.columns, rf.feature_importances_), key=lambda t: -t[1])}

    # Operating point: approve only if P(clean) >= threshold. Sweep to show STP vs risk trade-off.
    p_clean = proba[:, list(rf.classes_).index("clean")]
    sweep = []
    for th in np.linspace(0.30, 0.99, 36):
        # when not approved, label as the most likely non-clean class
        non =[i for i, c in enumerate(rf.classes_) if c != "clean"]
        best_non = rf.classes_[np.array(non)[proba[:, non].argmax(1)]]
        pr = np.where(p_clean >= th, "clean", best_non)
        m = product_metrics(yte, pr); m["threshold"] = round(float(th), 3); sweep.append(m)
    results["sweep"] = sweep
    ok = [s for s in sweep if s["false_approve_rate"] <= 0.02]
    results["operating_point_false_approve_le_2pct"] = max(ok, key=lambda s: s["stp_rate"]) if ok else None

    results["classification_report_rf"] = classification_report(yte, pred_rf, output_dict=True, zero_division=0)
    cm = confusion_matrix(yte, pred_rf, labels=CLASSES)

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
    ax[0].plot([s["false_approve_rate"] * 100 for s in sweep], [s["stp_rate"] * 100 for s in sweep], marker="o", ms=3, label="Random Forest (threshold sweep)")
    for name, key, mk in [("Rules 1%", "rules_strict_1pct", "s"), ("Rules 3%", "rules_tuned_3pct", "^")]:
        ax[0].scatter(results[key]["false_approve_rate"] * 100, results[key]["stp_rate"] * 100, marker=mk, s=70, label=name)
    ax[0].set_xlabel("False-approve rate (% of bad invoices auto-approved)"); ax[0].set_ylabel("STP rate (% auto-approved)")
    ax[0].set_title("Automation vs risk trade-off"); ax[0].grid(alpha=.3); ax[0].legend()
    im = ax[1].imshow(cm, cmap="Blues"); ax[1].set_xticks(range(6)); ax[1].set_yticks(range(6))
    ax[1].set_xticklabels(CLASSES, rotation=40, ha="right", fontsize=8); ax[1].set_yticklabels(CLASSES, fontsize=8)
    for i in range(6):
        for j in range(6): ax[1].text(j, i, cm[i, j], ha="center", va="center", fontsize=8, color="white" if cm[i, j] > cm.max() / 2 else "black")
    ax[1].set_title("Random Forest confusion matrix (test set)")
    plt.tight_layout(); plt.savefig(OUT / "tradeoff_and_confusion.png", dpi=140)

    (OUT / "metrics.json").write_text(json.dumps(results, indent=2, default=float))
    df.to_csv(OUT / "synthetic_invoices.csv", index=False)
    print(json.dumps({k: results[k] for k in ["n_invoices", "class_share", "rules_strict_1pct", "rules_tuned_3pct", "random_forest", "feature_importance", "operating_point_false_approve_le_2pct"]}, indent=2, default=float))


if __name__ == "__main__":
    main()
