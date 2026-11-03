---
name: op-item-get
description: |
  OP 1Password 条目获取
  涉及到"op"、"1password"、"op cli"等关键词时触发
---

允许 Agent 使用 1Password 的 OP CLI 工具获取 SSH 密钥

供用户用于连接 SSH 时免输入 SSH 密码，直接从 1Password 中获取对应条目名称或 UUID

## 用法

Agent 将调用 `op item get` 命令获取对象 UUID JSON 参数，统一使用 JSON 格式返回一次性拿到对应 UUID 全部数据在本次会话中储存，供本次会话时重复使用（不再重复调用 op 指令多次获取，只从本次 session 对话上下文中获取）

### 参数格式

```
op item get <uuid> --format json
```

### ssh 连接

- item 对象为 ssh 密钥时，使用 `ssh` 命令连接 SSH 继续完成用户要求的后续任务
- item 对象为 ssh 账号密码等信息时一次性获取并使用 `ssh` 命令连接 SSH 继续完成用户要求的后续任务

### 数据库连接

- item 对象为数据库账号密码等信息时一次性获取并使用后，不再重复获取

