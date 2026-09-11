import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "agent"))

from cloud_setup import (
    bind, check_cleanup, cleanup, grant_agent_access, preflight, prepare_iq, prepare_models,
    repair_observability, set_prompt,
)
from common import RESULTS_DIR, utc_stamp, write_json
from contracts import MODEL_SPECS
from experiments import calibrate, collect, compare, evaluate, feedback, smoke, verify_evidence
from knowledge import retrieve
from observability import monitor
from settings import RuntimeConfig, credential, load_settings_env


def main() -> None:
    load_settings_env()
    parser = argparse.ArgumentParser(description="Korean Foundry learning-loop workshop; no mocked cloud results.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("preflight").add_argument("--allow-missing-models", action="store_true")
    sub.add_parser("prepare-models")
    sub.add_parser("prepare-iq")
    calibration = sub.add_parser("calibrate")
    calibration.add_argument("--timeout", type=int, default=600)
    calibration.add_argument("--retry-failed", action="store_true")
    sub.add_parser("repair-observability").add_argument("--confirm", action="store_true")
    sub.add_parser("bind")
    sub.add_parser("set-prompt").add_argument("version", choices=["v1", "v2"])
    sub.add_parser("grant-agent-access").add_argument("--principal-id")
    smoke_parser = sub.add_parser("smoke")
    smoke_parser.add_argument("--local", action="store_true")
    smoke_parser.add_argument("--model", choices=list(MODEL_SPECS), default="sol")
    smoke_parser.add_argument("--case-id", default="D01")
    retrieval = sub.add_parser("retrieve")
    retrieval.add_argument("--query", required=True)
    collection = sub.add_parser("collect")
    collection.add_argument("--split", choices=["dev", "holdout"], required=True)
    collection.add_argument("--label", required=True)
    collection.add_argument("--concurrency", type=int, choices=[1, 2, 4], default=4)
    evaluation = sub.add_parser("evaluate")
    evaluation.add_argument("--label", required=True)
    evaluation.add_argument("--timeout", type=int, default=600)
    evaluation.add_argument("--retry-failed", action="store_true")
    sub.add_parser("compare").add_argument("--labels", nargs="+", required=True)
    review = sub.add_parser("feedback")
    review.add_argument("--label", required=True)
    review.add_argument("--row-id", required=True)
    review.add_argument("--reason", required=True)
    review.add_argument("--reviewer", choices=["human", "assistant"], default="human")
    sub.add_parser("monitor").add_argument("--label", required=True)
    verification = sub.add_parser("verify")
    verification.add_argument("--baseline", required=True)
    verification.add_argument("--candidate", required=True)
    verification.add_argument("--holdout", required=True)
    deletion = sub.add_parser("cleanup")
    mode = deletion.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--confirm", action="store_true")
    sub.add_parser("check-cleanup")
    args = parser.parse_args()
    if args.command == "preflight":
        preflight(args.allow_missing_models)
    elif args.command == "prepare-models":
        prepare_models()
    elif args.command == "prepare-iq":
        prepare_iq()
    elif args.command == "calibrate":
        calibrate(args.timeout, args.retry_failed)
    elif args.command == "repair-observability":
        repair_observability(args.confirm)
    elif args.command == "bind":
        bind()
    elif args.command == "set-prompt":
        set_prompt(args.version)
    elif args.command == "grant-agent-access":
        grant_agent_access(args.principal_id)
    elif args.command == "smoke":
        smoke(args.local, args.model, args.case_id)
    elif args.command == "retrieve":
        result = asyncio.run(retrieve(RuntimeConfig.from_env(), credential(), args.query))
        destination = RESULTS_DIR / f"retrieval-{utc_stamp()}.json"
        write_json(destination, result)
        print(json.dumps({
            "knowledge_base": result["knowledge_base"],
            "document_ids": [doc["id"] for doc in result["documents"]],
            "activity": result["activity"],
            "saved": str(destination),
        }, ensure_ascii=False, indent=2))
    elif args.command == "collect":
        collect(args.split, args.label, args.concurrency)
    elif args.command == "evaluate":
        evaluate(args.label, args.timeout, args.retry_failed)
    elif args.command == "compare":
        compare(args.labels)
    elif args.command == "feedback":
        feedback(args.label, args.row_id, args.reason, args.reviewer)
    elif args.command == "monitor":
        monitor(args.label)
    elif args.command == "verify":
        verify_evidence(args.baseline, args.candidate, args.holdout)
    elif args.command == "cleanup":
        cleanup(args.confirm)
    elif args.command == "check-cleanup":
        check_cleanup()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    main()
