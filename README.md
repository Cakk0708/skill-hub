# skill-hub

`skill-hub` 是一个本地 Python CLI，用一个目录维护 Skill，并通过目录链接把它们分发到多个项目。

## 设计

- `skills/` 是 Skill 的唯一维护位置。每个 Skill 是一个目录，入口文件为 `SKILL.md`，可包含脚本、参考资料和其他资源。
- `skillhub.yaml` 记录 Skill 源路径、项目路径、Provider 目录，以及项目使用的公共和专属 Skill。
- 每个项目里的目标项是指向 Skill Hub 源目录的链接。编辑源 Skill 后，链接到它的项目会立即看到更新。
- Provider 通过集中注册表定义，内置 `codex`、`claude`、`antigravity`，配置也可增加自定义 Provider。
- `LinkStrategy` 将检查、创建、删除链接统一成 `check`、`create`、`remove` 操作。
- `sync` 只创建缺失的链接，不会覆盖普通文件、普通目录、错误链接或断开的链接。遇到这些情况会报告错误，原目标保留。

当前版本没有版本管理、数据库、Web、GUI 或云同步。

## 安装

需要 Python 3.12 或更新版本。

```bash
python3.12 -m venv .venv
```

macOS/Linux：

```bash
source .venv/bin/activate
python -m pip install -e .
```

Windows PowerShell：

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -e .
```

## 初始化

在希望存放配置和 Skill 的目录运行：

```bash
skill-hub init
```

命令会创建 `skillhub.yaml`、`skills/` 和一个可编辑的 `skills/example/SKILL.md`。初始化不会覆盖现有配置文件。

## 配置示例

```yaml
settings:
  link_mode: auto

providers:
  codex:
    skill_dir: .agents/skills
  claude:
    skill_dir: .claude/skills
  antigravity:
    skill_dir: .agents/skills
  cursor:
    skill_dir: .cursor/skills

skills:
  python-review:
    path: skills/python-review
  release-check:
    path: skills/release-check
  claude-writing:
    path: skills/claude-writing

projects:
  billing-api:
    path: ../billing-api
    skills:
      - python-review
      - release-check
    providers:
      codex:
        enabled: true
        skills: []
      claude:
        enabled: true
        skills:
          - claude-writing
      antigravity:
        enabled: false
      cursor:
        enabled: true
        skills: []
```

Paths for `skills.*.path` and `projects.*.path` are relative to the directory containing `skillhub.yaml`; `~` and environment variables are expanded. The CLI automatically loads a `.env` file beside the selected `skillhub.yaml`. Copy `.env.example` to `.env` and set the project paths for the current computer:

```dotenv
AI_MASSAGE_PROJECT=/path/to/xiaozhi-AI
MES_PROJECT=/path/to/MES
SZWPOWER_PROJECT=/path/to/szwpower
```

Keep `.env` local; it is excluded from version control. If a referenced variable is unset or empty, configuration loading reports an error. A Provider's relative `skill_dir` is relative to each project root. A built-in Provider may override its directory. A custom Provider must supply `skill_dir`.

The final list for a project and Provider is the ordered union of the project's `skills` and that Provider's `skills`. Duplicate names are kept once. If a project omits its `providers` mapping, all configured Providers are enabled. When it specifies the mapping, only entries with `enabled: true` (or the default) are enabled.

Codex and Antigravity currently share the `.agents/skills` project directory. If both are enabled, a skill assigned to only one of them still appears in that shared directory and may be discovered by both tools. `doctor` reports this visibility overlap when their assigned lists differ. Choose separate supported folders in configuration only when the corresponding tool is set up to read those folders.

## 平台链接行为

- macOS/Linux：创建目录 symbolic link。
- Windows：先尝试目录 symbolic link；失败后用 Windows `mklink /J` 创建 directory junction。
- 检查链接时会识别 symbolic link 和 junction。删除操作只允许移除指向预期源目录的链接，不会递归删除目录。
- Windows symbolic link 可能受开发者模式或系统权限影响；junction 作为目录链接 fallback 通常不需要 symbolic link 权限。

如果目标路径已有普通文件或目录，`sync` 和 `doctor` 会报告路径冲突。Skill Hub 不会清理旧链接或移除未配置的 Skill 链接；需要迁移或清理时，请先检查 `status`，再由使用者显式处理。

## 命令

```bash
skill-hub init
skill-hub skill list
skill-hub project list
skill-hub help
skill-hub help python-review
skill-hub status
skill-hub sync
skill-hub doctor
```

可通过 `--config path/to/skillhub.yaml` 指定配置文件。`init` 可使用 `--directory path/to/hub` 指定初始化目录。

- `skill list`：列出 Skill 源目录和可用状态。
- `project list`：列出项目、启用的 Provider 和最终 Skill 列表。
- `help`：列出配置中的 Skill 名称和简短说明，不展开指令正文；可传 Skill 名称只列出一个，例如 `skill-hub help python-review`。
- `status`：显示每条期望链接的目标、源和实际状态。
- `sync`：创建缺失的链接；有冲突或路径缺失时报告并返回非零退出码。
- `doctor`：检查项目目录、Skill 源、断链、错误目标、普通文件/目录冲突，以及共享 Provider 目录上的技能可见性重叠。

## 验证

```bash
python -m unittest discover -s tests -v
skill-hub --help
```

Provider 默认目录依据各工具的项目级 Skill 文档：

- [Codex：Where Codex loads local skills](https://developers.openai.com/codex/skills)
- [Claude Code：Choose where skills load](https://code.claude.com/docs/en/skills)
- [Google Antigravity：Agent skills](https://antigravity.google/docs/skills)
# skill-hub
