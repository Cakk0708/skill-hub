from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from apps.config import load_config
from apps.errors import ConfigError, LinkSafetyError
from apps.links import CopyStrategy, LinkState, SystemLinkStrategy
from apps.models import Project, ProjectProvider
from apps.operations import build_plan, doctor, status, sync_rule_indexes
from apps.providers import ProviderRegistry
from main import main as run_main


class ConfigTests(unittest.TestCase):
    def test_discovers_all_immediate_skill_directories_on_each_load(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "source" / "skills" / "zeta").mkdir(parents=True)
            (root / "source" / "skills" / "alpha").mkdir(parents=True)
            (root / "source" / "skills" / "README.md").write_text(
                "not a skill", encoding="utf-8"
            )
            config_path = root / "skillhub.yaml"
            config_path.write_text("projects: {}\n", encoding="utf-8")

            first_config = load_config(config_path)
            (root / "source" / "skills" / "new-skill").mkdir()
            second_config = load_config(config_path)

            self.assertEqual(tuple(first_config.skills), ("alpha", "zeta"))
            self.assertEqual(tuple(second_config.skills), ("alpha", "new-skill", "zeta"))
            self.assertEqual(
                second_config.skills["new-skill"].path,
                (root / "source" / "skills" / "new-skill").resolve(),
            )

    def test_parses_configuration_and_resolves_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "source" / "skills" / "shared").mkdir(parents=True)
            (root / "skillhub.yaml").write_text(
                """settings:\n  link_mode: auto\nprojects:\n  app:\n    path: ../app\n    skills: [shared]\n""",
                encoding="utf-8",
            )

            config = load_config(root / "skillhub.yaml")

            self.assertEqual(
                config.skills["shared"].path,
                (root / "source" / "skills" / "shared").resolve(),
            )
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
                """providers:\n  codex:\n    skill_dir: .custom/codex\nprojects: {}\n""",
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
            source = root / "source" / "skills" / "one"
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
            source = root / "source" / "skills" / "one"
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
            (root / "source" / "skills" / "shared").mkdir(parents=True)
            (root / "source" / "skills" / "codex-only").mkdir(parents=True)
            project_path = root / "project"
            project_path.mkdir()
            (root / "skillhub.yaml").write_text(
                """projects:\n  app:\n    path: project\n    skills: [shared]\n    providers:\n      codex:\n        enabled: true\n        skills: [codex-only]\n      antigravity:\n        enabled: true\n""",
                encoding="utf-8",
            )

            issues = doctor(load_config(root / "skillhub.yaml"), SystemLinkStrategy())

            self.assertTrue(any(issue.code == "provider-overlap" and issue.level == "warning" for issue in issues))

    def test_plan_keeps_link_destination_after_link_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source" / "skills" / "shared"
            project_path = root / "project"
            source.mkdir(parents=True)
            project_path.mkdir()
            config_path = root / "skillhub.yaml"
            config_path.write_text(
                """projects:\n  app:\n    path: project\n    skills: [shared]\n    providers:\n      codex:\n        enabled: true\n""",
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


class CopyModeTests(unittest.TestCase):
    def test_parses_and_validates_provider_and_project_sync_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "source" / "skills" / "demo").mkdir(parents=True)
            (root / "project").mkdir()
            (root / "skillhub.yaml").write_text(
                """providers:
  codex:
    skill_dir: .codex/skills
    sync_mode: symlink
  antigravity:
    skill_dir: .agents/skills
    sync_mode: copy
projects:
  app:
    path: project
    skills: [demo]
    providers:
      codex:
        enabled: true
        sync_mode: copy
      antigravity:
        enabled: true
""",
                encoding="utf-8",
            )
            config = load_config(root / "skillhub.yaml")
            self.assertEqual(config.provider_sync_modes["antigravity"], "copy")
            plans = build_plan(config)
            self.assertTrue(all(plan.sync_mode == "copy" for plan in plans))

            (root / "invalid-provider.yaml").write_text(
                """providers:
  antigravity:
    sync_mode: hardlink
projects: {}
""",
                encoding="utf-8",
            )
            with self.assertRaises(ConfigError):
                load_config(root / "invalid-provider.yaml")

            (root / "invalid-project.yaml").write_text(
                """projects:
  app:
    path: project
    skills: [demo]
    providers:
      antigravity:
        enabled: true
        sync_mode: directory
""",
                encoding="utf-8",
            )
            with self.assertRaises(ConfigError):
                load_config(root / "invalid-project.yaml")

    def test_copy_strategy_replaces_old_symlink_and_stale_files_on_each_sync(self) -> None:
        strategy = CopyStrategy()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source" / "skills" / "demo"
            (source / "references").mkdir(parents=True)
            (source / "SKILL.md").write_text("# v1\n", encoding="utf-8")
            (source / "references" / "guide.md").write_text("guide v1\n", encoding="utf-8")
            (source / ".DS_Store").write_text("junk", encoding="utf-8")
            (source / "references" / "._guide.md").write_text("junk", encoding="utf-8")

            target = root / "project" / ".agents" / "skills" / "demo"
            target.parent.mkdir(parents=True)
            # Pre-existing symlink from old ln scheme
            target.symlink_to(source.resolve(), target_is_directory=True)
            self.assertEqual(strategy.check(source, target), LinkState.WRONG_TARGET)

            # Sync replaces symlink with real directory and real files
            strategy.create(source, target)
            self.assertTrue(target.is_dir())
            self.assertFalse(target.is_symlink())
            self.assertTrue((target / "SKILL.md").is_file())
            self.assertFalse((target / "SKILL.md").is_symlink())
            self.assertEqual((target / "SKILL.md").read_text(encoding="utf-8"), "# v1\n")
            self.assertFalse((target / "references").is_symlink())
            self.assertFalse((target / "references" / "guide.md").is_symlink())
            self.assertFalse((target / ".DS_Store").exists())
            self.assertFalse((target / "references" / "._guide.md").exists())
            self.assertEqual(strategy.check(source, target), LinkState.PRESENT)

            # Modify source and place a stale file in target; next sync deletes old & copies fresh
            (source / "SKILL.md").write_text("# v2\n", encoding="utf-8")
            (target / "stale.md").write_text("stale\n", encoding="utf-8")
            self.assertEqual(strategy.check(source, target), LinkState.WRONG_TARGET)

            strategy.create(source, target)
            self.assertEqual((target / "SKILL.md").read_text(encoding="utf-8"), "# v2\n")
            self.assertFalse((target / "stale.md").exists())
            self.assertEqual(strategy.check(source, target), LinkState.PRESENT)

            # Remove cleans up copied directory
            self.assertTrue(strategy.remove(target, source))
            self.assertFalse(target.exists())
            self.assertEqual(strategy.check(source, target), LinkState.MISSING)

    def test_main_and_rule_index_copy_mode_replaces_symlinks_with_real_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = root / "source" / "skills" / "demo"
            (skill / "references").mkdir(parents=True)
            (skill / "SKILL.md").write_text("# demo v1\n", encoding="utf-8")
            (skill / "references" / "ref.md").write_text("# ref\n", encoding="utf-8")

            rule_index = root / "source" / "rule-index" / "python-style.md"
            rule_index.parent.mkdir(parents=True)
            rule_index.write_text(
                "---\napplicable_path: '*.py'\ndescription: Python style\n---\n\n# v1\n",
                encoding="utf-8",
            )

            project = root / "project"
            project.mkdir()

            # Pre-existing symlinks for antigravity skill and rule-index
            agy_skill = project / ".agents" / "skills" / "demo"
            agy_skill.parent.mkdir(parents=True)
            agy_skill.symlink_to(skill.resolve(), target_is_directory=True)

            agy_rule = project / ".agents" / "rules" / "python-style.md"
            agy_rule.parent.mkdir(parents=True)
            agy_rule.symlink_to(rule_index.resolve(), target_is_directory=False)

            config_path = root / "skillhub.yaml"
            config_path.write_text(
                """providers:
  codex:
    skill_dir: .codex/skills
    rule_index_dir: .codex/rules
    rule_dir: AGENTS.md
  antigravity:
    skill_dir: .agents/skills
    sync_mode: copy
    rule_index_dir: .agents/rules
    rule_dir: GEMINI.md
projects:
  app:
    path: project
    skills: [demo]
    rule_index: [python-style]
    providers:
      codex:
        enabled: true
      antigravity:
        enabled: true
""",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = run_main(["--config", str(config_path)])

            self.assertEqual(code, 0, msg=stderr.getvalue())
            self.assertIn("Copied 1 skill(s).", stdout.getvalue())

            # Codex uses symlinks for both skills and rule-index
            self.assertTrue((project / ".codex" / "skills" / "demo").is_symlink())
            self.assertTrue((project / ".codex" / "rules" / "python-style.md").is_symlink())

            # Antigravity uses real copied directories and real copied files
            self.assertTrue(agy_skill.is_dir())
            self.assertFalse(agy_skill.is_symlink())
            self.assertFalse((agy_skill / "SKILL.md").is_symlink())
            self.assertEqual((agy_skill / "SKILL.md").read_text(encoding="utf-8"), "# demo v1\n")
            self.assertFalse((agy_skill / "references").is_symlink())
            self.assertFalse((agy_skill / "references" / "ref.md").is_symlink())

            self.assertTrue(agy_rule.is_file())
            self.assertFalse(agy_rule.is_symlink())
            self.assertIn("# v1", agy_rule.read_text(encoding="utf-8"))

            # Update source skill and rule-index, add stale file in agy_skill, re-sync
            (skill / "SKILL.md").write_text("# demo v2\n", encoding="utf-8")
            (agy_skill / "old-extra.md").write_text("stale\n", encoding="utf-8")
            rule_index.write_text(
                "---\napplicable_path: '*.py'\ndescription: Python style\n---\n\n# v2\n",
                encoding="utf-8",
            )

            stdout2 = io.StringIO()
            stderr2 = io.StringIO()
            with redirect_stdout(stdout2), redirect_stderr(stderr2):
                code2 = run_main(["--config", str(config_path)])
            self.assertEqual(code2, 0, msg=stderr2.getvalue())
            self.assertEqual((agy_skill / "SKILL.md").read_text(encoding="utf-8"), "# demo v2\n")
            self.assertFalse((agy_skill / "old-extra.md").exists())
            self.assertIn("# v2", agy_rule.read_text(encoding="utf-8"))

            config = load_config(config_path)
            self.assertEqual(doctor(config, SystemLinkStrategy()), ())
            self.assertTrue(all(row.state == "present" for row in status(config, SystemLinkStrategy())))

    def test_shared_directory_with_different_sync_modes_reports_plan_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "source" / "skills" / "demo").mkdir(parents=True)
            (root / "project").mkdir()
            config_path = root / "skillhub.yaml"
            config_path.write_text(
                """providers:
  codex:
    skill_dir: .agents/skills
    sync_mode: symlink
  antigravity:
    skill_dir: .agents/skills
    sync_mode: copy
projects:
  app:
    path: project
    skills: [demo]
    providers:
      codex:
        enabled: true
      antigravity:
        enabled: true
""",
                encoding="utf-8",
            )
            config = load_config(config_path)
            self.assertTrue(build_plan(config)[0].has_sync_mode_conflict)
            self.assertEqual(status(config, SystemLinkStrategy())[0].state, "plan conflict")
            self.assertTrue(any(i.code == "plan-conflict" for i in doctor(config, SystemLinkStrategy())))

            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = run_main(["--config", str(config_path)])
            self.assertEqual(code, 1)
            self.assertIn("plan-conflict", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
