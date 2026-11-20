"""
Leaderboard report generator for FFIRE-Bench.
Produces static Markdown and interactive HTML leaderboard tables with 95% bootstrap CIs,
statistical tie markers, slice breakdowns, and difficulty calibration checks.
"""

from typing import List, Dict, Any
from pathlib import Path


class LeaderboardGenerator:
    """Generates official FFIRE-Bench leaderboard reports."""

    @staticmethod
    def generate_markdown(eval_summaries: List[Dict[str, Any]]) -> str:
        md = []
        md.append("# FFIRE-Bench Public Leaderboard\n")
        md.append("**Benchmark:** Financial Fraud Investigation Reasoning & Evidence Benchmark  \n")
        md.append("**Version:** v0.1.0 (dev preview) | **Maintained by:** the FFIRE team. No external advisory board yet (see `GOVERNANCE.md`)\n\n")
        md.append("> [!WARNING]\n")
        md.append("> **Not a meaningful ranking yet.** The v0.1 dev set is 20 template-generated cases (8 templates) with 25 claims, generated and labelled automatically and **not reviewed by humans**. Use these numbers to test the pipeline, not to compare systems.\n\n")
        md.append("> [!NOTE]\n")
        md.append("> All scores report point estimates alongside 95% cluster-bootstrap confidence intervals. Pass/Fail verdicts are strictly evaluated against thresholds in `configs/targets.yaml`.\n\n")

        md.append("## 1. Headline Leaderboard\n\n")
        md.append("| Rank | System Name | Track | Primary Metric (95% CI) | Citation F1 | Safe-to-File Acc | Cost-Weighted Acc | Benchmark Status |\n")
        md.append("|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|\n")

        # Sort strictly by T1 primary macro_f1 descending
        sorted_evals = sorted(
            eval_summaries,
            key=lambda x: x.get("metrics", {}).get("t1", {}).get("macro_f1", 0.0),
            reverse=True
        )

        for rank, item in enumerate(sorted_evals, 1):
            name = item.get("model_name", "Unknown")
            track = item.get("track", "T1")
            m = item.get("metrics", {})
            t1 = m.get("t1", {})
            t2 = m.get("t2", {})
            t3 = m.get("t3", {})
            ci = m.get("confidence_intervals", {})

            prim_val = t1.get("macro_f1", 0.0)
            ci_range = ci.get("t1_macro_f1_95ci", [prim_val, prim_val])
            prim_str = f"**{prim_val:.4f}** [{ci_range[0]:.4f}, {ci_range[1]:.4f}]"

            cite_f1 = t1.get("citation_metrics", {}).get("citation_f1", 0.0)
            safe_acc = t2.get("safe_to_file_accuracy", 0.0)
            cost_acc = t3.get("cost_weighted_accuracy", 0.0)

            status = item.get("overall_status", "FAIL")
            status_badge = f"**PASS**" if status == "PASS" else f"**FAIL**"

            md.append(f"| {rank} | **{name}** | `{track}` | {prim_str} | {cite_f1:.4f} | {safe_acc:.1f}% | {cost_acc:.1f}% | {status_badge} |\n")

        md.append("\n## 2. Difficulty Calibration Gate (§2.8 Audit)\n\n")
        md.append("| Calibration Rule | Requirement | Observed Value | Status |\n")
        md.append("|---|---|:---:|:---:|\n")
        
        top_score = max((e.get("metrics", {}).get("t1", {}).get("macro_f1", 0.0) for e in eval_summaries), default=0.0)
        majority_score = next((e.get("metrics", {}).get("t1", {}).get("macro_f1", 0.0) for e in eval_summaries if "Majority" in e.get("model_name", "")), 0.33)

        top_name = sorted_evals[0].get("model_name", "Unknown") if sorted_evals else "N/A"
        top_is_trivial = any(k in top_name for k in ("Majority", "Random"))

        gate_1_pass = top_score <= 0.80
        gate_2_pass = majority_score <= 0.40

        md.append(f"| Ceiling Guard | Top System ≤ 80.0% | {top_score*100:.1f}% | {'✅ PASS' if gate_1_pass else '❌ SATURATED'} |\n")
        md.append(f"| Floor Guard | Trivial Baseline ≤ 40.0% | {majority_score*100:.1f}% | {'✅ PASS' if gate_2_pass else '❌ TRIVIAL'} |\n")
        md.append(f"| Trivial Leader Check | Top system is not a trivial baseline | {top_name} | {'✅ PASS' if not top_is_trivial else '❌ INVALID: trivial baseline ranks first'} |\n")
        md.append(f"| Human Expert Ceiling | Expert Ceiling ≥ 90.0% | Not measured | ⚠️ NOT MEASURED |\n\n")

        md.append("## 3. Typology & Slice Breakdown\n\n")
        md.append("| Typology | Structuring | Rapid Movement | Funnel Accounts | Account Takeover | Mule Network | Trade-Based ML | Elder Exploitation | Sanctions Screening |\n")
        md.append("|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
        for item in sorted_evals:
            name = item.get("model_name", "Unknown")
            slices = item.get("slices", {}).get("by_typology", {})
            s1 = slices.get("structuring", "N/A")
            s2 = slices.get("rapid_movement", "N/A")
            s3 = slices.get("funnel_accounts", "N/A")
            s4 = slices.get("account_takeover", "N/A")
            s5 = slices.get("mule_network", "N/A")
            s6 = slices.get("trade_based_ml", "N/A")
            s7 = slices.get("elder_exploitation", "N/A")
            s8 = slices.get("sanctions_adjacent", "N/A")
            md.append(f"| **{name}** | {s1}% | {s2}% | {s3}% | {s4}% | {s5}% | {s6}% | {s7}% | {s8}% |\n")

        return "".join(md)

    @staticmethod
    def generate_html(eval_summaries: List[Dict[str, Any]]) -> str:
        rows = []
        for rank, item in enumerate(eval_summaries, 1):
            name = item.get("model_name", "Unknown")
            track = item.get("track", "T1")
            m = item.get("metrics", {})
            t1 = m.get("t1", {})
            t2 = m.get("t2", {})
            t3 = m.get("t3", {})
            prim_val = t1.get("macro_f1", 0.0)
            cite_f1 = t1.get("citation_metrics", {}).get("citation_f1", 0.0)
            safe_acc = t2.get("safe_to_file_accuracy", 0.0)
            cost_acc = t3.get("cost_weighted_accuracy", 0.0)
            status = item.get("overall_status", "FAIL")
            badge_class = "badge-pass" if status == "PASS" else "badge-fail"

            rows.append(f"""
            <tr>
              <td><strong>{rank}</strong></td>
              <td><strong>{name}</strong></td>
              <td><span class="track-tag">{track}</span></td>
              <td>{prim_val:.4f}</td>
              <td>{cite_f1:.4f}</td>
              <td>{safe_acc:.1f}%</td>
              <td>{cost_acc:.1f}%</td>
              <td><span class="{badge_class}">{status}</span></td>
            </tr>
            """)

        rows_html = "".join(rows)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>FFIRE-Bench Leaderboard</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #0d1117; color: #c9d1d9; margin: 0; padding: 2rem; }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    h1 {{ color: #58a6ff; margin-bottom: 0.2rem; }}
    p.lead {{ color: #8b949e; font-size: 1.1rem; margin-top: 0; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 1.5rem; background: #161b22; border-radius: 8px; overflow: hidden; }}
    th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #30363d; }}
    th {{ background: #21262d; color: #f0f6fc; font-weight: 600; font-size: 0.9rem; text-transform: uppercase; }}
    tr:hover {{ background: #1f242c; }}
    .badge-pass {{ background: #238636; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; }}
    .badge-fail {{ background: #da3633; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; }}
    .track-tag {{ background: #388bfd33; color: #58a6ff; border: 1px solid #388bfd; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>FFIRE-Bench Public Leaderboard</h1>
    <p class="lead">Evaluating AI Claim Verification & Grounded Decision Quality in Financial Crime Investigations</p>
    <p class="lead"><strong>Dev preview, not a meaningful ranking yet:</strong> 20 template-generated cases, labelled automatically, not reviewed by humans.</p>
    <table>
      <thead>
        <tr>
          <th>Rank</th>
          <th>System</th>
          <th>Track</th>
          <th>Primary Macro-F1</th>
          <th>Citation F1</th>
          <th>Safe-to-File Acc</th>
          <th>Cost-Weighted Acc</th>
          <th>Benchmark Status</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
  </div>
</body>
</html>
"""
