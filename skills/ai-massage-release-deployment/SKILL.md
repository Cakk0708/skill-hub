---
name: ai-massage-release-deployment
description: |
  为 xiaozhi-AI 的 xiaozhi-esp32-server 执行生产 Docker 构建、交付、部署、验收和回滚，覆盖 xiaozhi-server 与 bundled manager-api/manager-web。用户提出服务端生产构建、Docker 发布、上传镜像、部署、切换生产镜像或回滚时使用。仅用于服务端应用发布，不用于 ESP32 固件烧录或通用数据库运维。
---

# 服务端多组件生产发布

## 1. 选择拓扑与发布目标

发布前先区分部署拓扑与本次要更新的应用镜像：

- `PROFILE=minimal`：只有 `xiaozhi-server`。
- `PROFILE=full`：`xiaozhi-server` 与 `xiaozhi-esp32-server-web`；后者当前把 manager-api、manager-web 打包在同一个镜像中，是一个发布单元。
- `TARGET=server`：只更新 server 镜像。
- `TARGET=manager_bundle`：只更新 web/API 镜像；仅当线上已处于 full 拓扑且版本兼容性已核实时允许。
- `TARGET=all`：更新 full 拓扑中的两个应用镜像。生产环境首次从 minimal 扩展到 full 必须使用此目标；隔离环境可以单独验证组件，但必须先建立并核验对应拓扑。

| Profile | 支持的目标 | 约束 |
| --- | --- | --- |
| minimal | server | 不构建或启动管理端，不验收 8002 |
| full | server、manager_bundle、all | 单组件更新须核对未更新组件、API 契约和数据库 schema 兼容；首次扩容或跨组件变更使用 all |

不要把 manager-api 和 manager-web 描述成两个独立容器或独立镜像，除非当前 Dockerfile、Compose 和回滚对象都已改为独立部署。full 方案当前是三个逻辑端、两个应用容器。

如果用户未指定 profile/target，先只读检查仓库和生产 Compose、正在运行的镜像、网络和目标变更，再选择；事实不足以判断兼容性时停止并说明。不得从旧 Compose 文件名或 Git 分支名推断线上拓扑。开始构建或远端变更前读取：
- minimal：[minimal 部署流程](references/minimal.md)
- full： [full 部署流程](references/full.md)
- TARGET 包含 server： [server 镜像基础层规则](references/server-image.md)
- 路由需要新增或调整： [Nginx 路由契约](references/nginx-routing.md)
- 本次涉及存储、数据库迁移或依赖网络： [数据库与网络条件步骤](references/database-network.md)

## 2. 当前组件、入口与共享依赖

构建目录为 `xiaozhi-esp32-server/`。线上主机和目录是候选事实，发布前仍须重新核对：`root@121.41.114.90`、`/home/projects/xiaozhi-esp32-server`。平台目标为 `linux/amd64`。

生产 Nginx 是 server 与 manager 共用的宿主机入口。公网原则上只开放 80/443；不得把 8001、数据库或 Redis 端口开放到公网。应用端口和代理目标按实际网络模式核对。minimal/full 的路径映射及 `/console/` 管理页面路径统一维护在 [Nginx 路由契约](references/nginx-routing.md)，不要在 profile 文档中复制另一套路由表。

MySQL 和 Redis 是应用依赖，不默认属于应用发布范围。线上已有实例时优先核实并复用；不得因使用 full Compose 就启动仓库内自带的 MySQL/Redis 或覆盖生产数据。容器网络、监听地址、ACL、防火墙和迁移事实不明时读取数据库与网络参考并停止相关切换。

## 3. 用户意图与变更边界

用户意图决定执行终点：

- “构建”：完成所选目标的本地镜像和验收。
- “打包/交付包”：再完成所选镜像的 docker save、文件大小和 SHA-256。
- “上传”：再完成远端摘要、空间、Compose 拓扑和回滚预检，不切换生产。
- “部署/发布/构建部署”：完成授权范围内的生产切换、验收、观察期和发布记录。
- “回滚”：精确恢复本次变更的应用镜像和配置。若本次是 full stack 联动或接口不兼容，成组恢复相关镜像；默认不做数据库 downgrade。

部署授权不包含创建数据库账户、修改 MySQL/Redis 系统配置、扩容、清理生产文件或镜像、数据库 downgrade。公网 Nginx 是共享配置：仅在该路由变更已纳入用户本次发布授权时修改；变更前单独备份，先执行 nginx -t，再 reload，并保留独立恢复步骤。若部署目标依赖尚未授权的 Nginx 变更，完成只读预检和可审查的配置草案后暂停该变更。

不得打印、复制、提交或打包密码、Token、数据库连接 URL 或完整生产配置。不得使用消息工具向他人发送信息。

## 4. 全目标共用发布门禁

任一门禁失败即停止后续变更并报告实际阻塞点：

