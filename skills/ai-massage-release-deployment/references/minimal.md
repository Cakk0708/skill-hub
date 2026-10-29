# minimal：既有 server-only 部署

仅在本次明确保留并核验 server-only 拓扑时使用，TARGET=server。不要用 minimal 代替用户选择的 full-split 目标。server 的 Dockerfile 和上下文位于 backend/device-server/，基础镜像遵循 [server 基础层规则](server-image.md)。

目录按 docker-production-standard 设计，生产变量来自根目录 .env.prod，Compose 显式指定文件组合和项目参数。只重建 server，保留现有数据依赖和回滚对象。网络为 host 时检查监听和冲突，bridge 时检查回环端口映射。

无 manager-api 的 minimal OTA 由 server HTTP 提供；按 [路由契约](nginx-routing.md) 验证 WebSocket、OTA、视觉、TLS 和本次专项行为，不把管理端入口作为本分支条件。执行 storage 导入、相关回归和规定观察窗口，失败恢复旧镜像及对应配置，不执行数据库 downgrade。
