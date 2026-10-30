from __future__ import annotations

import argparse
import sys
from pathlib import Path

from apps.config import load_config
from apps.errors import ConfigError, LinkSafetyError
from apps.links import LinkState, SystemLinkStrategy
from apps.operations import build_plan, sync_rule_indexes, sync_rules

ROOT_DIR = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create configured links and sync project rules and rule indexes."
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=ROOT_DIR / "skillhub.yaml",
        help="Path to the Skill Hub configuration file.",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except (ConfigError, OSError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2

    strategy = SystemLinkStrategy()
    created = 0
    already_present = 0
    migrated = 0
    issues: list[tuple[str, Path, str]] = []

    for plan in build_plan(config):
        if plan.has_source_conflict:
            issues.append(
                (
                    "plan-conflict",
                    plan.target,
                    "multiple providers assign different skills to this shared target: "
                    + ", ".join(str(path) for path in plan.sources),
                )
            )
            continue
        if not plan.project_path.is_dir():
            issues.append(
                ("project-missing", plan.project_path, "project directory does not exist")
            )
            continue

        assert plan.source is not None
        if not plan.source.is_dir():
            issues.append(
                ("source-missing", plan.source, "skill source directory does not exist")
            )
            continue

        before = strategy.check(plan.source, plan.target)
        was_migrated = False
        if before is LinkState.WRONG_TARGET:
            legacy_source = config.root / "skills" / plan.source.name
            legacy_state = strategy.check(legacy_source, plan.target)
            if legacy_state in (LinkState.PRESENT, LinkState.BROKEN):
                try:
                    strategy.remove(plan.target, legacy_source)
                except (OSError, LinkSafetyError) as exc:
                    issues.append(("link-error", plan.target, str(exc)))
                    continue
                before = LinkState.MISSING
                migrated += 1
                was_migrated = True

        try:
            strategy.create(plan.source, plan.target)
        except (OSError, LinkSafetyError) as exc:
            issues.append(("link-error", plan.target, str(exc)))
            continue

        if before is LinkState.PRESENT:
            already_present += 1
        elif not was_migrated:
            created += 1

    rule_result = sync_rules(config)
    issues.extend(
        (issue.code, issue.location, issue.message)
        for issue in rule_result.issues
    )
    rule_index_result = sync_rule_indexes(config)
    issues.extend(
        (issue.code, issue.location, issue.message)
        for issue in rule_index_result.issues
    )

    print(f"Created {created} link(s); {already_present} already current.")
    if migrated:
        print(f"Updated {migrated} link(s) from the previous skills/ location.")
    if rule_result.blocks_added or rule_result.blocks_removed:
        print(
            f"Rules: {rule_result.blocks_added} block(s) added; "
            f"{rule_result.blocks_removed} removed."
        )
    if rule_index_result.files_linked or rule_index_result.documents_updated:
        print(
            f"Rule indexes: {rule_index_result.files_linked} file(s) linked; "
            f"{rule_index_result.documents_updated} document(s) updated."
        )
    for code, location, message in issues:
        print(f"ERROR [{code}] {location}: {message}", file=sys.stderr)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
