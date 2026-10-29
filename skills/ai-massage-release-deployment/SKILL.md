---
name: ai-massage-release-deployment
description: >
  为 AI-Massage 服务端执行生产 Docker 构建、镜像交付、部署、验收和回滚，
  覆盖 backend/device-server、backend/manager-api 和 frontend/manager-web 三个独立应用镜像。
  用户提出服务端生产发布、上传镜像、部署、切换或回滚时使用；不用于固件烧录或通用数据库运维。
---

# 服务端生产发布

## 当前规范与发布范围

先读取 [线上目录标准](../docker-production-standard/SKILL.md)、[Docker 发布要求](../docker-deployment-requirements/SKILL.md) 和 当前部署入口（仓库根目录下的 `deploy/README.md`）。当前 Dockerfile、Compose 和用户本次选择定义目标结构；历史发布记录仅用于查证、识别迁移源及回滚对象，不能覆盖当前标准。主机地址通过本次授权的 OP 条目核实，不在技能中固定旧主机或部署目录。

生产配置采用目标根目录的 `.env.prod`，模板为仓库根目录 `.env.prod.example`。正式 Compose 不依赖临时 env 文件或历史 release 内的 env。旧 env 损坏应作为迁移源配置问题记录，不能据此要求恢复旧布局；目标必要配置无法核实时才阻止切换。

当前应用采用 `full-split`：server、manager-api、manager-web 三个独立发布单元。MySQL、Redis 是数据依赖，应用部署不默认重建数据服务。

| Profile | Target | 更新范围 |
| --- | --- | --- |
| full-split | server | 仅 Python server |
| full-split | manager_api | 仅 Java API |
| full-split | manager_web | 仅 Vue 页面/Nginx |
| full-split | server+manager_web | 两个对应应用，保持 API 不变 |
| full-split | all | 三个应用 |
| minimal | server | 仅在用户保留且已核验的 server-only 部署中使用 |

未指定范围时只读检查当前源码变更与运行实例，核对兼容性后确定目标。跨组件不兼容变更按 all 发布；不得构建旧的 manager bundle。选择 full-split 后读取 [拆分部署](references/full.md)；minimal 读取 [server-only 部署](references/minimal.md)；含 server 时读取 [基础镜像规则](references/server-image.md)。需要调整路由或数据依赖时分别读取 [路由](references/nginx-routing.md) 和 [数据库/网络](references/database-network.md)。

## 用户意图与授权

- 构建：完成所选镜像及本地验收。
- 打包：再生成镜像交付包、大小和 SHA-256。
- 上传：再完成传输、摘要和远端预检，不切换。
- 部署/发布：完成授权范围内切换、验收、观察和记录。
- 回滚：恢复本次变更对应的应用镜像与配置，数据库不自动 downgrade。

默认交付使用 ACR 固定标签或 digest，线上拉取核对后的镜像。用户明确需要 tar 交付时，上传前后逐个校验 SHA-256，一致后才能 load。

应用发布不默认授权创建数据库账户、修改数据服务配置、数据搬迁、清理生产文件/镜像或 schema downgrade。共享 Nginx 仅在路由变更属于本次授权范围时修改，先独立备份，再 nginx -t、reload，保留恢复步骤。凭据通过 OP 及受保护配置使用，不输出秘密、连接 URL、完整生产配置或含秘密的异常；不擅自删除现有配置中的凭据或改变运行功能。

## 发布门禁

门禁失败时暂停受影响的生产切换，继续核实原因、修复授权范围内的问题并重新验证；事实不明时报告具体阻塞点。区分目标规范、历史运行状态和本次实际结果。

1. 记录构建前后 git status 和实际提交，不覆盖、丢弃或擅自提交工作区改动。
2. 每个目标应用使用唯一、不可覆盖的固定镜像标签或 digest，禁止 latest。基础层、应用层均核对真实平台 linux/amd64 和 Image ID。
3. 核对本次构建输入、运行配置、API 和 schema 兼容性，执行相关回归；server 验证 core.storage/core.storage.models 可导入，API 验证 Java JAR，web 验证 /console/ 静态产物、Service Worker 和 Nginx。
4. 只读核对现有服务、网络、端口、持久化路径、依赖及空间。迁移或配置事实不明时禁止切换；不通过开放数据库公网端口解决连通问题。
5. 为目标布局准备可审查的 Compose/.env.prod，核对其与现有实例的必要差异。每次命令显式指定同一项目名、项目目录、.env.prod 和 Compose 文件组合。config --quiet、服务/镜像集合、固定引用、端口及挂载均须通过；不输出完整渲染配置。
6. 切换前为实际改动的 Compose、.env.prod 和运行配置创建唯一、受限权限备份；记录原镜像引用和 Image ID，确认回滚镜像可用。布局调整保留原数据路径/卷，未经核实不搬迁。
7. 空间不足停止，不做宽泛清理。只拉取/加载目标镜像，按 --no-deps --pull never 重建目标服务，避免隐式重建兄弟和数据容器。
8. 新版本完成验收前不删除新旧镜像、交付包、配置或备份。启动失败、重启循环、持续 degraded、健康入口失败或核心回归时恢复已备份的目标镜像和配置；跨组件故障按兼容范围成组恢复。

## 验收与发布记录

每个重建的应用至少观察 5 分钟；涉及数据库、Redis、连接池或异步问题时至少 10 分钟或覆盖实际触发窗口。核对运行状态、restart count、应用入口、错误日志和专项行为；验证 HTTPS、页面/API、OTA、视觉和 WS。没有在线设备时结果最多为 success_with_pending_validation，不宣称主板端到端成功。

发布记录采用 当前服务端发布文档（仓库根目录下的 `backend/device-server/docs/docker-production-deployment.md`） 的清单字段，逐个记录组件的引用、Image ID、平台、交付方式、大小/摘要或 Registry digest、基础层来源、原镜像、备份、实际 Compose/.env.prod 路径、网络/挂载、迁移、观察窗口、设备验证与例外。没有生成镜像或执行验收时填实际未执行状态，不补写成功。记录目标布局与历史迁移源的区别。
