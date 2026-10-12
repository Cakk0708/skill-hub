# full：server + manager bundle 拓扑

仅在入口确定 `PROFILE=full` 后读取。当前仓库的 `xiaozhi-esp32-server-web` 镜像把 Vue manager-web、Java manager-api 和容器内 Nginx 放在一起：三个逻辑端，两个应用容器。修改目标前先核对当前 Dockerfile、Compose 和运行服务；没有独立镜像与回滚对象时，不把 API 和页面拆成两个发布单元。

## 拓扑和端口

| 位置 | 端口 | 作用 |
| --- | --- | --- |
| 主机 -> server 容器 | 8000 | WebSocket |
| 主机 -> server 容器 | 8003 | server 视觉 HTTP |
| 主机 -> web 容器 | 8002 | manager 静态页面/API 网关 |
| web 容器内部 | 8003 | manager-api Java 服务，不单独发布 |

full 生产不发布 8001。内外两容器同为 8003 不构成主机冲突。bridge 是仓库 full 拓扑的候选；若生产是 host network，不套用 bridge ports，必须先有独立且验证过的 full host 拓扑，否则停止。Nginx 外层公网原则上只开放 80/443。

仓库的 `docker-compose_all.yml` 仅是候选文件，不可原样视为生产配置：发现 `latest`、仓库自带 MySQL/Redis 或不匹配的地址时，先建立与生产实际一致的配置。默认复用经核验的线上数据库依赖，不因选择 full 而启动或迁移数据服务。读取 [数据库与网络条件步骤](database-network.md)。

## TARGET 与兼容门禁

| TARGET | 构建和切换 | 允许条件 |
| --- | --- | --- |
| `server` | 只处理 `xiaozhi-esp32-server` | 当前 full 中 manager bundle 保持运行，验证新 server 与现有 API/schema 兼容 |
| `manager_bundle` | 只处理 `xiaozhi-esp32-server-web` | 当前线上已是 full；核对现有 server/API 契约和 DB schema 兼容 |
| `all` | 处理两个应用服务 | 首次从 minimal 扩展到 full、跨组件接口/配置变化或无法分别证明兼容时必须使用 |

只发布单个组件时，不重建兄弟容器；记录兄弟服务原镜像引用和 Image ID，并核实部署后未改变。首次 full 扩容需要检视配置、迁移和路由：manager 服务先启动并完成本地验收，server 按 full 配置连通 manager-api 后再切换 full OTA 路由。任何需要的数据迁移先遵循数据库参考并验证备份。

## 构建和验收

从 `xiaozhi-esp32-server/` 构建。为本次 release ID 下的每个要更新组件生成独立、固定且未使用过的镜像引用；目标含 server 时读取 [server 镜像和基础层规则](server-image.md)。检查编译实际使用的 Dockerfile、依赖、迁移与前端配置。

manager-web 以 `/console/` 为生产路径时，构建期 `VUE_APP_PUBLIC_PATH` 必须是 `/console/`；静态产物生成后仅在容器运行时设置环境变量不能改变资源路径。检查 `Dockerfile-web` 是否把构建值传给 Vue CLI；当前 `.env.production` 默认 `/`。若 Dockerfile 未传入该构建期值，先补充 Dockerfile 或生产 env 构建机制并纳入 manager 镜像，再构建；不能用容器运行时变量掩盖错误的静态资源路径。管理 API 的 `VUE_APP_API_BASE_URL=/xiaozhi` 保持与公网 `/xiaozhi/` 路由一致。参考 [Nginx 路由契约](nginx-routing.md)。 当前 service worker 将离线页面写作绝对路径 `/offline.html`；`/console/` 部署前必须使该地址适配前缀，并验证 worker 注册和离线页缓存。

只构建目标镜像；full stack 两组件的示例：

    cd xiaozhi-esp32-server
    RELEASE_ID='<唯一发布编号>'
    SERVER_IMAGE='<固定的 server 完整镜像引用>'
    WEB_IMAGE='<固定的 manager-bundle 完整镜像引用>'
    BASE_IMAGE='<已核验的固定基础镜像引用>'

    docker build --no-cache --platform linux/amd64 --pull=false \
      --build-arg "BASE_IMAGE=$BASE_IMAGE" \
      -f Dockerfile-server -t "$SERVER_IMAGE" .

    docker build --no-cache --platform linux/amd64 --pull=false \
      -f Dockerfile-web -t "$WEB_IMAGE" .

对单组件 TARGET 仅执行该镜像的 build、inspect、docker save 和 SHA-256；不得为了凑齐双镜像包把未选中的镜像重打标签或构建。检查目标镜像的 `RepoTags`、Image ID 和 `linux/amd64`。server 镜像还需验收 `core.storage` 与 `core.storage.models` 可导入；manager bundle 需验收 Java API 构建产物、前端 dist 和容器启动。构建门禁失败就停止。

上传时逐个核验远端摘要。Compose 必须经过 `config --quiet`，服务集合至少包含所需服务；每个被改服务的镜像引用逐字等于选定镜像。检查目标服务、旧镜像和 Compose 唯一备份存在，磁盘足够，实际 DB/Redis 网络可达。不要打印密钥或生产配置。

