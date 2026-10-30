from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from .links import LinkState, LinkStrategy
from .models import Config
from .providers import ProviderRegistry


@dataclass(frozen=True)
class LinkPlan:
    project_name: str
    project_path: Path
    target: Path
    source: Path | None
    sources: tuple[Path, ...]
    providers: tuple[str, ...]

    @property
    def has_source_conflict(self) -> bool:
        return len(self.sources) > 1


@dataclass(frozen=True)
class StatusRow:
    plan: LinkPlan
    state: str
    detail: str = ""


@dataclass(frozen=True)
class DoctorIssue:
    code: str
    location: Path
    message: str
    level: str = "error"


@dataclass(frozen=True)
class RuleSyncResult:
    blocks_added: int
    blocks_removed: int
    issues: tuple[DoctorIssue, ...]


@dataclass(frozen=True)
class RuleIndexDocument:
    name: str
    path: Path
    applicable_path: str
    description: str


@dataclass(frozen=True)
class RuleIndexSyncResult:
    files_linked: int
    documents_updated: int
    issues: tuple[DoctorIssue, ...]


_ATX_HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


def _markdown_headings(lines: list[str]) -> tuple[tuple[int, int, str], ...]:
    headings: list[tuple[int, int, str]] = []
    fence_character: str | None = None
    fence_length = 0
    for index, line in enumerate(lines):
        fence = _FENCE.match(line)
        if fence:
            marker = fence.group(1)
            if fence_character is None:
                fence_character = marker[0]
                fence_length = len(marker)
            elif marker[0] == fence_character and len(marker) >= fence_length:
                fence_character = None
            continue
        if fence_character is not None:
            continue
        heading = _ATX_HEADING.match(line.rstrip("\r\n"))
        if heading:
            headings.append((index, len(heading.group(1)), heading.group(2).strip()))
    return tuple(headings)


def _extract_rule_block(source: str) -> tuple[str, str] | None:
    lines = source.splitlines(keepends=True)
    headings = _markdown_headings(lines)
    for heading_index, level, title in headings:
        if level != 2:
            continue
        end = next(
            (index for index, next_level, _ in headings if index > heading_index and next_level <= 2),
            len(lines),
        )
        block = "".join(lines[heading_index:end]).strip("\r\n")
        if block.strip():
            return block, title
    return None


def _remove_rule_blocks(content: str, headings_to_remove: set[str]) -> tuple[str, int]:
    if not content or not headings_to_remove:
        return content, 0

    lines = content.splitlines(keepends=True)
    headings = _markdown_headings(lines)
    matches = [
        (index, title)
        for index, level, title in headings
        if level == 2 and title in headings_to_remove
    ]
    if not matches:
        return content, 0

    intervals: list[tuple[int, int]] = []
    for heading_index, _ in matches:
        start = heading_index
        while start > 0 and not lines[start - 1].strip():
            start -= 1
        next_heading = next(
            (
                index
                for index, level, _ in headings
                if index > heading_index and level <= 2
            ),
            len(lines),
        )
        end = next_heading
        if next_heading < len(lines) and end > heading_index and not lines[end - 1].strip():
            end -= 1
        intervals.append((start, end))

    intervals.sort()
    merged: list[tuple[int, int]] = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    removed_lines: set[int] = set()
    for start, end in merged:
        removed_lines.update(range(start, end))
    remaining = [line for index, line in enumerate(lines) if index not in removed_lines]
    while remaining and not remaining[0].strip():
        remaining.pop(0)
    while remaining and not remaining[-1].strip():
        remaining.pop()
    return "".join(remaining), len(matches)


def _append_rule_block(content: str, block: str) -> str:
    newline = "\r\n" if "\r\n" in content else "\n"
    normalized_block = block.replace("\r\n", "\n").replace("\r", "\n")
    normalized_block = normalized_block.replace("\n", newline).strip("\r\n")
    prefix = content.rstrip("\r\n")
    if not prefix.strip():
        return f"{normalized_block}{newline}"
    return f"{prefix}{newline}{newline}{normalized_block}{newline}"


