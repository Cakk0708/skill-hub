class SkillHubError(Exception):
    """Base error for expected Skill Hub failures."""


class ConfigError(SkillHubError):
    """The configuration file is invalid or incomplete."""


class LinkSafetyError(SkillHubError):
    """A link operation would replace an unrecognized filesystem entry."""

