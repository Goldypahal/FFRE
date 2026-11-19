"""
One-Command Leaderboard & Benchmark Reproduction Script for FFIRE-Bench v0.1.0.

Executes the entire end-to-end evaluation lifecycle:
1. Generates 20 gold-standard cases across 8 typologies.
2. Runs the offline baselines (Majority, Random, Heuristic). The LLM and FFIRE
   runners only run when configured, because they need a real model / backend:
     FFIRE_BENCH_LLM_PROVIDER=openai|anthropic  FFIRE_BENCH_LLM_MODEL=<model>
     (plus OPENAI_API_KEY / OPENAI_BASE_URL or ANTHROPIC_API_KEY)
     FFIRE_VERIFIER_URL=http://localhost:8000   FFIRE_API_TOKEN=<token>
3. Evaluates all model predictions against configured targets with bootstrap CIs.
4. Generates public leaderboard artifacts (docs/LEADERBOARD.md and docs/leaderboard.html).
5. Asserts difficulty calibration gates (§2.8).
"""

import os
import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ffire_bench.generators.ffire_gen import FFIREGenerator
from ffire_bench.schema.models import Case, Track, Split
from ffire_bench.runners import (
    MajorityBaselineRunner,
    RandomBaselineRunner,
    HeuristicRuleRunner,
    LLMPromptRunner,
    FFIREVerifierRunner,
    make_caller
)
from ffire_bench.scoring.evaluator import BenchmarkEvaluator
from ffire_bench.leaderboard.generator import LeaderboardGenerator


def main():
    print("=" * 80)
    print("FFIRE-Bench v0.1.0 Official Leaderboard Reproduction Engine")
    print("=" * 80)

    # 1. Generate 20 Gold Standard Cases
    print("\n[1/4] Generating 20 Gold-Standard Evaluation Cases across 8 Typologies...")
    gen = FFIREGenerator(seed=42)
    gold_cases: list[Case] = []
    for i in range(1, 21):
        c = gen.generate_case(
            case_idx=i,
            track=Track.T1,
            split=Split.DEV,
            inject_error=(i % 2 == 1)
        )
        gold_cases.append(c)

    gold_path = REPO_ROOT / "data" / "gold_standard_20_cases.json"
    gold_path.parent.mkdir(parents=True, exist_ok=True)
    with open(gold_path, "w", encoding="utf-8") as f:
        json.dump([c.model_dump() for c in gold_cases], f, indent=2)
    print(f"  -> Generated {len(gold_cases)} cases saved to {gold_path}")

    # 2. Run Baseline Models
    print("\n[2/4] Executing Runners...")
    runners = [
        ("majority", MajorityBaselineRunner()),
        ("random", RandomBaselineRunner(seed=42)),
        ("heuristic", HeuristicRuleRunner()),
    ]
    provider = os.environ.get("FFIRE_BENCH_LLM_PROVIDER")
    model = os.environ.get("FFIRE_BENCH_LLM_MODEL")
    if provider and model:
        runners.append(("llm", LLMPromptRunner(model_name=f"{provider}:{model}", api_caller=make_caller(provider, model))))
    else:
        print("  -> Skipping LLM runner (set FFIRE_BENCH_LLM_PROVIDER and FFIRE_BENCH_LLM_MODEL to run a real model)")
    if os.environ.get("FFIRE_VERIFIER_URL"):
        runners.append(("ffire", FFIREVerifierRunner()))
    else:
        print("  -> Skipping FFIRE runner (set FFIRE_VERIFIER_URL to a running FFIRE backend)")

    results_dir = REPO_ROOT / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    evaluator = BenchmarkEvaluator()
    eval_summaries = []

    for key, runner in runners:
        print(f"  -> Running '{runner.name}'...")
        pred_bundle = runner.run_benchmark(gold_cases, track=Track.T1)
        pred_file = results_dir / f"preds_{key}.json"
        with open(pred_file, "w", encoding="utf-8") as f:
            json.dump(pred_bundle.model_dump(), f, indent=2)

        # 3. Evaluate Predictions
        eval_res = evaluator.evaluate(gold_cases, pred_bundle, num_resamples=500)
        eval_file = results_dir / f"eval_{key}.json"
        with open(eval_file, "w", encoding="utf-8") as f:
            json.dump(eval_res, f, indent=2)
        eval_summaries.append(eval_res)

    # 4. Generate Leaderboard Reports
    print("\n[3/4] Compiling Leaderboard Reports...")
    md_content = LeaderboardGenerator.generate_markdown(eval_summaries)
    md_path = REPO_ROOT / "docs" / "LEADERBOARD.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    html_content = LeaderboardGenerator.generate_html(eval_summaries)
    html_path = REPO_ROOT / "docs" / "leaderboard.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"  -> Leaderboard Markdown saved to: {md_path}")
    print(f"  -> Leaderboard HTML saved to:     {html_path}")

    # 5. Check Difficulty Calibration Gates
    print("\n[4/4] Verifying Difficulty Calibration Gates (§2.8)...")
    top_score = max(e["metrics"]["t1"]["macro_f1"] for e in eval_summaries)
    maj_score = next(e["metrics"]["t1"]["macro_f1"] for e in eval_summaries if "Majority" in e["model_name"])

    print(f"  - Floor Guard:   Trivial Majority F1 = {maj_score:.4f} (Target <= 0.40) -> {'PASS' if maj_score <= 0.40 else 'FAIL'}")
    print(f"  - Ceiling Guard: Top Baseline F1     = {top_score:.4f} (Target <= 0.80) -> {'PASS' if top_score <= 0.80 else 'FAIL'}")
    print("  - Human Ceiling: NOT MEASURED (no human annotation has been done yet)")

    assert maj_score <= 0.40, "Trivial baseline exceeded floor guard"
    assert top_score <= 0.80, "Top baseline exceeded ceiling guard"

    print("\n" + "=" * 80)
    print("ALL REPRODUCTION MILESTONES COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
