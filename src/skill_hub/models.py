from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class Skill:
    name: str
    path: Path


@dataclass(frozen=True)
class Provider:
    name: str
    default_skill_dir: Path

    def skill_dir(self, override: str | Path | None = None) -> Path:
        """Return the configured destination directory or this provider's default."""
        return Path(override) if override is not None else self.default_skill_dir


@dataclass(frozen=True)
class ProjectProvider:
    enabled: bool = True
    skills: tuple[str, ...] = ()


@dataclass(frozen=True)
class Project:
    name: str
    path: Path
    skills: tuple[str, ...] = ()
    providers: Mapping[str, ProjectProvider] = field(default_factory=dict)

    def skills_for(self, provider_name: str) -> tuple[str, ...]:
        """Merge shared and provider-specific skills while preserving order."""
        specific = self.providers.get(provider_name, ProjectProvider()).skills
        return tuple(dict.fromkeys((*self.skills, *specific)))

    def enabled_providers(self, available: tuple[str, ...]) -> tuple[str, ...]:
        if not self.providers:
            return available
        return tuple(
            name
            for name, configuration in self.providers.items()
            if configuration.enabled
        )


@dataclass(frozen=True)
class Config:
    file_path: Path
    settings: Mapping[str, object]
    provider_overrides: Mapping[str, Path]
    skills: Mapping[str, Skill]
    projects: Mapping[str, Project]

    @property
    def root(self) -> Path:
        return self.file_path.parent

