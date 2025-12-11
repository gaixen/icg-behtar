import argparse

from unified_runner import UnifiedRunner


def main():
    parser = argparse.ArgumentParser(
        description="Mental Health Chatbot Evaluation System"
    )
    subparsers = parser.add_subparsers(dest="command")

    ingest_parser = subparsers.add_parser("ingest")
    ingest_parser.add_argument("--source", required=True, help="Path to file or 'db'")

    eval_parser = subparsers.add_parser("eval")
    eval_parser.add_argument(
        "--source", default="redteam", help="persona, redteam, or dataset"
    )
    eval_parser.add_argument(
        "--limit", type=int, default=10, help="Number of prompts to evaluate"
    )

    cluster_parser = subparsers.add_parser("cluster")
    cluster_parser.add_argument("--since", help="Timestamp to start clustering from")
    cluster_parser.add_argument("--method", default="auto", help="auto or fallback")

    test_parser = subparsers.add_parser("run-tests")
    test_parser.add_argument(
        "--test-ids", required=True, help="Comma-separated list of test IDs"
    )
    test_parser.add_argument(
        "--prompts", default="dataset", help="Source of prompts to run tests on"
    )

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument(
        "--clusters", action="store_true", help="Export cluster data"
    )
    export_parser.add_argument(
        "--path", default="output/export.csv", help="Output path for CSV"
    )

    args = parser.parse_args()
    runner = UnifiedRunner()

    if args.command == "ingest":
        runner.prompt_ingestor.ingest_from_file(args.source, "cli-ingest")
    elif args.command == "eval":
        runner.run_evaluation_cycle(args.source, args.limit)
    elif args.command == "cluster":
        runner.cluster_and_analyze(time_window=args.since, method=args.method)
    elif args.command == "run-tests":
        test_ids = [int(tid) for tid in args.test_ids.split(",")]
        runner.run_psych_tests_sequential(test_ids, args.prompts)
    elif args.command == "export":
        if args.clusters:
            df = runner.cluster_engine.cluster_and_save(limit=10000)
            runner.visualizer.save_cluster_csv(df, args.path)


if __name__ == "__main__":
    main()
