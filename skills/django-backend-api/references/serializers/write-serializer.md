
# 写入序列化器（WriteSerializer）规范

## 字段规范

- Serializer 声明名使用 Python `snake_case`；项目的 camel-case parser/renderer 负责将公开 JSON 字段映射为 `camelCase`。例如内部 `project_node_id` 对应请求体中的 `projectNodeId`。
- 不要同时声明蛇形和驼峰两套字段，也不要再用硬编码别名做同一 casing 转换。维护既有接口时保留其已发布的线上字段名；若旧 Serializer 使用 camelCase 声明名，先确认解析器映射后再做兼容调整。
- 外部字段名与 Model 属性名不同时，通过 `source` 显式映射。
- 涉及外键或关联模型的 ID 字段使用 `PrimaryKeyRelatedField` 和合适的 `queryset` 做存在性校验，不用 `IntegerField` 代替。

## 正确示例

```python
class DeliverableWriteSerializer(serializers.Serializer):
    """创建交付物序列化器"""
    project_node_id = serializers.PrimaryKeyRelatedField(
        source="project_node",
        queryset=ProjectNode.objects.all(),
        error_messages=serializer_func.error_data
    )
    assigned_user_id = serializers.PrimaryKeyRelatedField(
        source="assigned_user",
        queryset=User.objects.all(),
        error_messages=serializer_func.error_data
    )
```

## 错误示例

```python
# ❌ 关联 ID 未校验关联对象是否存在
project_node_id = serializers.IntegerField()

# 错误：公开的 projectNodeId 会先被 parser 转为 project_node_id，无法匹配 camelCase 声明名
projectNodeId = serializers.PrimaryKeyRelatedField(
    source="project_node",
    queryset=ProjectNode.objects.all()
)
```
