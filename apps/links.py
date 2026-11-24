from __future__ import annotations

import os
import shutil
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


_IGNORED_ENTRY_NAMES = frozenset({".DS_Store", "Thumbs.db", "desktop.ini"})


def _is_ignored_entry(name: str) -> bool:
    return name in _IGNORED_ENTRY_NAMES or name.startswith("._")


def _ignore_os_junk(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if _is_ignored_entry(name)}


def _is_junction(path: Path) -> bool:
    checker = getattr(os.path, "isjunction", None)
    return bool(checker(path)) if checker else False


def _is_directory_link(path: Path) -> bool:
    return path.is_symlink() or _is_junction(path)


def _snapshot_tree(root: Path) -> tuple[set[Path], dict[Path, Path]] | None:
    """Collect relative dirs and regular files under root; return None if any entry is a link."""
    rel_dirs: set[Path] = set()
    rel_files: dict[Path, Path] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dir_path = Path(dirpath)
        rel_root = dir_path.relative_to(root)
        kept_dirs: list[str] = []
        for dirname in sorted(dirnames):
            if _is_ignored_entry(dirname):
                continue
            subdir = dir_path / dirname
            if _is_directory_link(subdir):
                return None
            rel_dirs.add(rel_root / dirname if rel_root != Path(".") else Path(dirname))
            kept_dirs.append(dirname)
        dirnames[:] = kept_dirs
        for filename in sorted(filenames):
            if _is_ignored_entry(filename):
                continue
            file_path = dir_path / filename
            if file_path.is_symlink():
                return None
            rel_file = rel_root / filename if rel_root != Path(".") else Path(filename)
            rel_files[rel_file] = file_path
    return rel_dirs, rel_files


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


class CopyStrategy(LinkStrategy):
    """Replace target with a fresh real-file copy of source on every sync."""

    def check(self, source: Path, target: Path) -> LinkState:
        if not os.path.lexists(target):
            return LinkState.MISSING
        if _is_directory_link(target):
            return LinkState.WRONG_TARGET
        if not target.is_dir():
            return LinkState.CONFLICT
        if not source.is_dir():
            return LinkState.BROKEN

        target_snapshot = _snapshot_tree(target)
        if target_snapshot is None:
            return LinkState.WRONG_TARGET
        target_dirs, target_files = target_snapshot

        source_dirs: set[Path] = set()
        source_files: dict[Path, Path] = {}
        for dirpath, dirnames, filenames in os.walk(source):
            dirnames[:] = sorted(name for name in dirnames if not _is_ignored_entry(name))
            dir_path = Path(dirpath)
            rel_root = dir_path.relative_to(source)
            if rel_root != Path("."):
                source_dirs.add(rel_root)
            for filename in sorted(filenames):
                if _is_ignored_entry(filename):
                    continue
                rel_file = rel_root / filename if rel_root != Path(".") else Path(filename)
                source_files[rel_file] = dir_path / filename

        if target_dirs != source_dirs or set(target_files) != set(source_files):
            return LinkState.WRONG_TARGET

        for rel_file, source_file in source_files.items():
            try:
                if target_files[rel_file].read_bytes() != source_file.read_bytes():
                    return LinkState.WRONG_TARGET
            except OSError:
                return LinkState.WRONG_TARGET

        return LinkState.PRESENT

    def create(self, source: Path, target: Path) -> None:
        if not source.is_dir():
            raise FileNotFoundError(f"skill source directory not found: {source}")

        if os.path.lexists(target):
            if _is_junction(target):
                target.rmdir()
            elif target.is_symlink():
                target.unlink()
            elif target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target, ignore=_ignore_os_junk, symlinks=False)

    def remove(self, target: Path, expected_source: Path) -> bool:
        del expected_source
        if not os.path.lexists(target):
            return False
        if _is_junction(target):
            target.rmdir()
        elif target.is_symlink():
            target.unlink()
        elif target.is_dir():
            shutil.rmtree(target)
        else:
            raise LinkSafetyError(
                f"refusing to remove '{target}': destination is not a directory or link"
            )
        return True

