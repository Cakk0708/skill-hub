from __future__ import annotations

from pathlib import Path

import typer
import yaml

from .config import load_config
from .errors import ConfigError, SkillHubError
from .links import SystemLinkStrategy
from .operations import doctor as run_doctor
from .operations import status as run_status
from .operations import sync as run_sync
from .providers import ProviderRegistry

app = typer.Typer(help="Manage shared AI coding skills across projects.", no_args_is_help=True)
skill_app = typer.Typer(help="Inspect configured skills.", no_args_is_help=True)
project_app = typer.Typer(help="Inspect configured projects.", no_args_is_help=True)
app.add_typer(skill_app, name="skill")
app.add_typer(project_app, name="project")


SAMPLE_CONFIG = """# Paths for skills and projects are relative to this file unless absolute.
settings:
  link_mode: auto

providers:
  codex:
    skill_dir: .agents/skills
  claude:
    skill_dir: .claude/skills
  antigravity:
    skill_dir: .agents/skills

skills:
  example:
    path: skills/example

projects:
  example-project:
    path: ../example-project
    skills:
      - example
    providers:
      codex:
        enabled: true
      claude:
        enabled: true
      antigravity:
        enabled: false
"""

SAMPLE_SKILL = """---
name: example
description: A small example skill managed by skill-hub.
---

# Example Skill

Replace this text with reusable instructions for your coding agent.
"""


def _config(config_path: Path):
    try:
        return load_config(config_path)
    except (ConfigError, OSError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc


def _skill_description(instruction_path: Path) -> str | None:
    try:
        with instruction_path.open(encoding="utf-8") as instruction_file:
            if instruction_file.readline().strip() != "---":
                return None
            front_matter: list[str] = []
            for line in instruction_file:
                if line.strip() == "---":
                    break
                front_matter.append(line)
        metadata = yaml.safe_load("".join(front_matter))
    except (OSError, UnicodeError, yaml.YAMLError):
        return None

    if not isinstance(metadata, dict):
        return None
    description = metadata.get("description")
    if not isinstance(description, str):
        return None
    return " ".join(description.split()) or None


@app.command()
def init(
    directory: Path = typer.Option(
        Path.cwd(), "--directory", "-d", help="Folder where skillhub.yaml and skills/ are created."
    ),
) -> None:
    """Create a readable starter configuration and example skill."""
    directory = directory.expanduser().resolve()
    config_path = directory / "skillhub.yaml"
    skill_dir = directory / "skills" / "example"
    skill_file = skill_dir / "SKILL.md"
    if config_path.exists():
        typer.echo(f"Error: refusing to overwrite {config_path}", err=True)
        raise typer.Exit(code=2)
    if skill_file.exists():
        typer.echo(f"Error: refusing to overwrite {skill_file}", err=True)
        raise typer.Exit(code=2)
    try:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "skills").mkdir(parents=True, exist_ok=True)
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(SAMPLE_SKILL, encoding="utf-8")
        config_path.write_text(SAMPLE_CONFIG, encoding="utf-8")
    except OSError as exc:
        typer.echo(f"Error: could not initialize project: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"Created {config_path}")
    typer.echo(f"Created {skill_file}")


@skill_app.command("list")
def skill_list(
    config_path: Path = typer.Option(Path("skillhub.yaml"), "--config", "-c"),
) -> None:
    """List configured skills and their source directories."""
    config = _config(config_path)
    if not config.skills:
        typer.echo("No skills configured.")
        return
    for skill in config.skills.values():
        source_state = "available" if skill.path.is_dir() else "missing"
        typer.echo(f"{skill.name}\t{source_state}\t{skill.path}")


@project_app.command("list")
def project_list(
    config_path: Path = typer.Option(Path("skillhub.yaml"), "--config", "-c"),
) -> None:
    """List projects, providers, and the skills assigned to them."""
    config = _config(config_path)
    registry = ProviderRegistry.from_overrides(config.provider_overrides)
    if not config.projects:
        typer.echo("No projects configured.")
        return
    for project in config.projects.values():
        providers = project.enabled_providers(registry.names)
        typer.echo(f"{project.name}\t{project.path}")
        for provider in providers:
            skills = ", ".join(project.skills_for(provider)) or "(none)"
            typer.echo(f"  {provider}: {skills}")


@app.command("help")
def skill_help(
    skill_name: str | None = typer.Argument(
        None, help="Optional skill name. Omit it to list every configured skill."
    ),
    config_path: Path = typer.Option(Path("skillhub.yaml"), "--config", "-c"),
) -> None:
    """List configured skills and their short descriptions."""
    config = _config(config_path)
    if skill_name is None:
        skills = tuple(config.skills.values())
    else:
        skill = config.skills.get(skill_name)
        if skill is None:
            available = ", ".join(config.skills) or "none"
            typer.echo(
                f"Error: unknown skill '{skill_name}'. Available skills: {available}",
                err=True,
            )
            raise typer.Exit(code=2)
        skills = (skill,)

    if not skills:
        typer.echo("No skills configured.")
        return

    for skill in skills:
        description = _skill_description(skill.path / "SKILL.md")
        if description:
            typer.echo(f"{skill.name}\t{description}")
        else:
            typer.echo(skill.name)


@app.command()
def sync(
    config_path: Path = typer.Option(Path("skillhub.yaml"), "--config", "-c"),
) -> None:
    """Create missing links for configured project skills."""
    result = run_sync(_config(config_path), SystemLinkStrategy())
    typer.echo(f"Created {result.created} link(s); {result.already_present} already current.")
    for issue in result.issues:
        typer.echo(f"ERROR [{issue.code}] {issue.location}: {issue.message}", err=True)
    if result.issues:
        raise typer.Exit(code=1)


@app.command()
def status(
    config_path: Path = typer.Option(Path("skillhub.yaml"), "--config", "-c"),
) -> None:
    """Show expected links and their current state."""
    rows = run_status(_config(config_path), SystemLinkStrategy())
    if not rows:
        typer.echo("No links are configured.")
        return
    for row in rows:
        providers = ",".join(row.plan.providers)
        detail = f" — {row.detail}" if row.detail else ""
        source = str(row.plan.source) if row.plan.source else "multiple sources"
        typer.echo(
            f"{row.state.upper()}\t{row.plan.target}\t<- {source}"
            f"\t[{row.plan.project_name}/{providers}]{detail}"
        )


@app.command()
def doctor(
    config_path: Path = typer.Option(Path("skillhub.yaml"), "--config", "-c"),
) -> None:
    """Check configured sources, projects, and destination links."""
    issues = run_doctor(_config(config_path), SystemLinkStrategy())
    if not issues:
        typer.echo("Doctor found no issues.")
        return
    for issue in issues:
        typer.echo(f"[{issue.level}] {issue.code}: {issue.location}: {issue.message}")
    errors = sum(issue.level == "error" for issue in issues)
    warnings = len(issues) - errors
    typer.echo(f"Found {errors} error(s) and {warnings} warning(s).", err=errors > 0)
    if errors:
        raise typer.Exit(code=1)
