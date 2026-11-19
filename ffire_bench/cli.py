"""
Command Line Interface for FFIRE-Bench.
Supports dataset generation, baseline benchmarking, evaluation, and leaderboard generation.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List

from ffire_bench.schema.models import Case, PredictionBundle, Track, Split
from ffire_bench.generators.ffire_gen import FFIREGenerator
from ffire_bench.scoring.evaluator import BenchmarkEvaluator
from ffire_bench.leaderboard.generator import LeaderboardGenerator
from ffire_bench.runners import (
    MajorityBaselineRunner,
    RandomBaselineRunner,
    HeuristicRuleRunner,
    LLMPromptRunner,
    FFIREVerifierRunner,
    make_caller
)


def cmd_generate(args):
    """Generate synthetic evaluation cases."""
    print(f"[*] Generating {args.num_cases} cases (seed={args.seed}, track={args.track}, split={args.split})...")
    gen = FFIREGenerator(seed=args.seed)
    track_enum = Track(args.track)
    split_enum = Split(args.split)

    cases = []
    for i in range(1, args.num_cases + 1):
        c = gen.generate_case(
            case_idx=i,
            track=track_enum,
            split=split_enum,
            inject_error=(i % 2 == 1)  # alternate clean and error-injected cases
        )
        cases.append(c.model_dump())

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2)

    print(f"[+] Successfully wrote {len(cases)} cases to: {out_path}")


def cmd_benchmark(args):
    """Run a baseline or model runner against an evaluation dataset."""
    print(f"[*] Running model '{args.runner}' against dataset '{args.dataset}'...")

    with open(args.dataset, "r", encoding="utf-8") as f:
        data = json.load(f)
    cases = [Case(**c) for c in data]

    def make_llm():
        if not args.model:
            raise ValueError("--model is required for the llm runner (e.g. --provider openai --model gpt-4o)")
        caller = make_caller(args.provider, args.model, base_url=args.base_url)
        return LLMPromptRunner(model_name=f"{args.provider}:{args.model}", api_caller=caller)

    # Factories, so runners that need an API key or a live backend are only
    # built when selected.
    runner_map = {
        "majority": lambda: MajorityBaselineRunner(),
        "random": lambda: RandomBaselineRunner(seed=args.seed),
        "heuristic": lambda: HeuristicRuleRunner(),
        "llm": make_llm,
        "ffire": lambda: FFIREVerifierRunner(endpoint_url=args.ffire_url),
    }

    factory = runner_map.get(args.runner.lower())
    if not factory:
        print(f"[!] Unknown runner '{args.runner}'. Choose from: {list(runner_map.keys())}")
        sys.exit(1)
    try:
        runner = factory()
    except ValueError as exc:
        print(f"[!] {exc}")
        sys.exit(1)

    track_enum = Track(args.track)
    bundle = runner.run_benchmark(cases, track=track_enum)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(bundle.model_dump(), f, indent=2)

    print(f"[+] Predictions exported to: {out_path}")


def cmd_eval(args):
    """Evaluate model predictions against gold-standard cases."""
    print(f"[*] Evaluating predictions '{args.predictions}' against ground-truth '{args.ground_truth}'...")

    with open(args.ground_truth, "r", encoding="utf-8") as f:
        gt_data = json.load(f)
    gold_cases = [Case(**c) for c in gt_data]

    with open(args.predictions, "r", encoding="utf-8") as f:
        pred_data = json.load(f)
    predictions = PredictionBundle(**pred_data)

    evaluator = BenchmarkEvaluator()
    results = evaluator.evaluate(gold_cases, predictions)

    print("\n" + "=" * 75)
    print(f"FFIRE-Bench Evaluation Summary: {results['model_name']} (Track {results['track']})")
    print("=" * 75)
    t1 = results["metrics"].get("t1", {})
    t2 = results["metrics"].get("t2", {})
    t3 = results["metrics"].get("t3", {})

    if t1:
        print(f"Track 1 (Claim Verification):")
        print(f"  Macro-F1:            {t1.get('macro_f1', 0.0):.4f}")
        print(f"  Evidence Citation F1:{t1.get('citation_metrics', {}).get('citation_f1', 0.0):.4f}")
    if t2:
        print(f"Track 2 (Error Detection):")
        print(f"  Safe-to-File Acc:    {t2.get('safe_to_file_accuracy', 0.0):.2f}%")
        print(f"  Critical Error Rec:  {t2.get('critical_error_recall', 0.0):.2f}%")
    if t3:
        print(f"Track 3 (Disposition & Abstention):")
        print(f"  Cost-Weighted Acc:   {t3.get('cost_weighted_accuracy', 0.0):.2f}%")
        print(f"  Brier Calibration:   {t3.get('brier_score', 0.0)}")
        print(f"  15-bin ECE:          {t3.get('ece_15_bins', 0.0)}")

    print(f"Benchmark Status:      {results['overall_status']} ({results['targets_passed']}/{results['targets_total']} Targets Met)")
    print("=" * 75)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"[+] Detailed evaluation report saved to: {out_path}")


def cmd_leaderboard(args):
    """Compile evaluation reports into a public leaderboard."""
    print(f"[*] Compiling leaderboard from results...")
    eval_summaries = []

    for file_path in args.results:
        p = Path(file_path)
        if p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "metrics" in data:
                    eval_summaries.append(data)
        elif p.is_dir():
            for fpath in p.glob("eval_*.json"):
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "metrics" in data:
                        eval_summaries.append(data)

    if not eval_summaries:
        print("[!] No evaluation result files found.")
        return

    md_content = LeaderboardGenerator.generate_markdown(eval_summaries)
    if args.output_md:
        out_md = Path(args.output_md)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        with open(out_md, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"[+] Leaderboard Markdown written to: {out_md}")

    if args.output_html:
        html_content = LeaderboardGenerator.generate_html(eval_summaries)
        out_html = Path(args.output_html)
        out_html.parent.mkdir(parents=True, exist_ok=True)
        with open(out_html, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[+] Leaderboard HTML written to: {out_html}")


def main():
    parser = argparse.ArgumentParser(
        prog="ffire-bench",
        description="FFIRE-Bench: Financial Fraud Investigation Reasoning & Evidence Benchmark CLI"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Generate
    p_gen = subparsers.add_parser("generate", help="Generate synthetic evaluation cases")
    p_gen.add_argument("--num-cases", type=int, default=20, help="Number of cases to generate")
    p_gen.add_argument("--output", type=str, default="data/gold_standard_20_cases.json", help="Output JSON path")
    p_gen.add_argument("--seed", type=int, default=42, help="Random seed for deterministic generation")
    p_gen.add_argument("--track", type=str, default="T1", choices=["T1", "T2", "T3", "T4", "T5", "T6"])
    p_gen.add_argument("--split", type=str, default="dev", choices=["dev", "public_test", "private_test"])
    p_gen.set_defaults(func=cmd_generate)

    # Benchmark
    p_bench = subparsers.add_parser("benchmark", help="Run a model runner against a dataset")
    p_bench.add_argument("--runner", type=str, required=True, choices=["majority", "random", "heuristic", "llm", "ffire"], help="Model adapter")
    p_bench.add_argument("--dataset", type=str, required=True, help="Path to input dataset JSON")
    p_bench.add_argument("--output", type=str, required=True, help="Path to output predictions JSON")
    p_bench.add_argument("--track", type=str, default="T1")
    p_bench.add_argument("--seed", type=int, default=42)
    p_bench.add_argument("--provider", type=str, default="openai", choices=["openai", "anthropic"],
                         help="llm runner: 'openai' = any OpenAI-compatible API, 'anthropic' = Anthropic API")
    p_bench.add_argument("--model", type=str, default=None, help="llm runner: model name, e.g. gpt-4o")
    p_bench.add_argument("--base-url", type=str, default=None,
                         help="llm runner: OpenAI-compatible base URL (default OPENAI_BASE_URL or api.openai.com)")
    p_bench.add_argument("--ffire-url", type=str, default=None,
                         help="ffire runner: FFIRE backend URL (default FFIRE_VERIFIER_URL)")
    p_bench.set_defaults(func=cmd_benchmark)

    # Eval
    p_eval = subparsers.add_parser("eval", help="Score model predictions against ground truth")
    p_eval.add_argument("--predictions", type=str, required=True, help="Path to predictions JSON")
    p_eval.add_argument("--ground-truth", type=str, required=True, help="Path to ground-truth cases JSON")
    p_eval.add_argument("--output", type=str, default=None, help="Path to save detailed evaluation report JSON")
    p_eval.set_defaults(func=cmd_eval)

    # Leaderboard
    p_lb = subparsers.add_parser("leaderboard", help="Generate leaderboard Markdown and HTML")
    p_lb.add_argument("--results", nargs="+", required=True, help="Path(s) to evaluation report JSON file(s) or directory")
    p_lb.add_argument("--output-md", type=str, default="docs/LEADERBOARD.md", help="Output markdown path")
    p_lb.add_argument("--output-html", type=str, default="docs/leaderboard.html", help="Output HTML path")
    p_lb.set_defaults(func=cmd_leaderboard)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
