from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from .errors import ConfigError
from .models import Config, Project, ProjectProvider, Skill
from .providers import ProviderRegistry, parse_provider_overrides

_ENVIRONMENT_VARIABLE = re.compile(
    r"\$(?:\{(?P<braced>[A-Za-z_][A-Za-z0-9_]*)\}|(?P<plain>[A-Za-z_][A-Za-z0-9_]*))"
)


def _mapping(value: object, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"'{label}' must be a mapping")
    return value


def _path_from(base: Path, value: object, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"'{label}' must be a non-empty path string")
    for match in _ENVIRONMENT_VARIABLE.finditer(value):
        variable = match.group("braced") or match.group("plain")
        if not os.environ.get(variable):
            raise ConfigError(
                f"environment variable '{variable}' used in '{label}' is not set; "
                "define it in the .env file next to skillhub.yaml"
            )
    expanded = Path(os.path.expandvars(value)).expanduser()
    if not expanded.is_absolute():
        expanded = base / expanded
    return expanded.resolve(strict=False)


def _names(value: object, label: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ConfigError(f"'{label}' must be a list of non-empty strings")
    return tuple(dict.fromkeys(value))


def _validate_skill_name(name: object, label: str) -> str:
    if (
        not isinstance(name, str)
        or not name.strip()
        or name in {".", ".."}
        or "/" in name
        or "\\" in name
    ):
        raise ConfigError(f"{label} must be a single non-empty directory name")
    return name


def load_config(file_path: Path) -> Config:
    file_path = file_path.expanduser().resolve(strict=False)
    if not file_path.is_file():
        raise ConfigError(f"configuration file not found: {file_path}")
    load_dotenv(dotenv_path=file_path.parent / ".env")
    try:
        raw = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"could not read configuration: {exc}") from exc
    document = _mapping(raw, "configuration")

    settings = _mapping(document.get("settings"), "settings")
    link_mode = settings.get("link_mode", "auto")
    if link_mode != "auto":
        raise ConfigError("settings.link_mode currently supports only 'auto'")

    provider_overrides = parse_provider_overrides(document.get("providers"))
    registry = ProviderRegistry.from_overrides(provider_overrides)

    skills: dict[str, Skill] = {}
    for raw_name, raw_settings in _mapping(document.get("skills"), "skills").items():
        name = _validate_skill_name(raw_name, "skill name")
        values = _mapping(raw_settings, f"skills.{name}")
        skills[name] = Skill(
            name=name,
            path=_path_from(file_path.parent, values.get("path"), f"skills.{name}.path"),
        )

    projects: dict[str, Project] = {}
    for raw_name, raw_settings in _mapping(document.get("projects"), "projects").items():
        name = _validate_skill_name(raw_name, "project name")
        values = _mapping(raw_settings, f"projects.{name}")
        project_providers: dict[str, ProjectProvider] = {}
        for provider_name, provider_settings in _mapping(
            values.get("providers"), f"projects.{name}.providers"
        ).items():
            if provider_name not in registry:
                raise ConfigError(
                    f"project '{name}' references unknown provider '{provider_name}'"
                )
            provider_values = _mapping(
                provider_settings, f"projects.{name}.providers.{provider_name}"
            )
            enabled = provider_values.get("enabled", True)
            if not isinstance(enabled, bool):
                raise ConfigError(
                    f"projects.{name}.providers.{provider_name}.enabled must be true or false"
                )
            project_providers[provider_name] = ProjectProvider(
                enabled=enabled,
                skills=_names(
                    provider_values.get("skills"),
                    f"projects.{name}.providers.{provider_name}.skills",
                ),
            )

        project = Project(
            name=name,
            path=_path_from(file_path.parent, values.get("path"), f"projects.{name}.path"),
            skills=_names(values.get("skills"), f"projects.{name}.skills"),
            providers=project_providers,
        )
        for skill_name in (*project.skills, *(s for p in project_providers.values() for s in p.skills)):
            if skill_name not in skills:
                raise ConfigError(
                    f"project '{name}' references unknown skill '{skill_name}'"
                )
        projects[name] = project

    return Config(
        file_path=file_path,
        settings=settings,
        provider_overrides=provider_overrides,
        skills=skills,
        projects=projects,
    )
