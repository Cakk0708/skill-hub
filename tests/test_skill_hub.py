from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from skill_hub.config import load_config
from skill_hub.errors import LinkSafetyError
from skill_hub.links import LinkState, SystemLinkStrategy
from skill_hub.models import Project, ProjectProvider
from skill_hub.operations import build_plan, doctor, status
from skill_hub.providers import ProviderRegistry


class ConfigTests(unittest.TestCase):
    def test_parses_configuration_and_resolves_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "skills" / "shared").mkdir(parents=True)
            (root / "skillhub.yaml").write_text(
                """settings:\n  link_mode: auto\nskills:\n  shared:\n    path: skills/shared\nprojects:\n  app:\n    path: ../app\n    skills: [shared]\n""",
                encoding="utf-8",
            )

            config = load_config(root / "skillhub.yaml")

            self.assertEqual(config.skills["shared"].path, (root / "skills" / "shared").resolve())
            self.assertEqual(config.projects["app"].path, (root.parent / "app").resolve())
            self.assertEqual(config.projects["app"].skills, ("shared",))

    def test_provider_defaults_and_configured_override(self) -> None:
        registry = ProviderRegistry.from_overrides({"claude": Path("custom/claude-skills")})

        self.assertEqual(registry["codex"].skill_dir(), Path(".agents/skills"))
        self.assertEqual(registry["claude"].skill_dir(), Path("custom/claude-skills"))
        self.assertEqual(registry["antigravity"].skill_dir(), Path(".agents/skills"))

    def test_provider_skill_dir_override_is_read_from_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "skillhub.yaml").write_text(
                """providers:\n  codex:\n    skill_dir: .custom/codex\nskills: {}\nprojects: {}\n""",
                encoding="utf-8",
            )
            config = load_config(root / "skillhub.yaml")
            registry = ProviderRegistry.from_overrides(config.provider_overrides)

            self.assertEqual(registry["codex"].skill_dir(), Path(".custom/codex"))


class ProjectTests(unittest.TestCase):
    def test_common_and_provider_skills_merge_without_duplicates(self) -> None:
        project = Project(
            name="api",
            path=Path("/tmp/api"),
            skills=("python", "review"),
            providers={"claude": ProjectProvider(skills=("review", "claude-only"))},
        )

        self.assertEqual(project.skills_for("claude"), ("python", "review", "claude-only"))
        self.assertEqual(project.skills_for("codex"), ("python", "review"))


class LinkTests(unittest.TestCase):
    def test_check_reports_missing_present_wrong_target_and_conflict(self) -> None:
        strategy = SystemLinkStrategy()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "hub" / "one"
            other = root / "hub" / "two"
            project = root / "project"
            target = project / ".agents" / "skills" / "one"
            source.mkdir(parents=True)
            other.mkdir(parents=True)
            project.mkdir()

            self.assertEqual(strategy.check(source, target), LinkState.MISSING)
            target.parent.mkdir(parents=True)
            target.symlink_to(source, target_is_directory=True)
            self.assertEqual(strategy.check(source, target), LinkState.PRESENT)
            self.assertEqual(strategy.check(other, target), LinkState.WRONG_TARGET)

            target.unlink()
            target.mkdir()
            self.assertEqual(strategy.check(source, target), LinkState.CONFLICT)

    def test_create_and_remove_symlink_when_supported(self) -> None:
        strategy = SystemLinkStrategy()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "skills" / "one"
            target = root / "project" / ".agents" / "skills" / "one"
            source.mkdir(parents=True)
            try:
                strategy.create(source, target)
            except OSError as exc:
                self.skipTest(f"directory symlinks are unavailable: {exc}")

            self.assertEqual(strategy.check(source, target), LinkState.PRESENT)
            self.assertTrue(strategy.remove(target, source))
            self.assertEqual(strategy.check(source, target), LinkState.MISSING)

    def test_create_refuses_to_replace_ordinary_directory(self) -> None:
        strategy = SystemLinkStrategy()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "skills" / "one"
            target = root / "project" / ".agents" / "skills" / "one"
            source.mkdir(parents=True)
            target.mkdir(parents=True)
            sentinel = target / "keep.txt"
            sentinel.write_text("keep", encoding="utf-8")

            with self.assertRaises(LinkSafetyError):
                strategy.create(source, target)

            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_doctor_warns_when_providers_share_a_directory_with_different_skills(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "skills" / "shared").mkdir(parents=True)
            (root / "skills" / "codex-only").mkdir(parents=True)
            project_path = root / "project"
            project_path.mkdir()
            (root / "skillhub.yaml").write_text(
                """skills:\n  shared:\n    path: skills/shared\n  codex-only:\n    path: skills/codex-only\nprojects:\n  app:\n    path: project\n    skills: [shared]\n    providers:\n      codex:\n        enabled: true\n        skills: [codex-only]\n      antigravity:\n        enabled: true\n""",
                encoding="utf-8",
            )

            issues = doctor(load_config(root / "skillhub.yaml"), SystemLinkStrategy())

            self.assertTrue(any(issue.code == "provider-overlap" and issue.level == "warning" for issue in issues))

    def test_plan_keeps_link_destination_after_link_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "skills" / "shared"
            project_path = root / "project"
            source.mkdir(parents=True)
            project_path.mkdir()
            config_path = root / "skillhub.yaml"
            config_path.write_text(
                """skills:\n  shared:\n    path: skills/shared\nprojects:\n  app:\n    path: project\n    skills: [shared]\n    providers:\n      codex:\n        enabled: true\n""",
                encoding="utf-8",
            )
            config = load_config(config_path)
            strategy = SystemLinkStrategy()
            first_plan = build_plan(config)[0]
            strategy.create(source, first_plan.target)

            second_plan = build_plan(config)[0]

            self.assertEqual(second_plan.target, first_plan.target)
            self.assertNotEqual(second_plan.target, source)
            self.assertEqual(status(config, strategy)[0].state, "present")


if __name__ == "__main__":
    unittest.main()
