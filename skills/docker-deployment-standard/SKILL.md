---
name: docker-deployment-standard
description: >
  Docker 项目首次线上部署目录结构规范
  在使用 Docker 部署应用时使用。遵循标准的 Dockerfile、docker-compose.yml 和部署流程，确保应用的可重复构建、版本控制和环境一致性。|
---


## 1. 目标

本规范用于指导 Docker 化项目首次部署到线上服务器时的目录设计。

核心原则：

> **源码负责开发，镜像负责交付，服务器负责运行。**

生产环境不保存业务源码，而通过 Docker Image + Compose 文件完成服务部署。

---

# 2. 核心架构思想

开发环境：

```
源码
 |
 | docker build
 ↓
Docker Image
 |
 | push
 ↓
镜像仓库
 |
 | pull
 ↓
生产服务器
```

生产服务器只负责：

- 拉取镜像
- 管理容器
- 保存持久化数据
- 管理运行配置


---

# 3. 开发环境结构

开发阶段：

```
project/

├── service-a/
│
├── service-b/
│
├── service-c/
│
├── docker-compose.dev.yml
│
└── .env
```

例如：

```
ai-massage/

├── xiaozhi-server/
├── manager-api/
├── manager-web/
├── docker-compose.yml
└── .env
```

这里保存：

- 后端源码
- 前端源码
- Dockerfile
- 开发配置

用于：

- 本地开发
- 本地调试
- 构建镜像


---

# 4. 生产环境目录标准

推荐：

```
/opt/project-name/

├── compose/
│   └── docker-compose.prod.yml
│
├── .env
│
├── volumes/
│   ├── mysql/
│   ├── redis/
│   ├── uploads/
│   └── models/
│
├── nginx/
│   └── project.conf
│
├── logs/
│
└── scripts/
    ├── deploy.sh
    └── backup.sh
```

例如：

```
/opt/ai-massage/

├── compose/
│   └── docker-compose.prod.yml
│
├── .env
│
├── volumes/
│   ├── mysql/
│   ├── redis/
│   ├── models/
│   └── uploads/
│
├── nginx/
│   └── ai-massage.conf
│
├── logs/
│
└── scripts/
```

---

# 5. 生产环境不存放源码

生产服务器不应该存在：

```
/opt/project/

├── manager-api/
├── manager-web/
└── server/
```

原因：

## 5.1 避免线上代码漂移

禁止：

```
服务器修改源码
```

否则：

- Git版本不可追踪
- 无法复现部署
- 难以回滚


---

## 5.2 保证部署一致性

标准流程：

```
代码仓库

↓

Docker Build

↓

Docker Registry

↓

生产服务器 Pull

↓

Docker Compose启动
```

---

# 6. 服务与 Docker Image 的关系

源码：

```
project/

├── manager-api
├── manager-web
└── server
```

构建后：

```
Docker Image:

ai-massage-api:v1.0.0

ai-massage-web:v1.0.0

ai-massage-server:v1.0.0
```

生产运行：

```
docker ps

CONTAINER

├── ai-massage-api
├── ai-massage-web
├── ai-massage-server
├── mysql
└── redis
```

三个业务服务没有合并。

它们是：

- 独立镜像
- 独立容器
- 独立升级


---

# 7. Production Compose 规范

生产环境 compose 不使用 build。

错误：

```yaml
manager-api:

  build:
    context: ./manager-api
```

生产禁止。


正确：

```yaml
manager-api:

  image: registry.example.com/ai-massage-api:v1.0.0
```


生产 compose 只负责：

- 服务编排
- 网络关系
- 数据挂载
- 环境变量


---

# 8. 数据持久化规范

容器生命周期：

```
container

可删除
```

数据生命周期：

```
volume

长期保存
```


数据库：

```
mysql container

        |

        ↓

/opt/project/volumes/mysql
```


删除容器：

```
docker rm mysql
```

数据仍然存在。


---

# 9. 镜像分类规范

推荐：

```
registry/

├── project-api
│
├── project-web
│
└── project-server
```


版本：

```
project-api:v1.0.0

project-web:v1.0.0

project-server:v1.0.0
```


禁止：

```
latest
```

生产环境必须固定版本。

---

# 10. 更新流程规范


## API升级

开发：

```
修改代码

↓

build image

↓

push
```

生产：

```
docker compose pull manager-api

docker compose up -d manager-api
```


只更新 API。

其他服务不受影响。


---

# 11. 不同部署场景


## 11.1 云端 SaaS

推荐：

```
ECS

├── web
├── api
├── server
└── redis


RDS

└── mysql
```

数据库独立。


---

## 11.2 私有化部署

推荐：

```
一台服务器

Docker

├── nginx
├── web
├── api
├── server
├── mysql
└── redis
```

适合：

- 工厂
- 企业内部
- 离线环境


---

# 12. 最终原则

首次线上部署 Docker 项目时：

1. 生产服务器不保存源码
2. 生产服务器只保存部署文件
3. 业务服务拆分为独立 Image
4. Compose 只负责组合服务
5. 数据必须通过 Volume 持久化
6. 镜像必须版本化
7. 开发 Compose 与生产 Compose 分离

最终目标：

```
源码
 |
Docker Image
 |
Compose
 |
生产环境
```

形成稳定、可复制、可回滚的部署体系。