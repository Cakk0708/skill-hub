# Nginx 路由契约

目标路由以当前 deploy/nginx/nginx.conf、生产 Compose 和本次用户选择为准。先读实际生效配置用于比较迁移差异，不把历史端口、域名或路径当作新发布约定。Nginx 是共享入口，只有授权范围内的路由变更才修改；独立备份，nginx -t 通过后 reload，保留恢复步骤。

| 外部入口 | full-split 的目标服务 | 仓库默认回环上游 |
| --- | --- | --- |
| /console/ | manager-web 80，去掉外部前缀 | 127.0.0.1:8002/ |
| /xiaozhi/ | manager-api 8002，保留路径 | 127.0.0.1:18004 |
| /api/ota/ | manager-api /xiaozhi/ota/ | 127.0.0.1:18004/xiaozhi/ota/ |
| /api/vision/ | server /mcp/vision/ | 127.0.0.1:8003/mcp/vision/ |
| /ws/ | server /xiaozhi/ | 127.0.0.1:8000/xiaozhi/ |
| /ws/app | server，保留现网客户端契约 | 127.0.0.1:8000 |

只有无 manager-api 的 minimal 部署才使用 server HTTP 的 /xiaozhi/ota/。若旧实例把 OTA 转到 server，这是待比较的现状，不能替代 full-split 的目标路由。

manager-web 构建期传入 /console/ 与 API base /xiaozhi，验证实际 JS/CSS 路径、Vue Router base、深层刷新、Service Worker 作用域及离线页；不能用运行时环境变量改写已生成静态资源。核对 proxy_pass 是否携带 URI 和尾斜杠，避免丢失或重复前缀。

验收覆盖本机与公网的页面、资源、API、OTA、视觉、WS 握手及连接保持、TLS 证书。公网应用入口只经 80/443，应用回环端口和数据服务不为发布方便开放到公网。没有改动 Nginx 时记录 not_changed。
