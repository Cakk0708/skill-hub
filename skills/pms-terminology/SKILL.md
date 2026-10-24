---
name: terminology
description: 这是关于项目术语引导skills，当用户提到任何项目术语时都可以通过参考本skills快速掌握和定位项目
---

# PMS 项目术语映射

## 用途
当用户提到以下术语时，快速定位到对应的模块/文件/功能。

## 模块术语映射

### PM 模块（项目管理）

| 术语 | 对应模块 | 路径 |
|------|----------|------|
| 项目 | 项目列表 | `apps/PM/project/` |
| 项目列表 | 项目列表 | `apps/PM/project/` |
| 项目详情 | 项目详情 | `apps/PM/project/` |
| 节点 | 项目节点 | `apps/PM/node/` |
| 节点列表 | 节点列表 | `apps/PM/nodelist/` |
| 节点规则 | 节点规则配置 | `apps/PM/node_rule/` |
| 项目变更、设计变更 | 项目设计变更 | `apps/PM/change/` |
| 变更 | 项目设计变更 | `apps/PM/change/` |
| 项目暂停、暂停申请 | 项目暂停申请 | `apps/PM/pause/` |
| 项目继续、继续申请 | 项目继续申请 | `apps/PM/continuation/` |
| 绩效 | 绩效管理 | `apps/PM/performance/` |
| 绩效管理 | 绩效管理 | `apps/PM/performance/` |
| 评价 | 绩效评价（1.0已废弃） | `apps/PM/evaluate/` |
| 硬件 | 硬件信息管理 | `apps/PM/hardware/` |
| 交付物 | 交付物管理 | `apps/PM/deliverable/` |
| 项目模板 | 项目模板 | `apps/PM/template/` |

### SM 模块（系统管理）

| 术语 | 对应模块 | 路径 |
|------|----------|------|
| 用户 | 用户管理 | `apps/SM/user/` |
| 用户管理 | 用户管理 | `apps/SM/user/` |
| 角色 | 角色管理 | `apps/SM/role/` |
| 权限 | 权限管理 | `apps/SM/authority/` |
| 验证码 | 验证码管理 | `apps/SM/code/` |
| 审批流 | 审批流管理 | `apps/SM/approval/` |
| 审批 | 审批流管理 | `apps/SM/approval/` |
| 消息 | 消息管理 | `apps/SM/message/` |
| 评审模板 | 评审模板 | `apps/SM/template/` |

### BDM 模块（商务数据管理）

| 术语 | 对应模块 | 路径 |
|------|----------|------|
| 客户 | 客户管理 | `apps/BDM/cust/` |
| 部门 | 部门管理 | `apps/BDM/dept/` |

### API 模块

| 术语 | 对应模块 | 路径 |
|------|----------|------|
| 飞书接口、飞书API | 飞书接口封装 | `apps/API/feishu.py` |
| 配置 | 配置相关 | `apps/API/configuration/` |
| 报告 | 报告相关 | `apps/API/report/` |

## 核心文件映射

| 术语 | 文件路径 |
|------|----------|
| 信号、PM信号 | `apps/PM/signals.py` |
| SM信号 | `apps/SM/signals.py` |
| 节点信号 | `apps/PM/nodelist/signals.py` |
| 异步任务、PM任务 | `apps/PM/tasks.py` |
| SM任务 | `apps/SM/tasks.py` |
| 飞书封装 | `assists/feishu.py` |
| OSS、阿里云OSS | `assists/aliyun_oss.py` |
| 公共方法 | `assists/common.py` |
| 配置、系统配置 | `config/info.py` |
| 主路由 | `home/urls.py` |

## 状态码映射

### 节点状态
| 值 | 状态 |
|----|------|
| 0 | 未开始（灰色） |
| 1 | 进行中（黄色） |
| 2 | 已完成（绿色） |
| 3 | 暂停（红色） |
| 4 | 项目变更中（紫色） |

### 项目状态
| 值 | 状态 |
|----|------|
| 0 | 删除 |
| 1 | 进行中 |
| 2 | 已完成 |
| 3 | 变更中 |

## 外部系统

### pms-admin（管理后台）

**概念**：pms-admin 是一个独立的微服务系统（管理后台），用于管理系统配置数据。

**与 PMS 后端的关系**：
- PMS 后端通过 API 调用 pms-admin 获取各种配置数据
- 两者之间使用 JWT + AES 安全协议进行通信

**pms-admin 管理的功能**：
| 功能 | 说明 | API 路径 |
|------|------|----------|
| 版本管理 | 系统版本号、版本更新内容 | `/bdm/version/current` |
| 评价配置 | 项目评价相关配置 | `/pm/sys/evaluation/...` |
| 硬件管理 | 硬件规格、硬件使用记录 | `/pm/sys/hardware/...` |
| 节点规则 | 项目节点规则配置 | `/pm/sys/node/rule` |

**配置位置**：
- API 基地址：`settings.PMS_ADMIN_BASE_URL`
- 安全协议：`settings.API_SECURITY_PROTOCOL['PMS-ADMIN']`

**开发环境端口**：8050

**当用户提到以下术语时，应该联想到从 pms-admin 获取**：
- 版本号、版本信息、系统版本
- 版本更新内容、更新日志
- 管理后台配置的任何数据

## 使用说明

当用户提到上述术语时，你应该：
1. 自动联想到对应的模块路径
2. 在搜索代码时优先搜索对应目录
3. 在解释功能时引用正确的模块位置
4. 涉及版本、配置等数据时，考虑是否需要从 pms-admin 获取
