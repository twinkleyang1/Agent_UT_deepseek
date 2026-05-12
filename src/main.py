#!/usr/bin/env python3
"""
UT Generation Orchestrator - Main Entry Point

A long-running multi-agent system that auto-generates Java unit tests
using Claude Code's Orchestrator + Subagent architecture.

Usage:
    # Initialize and scan project
    python src/main.py init

    # Show current status
    python src/main.py status

    # Run one iteration (init/generate/evaluate)
    python src/main.py run

    # Run full loop until complete (requires Claude Code for subagent dispatch)
    python src/main.py loop --max-iterations 200

    # Get subagent prompts for current batch
    python src/main.py prompts

    # Apply results from dispatched subagents
    python src/main.py apply --results-file results.json

    # Reset all state files
    python src/main.py reset --force
"""

import argparse
import json
import os
import sys

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.config import ProjectConfig
from src.orchestrator import Orchestrator


def cmd_init(orchestrator: Orchestrator, args) -> int:
    """Initialize: scan project, create state files, sync existing tests."""
    if orchestrator.state.is_initialized() and not args.force:
        print("Already initialized. Use --force to re-initialize.")
        return 0

    orchestrator.run_phase1()

    # Auto-sync existing test files
    test_dir = os.path.join(orchestrator.java_project_path,
                            "src", "test", "java")
    if os.path.exists(test_dir):
        sync_result = orchestrator.state.sync_existing_tests(test_dir)
        print(f"\nSynced existing tests: {sync_result['synced']} matched, "
              f"{sync_result['skipped']} unmatched "
              f"({sync_result.get('classes_with_tests', 0)} test classes)")

    print("\nInitialization complete.")
    print(f"Run 'python src/main.py status' to see status.")
    print(f"Run 'python src/main.py run' to execute next phase.")
    return 0


def cmd_status(orchestrator: Orchestrator) -> int:
    """Show current status."""
    summary = orchestrator.state.get_summary()
    m = summary["methods"]
    c = summary["coverage"]

    print("=" * 50)
    print("UT Generation Orchestrator Status")
    print("=" * 50)
    print(f"Phase:        {summary['phase']}")
    print(f"Initialized:  {summary['initialized']}")
    print()
    print("Methods:")
    print(f"  Total:      {m['total']}")
    print(f"  Passed:     {m['pass']}")
    print(f"  Failed:     {m['fail']}")
    print(f"  Pending:    {m['pending']}")
    print(f"  In Progress:{m['in_progress']}")
    print()
    print("Coverage:")
    print(f"  Line:       {c['line']*100:.1f}%")
    print(f"  Branch:     {c['branch']*100:.1f}%")
    print(f"  Method:     {c['method']*100:.1f}%")
    print()
    print(f"Targets Met:  {summary['targets_met']}")
    print("=" * 50)

    # Also print pending methods if in generate phase
    if summary["phase"] == "generate":
        pending = orchestrator.state.get_pending_methods()[:10]
        if pending:
            print(f"\nNext {min(10, len(pending))} pending methods:")
            for p in pending:
                print(f"  [{p['priority']}] {p['class_name']}.{p['method_name']} "
                      f"({p['complexity']})")

    return 0


def cmd_run(orchestrator: Orchestrator, args) -> int:
    """Run one iteration of the current phase."""
    result = orchestrator.run_iteration()
    phase = result.get("phase", "unknown")
    print(f"\nPhase: {phase}")

    if phase == "generate":
        prompts = result.get("prompts", [])
        print(f"Subagent prompts ready: {len(prompts)}")
        if args.print_prompts:
            for i, p in enumerate(prompts):
                print(f"\n{'='*40}")
                print(f"PROMPT {i+1}: {p['task']['class_name']}.{p['task']['method_name']}")
                print(f"{'='*40}")
                print(p["prompt"])

    return 0


def cmd_loop(orchestrator: Orchestrator, args) -> int:
    """Run the full orchestration loop."""
    print("Starting orchestration loop...")
    print("NOTE: Phase 2 (subagent dispatch) requires Claude Code Agent tool.")
    print("This script will generate prompts for subagent dispatch.")
    print()

    result = orchestrator.run(max_iterations=args.max_iterations)
    return 0 if result.get("status") == "complete" else 1


