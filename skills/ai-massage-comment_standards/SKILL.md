---
name: ai-massage-comment_standards
description: >
  在新增、修改或审查 xiaozhi-esp32-server/main/xiaozhi-server 下的
  Python 注释或 docstring 时使用。不要用于非 Python 文件、生成文件、
  其他目录或与注释无关的普通代码修改。
---

# xiaozhi-server Python 注释与 Docstring 规范

## 适用范围

- 仅适用于 `xiaozhi-esp32-server/main/xiaozhi-server/` 下的 Python 文件。
- 只在任务涉及新增、修改或审查注释、docstring 时使用。
- 不将 Python 注释规则套用到 JavaScript、TypeScript、JSON、YAML、Markdown、音频或生成文件。

## 三级注释体系

### 一级：模块或核心逻辑块

用于模块入口、复杂业务流程、重要算法和关键架构逻辑。

```python
"""
=============
说明内容（可多行）
=============
"""
```

规则：

- 使用模块 docstring 或逻辑块 docstring。
- 上下使用长度一致的 `=============` 分隔线。
- 只说明会影响理解、维护或安全性的背景，不重复代码表面含义。

### 二级：类、公共函数和复杂方法

```python
class OrderService:
    """订单服务，负责订单创建与状态管理。"""

    def create_order(self, user_id: int):
        """创建订单。"""
```

规则：

- 类、公共函数和复杂方法使用简洁 docstring。
- docstring 紧跟定义行，不加无意义分隔线。
- 对简单、显而易见的私有辅助函数，不强制添加冗余说明。

### 三级：局部逻辑说明

用于复杂判断、特殊逻辑、临时 workaround 和关键变量说明。

```python
# 主板状态可能晚于 ACK 到达，因此这里等待状态快照确认。
if not state_confirmed:
    retry()
```

规则：

- 使用 `#`，放在相关代码上方，不写行尾解释性注释。
- 说明为什么这样做，不重复代码已经表达的内容。

## 禁止行为

- 不写“设置变量”“遍历列表”等重复代码含义的注释。
- 不为简单变量、简单分支或显而易见的返回值强行添加注释。
- 不在每个文件中强制写固定作者名；作者信息容易过期且不能替代维护记录。
- 不修改生成文件中的注释格式，除非任务明确要求重新生成源文件。

## 修改检查

修改注释或 docstring 后，确认：

1. 说明的是背景、原因、约束或副作用，而不是逐行翻译代码。
2. 内容与当前实现一致，没有保留过期行为描述。
3. 没有把本规则应用到非 Python 文件或无关目录。
