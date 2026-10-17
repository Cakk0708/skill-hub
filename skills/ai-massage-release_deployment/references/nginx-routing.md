# Nginx 路由契约

当前生产候选管理页面为 `https://ai-massage.lingyang-electronics.com/console/`；发布前重新核对实际域名、DNS、证书和生效 vhost。

本文件维护宿主机 Nginx 的应用路径和上游。发布前读取当前生效 vhost，按当前 PROFILE 对照；不要因仓库候选文件而覆盖线上自定义规则。公网原则上只开放 Nginx 的 80/443。

## 路由映射

| Profile / 外部路径 | 上游 | 路径处理 |
| --- | --- | --- |
| 两种 profile：`/ws/app`（若现网客户端使用） | `127.0.0.1:8000` | 保留原路径，精确匹配也需核对 |
| 两种 profile：`/ws/` | `127.0.0.1:8000/xiaozhi/` | 保留 WebSocket Upgrade/Connection，长连接超时符合客户端心跳 |
| minimal：`/api/ota/` | `127.0.0.1:8003/xiaozhi/ota/` | server Python HTTP 提供 OTA |
| full：`/console/` | `127.0.0.1:8002/` | 外层去掉 `/console/` 前缀；manager-web 静态页面 |
| full：`/xiaozhi/` | `127.0.0.1:8002/xiaozhi/` | manager API 经 web 容器 Nginx 到同容器的 Java API |
| full：`/api/ota/` | `127.0.0.1:8002/xiaozhi/ota/` | OTA 由 manager-api 提供 |
| 两种 profile：`/api/vision/` | `127.0.0.1:8003/mcp/vision/` | server Python HTTP 提供视觉接口 |

full 下 manager-api 在 web 容器内部监听 8003；该端口与 server 容器映射到主机的视觉 8003 不冲突。外层 Nginx 只访问主机上的 web 入口 8002，不应把 Java API 容器内端口单独发布到公网。生产 full 不发布 manager-web 本地开发端口 8001。

## /console/ 前缀

manager-web 的 `publicPath` 和 Vue Router `base` 都读取 `VUE_APP_PUBLIC_PATH`。当前生产环境文件默认值为 `/`；full 打包必须将构建期值设置为 `/console/`。`Dockerfile-web` 需要在前端构建阶段显式传入或加载该值，不能只在运行容器时设置，因为静态资源路径已经写入构建产物。API base 保持 `/xiaozhi`。 当前 `src/service-worker.js` 把离线页写成绝对路径 `/offline.html`；在子路径部署前须使离线页 URL 前缀感知，并验收 Service Worker 安装、作用域和缓存。

外层 Nginx 的路径替换应等效于：

    location = /console {
        return 301 /console/;
    }

    location ^~ /console/ {
        proxy_pass http://127.0.0.1:8002/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

上游 `proxy_pass` 的尾斜杠用于把外部 `/console/...` 映射到 web 容器的 `/...`。不得再通过静态替换 HTML 来模拟 publicPath。生产路由若选用其他 hostname/path，先记录用户选择并同步更新前端构建路径和本文件的验收 URL。

## 修改和验收

只有路由变更属于本次用户授权范围时才修改生效 vhost。变更前创建唯一备份；修改后先运行对应 Nginx 的 `nginx -t`，通过后再 reload。保留备份路径和恢复步骤。

full 需要从宿主机入口和公网域名分别验证：

- `/console/` 返回管理页面；HTML 引用的 JS/CSS/字体等资源均从 `/console/` 前缀加载。
- 深层页面（例如管理路由）直接刷新仍返回 SPA 页面，Vue Router 地址不丢前缀。
- Service Worker 在 `/console/service-worker.js` 注册在管理端子路径作用域中，离线页面可从该路径缓存和加载。
- 浏览器 API 请求仍打到同域 `/xiaozhi/` 并获得符合契约的响应。
- `/api/ota/` 到达 manager-api；`/api/vision/` 到达 server。
- `/ws/` 与现网 `/ws/app`（若使用）按接口契约完成 WebSocket 握手、保持连接。
- HTTPS 证书覆盖实际域名，公网只经 80/443 访问，不以本机 8002/8003 检查替代公网验收。

`proxy_pass` 指定 URI 时会替换匹配的 location 前缀；不带 URI 时保留请求路径。改动前据此检查尾斜杠，避免 API 路径被重复拼接或截断。