def cmd_prompts(orchestrator: Orchestrator, args) -> int:
    """Print subagent prompts for the current batch."""
    phase = orchestrator.state.detect_phase()

    if phase != "generate":
        print(f"Current phase is '{phase}'. No subagent dispatch needed.")
        print("Run 'python src/main.py status' to check state.")
        return 0

    batch_info = orchestrator.run_phase2()
    prompts = batch_info.get("prompts", [])

    if not prompts:
        print("No pending methods.")
        return 0

    if args.output:
        # Write prompts to file
        output_data = {
            "batch": batch_info.get("batch", []),
            "prompts": [{"task": p["task"], "prompt": p["prompt"]} for p in prompts],
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"Prompts written to: {args.output}")
    else:
        for i, p in enumerate(prompts):
            task = p["task"]
            print(f"\n--- Subagent {i+1}: {task['class_name']}.{task['method_name']} ---")
            print(p["prompt"])

    return 0


def cmd_apply(orchestrator: Orchestrator, args) -> int:
    """Apply subagent results from a JSON file."""
    if not os.path.exists(args.results_file):
        print(f"Results file not found: {args.results_file}")
        return 1

    with open(args.results_file, "r", encoding="utf-8") as f:
        results = json.load(f)

    if isinstance(results, dict):
        results = results.get("results", [results])

    print(f"Applying {len(results)} subagent results...")
    summary = orchestrator.apply_batch_results(results)
    print(f"Done. Phase: {summary['phase']}")

    return 0


def cmd_reset(orchestrator: Orchestrator, args) -> int:
    """Reset all state files."""
    if not args.force:
        print("WARNING: This will delete all state files in shared/.")
        print("Use --force to confirm.")
        return 1

    orchestrator.state.reset()
    print("State files reset.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="UT Generation Orchestrator - Multi-agent Java UT auto-generation"
    )

    parser.add_argument(
        "--project-root",
        default=PROJECT_ROOT,
        help="Root directory of the project",
    )
    parser.add_argument(
        "--java-project",
        default="dianping",
        help="Java project sub-directory name",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to a Java project directory (enables ProjectConfig mode)",
    )
    parser.add_argument(
        "--maven-bin",
        default=None,
        help="Custom Maven binary path (used with --config)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # init
    init_parser = subparsers.add_parser("init", help="Scan project and create state files")
    init_parser.add_argument("--force", action="store_true",
                             help="Force re-initialization")

    # status
    subparsers.add_parser("status", help="Show current status")

    # run
    run_parser = subparsers.add_parser("run", help="Run one iteration")
    run_parser.add_argument("--print-prompts", action="store_true",
                            help="Print full subagent prompts")

    # loop
    loop_parser = subparsers.add_parser("loop", help="Run full orchestration loop")
    loop_parser.add_argument("--max-iterations", type=int, default=200,
                             help="Maximum iterations (default: 200)")

    # prompts
    prompts_parser = subparsers.add_parser("prompts", help="Get subagent prompts")
    prompts_parser.add_argument("--output", "-o", help="Write prompts to JSON file")

    # apply
    apply_parser = subparsers.add_parser("apply", help="Apply subagent results")
    apply_parser.add_argument("--results-file", "-f", required=True,
                              help="JSON file with subagent results")

    # reset
    reset_parser = subparsers.add_parser("reset", help="Reset all state files")
    reset_parser.add_argument("--force", action="store_true", help="Confirm reset")

    args = parser.parse_args()

    config = None
    if args.config:
        config = ProjectConfig(
            id=os.path.basename(args.config.rstrip('/')),
            path=os.path.abspath(args.config),
            maven_bin=args.maven_bin or "/home/twinkle/app/maven/bin/mvn",
        )

    orchestrator = Orchestrator(
        project_root=args.project_root,
        java_project=args.java_project or "dianping",
        config=config,
    )

    if args.command == "init":
        return cmd_init(orchestrator, args)
    elif args.command == "status":
        return cmd_status(orchestrator)
    elif args.command == "run":
        return cmd_run(orchestrator, args)
    elif args.command == "loop":
        return cmd_loop(orchestrator, args)
    elif args.command == "prompts":
        return cmd_prompts(orchestrator, args)
    elif args.command == "apply":
        return cmd_apply(orchestrator, args)
    elif args.command == "reset":
        return cmd_reset(orchestrator, args)
    else:
        # Default: show status
        return cmd_status(orchestrator)


if __name__ == "__main__":
    sys.exit(main() or 0)
