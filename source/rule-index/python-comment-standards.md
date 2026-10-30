---
title: Python 注释规范
description: Python 文件中的 docstring 与行内注释约定
applicable_path: "*.py"
---

# Python 注释规范

- 遵循项目现有的 docstring 和注释风格；新增代码不必为了满足固定层级而补充无实际帮助的注释。
- 模块、类或函数需要公开说明时，使用简洁的 docstring，描述职责、参数约束或返回值等读者需要的信息。
- 局部注释用于解释不明显的原因、业务约束或 workaround，放在对应代码上方；避免重复描述代码已经表达的内容。
- 重要业务流程可用模块 docstring 或分段注释说明其背景和不变量；无需为每个文件强制添加固定模板的头部注释。

```python
class InventoryService:
    """检查并管理库存。"""

    def check_stock(self, product_id: int, quantity: int):
        """确认指定商品有足够库存。"""
        stock = self.get_stock(product_id)

        # 此处需在写入订单前校验，避免并发请求导致超卖。
        if stock < quantity:
            raise OutOfStockError()
```

- 不写“设置变量”“遍历列表”等重复代码含义的注释。
- 仅在任务涉及的代码范围内补充或调整注释，不顺手改写无关模块的文档。
