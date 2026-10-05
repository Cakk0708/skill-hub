from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .errors import LinkSafetyError
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
class SyncResult:
    created: int
    already_present: int
    issues: tuple[DoctorIssue, ...]


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


def sync(config: Config, strategy: LinkStrategy) -> SyncResult:
    created = 0
    already_present = 0
    issues: list[DoctorIssue] = []
    for plan in build_plan(config):
        if plan.has_source_conflict:
            issues.append(
                DoctorIssue(
                    "plan-conflict",
                    plan.target,
                    f"multiple providers assign different skills to this shared target: "
                    f"{', '.join(str(path) for path in plan.sources)}",
                )
            )
            continue
        if not plan.project_path.is_dir():
            issues.append(
                DoctorIssue("project-missing", plan.project_path, "project directory does not exist")
            )
            continue
        assert plan.source is not None
        if not plan.source.is_dir():
            issues.append(
                DoctorIssue("source-missing", plan.source, "skill source directory does not exist")
            )
            continue
        before = strategy.check(plan.source, plan.target)
        try:
            strategy.create(plan.source, plan.target)
        except (OSError, LinkSafetyError) as exc:
            issues.append(DoctorIssue("link-error", plan.target, str(exc)))
            continue
        if before is LinkState.PRESENT:
            already_present += 1
        else:
            created += 1
    return SyncResult(created, already_present, tuple(issues))


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
