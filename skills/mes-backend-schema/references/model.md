# Django Model 约定

## Meta

- 新建 Model 时提供清楚的 verbose_name。
- 只有在需要固定既有表名或遵循模块显式表名约定时设置 db_table；显式表名遵循 `.codex/rules/backend/naming-conventions.md`。使用 Django 默认表名时，不要仅为满足模板而重复声明。
- 只有在该 Model 由项目自定义权限体系管理、且不需要 Django 默认 CRUD 权限时，才设置 default_permissions = ()。若有自定义 permissions，先确认现有模块的权限做法。
- Meta 通常放在字段声明之后；使用标准空行。不要为了格式重排无关方法。

## 关系字段

- 一对多或多对一使用 ForeignKey。
- 多对多关系按本项目现有模式使用 ManyToManyField，并显式声明 through 中间 Model；中间 Model 用 ForeignKey 表达两端关系。
- 不要把单个 ForeignKey 当成 ManyToManyField 的等价替代。两者的数据语义不同。
- 若修改已有关系，先检查现有 through Model、相关查询和迁移影响。

~~~python
class Customer(models.Model):
    tags = models.ManyToManyField(
        "BDM.Tag",
        through="CustomerTag",
        related_name="customers",
    )


class CustomerTag(models.Model):
    customer = models.ForeignKey("BDM.Customer", on_delete=models.CASCADE)
    tag = models.ForeignKey("BDM.Tag", on_delete=models.CASCADE)
~~~
