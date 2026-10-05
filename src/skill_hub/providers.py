from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .errors import ConfigError
from .models import Provider


class ProviderRegistry:
    """Provider definitions live in one registry and can be extended by config."""

    BUILT_INS: Mapping[str, Path] = {
        "codex": Path(".agents/skills"),
        "claude": Path(".claude/skills"),
        "antigravity": Path(".agents/skills"),
    }

    def __init__(self, providers: Mapping[str, Provider]) -> None:
        self._providers = dict(providers)

    @classmethod
    def from_overrides(cls, overrides: Mapping[str, Path]) -> ProviderRegistry:
        providers = {
            name: Provider(name=name, default_skill_dir=skill_dir)
            for name, skill_dir in cls.BUILT_INS.items()
        }
        for name, skill_dir in overrides.items():
            providers[name] = Provider(name=name, default_skill_dir=skill_dir)
        return cls(providers)

    def __contains__(self, name: str) -> bool:
        return name in self._providers

    def __getitem__(self, name: str) -> Provider:
        return self._providers[name]

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._providers)

    @classmethod
    def built_in_defaults(cls) -> ProviderRegistry:
        return cls.from_overrides({})


def parse_provider_overrides(value: object) -> dict[str, Path]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError("'providers' must be a mapping of provider names to settings")

    known = set(ProviderRegistry.BUILT_INS)
    overrides: dict[str, Path] = {}
    for name, settings in value.items():
        if not isinstance(name, str) or not name.strip():
            raise ConfigError("provider names must be non-empty strings")
        if not isinstance(settings, dict):
            raise ConfigError(f"provider '{name}' settings must be a mapping")
        skill_dir = settings.get("skill_dir")
        if skill_dir is None:
            if name not in known:
                raise ConfigError(
                    f"custom provider '{name}' must define a 'skill_dir'"
                )
            continue
        if not isinstance(skill_dir, str) or not skill_dir.strip():
            raise ConfigError(f"provider '{name}' skill_dir must be a non-empty string")
        overrides[name] = Path(skill_dir).expanduser()
    return overrides