## 镜像交付、远端预检与切换

本地按 TARGET 为每个被选镜像执行 `docker image inspect`，确认固定引用、Image ID 和平台。只将选中的镜像保存为交付包：

    DELIVERY_DIR="$(mktemp -d /tmp/xiaozhi-full-release.XXXXXX)"
    case "$TARGET" in
      server)
        docker save -o "$DELIVERY_DIR/xiaozhi-server-$RELEASE_ID.tar" "$SERVER_IMAGE"
        ;;
      manager_bundle)
        docker save -o "$DELIVERY_DIR/xiaozhi-server-web-$RELEASE_ID.tar" "$WEB_IMAGE"
        ;;
      all)
        docker save -o "$DELIVERY_DIR/xiaozhi-server-$RELEASE_ID.tar" "$SERVER_IMAGE"
        docker save -o "$DELIVERY_DIR/xiaozhi-server-web-$RELEASE_ID.tar" "$WEB_IMAGE"
        ;;
      *)
        exit 2
        ;;
    esac
    shasum -a 256 "$DELIVERY_DIR"/*.tar
    ls -lh "$DELIVERY_DIR"/*.tar

分别记录每个交付文件的路径、字节数和 SHA-256。上传后在远端逐个重算 SHA-256；任一不一致时禁止加载任何新镜像。

远端先确认生产 Compose 路径、实际服务/镜像、磁盘、当前容器 Image ID 和回滚镜像。执行 `docker compose -f <已核对文件> config --quiet`、`config --services`、`config --images`；不要打印完整配置。为每份要编辑的 Compose 文件创建唯一备份。只精确替换 TARGET 对应服务的 image 引用，检查 diff 后再次执行 config 校验，确保兄弟服务及数据服务引用不变。

摘要逐一相符后，仅加载选中镜像并检查远端 Image ID/平台：

    docker load -i '<选中组件的交付包>'
    docker image inspect '<选中的完整镜像引用>' \
      --format '{{.RepoTags}} {{.Id}} {{.Architecture}}/{{.Os}}'

使用下一节中与 TARGET 对应的单服务或双服务命令切换。不要使用 Compose 默认文件，不要因为文件声明 DB/Redis 就启动它们。切换前如需更新 Nginx 路由，按 [Nginx 路由契约](nginx-routing.md)创建独立备份、运行 `nginx -t`，并确认该变更属于当前授权范围。

按 TARGET 仅更新对应服务：

    # TARGET=server
    docker compose -f "$COMPOSE_FILE" up -d --no-deps --force-recreate --pull never xiaozhi-esp32-server

    # TARGET=manager_bundle
    docker compose -f "$COMPOSE_FILE" up -d --no-deps --force-recreate --pull never xiaozhi-esp32-server-web

    # TARGET=all
    docker compose -f "$COMPOSE_FILE" up -d --no-deps --force-recreate --pull never xiaozhi-esp32-server xiaozhi-esp32-server-web

上面的目标服务命令不可混用；第一次扩容到 full 需先核对目标 Compose 中所有依赖，使用 `--no-deps` 只重建应用服务，不意外启动 Compose 文件声明的数据服务。任何必要依赖未运行或不可达时停止。

## full 验收

根据本次 TARGET 检验变更和未变更服务的镜像引用、Image ID、运行状态、restart count、端口和日志。TARGET 含 server 时执行 server 存储导入和 server 专项验收；TARGET 含 manager_bundle 时执行 web 页面与 API 专项验收；TARGET=all 时两套都执行。

按真实接口契约判断本机入口，不把端口 LISTEN 当业务成功：

    curl -fsS -o /dev/null -w 'manager-web %{http_code}\n' \
      http://127.0.0.1:8002/
    curl -fsS -o /dev/null -w 'manager-api/ota %{http_code}\n' \
      http://127.0.0.1:8002/xiaozhi/ota/
    curl -fsS -o /dev/null -w 'vision-options %{http_code}\n' \
      -X OPTIONS http://127.0.0.1:8003/mcp/vision/explain

若采用 `/console/`，除容器本机页面外还须从外层 Nginx 和公网检查 `/console/`、静态资源前缀、至少一个可刷新深层路由、同域 `/xiaozhi/` API、`/api/ota/`、`/api/vision/`、HTTPS 和 WS。不能只依赖本机 8002/8003 检查。完整路由步骤见 [Nginx 路由契约](nginx-routing.md)。

## 回滚

单组件且兼容性门禁通过时，只恢复本次变更的服务和上一固定镜像。若 `TARGET=all`、有跨组件接口变更，或故障表明版本需配对，则恢复 server 与 manager bundle 两者的备份镜像及 Compose 状态。数据库不随镜像自动 downgrade。若 Nginx 也在本次授权范围内修改，按独立备份恢复，先执行 `nginx -t` 再 reload。

回滚后核对所有目标服务和未变更服务的镜像 ID、端口、页面/API、OTA、视觉、WS、依赖连接与观察窗口，结果记为 `rolled_back`。
