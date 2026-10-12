# minimal：server-only 拓扑打包与部署

仅在入口选定 `PROFILE=minimal`、`TARGET=server` 时读取。本 profile 只发布 xiaozhi-server，不构建、不切换 manager bundle。首次增加管理端不是 minimal 发布；选择 `PROFILE=full`、`TARGET=all` 并读取 [full 部署流程](full.md)。

## 拓扑门禁

- 构建输入是 `Dockerfile-server`；构建或复用基础层前读取 [server 镜像和基础层规则](server-image.md)。
- 生产 Compose 必须明确只有目标 server 服务，或明确声明的既有依赖；当前实际文件、服务名和镜像引用必须通过远端只读检查确认。
- 传统 `network_mode: host` 拓扑可以没有 Compose ports，但应用配置必须实际监听 8000 和 8003；bridge 拓扑则必须显式映射 8000:8000 和 8003:8003。
- minimal 且未启用 manager-api 时，Python HTTP 服务的 `8003/xiaozhi/ota/` 才是 OTA 入口，同时提供视觉接口。
- 不得把 8001、8002 或管理端路由加入本分支的成功条件。
- 按 [Nginx 路由契约](nginx-routing.md)核对 minimal 的 `/ws/`、`/api/ota/` 和 `/api/vision/`；不得把 full 的 manager-api OTA 入口当作 minimal 验收目标。

## 本地构建与验收

    cd xiaozhi-esp32-server

    RELEASE_TAG='<已核对的唯一标签>'
    BASE_IMAGE='xiaozhi/server-base:<已核对的固定标签>'
    test -n "$RELEASE_TAG" -a -n "$BASE_IMAGE"

    docker image inspect "$BASE_IMAGE" \
      --format 'base_id={{.Id}} {{.Architecture}}/{{.Os}} created={{.Created}}'

    docker build --no-cache --platform linux/amd64 --pull=false \
      --build-arg "BASE_IMAGE=$BASE_IMAGE" \
      -f Dockerfile-server \
      -t "xiaozhi/server:$RELEASE_TAG" .

    docker image inspect "xiaozhi/server:$RELEASE_TAG" \
      --format 'image_id={{.Id}} {{.Architecture}}/{{.Os}} created={{.Created}}'

    docker run --rm --platform linux/amd64 --entrypoint python \
      "xiaozhi/server:$RELEASE_TAG" \
      -c 'import core.storage; import core.storage.models; print("storage-import-ok")'

追加本次 server 变更对应的专项验收。任一失败都停止打包。共享构建门禁和镜像标签要求见入口 skill。

## 单镜像交付包

使用唯一临时目录，交付包不加入 Git：

    DELIVERY_DIR="$(mktemp -d /private/tmp/xiaozhi-server-release.XXXXXX)"
    DELIVERY_TAR="$DELIVERY_DIR/xiaozhi-server-$RELEASE_TAG.tar"
    docker save -o "$DELIVERY_TAR" "xiaozhi/server:$RELEASE_TAG"
    shasum -a 256 "$DELIVERY_TAR"
    ls -lh "$DELIVERY_TAR"

记录 delivery_file、字节数和 SHA-256。上传后必须重新计算远端摘要；不一致时禁止 docker load。

## 远端切换

先将 COMPOSE_FILE 设置为已核对的生产文件，不能依赖默认文件名：

    COMPOSE_FILE='<已核对的生产 Compose 路径>'
    docker compose -f "$COMPOSE_FILE" config --quiet
    docker compose -f "$COMPOSE_FILE" config --services
    docker compose -f "$COMPOSE_FILE" config --images
    sha256sum "xiaozhi-server-$RELEASE_TAG.tar"

继续前确认：目标 server 服务名唯一、Compose 中目标镜像为本次固定引用、空间足够、上一镜像和 Compose 备份可识别、网络模式与端口拓扑属于 minimal。只在摘要一致后执行：

    docker load -i "xiaozhi-server-$RELEASE_TAG.tar"
    docker image inspect "xiaozhi/server:$RELEASE_TAG" \
      --format '{{.Id}} {{.Architecture}}/{{.Os}}'

    cp -p '<唯一的本次部署前 Compose 备份源>' \
      '<唯一的本次部署前 Compose 备份目标>'

    # 仅精确替换已核对的旧 server 镜像引用，不做宽泛替换。
    docker compose -f "$COMPOSE_FILE" config --quiet
    docker compose -f "$COMPOSE_FILE" up -d --no-deps --force-recreate --pull never xiaozhi-esp32-server

若本次确需修改生产 `data/.config.yaml`，必须先另行创建唯一备份并记录差异；不因发布方便而复制、重写或打印生产凭据。

## minimal 生产验收

根据实际网络模式执行并人工判断：

    docker inspect xiaozhi-esp32-server \
      --format '{{.Config.Image}}|{{.Image}}|{{.State.Status}}|restart_count={{.RestartCount}}'
    ss -lntp | grep -E ':(8000|8003)[[:space:]]'
    curl -fsS -o /dev/null -w '%{http_code}\n' \
      http://127.0.0.1:8003/xiaozhi/ota/
    docker exec xiaozhi-esp32-server python -c \
      'import core.storage; import core.storage.models; print("storage-import-ok")'
    docker logs --since 15m xiaozhi-esp32-server

同时按实际 Nginx 配置从本机和公网入口验证 `/ws/`、`/api/ota/` 和 `/api/vision/`；HTTP 方法、WebSocket 握手和业务响应必须按接口契约人工判断，不能仅凭端口处于 LISTEN 就通过。路由变更的备份与检查按 Nginx 路由契约执行。

## minimal 回滚

出现启动失败、重启循环、OTA/视觉失败或核心回归时，恢复唯一 Compose 备份和上一固定 server 镜像：

    cp -p '<本次部署前 Compose 备份>' "$COMPOSE_FILE"
    docker compose -f "$COMPOSE_FILE" config --quiet
    docker compose -f "$COMPOSE_FILE" up -d --no-deps --force-recreate --pull never xiaozhi-esp32-server

确认上一 Image ID、8000/8003、OTA、日志和观察窗口恢复后，记录 `result: rolled_back`。不得执行数据库 downgrade。
