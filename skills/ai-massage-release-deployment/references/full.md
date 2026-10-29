# full-split：三个独立应用镜像

生产目录及 .env.prod 按 [线上目录标准](../../docker-production-standard/SKILL.md)。构建路径以当前仓库为准：

| 服务 | Dockerfile 与构建上下文 |
| --- | --- |
| server | backend/device-server/Dockerfile；backend/device-server/ |
| manager-api | backend/manager-api/Dockerfile；backend/manager-api/ |
| manager-web | frontend/manager-web/Dockerfile；frontend/manager-web/ |

TARGET 支持 server、manager_api、manager_web、server+manager_web、all。只处理目标镜像，保持未更新组件的镜像、配置和容器不变。当前无合并的 manager bundle 发布单元。

manager-web 在构建阶段传入 VUE_APP_PUBLIC_PATH=/console/、VUE_APP_API_BASE_URL=/xiaozhi；bridge 模式使用监听容器 80 的 Nginx 配置，不套用旧 host 网络配置。检查 JAR、前端产物、子路径刷新、Service Worker 和离线页面；server 通过基础层及 storage 门禁。

目标 Compose 为根目录 compose/ 下的共用定义与生产 overlay，统一由根目录 .env.prod 插值。示例布局及命令见 部署入口（仓库根目录下的 `deploy/README.md`）。每次显式指定项目名、项目目录、.env.prod 和所有 Compose 文件，再执行 config --quiet、config --services、config --images；渲染值不得完整输出。

新布局不自动继承历史端口或数据库配置。比较旧实例与目标布局的端口、路由、网络、凭据来源和数据挂载；保留既有数据卷/路径，数据搬迁或新建数据库需要相应授权和备份。切换前对实际修改的文件逐份创建唯一备份，保留旧固定镜像。

仅以 --no-deps --pull never 重建 TARGET 对应应用，不隐式启动或重建 MySQL/Redis。首次扩展管理端时先完成 manager-api 和 manager-web 验收，再切换 server 和授权范围内路由。详细构建、验收、观察与回滚见 当前发布文档（仓库根目录下的 `backend/device-server/docs/docker-production-deployment.md`），发生冲突以当前 Compose/Dockerfile 和用户本次选择为准。
