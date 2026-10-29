# server 基础镜像与应用镜像

构建上下文为 backend/device-server/。Dockerfile-base 包含系统依赖、Python 包及 CPU PyTorch；Dockerfile 只复制应用源码与内嵌 MassageAgent。生产基础镜像采用固定引用，上游 Python parent 使用核验的 linux/amd64 digest。

基础层记录引用、Image ID、平台、创建时间、构建来源及依赖输入。Dockerfile-base、requirements.txt、系统依赖或兼容门禁变化时核对并重建；纯源码发布复用已验证的固定基础层，不为应用发布重复重打基础镜像标签。来源无法核实时停止，不用 latest 或删除断言绕过门禁。

构建和版本/API 检查使用 当前发布文档（仓库根目录下的 `backend/device-server/docs/docker-production-deployment.md`） 中的具体命令。核对 torch/torchaudio CPU 版本、SQLAlchemy/asyncmy/PyMySQL 和 ping 方法签名；应用镜像检查 core.storage、core.storage.models 导入及本次变更回归。

只从经过审查的构建上下文复制代码，运行时配置和模型挂载遵循 .dockerignore 与目标 Compose。发现配置中已有凭据时，不输出其值；先核对配置来源、镜像构建范围及运行时覆盖关系，保持现有功能，未经明确授权不删除或清空配置值。
