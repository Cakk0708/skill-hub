---
name: op-ssh-key
description: |
  OP 服务器 SSH 密钥管理
  涉及到“ecs”、“ssh”、“密钥”等关键词时触发
---

允许 Agent 使用 1Password 的 OP CLI 工具获取 SSH 密钥，当用户要求 Agent 连接 SSH 时向用户询问 SSH 密码对应 1Password 中的条目名称或 UUID

Agent 将调用 `op item get` 命令获取 SSH 密钥后，使用 `ssh` 命令连接 SSH 继续完成用户要求的后续任务