1. 每个要构建的应用镜像使用唯一、固定且可追溯的标签，禁止 `latest`，禁止覆盖已有标签、交付包或备份。可用一个 release ID 关联多镜像，但发布记录必须逐个写出镜像引用和 Image ID。
2. 本地和远端每个镜像均验证为 `amd64/linux`；宿主机架构不能代替镜像平台验证。
3. 不丢弃、覆盖或擅自提交工作树改动；记录构建前后 `git status --short`。
4. 按目标执行通用及专项验收。目标含 server 时验证 server 存储导入；目标含 manager_bundle 时验证 Java API 构建产物、前端产物、容器启动和管理路由。
5. 每个交付包上传前后 SHA-256 必须一致；任一不一致都禁止 docker load。
6. 切换前记录目标服务的当前固定镜像引用与 Image ID，并为每份实际使用的 Compose 文件创建唯一备份。记录未更新的兄弟服务镜像，确认其未被隐式重建。
7. 空间不足时停止。禁止宽泛清理、强制删镜像或删除回滚目标；清理生产资源须另行授权并限定到具体对象。
8. 迁移、配置和网络是条件步骤；事实不明时禁止切换。外部 MySQL/Redis 保持原实例，除非用户明确选择独立的数据库发布方案。
9. 生产 Compose 的实际应用镜像必须是固定、可核对的引用。执行显式 `docker compose -f <已核对文件>`；`config --quiet`、服务集合、镜像集合、目标标签和端口拓扑核验通过后才重建目标服务。
10. 不因默认文件名存在就选错拓扑；不要打印完整 Compose 渲染值、生产 `.config.yaml`、环境变量值或异常中的凭据。
11. 新容器、应用接口和公网路由验收前不得删除新旧镜像、交付包、配置或备份。
12. 只记录实际观察结果；未运行、没有设备条件或未覆盖的验收必须写明“待验证”，不能声称成功。

## 5. 发布执行

从仓库根目录记录：

    git status --short
    git rev-parse --short HEAD
    git log -1 --format='%h %s'
    docker info

读取 `AGENTS.md` 和本次变更涉及的路径级规则。对每个实际要发布的镜像核对 Dockerfile、配置、迁移和构建输入；若接口跨 server 与 manager 变化，按 `TARGET=all` 做兼容发布。

先只读预检生产目录、磁盘、Docker、服务、端口、Compose 服务与镜像。不要输出完整 Compose 或生产密钥。`network_mode: host` 时不能因 Compose 没有 `ports` 就判错，需核对应用监听；bridge 模式需核对端口映射、服务名网络和依赖可达性。

为每个选中组件生成唯一固定镜像标签，并让生产 Compose 中该组件的镜像引用逐字匹配。构建、交付和切换只覆盖 `TARGET` 指定服务；首次 minimal 到 full 扩容、接口不兼容或共享迁移时按 full 流程成组部署。任何生产 Compose 替换都先备份，且只精确更新目标镜像引用。

本次变更的每个应用容器启动后观察至少 5 分钟；涉及 DB/Redis、连接池或异步问题时至少 10 分钟或覆盖实际触发窗口。观察目标容器状态、restart count、端口、健康入口、错误日志和本次专项行为。full 还要验收管理页面/API、OTA、视觉、WS 与公网 Nginx/TLS 路由。没有在线设备时可完成服务端发布，但结果为 `success_with_pending_validation`，不得声称设备或按摩主板端到端验收完成。

出现启动失败、重启循环、持续 degraded、健康入口失败或核心回归时，恢复目标镜像和 Compose 备份；若本次跨组件联动，恢复成组镜像。Nginx 若在本次发布中修改，按唯一备份单独恢复并先 `nginx -t`。应用回滚不等于数据库 downgrade；未经验证不得执行。清理不属于默认发布，至少保留一个已验证回滚版本。

## 6. 发布记录

最终输出以下字段，并为每个参与发布的组件填写独立镜像项：

    profile: "minimal | full"
    target: "server | manager_bundle | all"
    release_id: "用于关联本次组件镜像的唯一标识"
    git_commit: "实际提交 SHA"
    dirty_worktree_at_build: "实际值"
    dirty_worktree_after: "实际值"
    compose_file: "实际生产 Compose 路径"
    services_changed: ["实际重建的服务"]
    images:
      - component: "xiaozhi-server | manager-bundle"
        action: "built | reused | unchanged"  # reused = verified fixed image retained in the release cohort; unchanged = outside TARGET
        image_ref: "固定完整引用"
        image_id: "Image ID"
        platform: "amd64/linux"
        delivery_file: "实际文件路径或 not_applicable"
        delivery_size_bytes: 0
        delivery_sha256: "SHA-256 或 not_applicable"
    server_base_image: "引用、Image ID 与策略；未发布 server 时 not_applicable"
    previous_images: ["目标组件上一固定引用和 Image ID"]
    compose_backup: "实际备份路径"
    nginx_backup: "实际备份路径或 not_changed"
    port_topology: "实际端口与网络模式"
    database_migration: "not_required | revision | blocked"
    deployed_at: "Asia/Shanghai 时间"
    result: "success | success_with_pending_validation | rolled_back | blocked"
    validation: "组件行为、公网路由、观察窗口和设备状态"
    exceptions: "受控例外或 none"

只在所选目标的基础设施、组件行为、所需公网入口和观察窗口均完成后记录 `success`。

## 7. 参考文件

- [minimal：server-only 拓扑](references/minimal.md)
- [full：server 与 manager bundle 拓扑](references/full.md)
- [server 镜像和基础层](references/server-image.md)
- [Nginx 路由契约](references/nginx-routing.md)
- [数据库与网络条件步骤](references/database-network.md)

仅在排障或确认历史时读取历史发布记录；不得复用旧标签、摘要、Image ID 或完成状态：

- docs/【已完成】2026-08-08-xiaozhi-server生产Docker部署.md
- docs/【已完成】2026-08-10-xiaozhi-server数据库连接修复完整部署SOP.md
