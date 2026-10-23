---
name: docker-local-project-layout
description: >
  规定 Docker 项目的本地源码仓库、Dockerfile、Compose 和环境模板布局。
  设计或整理本地开发仓库的 Docker 文件结构时使用。
---

# 本地文件结构标准

本地仓库保存应用源码和构建、编排所需的受版本控制文件。保持各服务当前的源码目录；下面展示的是职责划分，不要求把所有项目改成相同目录名。

```text
project/
├── service-a/                   # 服务源码与对应 Dockerfile
├── service-b/
├── deploy/
│   ├── compose/
│   │   ├── compose.yaml          # 多环境共用的服务定义（需要时）
│   │   ├── compose.dev.yaml      # 本地开发差异
│   │   └── compose.prod.yaml     # 生产差异
│   ├── nginx/                    # 项目维护的代理配置（需要时）
│   └── scripts/                  # 可重复执行的本地构建与启动脚本
├── .env.example
├── .env.prod.example
└── .gitignore
```

## 文件放置

- Dockerfile 放在服务源码附近，或放在该服务明确的构建目录中；Compose 的 `build.context` 应覆盖构建所需文件，避免无意把整个仓库或凭据发送给构建器。
- Compose 文件属于部署层，不必放入某个业务服务目录。存在多环境时，可用共用文件和环境 overlay 表达共享服务定义与差异；简单项目不必为此增加空文件。
- 本地开发配置可以使用 `build:`、源码 bind mount 和开发端口。生产配置用镜像引用；生产发布细节由部署要求 skill 定义。
- 仓库只提交 `.env.example`、`.env.prod.example` 等不含真实凭据的模板。实际 `.env`、生产环境文件、密钥、数据库数据、上传文件和模型缓存应由 `.gitignore` 排除，按项目需要保存在仓库外或专用运行目录。
- 服务间独立部署或扩缩容时，保持独立 Dockerfile、镜像和容器；是否拆分服务按真实发布边界决定，不按服务数量套模板。

## 本地数据

开发数据库、上传目录和模型缓存应有明确的数据生命周期。绑定到仓库外的目录或命名 volume 都可以；需要重建容器时，不要顺带删除仍需保留的数据卷。

Compose 命令应显式使用项目约定的 project name、env file 和 Compose 文件集合，避免从不同目录启动后生成另一套网络或 volume。