def _load_rule_sources(
    config: Config, issues: list[DoctorIssue]
) -> dict[str, tuple[str, str | None]]:
    rules_dir = config.root / "source" / "rules"
    if not rules_dir.exists():
        return {}
    if not rules_dir.is_dir():
        issues.append(DoctorIssue("rule-source-error", rules_dir, "rules source path is not a directory"))
        return {}

    sources: dict[str, tuple[str, str | None]] = {}
    try:
        paths = sorted(rules_dir.glob("*.md"), key=lambda path: path.name)
    except OSError as exc:
        issues.append(DoctorIssue("rule-source-error", rules_dir, str(exc)))
        return {}

    for path in paths:
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            issues.append(DoctorIssue("rule-source-error", path, str(exc)))
            continue
        parsed = _extract_rule_block(source)
        sources[path.stem] = (source, parsed[1] if parsed else None)
    return sources


def sync_rules(config: Config) -> RuleSyncResult:
    """Apply configured source/rules blocks to each enabled provider's rule document."""
    issues: list[DoctorIssue] = []
    sources = _load_rule_sources(config, issues)
    managed_headings = {heading for _, heading in sources.values() if heading is not None}
    added = 0
    removed = 0
    registry = ProviderRegistry.from_overrides(config.provider_overrides)

    for project in config.projects.values():
        enabled_providers = project.enabled_providers(registry.names)
        has_rule_target = any(
            provider_name in config.provider_rule_dirs
            for provider_name in enabled_providers
        )
        if not project.path.is_dir():
            if project.rules or has_rule_target:
                issues.append(
                    DoctorIssue("project-missing", project.path, "project directory does not exist")
                )
            continue

        active_blocks: list[tuple[str, str]] = []
        for rule_name in project.rules:
            source = sources.get(rule_name)
            source_path = config.root / "source" / "rules" / f"{rule_name}.md"
            if source is None:
                issues.append(
                    DoctorIssue(
                        "rule-source-missing",
                        source_path,
                        f"project '{project.name}' references a missing rule source",
                    )
                )
                continue
            parsed = _extract_rule_block(source[0])
            if parsed is None:
                issues.append(
                    DoctorIssue(
                        "rule-source-invalid",
                        source_path,
                        "rule source must contain a level-two Markdown heading",
                    )
                )
                continue
            active_blocks.append(parsed)

        active_headings = {heading for _, heading in active_blocks}
        inactive_headings = managed_headings - active_headings
        targets: dict[str, Path] = {}
        for provider_name in enabled_providers:
            rule_dir = config.provider_rule_dirs.get(provider_name)
            if rule_dir is None:
                if project.rules:
                    issues.append(
                        DoctorIssue(
                            "rule-dir-missing",
                            project.path,
                            f"provider '{provider_name}' has no configured rule_dir",
                        )
                    )
                continue
            target = rule_dir if rule_dir.is_absolute() else project.path / rule_dir
            target = Path(os.path.abspath(target))
            targets.setdefault(os.path.normcase(str(target)), target)

        for target in targets.values():
            try:
                if target.exists() or target.is_symlink():
                    original = target.read_text(encoding="utf-8")
                else:
                    original = ""
            except (OSError, UnicodeError) as exc:
                issues.append(DoctorIssue("rule-document-error", target, str(exc)))
                continue

            updated, removed_count = _remove_rule_blocks(original, inactive_headings)
            present_headings = {
                title
                for _, level, title in _markdown_headings(updated.splitlines(keepends=True))
                if level == 2
            }
            added_count = 0
            for block, heading in active_blocks:
                if heading in present_headings:
                    continue
                updated = _append_rule_block(updated, block)
                present_headings.add(heading)
                added_count += 1

            if updated == original:
                continue
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(updated, encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                issues.append(DoctorIssue("rule-document-error", target, str(exc)))
                continue
            added += added_count
            removed += removed_count

    return RuleSyncResult(added, removed, tuple(issues))


def _read_rule_index(path: Path) -> tuple[RuleIndexDocument | None, str | None]:
    try:
        source = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, "source file does not exist"
    except (OSError, UnicodeError) as exc:
        return None, str(exc)

    lines = source.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, "rule-index file must start with YAML front matter"
    closing_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
    if closing_index is None:
        return None, "rule-index YAML front matter is not closed"
    try:
        metadata = yaml.safe_load("".join(lines[1:closing_index]))
    except yaml.YAMLError as exc:
        return None, f"invalid YAML front matter: {exc}"
    if not isinstance(metadata, dict):
        return None, "rule-index front matter must be a mapping"

    applicable_path = metadata.get("applicable_path")
    description = metadata.get("description")
    if not isinstance(applicable_path, str) or not applicable_path.strip():
        return None, "front matter must define a non-empty applicable_path"
    if not isinstance(description, str) or not description.strip():
        return None, "front matter must define a non-empty description"

    applicable_path = " ".join(applicable_path.split())
    if len(applicable_path) >= 2 and applicable_path[0] == applicable_path[-1] == "`":
        applicable_path = applicable_path[1:-1]
    description = " ".join(description.split())
    return (
        RuleIndexDocument(path.stem, path, applicable_path, description),
        None,
    )


def _absolute_project_path(project_path: Path, configured_path: Path) -> Path:
    path = configured_path if configured_path.is_absolute() else project_path / configured_path
    return Path(os.path.abspath(path))


def _ensure_rule_index_link(source: Path, target: Path) -> tuple[bool, str | None]:
    if not source.is_file():
        return False, f"rule-index source file does not exist: {source}"

    if os.path.lexists(target):
        if not target.is_symlink():
            return False, "target exists and is not a symbolic link"
        if target.resolve(strict=False) != source.resolve(strict=False):
            return False, "symbolic link points to a different source"
        if not target.exists():
            return False, "symbolic link is broken"
        return False, None

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(source.resolve(), target_is_directory=False)
    except OSError as exc:
        return False, str(exc)
    return True, None


def _markdown_cell(value: str) -> str:
    return " ".join(value.replace("|", "\\|").split())


def _inline_code(value: str) -> str:
    return f"`{_markdown_cell(value).replace('`', '%60')}`"


def _rule_index_sections(
    rows: list[tuple[str, str, str]], directories: tuple[str, ...]
) -> tuple[str, str]:
    if len(directories) == 1:
        directory_list = _inline_code(directories[0].rstrip("/\\") + "/")
        storage_rule = f"项目专项规则统一存放于 {directory_list}。"
    else:
        directory_list = "、".join(
            _inline_code(directory.rstrip("/\\") + "/") for directory in directories
        )
        storage_rule = f"项目专项规则统一存放于各 Provider 的规则目录（{directory_list}）。"

    loading_section = "\n".join(
        (
            "### 规则加载机制",
            "",
            f"- {storage_rule}",
            "- 执行任务前，根据任务涉及的文件路径识别适用规则，并阅读对应规则文件。",
            "- 任务执行过程中，如果新增涉及其他目录，必须补充读取相关规则。",
            "- 未匹配的规则无需读取。",
            "- 适用的规则在当前任务中必须遵循。",
            "",
        )
    )

    index_lines = [
        "### 规则索引",
        "",
        "| 适用路径 | 规则文件 | 说明 |",
        "|---|---|---|",
    ]
    index_lines.extend(
        f"| {_inline_code(applicable_path)} | {_inline_code(rule_path)} | {_markdown_cell(description)} |"
        for applicable_path, rule_path, description in rows
    )
    index_lines.append("")
    return loading_section, "\n".join(index_lines)


def _migrate_legacy_rule_index_headings(content: str) -> str:
    """Move the previously generated H1/H2 block to the current H2/H3 hierarchy."""
    lines = content.splitlines(keepends=True)
    headings = _markdown_headings(lines)
    roots = [
        index
        for index, level, title in headings
        if level == 1 and title == "项目开发规范"
    ]
    if not roots:
        return content

    for root_index in roots:
        root_end = next(
            (
                index
                for index, level, _ in headings
                if index > root_index and level == 1
            ),
            len(lines),
        )
        for index, level, title in headings:
            if index == root_index:
                newline = "\r\n" if lines[index].endswith("\r\n") else "\n"
                lines[index] = f"## 项目规则索引规范{newline}"
            elif (
                root_index < index < root_end
                and level == 2
                and title in {"规则加载机制", "规则索引"}
            ):
                newline = "\r\n" if lines[index].endswith("\r\n") else "\n"
                lines[index] = f"### {title}{newline}"
    return "".join(lines)


def _upsert_project_rule_section(
    content: str,
    section: str,
    heading_title: str,
    *,
    insert_before: str | None = None,
    insert_after: str | None = None,
) -> str:
    newline = "\r\n" if "\r\n" in content else "\n"
    normalized_section = section.replace("\r\n", "\n").replace("\r", "\n")
    section_lines = [
        line.replace("\n", newline) for line in normalized_section.splitlines(keepends=True)
    ]
    if section_lines and not section_lines[-1].endswith(("\n", "\r")):
        section_lines[-1] += newline
    section_lines.append(newline)

    lines = content.splitlines(keepends=True)
    headings = _markdown_headings(lines)
    root = next(
        (
            (index, level)
            for index, level, title in headings
            if level == 2 and title == "项目规则索引规范"
        ),
        None,
    )
    if root is None:
        block = "## 项目规则索引规范\n\n" + normalized_section
        return _append_rule_block(content, block)

    root_index = root[0]

    def root_end_for(current_headings: tuple[tuple[int, int, str], ...]) -> int:
        return next(
            (index for index, level, _ in current_headings if index > root_index and level <= 2),
            len(lines),
        )

    root_end = root_end_for(headings)
    target = next(
        (
            index
            for index, level, title in headings
            if root_index < index < root_end and level == 3 and title == heading_title
        ),
        None,
    )
    if target is not None:
        end = next(
            (
                index
                for index, level, _ in headings
                if target < index < root_end and level <= 3
            ),
            root_end,
        )
        lines[target:end] = section_lines
        return "".join(lines)

    insertion = root_end
    if insert_before is not None:
        insertion = next(
            (
                index
                for index, level, title in headings
                if root_index < index < root_end and level == 3 and title == insert_before
            ),
            insertion,
        )
    elif insert_after is not None:
        after_heading = next(
            (
                index
                for index, level, title in headings
                if root_index < index < root_end and level == 3 and title == insert_after
            ),
            None,
        )
        if after_heading is not None:
            insertion = next(
                (
                    index
                    for index, level, _ in headings
                    if after_heading < index < root_end and level <= 3
                ),
                root_end,
            )
    else:
        insertion = next(
            (
                index
                for index, level, _ in headings
                if root_index < index < root_end and level == 3
            ),
            root_end,
        )

    before = lines[:insertion]
    if before and before[-1].strip():
        before.append(newline)
    return "".join((*before, *section_lines, *lines[insertion:]))


def _sync_rule_index_document(
    target: Path,
    rows: list[tuple[str, str, str]],
    directories: tuple[str, ...],
) -> tuple[bool, str | None]:
    try:
        original = target.read_text(encoding="utf-8") if target.exists() else ""
    except (OSError, UnicodeError) as exc:
        return False, str(exc)

    original = _migrate_legacy_rule_index_headings(original)
    loading_section, index_section = _rule_index_sections(rows, directories)
    updated = _upsert_project_rule_section(
        original,
        loading_section,
        "规则加载机制",
        insert_before="规则索引",
    )
    updated = _upsert_project_rule_section(
        updated,
        index_section,
        "规则索引",
        insert_after="规则加载机制",
    )
    if updated == original:
        return False, None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(updated, encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return False, str(exc)
    return True, None


def _remove_rule_index_document_section(target: Path) -> tuple[bool, str | None]:
    try:
        original = target.read_text(encoding="utf-8") if target.exists() else ""
    except (OSError, UnicodeError) as exc:
        return False, str(exc)

    original = _migrate_legacy_rule_index_headings(original)
    updated, removed = _remove_rule_blocks(original, {"项目规则索引规范"})
    if not removed:
        return False, None
    try:
        target.write_text(updated, encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return False, str(exc)
    return True, None


def sync_rule_indexes(config: Config) -> RuleIndexSyncResult:
    """Link configured rule-index files and update each Provider's rule document."""
    issues: list[DoctorIssue] = []
    files_linked = 0
    documents_updated = 0
    registry = ProviderRegistry.from_overrides(config.provider_overrides)

    active_targets: set[str] = set()
    for project in config.projects.values():
        if not project.rule_indexes:
            continue
        for provider_name in project.enabled_providers(registry.names):
            rule_dir = config.provider_rule_dirs.get(provider_name)
            if rule_dir is not None:
                target = _absolute_project_path(project.path, rule_dir)
                active_targets.add(os.path.normcase(str(target)))

    for project in config.projects.values():
        if not project.rule_indexes:
            if not project.path.is_dir():
                continue

            targets: dict[str, Path] = {}
            for provider_name in project.enabled_providers(registry.names):
                rule_dir = config.provider_rule_dirs.get(provider_name)
                if rule_dir is None:
                    continue
                target = _absolute_project_path(project.path, rule_dir)
                target_key = os.path.normcase(str(target))
                if target_key not in active_targets:
                    targets.setdefault(target_key, target)

            for target in targets.values():
                updated, error = _remove_rule_index_document_section(target)
                if error is not None:
                    issues.append(DoctorIssue("rule-index-document-error", target, error))
                elif updated:
                    documents_updated += 1
            continue
        if not project.path.is_dir():
            issues.append(
                DoctorIssue("project-missing", project.path, "project directory does not exist")
            )
            continue

        documents: list[RuleIndexDocument] = []
        for name in project.rule_indexes:
            source_path = config.root / "source" / "rule-index" / f"{name}.md"
            document, error = _read_rule_index(source_path)
            if error is not None:
                code = "rule-index-source-missing" if not source_path.exists() else "rule-index-source-invalid"
                issues.append(DoctorIssue(code, source_path, error))
                continue
            assert document is not None
            documents.append(document)

        enabled_providers = project.enabled_providers(registry.names)
        targets: dict[str, tuple[Path, list[tuple[str, str, str]], set[str]]] = {}
        for provider_name in enabled_providers:
            rule_dir = config.provider_rule_dirs.get(provider_name)
            index_dir = config.provider_rule_index_dirs.get(provider_name)
            if rule_dir is None:
                issues.append(
                    DoctorIssue(
                        "rule-dir-missing",
                        project.path,
                        f"provider '{provider_name}' has no configured rule_dir",
                    )
                )
                continue

            rule_target = _absolute_project_path(project.path, rule_dir)
            target_key = os.path.normcase(str(rule_target))
            group = targets.setdefault(target_key, (rule_target, [], set()))
            if index_dir is None:
                issues.append(
                    DoctorIssue(
                        "rule-index-dir-missing",
                        project.path,
                        f"provider '{provider_name}' has no configured rule_index_dir",
                    )
                )
                continue

            directory_path = _absolute_project_path(project.path, index_dir)
            try:
                directory_display = directory_path.relative_to(project.path).as_posix()
            except ValueError:
                directory_display = str(directory_path)
            group[2].add(directory_display)

            for document in documents:
                link_target = Path(os.path.abspath(directory_path / document.path.name))
                created, error = _ensure_rule_index_link(document.path, link_target)
                if error is not None:
                    issues.append(DoctorIssue("rule-index-link-error", link_target, error))
                    continue
                if created:
                    files_linked += 1
                try:
                    rule_file_display = link_target.relative_to(project.path).as_posix()
                except ValueError:
                    rule_file_display = os.path.relpath(link_target, project.path).replace(os.sep, "/")
                row = (document.applicable_path, rule_file_display, document.description)
                if row not in group[1]:
                    group[1].append(row)

        for target, rows, directory_set in targets.values():
            directories = tuple(sorted(directory_set))
            if not directories:
                continue
            updated, error = _sync_rule_index_document(target, rows, directories)
            if error is not None:
                issues.append(DoctorIssue("rule-index-document-error", target, error))
            elif updated:
                documents_updated += 1

    return RuleIndexSyncResult(files_linked, documents_updated, tuple(issues))


def build_plan(config: Config, registry: ProviderRegistry | None = None) -> tuple[LinkPlan, ...]:
    registry = registry or ProviderRegistry.from_overrides(config.provider_overrides)
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    for project in config.projects.values():
        for provider_name in project.enabled_providers(registry.names):
            provider = registry[provider_name]
            provider_dir = provider.skill_dir(config.provider_overrides.get(provider_name))
            skill_dir = provider_dir if provider_dir.is_absolute() else project.path / provider_dir
            for skill_name in project.skills_for(provider_name):
                source = config.skills[skill_name].path.resolve(strict=False)
                # Keep the final path lexical: resolving an existing link here would
                # collapse the destination to its source and break status/idempotency.
                target = Path(os.path.abspath(skill_dir / skill_name))
                target_key = os.path.normcase(str(target))
                source_key = os.path.normcase(str(source))
                key = (os.path.normcase(str(project.path)), target_key)
                group = grouped.setdefault(
                    key,
                    {
                        "project_name": project.name,
                        "project_path": project.path,
                        "target": target,
                        "sources": {},
                        "providers": [],
                    },
                )
                sources = group["sources"]
                assert isinstance(sources, dict)
                sources[source_key] = source
                providers = group["providers"]
                assert isinstance(providers, list)
                if provider_name not in providers:
                    providers.append(provider_name)

    plans: list[LinkPlan] = []
    for group in grouped.values():
        source_map = group["sources"]
        assert isinstance(source_map, dict)
        sources = tuple(source_map.values())
        plans.append(
            LinkPlan(
                project_name=str(group["project_name"]),
                project_path=Path(group["project_path"]),
                target=Path(group["target"]),
                source=sources[0] if len(sources) == 1 else None,
                sources=sources,
                providers=tuple(group["providers"]),  # type: ignore[arg-type]
            )
        )
    return tuple(plans)


def status(config: Config, strategy: LinkStrategy) -> tuple[StatusRow, ...]:
    rows: list[StatusRow] = []
    for plan in build_plan(config):
        if plan.has_source_conflict:
            rows.append(
                StatusRow(plan, "plan conflict", "providers assign different skills to one path")
            )
        elif not plan.project_path.is_dir():
            rows.append(StatusRow(plan, "project missing"))
        else:
            assert plan.source is not None
            state = strategy.check(plan.source, plan.target)
            rows.append(StatusRow(plan, state.value))
    return tuple(rows)


def doctor(config: Config, strategy: LinkStrategy) -> tuple[DoctorIssue, ...]:
    issues: list[DoctorIssue] = []
    registry = ProviderRegistry.from_overrides(config.provider_overrides)
    for project in config.projects.values():
        if not project.path.is_dir():
            issues.append(
                DoctorIssue("project-missing", project.path, f"project '{project.name}' does not exist")
            )
            continue
        directory_assignments: dict[str, dict[str, frozenset[str]]] = {}
        for provider_name in project.enabled_providers(registry.names):
            provider = registry[provider_name]
            provider_dir = provider.skill_dir(config.provider_overrides.get(provider_name))
            target_dir = provider_dir if provider_dir.is_absolute() else project.path / provider_dir
            directory_key = os.path.normcase(str(target_dir.resolve(strict=False)))
            directory_assignments.setdefault(directory_key, {})[provider_name] = frozenset(
                project.skills_for(provider_name)
            )
        for directory, assignments in directory_assignments.items():
            if len(assignments) > 1 and len(set(assignments.values())) > 1:
                provider_names = ", ".join(assignments)
                issues.append(
                    DoctorIssue(
                        "provider-overlap",
                        Path(directory),
                        f"{provider_names} share this directory but have different skill lists; "
                        "all linked skills may be discovered by each provider",
                        level="warning",
                    )
                )

    for skill in config.skills.values():
        if not skill.path.is_dir():
            issues.append(
                DoctorIssue("source-missing", skill.path, f"skill '{skill.name}' source is missing")
            )

    for plan in build_plan(config):
        if plan.has_source_conflict:
            issues.append(
                DoctorIssue(
                    "plan-conflict",
                    plan.target,
                    "providers sharing this target assign different source skills",
                )
            )
            continue
        if not plan.project_path.is_dir():
            continue
        assert plan.source is not None
        state = strategy.check(plan.source, plan.target)
        if state is LinkState.BROKEN:
            issues.append(DoctorIssue("broken-link", plan.target, "link target is missing"))
        elif state is LinkState.WRONG_TARGET:
            issues.append(
                DoctorIssue("wrong-target", plan.target, f"link should point to '{plan.source}'")
            )
        elif state is LinkState.CONFLICT:
            issues.append(
                DoctorIssue(
                    "path-conflict",
                    plan.target,
                    "ordinary file or directory exists; it was left untouched",
                )
            )
    return tuple(issues)
