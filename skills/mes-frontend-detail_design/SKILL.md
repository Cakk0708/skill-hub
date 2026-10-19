---
name: mes-frontend-detail_design
description: 
  设计MES前端页面设计说明
  涉及“前端详情页”、“详情页设计”、“详情页模块”相关设计、改造时触发本技能
---

## 模式介绍

详情页有多种模式：

- 查看模式（默认）
- 编辑模式
- 新增模式

## 页面组成结构

页面由组件 TechTableLayout 包裹，内部包含以下组件

- **TechParticleCanvas**: 酷炫科技粒子背景
- **DataPageToolbar**: 顶部操作条

### 顶部操作条

顶部操作条包含以下按钮：

- 左边
  - 返回按钮
  - 描述
- 右边
  - 打印单据
  - 复制模板
  - 业务操作
  - 停用
  - 编辑修改
  - 刷新按钮
