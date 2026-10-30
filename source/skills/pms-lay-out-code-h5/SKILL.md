---
name: lay-out-code-h5
description: |
  当用户提到“部署代码”时触发这条 skill
  将某个工程的代码打包后部署到某个环境
---

## 流程
1. **确认**: 确认部署目标环境
2. **打包**: 打包执行环境前端包
3. **推送**: 使用 rsync 上传到目标环境

## 确认

根据用户提到的环境名称、工程名称，确认部署目标环境及目标，若用户提供的信息没有明确环境名称或工程名称时向用户确认，由于服务器可能没有建立短期免密连接，在人物开始之初应先测试免密连接情况，若被拒绝则需要向用户所要服务器密码

### 1. 环境名称

- 测试环境
- 生产环境

### 2. 工程名称

- 管理后台：frontend-admin
- 前端：frontend-h5

## 打包

### 管理后台

#### 测试环境

```bash
cd frontend-admin

npm run build:test
```

#### 生产环境

```bash
cd frontend-admin

npm run build:prod
```

### 前端

#### 测试环境

```bash
printf 'h5-test\n' > /Users/ly/Code/PMS/frontend-h5/.h5-env

ENV_TYPE=h5-test UNI_SCRIPT=h5-test \
/Applications/HBuilderX.app/Contents/MacOS/cli publish web \
  --project /Users/ly/Code/PMS/frontend-h5
```

#### 生产环境

```bash
printf 'h5-prod\n' > /Users/ly/Code/PMS/frontend-h5/.h5-env

ENV_TYPE=h5-prod UNI_SCRIPT=h5-prod \
/Applications/HBuilderX.app/Contents/MacOS/cli publish web \
  --project /Users/ly/Code/PMS/frontend-h5
```

## 推送

### 管理后台

#### 测试环境

```bash
rsync -avz \
  --delete /Users/ly/Code/PMS/frontend-admin/dist/ \
  root@121.41.114.90:/home/www/PMS-test/frontend-admin
```

#### 生产环境

```bash
rsync -avz \
  --delete /Users/ly/Code/PMS/frontend-admin/dist/ \
  root@121.41.114.90:/home/www/PMS-admin
```

### 前端

使用 rsync 推送打包后代码到服务器，若需要服务器密码时向用户询问密码（注意：不要在代码中硬编码密码）

```bash
rsync -avz --delete \
  {来源目录} \
  {服务器用户}@{服务器地址}:{目标目录}
```

#### 测试环境

- 来源目录: /Users/ly/Code/PMS/frontend-h5/unpackage/dist/build/web/
- 服务器用户: root
- 服务器地址: 121.41.114.90
- 目标目录: /home/www/PMS-test/frontend/

```bash
rsync -avz --delete \
  /Users/ly/Code/PMS/frontend-h5/unpackage/dist/build/web/ \
  root@121.41.114.90:/home/www/PMS-test/frontend/
```

#### 生产环境

- 来源目录: /Users/ly/Code/PMS/frontend-h5/unpackage/dist/build/web/
- 服务器用户: root
- 服务器地址: 121.41.114.90
- 目标目录: /home/www/PMS/

```bash
rsync -avz \
  --delete /Users/ly/Code/PMS/frontend-h5/unpackage/dist/build/web/ \
  root@121.41.114.90:/home/www/PMS/
```