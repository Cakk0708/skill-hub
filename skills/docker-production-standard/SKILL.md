---
name: docker-deployment-standard
description: >
  规定 Docker 项目的线上服务器目录结构和文件职责。
  设计或审查生产主机上的 Compose、环境配置、持久化数据和备份目录时使用。
---

# 线上文件结构标准

线上主机保存容器运行所需的部署配置和持久化数据，不保存用于构建镜像的完整业务源码。以固定的项目根目录为例：

```text
/opt/<project>/
├── compose/
│   ├── compose.yaml             # 共用服务定义（如果项目采用共用文件）
│   └── compose.prod.yaml        # 生产配置
├── .env.prod                    # 生产运行变量，权限仅授予部署账号
├── releases/
│   └── <release-id>/            # 可选：发布用 Compose 副本和镜像清单
├── volumes/                     # 仅用于显式 bind mount 的宿主机数据
│   ├── app-data/
│   ├── uploads/
│   └── models/
└── backups/                     # 数据和配置的受控备份
```

`nginx/` 只在项目确实由这台主机管理反向代理配置时加入；容器日志默认由容器运行时或日志平台管理，不必创建未被服务使用的 `logs/` 目录。

## 目录职责

- **compose/**：只放部署所需的 Compose 文件及必要脚本。生产 Compose 不依赖主机上的源码构建上下文。
- **.env.prod**：只保存生产运行配置。设置为仅部署账号可读（通常 `chmod 600`），不提交 Git，不放进 Web 可访问目录，也不复制到普通发布包中。
- **releases/**：按需保留可回滚的 Compose 文件副本、镜像标签或 digest 清单及发布记录；不要将密钥或业务数据无保护地复制进发布快照。
- **volumes/**：只用于 Compose 明确配置的宿主机 bind mount，例如上传文件、模型和服务运行数据。路径应稳定、明确，并与发布版本目录分离。
- **backups/**：保存数据库、关键运行数据及恢复所需配置的备份；备份与活动数据分开管理，并验证恢复路径。

## Volume 与 bind mount

Compose 命名 volume 的实际数据由 Docker 管理，不会自动出现在 `/opt/<project>/volumes/`。宿主机目录只有在配置了 bind mount 时才应进入项目目录。两种方式都要定义备份和恢复方法；不要为了让目录树看起来一致而迁移现有数据。

模型等只读运行资产可从固定宿主机路径挂载，并在 Compose 中设为只读。数据库、上传和其他需保留的状态不得依赖容器可写层。

实际主机已有目录、卷和挂载路径在变更前必须先核对，不能仅按此示例推断。
