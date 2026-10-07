
# 写入序列化器（WriteSerializer）规范

## 字段规范

- 请求字段名遵循该接口的公开契约。新 API 与项目响应示例使用 snake_case；维护已有接口时保留已有 camelCase 等字段名。
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

# 既有接口可能保留 camelCase；外部字段名不同于 Model 属性名时，显式声明 source
projectNodeId = serializers.PrimaryKeyRelatedField(
    source="project_node",
    queryset=ProjectNode.objects.all()
)
```
