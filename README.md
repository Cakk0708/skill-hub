Skill Hub 是一个本地 Python 工具，通过 `run.sh` 将统一维护的 Skill 和规则同步到多个项目。

## 设计

- `source/skills/` 是 Skill 的唯一维护位置。每个 Skill 是一个目录，入口文件为 `SKILL.md`，可包含脚本、参考资料和其他资源。
- `source/rules/` 存放规则文档。项目在 `skillhub.yaml` 中选择规则后，`main.py` 会将对应的二级标题块同步到启用 Provider 的规则文档。
- `source/rule-index/` 存放带 YAML 属性头的规则索引文档。项目可用 `rule_index` 选择索引；同步会将原文链接到 Provider 配置的目录，并在规则文档中维护路径索引表。
- `skillhub.yaml` 自动发现 `source/skills/` 下的一级 Skill 目录，并记录项目路径、Provider 目录，以及项目使用的公共和专属 Skill。
- 每个项目里的目标项是指向 Skill Hub 源目录的链接。编辑源 Skill 后，链接到它的项目会立即看到更新。
- Provider 通过集中注册表定义，内置 `codex`、`claude`、`antigravity`，配置也可增加自定义 Provider。
- `LinkStrategy` 将检查、创建、删除链接统一成 `check`、`create`、`remove` 操作。
- 根目录 `main.py` 是 Skill 链接管理入口；通过 `bash run.sh` 调用。
- 链接管理会创建缺失的链接；迁移时只会重定向指向旧 `skills/<name>` 源目录的链接。其他冲突目标保持原样并报告错误。

当前版本没有版本管理、数据库、Web、GUI 或云同步。

## 安装

需要 Python 3.12 或更新版本。

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 配置

仓库已经包含 `skillhub.yaml`、`source/skills/`、`source/rules/` 和 `source/rule-index/`。根据当前机器修改 `skillhub.yaml` 中的项目路径，并在 `source/skills/` 下添加或编辑 Skill 目录。

## 配置示例

```yaml
settings:
  link_mode: auto

providers:
  codex:
    skill_dir: .agents/skills
    rule_index_dir: .agents/rules
    rule_dir: AGENTS.md
  claude:
    skill_dir: .claude/skills
    rule_index_dir: .claude/rules
    rule_dir: CLAUDE.md
  antigravity:
    skill_dir: .agents/skills
    rule_index_dir: .agents/rules
    rule_dir: AGENTS.md
  cursor:
    skill_dir: .cursor/skills

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

Every immediate subdirectory of `source/skills/` is discovered as a Skill. The directory name is the Skill name and its path is derived automatically; files directly inside `source/skills/` are ignored. Add or remove a Skill directory and the next `run.sh` invocation sees the change without editing `skillhub.yaml`. Project paths are relative to the directory containing `skillhub.yaml`; `~` and environment variables are expanded. The configuration loader automatically reads a `.env` file beside `skillhub.yaml`. Copy `.env.example` to `.env` and set the project paths for the current computer:

```dotenv
AI_MASSAGE_PROJECT=/path/to/xiaozhi-AI
MES_PROJECT=/path/to/MES
SZWPOWER_PROJECT=/path/to/szwpower
DUOLINGO_PROJECT=/path/to/duolingo
PMS_PROJECT=/path/to/PMS
```

Keep `.env` local; it is excluded from version control. A project whose path references an unset or empty variable is skipped, so each computer can configure only the projects it uses. A Provider's relative `skill_dir` is relative to each project root. A built-in Provider may override its directory. A custom Provider must supply `skill_dir`.

Use `projects.<name>.rules` to select files from `source/rules/` without the `.md` suffix. For example, `rules: [pen]` applies `source/rules/pen.md`. Provider `rule_dir` entries name the project document to update; shared targets such as Codex and Antigravity's `AGENTS.md` are processed once per project. `main.py` adds missing rule blocks and removes known rule blocks that are no longer selected.

Use `projects.<name>.rule_index` to select files from `source/rule-index/` without the `.md` suffix. Each selected file must start with YAML front matter containing `applicable_path` and `description`. Provider `rule_index_dir` sets the project-relative destination directory for symbolic links to those files. `main.py` adds `## 项目规则索引规范` with `### 规则加载机制` and `### 规则索引` sections to each enabled Provider's `rule_dir` document. When Providers share a document, the table includes each configured rule-file path.

The final list for a project and Provider is the ordered union of the project's `skills` and that Provider's `skills`. Duplicate names are kept once. If a project omits its `providers` mapping, all configured Providers are enabled. When it specifies the mapping, only entries with `enabled: true` (or the default) are enabled.

Codex and Antigravity currently share the `.agents/skills` project directory. If both are enabled, a skill assigned to only one of them still appears in that shared directory and may be discovered by both tools. Choose separate supported folders in configuration only when the corresponding tool is set up to read those folders.

## 平台链接行为

- macOS/Linux：`main.py` 创建目录 symbolic link。
- Windows：先尝试目录 symbolic link；失败后用 Windows `mklink /J` 创建 directory junction。
- `bash run.sh` 需要 Bash、Python 环境和 `requirements.txt` 中的依赖。

如果目标路径已有普通文件或目录，`main.py` 会报告路径冲突，不会覆盖现有内容。Skill Hub 不会自动清理旧链接或移除未配置的 Skill；如需迁移或清理，请先检查目标路径并手动处理。

## 运行

在仓库根目录运行：

```bash
bash run.sh
```

`run.sh` 会调用 `main.py`，并将参数继续传入。可通过 `--config` 指定配置文件：

```bash
bash run.sh --config path/to/skillhub.yaml
```

运行时会按 `skillhub.yaml` 创建缺失的 Skill 链接，并同步选中的规则块和规则索引。遇到项目、源目录或目标路径错误时会报告并返回非零退出码。

## 验证

```bash
python -m unittest discover -s tests -v
```

Provider 默认目录依据各工具的项目级 Skill 文档：

- [Codex：Where Codex loads local skills](https://developers.openai.com/codex/skills)
- [Claude Code：Choose where skills load](https://code.claude.com/docs/en/skills)
- [Google Antigravity：Agent skills](https://antigravity.google/docs/skills)



