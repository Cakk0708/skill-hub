from __future__ import annotations

import os
import subprocess
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

from .errors import LinkSafetyError


class LinkState(str, Enum):
    MISSING = "missing"
    PRESENT = "present"
    BROKEN = "broken"
    WRONG_TARGET = "wrong target"
    CONFLICT = "conflict"


def _is_junction(path: Path) -> bool:
    checker = getattr(os.path, "isjunction", None)
    return bool(checker(path)) if checker else False


def _is_directory_link(path: Path) -> bool:
    return path.is_symlink() or _is_junction(path)


class LinkStrategy(ABC):
    """Platform-independent directory link operations used by business logic."""

    @abstractmethod
    def create(self, source: Path, target: Path) -> None:
        """Create a directory link, refusing to replace any existing entry."""

    @abstractmethod
    def remove(self, target: Path, expected_source: Path) -> bool:
        """Remove only a link that points to expected_source; return if removed."""

    @abstractmethod
    def check(self, source: Path, target: Path) -> LinkState:
        """Check the state of the expected directory link."""


class SystemLinkStrategy(LinkStrategy):
    """Use symlinks everywhere, with a Windows junction fallback."""

    def check(self, source: Path, target: Path) -> LinkState:
        if not os.path.lexists(target):
            return LinkState.MISSING
        if not _is_directory_link(target):
            return LinkState.CONFLICT

        expected = source.resolve(strict=False)
        actual = target.resolve(strict=False)
        if actual != expected:
            return LinkState.WRONG_TARGET
        if not target.exists():
            return LinkState.BROKEN
        return LinkState.PRESENT

    def create(self, source: Path, target: Path) -> None:
        state = self.check(source, target)
        if state is LinkState.PRESENT:
            return
        if state is not LinkState.MISSING:
            raise LinkSafetyError(
                f"refusing to create link at '{target}': destination is {state.value}"
            )
        if not source.is_dir():
            raise FileNotFoundError(f"skill source directory not found: {source}")

        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            target.symlink_to(source.resolve(), target_is_directory=True)
        except OSError as symlink_error:
            if os.name != "nt":
                raise
            self._create_junction(source.resolve(), target, symlink_error)

    def remove(self, target: Path, expected_source: Path) -> bool:
        state = self.check(expected_source, target)
        if state is LinkState.MISSING:
            return False
        if state is not LinkState.PRESENT and state is not LinkState.BROKEN:
            raise LinkSafetyError(
                f"refusing to remove '{target}': destination is {state.value}"
            )
        if target.resolve(strict=False) != expected_source.resolve(strict=False):
            raise LinkSafetyError(
                f"refusing to remove '{target}': it does not point to '{expected_source}'"
            )

        if _is_junction(target):
            target.rmdir()
        else:
            target.unlink()
        return True

    @staticmethod
    def _create_junction(source: Path, target: Path, symlink_error: OSError) -> None:
        try:
            result = subprocess.run(
                ["cmd.exe", "/c", "mklink", "/J", str(target), str(source)],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as junction_error:
            raise OSError(
                f"could not create a directory symlink or junction at '{target}'"
            ) from junction_error
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip()
            raise OSError(
                f"directory symlink failed ({symlink_error}); junction failed: {detail}"
            )

