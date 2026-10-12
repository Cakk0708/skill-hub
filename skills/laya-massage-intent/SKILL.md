---
name: laya-massage-intent
description: |
  当新增或修复按摩口语表达、同义词、连续对话训练样本，或出现 Laya 把明确按摩控制路由为 uncertain/通用处理、回复不支持、错误参数、LLM 兜底、语义动作未执行、能力声明缺失、MCP 映射失败时触发此技能。
  本技能用于沿 xiaozhi-AI 唯一按摩主链路定位不兼容点，完成从内嵌 MassageAgent 的确定性识别、状态计算和语义动作，到 xiaozhi-server 能力声明与执行编排、ESP32 MCP、MassageController、BoardAdapter、岭阳协议适配及回归验证的闭环修改，禁止只改回复文案或绕过语义边界。
---

# 常用概念

先阅读仓库根目录 `AGENTS.md`，并遵守唯一主链路：

```text
用户对话
  -> ASR 文本与按摩口语归一化
  -> Laya 一级路由与分发
  -> xiaozhi-esp32-server 内嵌 MassageAgent
  -> 语义执行计划
  -> xiaozhi-server 执行编排与 ESP32 MCP
  -> ESP32 MassageController / MassageBoardAdapter
  -> 岭阳协议适配层
  -> UART / 主板
```

常用服务端路径：

- `xiaozhi-esp32-server/main/xiaozhi-server/core/providers/intent/laya_router/taxonomy.py`：Laya 一级意图定义与分类说明。
- `xiaozhi-esp32-server/main/xiaozhi-server/core/providers/intent/laya_router/policy.py`：一级路由确定性校准、明确控制证据与安全拒判。
- `xiaozhi-esp32-server/main/xiaozhi-server/core/providers/intent/laya_router/service.py`：模型原始分类、概率门限与校准策略的合并。
- `xiaozhi-esp32-server/main/xiaozhi-server/core/handle/intentHandler.py`：按最终 route 分发到按摩、天气、音乐或通用处理器。
- `xiaozhi-esp32-server/main/xiaozhi-server/core/assistant/massage_domain/services/conversation_service.py`：确定性口语识别、相对值计算、会话上下文和回复生成。
- `xiaozhi-esp32-server/main/xiaozhi-server/core/assistant/massage_domain/agent.py`：把 `DeviceCommand` 转换为稳定的 `massage.*` 语义动作，并按设备能力筛选执行计划。
- `xiaozhi-esp32-server/main/xiaozhi-server/core/assistant/massage_domain/schemas/`：`DeviceState`、`DeviceCommand`、按摩 DSL 和语义程序模型。
- `xiaozhi-esp32-server/main/xiaozhi-server/core/providers/massage/massage_agent_adapter.py`：读取设备状态、声明 `supported_app_commands`、发现 MCP 工具并执行。
- `xiaozhi-esp32-server/main/xiaozhi-server/core/providers/massage/command_mapper.py`：把 `massage.*` 映射为 `self.massage.*`；不得在此生成岭阳裸报文。
- `xiaozhi-esp32-server/main/xiaozhi-server/tests/massage/`：内嵌 Agent 与执行编排回归测试。

常用 ESP32 路径：

- `xiaozhi-esp32/main/massage/massage_command.*`：主板无关的 `MassageCommandName`、参数校验和幂等指纹。
- `xiaozhi-esp32/main/massage/massage_mcp_tools.cc`：`self.massage.*` MCP 注册、参数范围和提交入口。
- `xiaozhi-esp32/main/massage/massage_controller.*`：队列、ACK、确认、停止优先级和状态合并。
- `xiaozhi-esp32/main/massage/massage_safety_guard.cc`：状态新鲜度、时效、故障和运行阶段的本地二次校验。
- `xiaozhi-esp32/main/massage/massage_board_adapter.*`：稳定完成条件，不包含主板功能码。
- `xiaozhi-esp32/main/massage/lingyang/`：岭阳功能码、帧编码、ACK、状态位和故障位的唯一归属。
- `xiaozhi-esp32/tests/lingyang_protocol_test.cc`、`xiaozhi-esp32/tests/massage_controller_test.cc`：Mac 主机协议与 Controller 测试。

关键概念：

- **训练样本**：用户口语及其期望业务含义，不等于只向 LLM prompt 添加示例。能确定匹配的设备控制优先走确定性识别。
- **语义动作**：如 `massage.stop`、`massage.set_intensity`、`massage.set_time`；服务端不得携带功能码、键值或 UART 字节。
- **能力声明**：Agent 生成动作后，还必须出现在 `supported_app_commands` 中，并能映射到设备实际暴露的 MCP 工具，否则会被覆盖为“不支持”。
- **状态基准**：相对控制必须使用语义正确且最新的状态字段。例如“再增加 5 分钟”应基于 `remaining_sec`，不能把缺失的 `duration_min` 猜成当前值。
- **执行反馈**：不能只生成“已设置”“已延长”等成功文案；必须存在可执行计划，并由真实执行结果决定最终成功、失败或超时反馈。
- **局部 ACK**：只更新对应字段，再合并到完整 `MassageState` 快照；不能把单条 ACK 当成完整设备状态。
- **黄金报文**：必须写明业务含义、十六进制、期望结果和来源。历史项目只能作为待验证参考，不得伪装成真板事实。

## Laya 一级路由诊断

看到 Laya 把明确的设备控制表达路由为 `uncertain` 或通用处理器时，先定位路由边界，不从最终播报文案反推设备动作：

1. 对照 ASR 最终文本、归一化文本和路由请求，确认问题原句没有在入口处被改写或截断。
2. 分开读取模型原始 route/概率与最终 route。`top1/top2` 描述模型分类；`confidence`、`accepted`、`abstain_reason` 和校准规则描述最终决策。`abstain_reason=route_policy_uncertain` 表示确定性策略选择了拒判，即使调整模型提示或置信度阈值也不会越过该策略。
3. 检查 `intentHandler.py` 的最终分支。`uncertain` 会进入通用处理流程，MassageAgent 不会获得本轮控制请求；因此由通用回复产生的建议不能视为设备执行结果。
4. 在 `policy.py` 为有明确目标和方向的省略式控制补充窄匹配，并在 `taxonomy.py` 同步分类说明和正例。保留问句、否定、假设及多意图保护；不要把所有按摩词或所有 `uncertain` 直接升级为设备控制，也不要只降低全局阈值。
5. 路由到 `massage_command` 后继续检查 MassageAgent 是否能确定性识别同一句、正确选择目标字段并计算参数。路由修复只负责把请求送入按摩链路；若下游没有对应语义字段或含义尚未确认，应澄清，不能凭 route 推断动作。
6. taxonomy 分类边界改变时同步更新 `TAXONOMY_VERSION`，并用基线样本覆盖原句、相近正例、问句/否定/假设反例和多意图表达。


# 任务目标

1. 用用户提供的原句建立路由与领域回归样本，保留标点、数字写法、口语助词和多轮上下文；不要先把问题概括成宽泛意图。
2. 使用真实入口或最接近真实入口的请求复现，记录原始/归一化文本、模型 route 与概率、最终 route、`accepted`、`abstain_reason`、最终 handler，以及下游的 `device_state`、`capabilities`、会话上下文、`reply_text` 和 `execution`。
3. 按以下顺序定位首次偏差，发现断点后仍检查下游是否完整：

```text
ASR 最终文本与按摩口语归一化
  -> Laya 模型原始分类
  -> route policy 校准
  -> intentHandler 最终分发
  -> MassageAgent 确定性表达识别
  -> DeviceCommand / DSL
  -> MassageAgent._semantic_action
  -> supported_app_commands
  -> MassageCommandMapper
  -> self.massage.* MCP 是否存在
  -> MassageCommand 参数与 SafetyGuard
  -> BoardAdapter 编码与 ACK token
  -> 状态合并与完成条件
  -> execution_feedback 最终回复
```

4. 判断本次训练属于哪一类：

   - 仅缺少同义表达：扩展最窄的确定性匹配，并避免误伤力度、模式、开关等其他控制。
   - 相对值计算错误：基于正确状态字段计算，处理取整、上下限、未知状态和过期状态。
   - 已生成 `DeviceCommand` 但回复“不支持”：检查 `_semantic_action`、能力声明、MCP 工具发现和 mapper，禁止只删掉“不支持”文案。
   - 新语义动作：补齐服务端动作、mapper、ESP32 MCP、命令模型、校验、安全规则、BoardAdapter 和执行确认。
   - 回复错误：先确认执行计划和执行结果正确，再调整确定性回复或回复 prompt。

5. 对设备控制表达采用主板无关的数据模型。只有 `xiaozhi-esp32/main/massage/lingyang/` 可以新增岭阳功能码、键值、帧布局和状态位解析。
6. 为每个原始表达增加表驱动测试，至少断言：不发生非预期 LLM 调用、回复符合业务语义、执行类型正确、动作及参数正确、没有裸报文泄漏。
7. 增加一个带现有 `current_intent` 的多轮测试，确保控制型补充语句不会错误重建或重启完整语义程序。
8. 若修改 ESP32 命令链，增加 mapper、MCP/Controller、ACK 状态合并和完成条件测试；若修改岭阳协议，增加带来源说明的黄金报文测试。
9. 运行与风险匹配的验证。岭阳编解码或适配层变化至少运行 Mac 主机协议测试、Controller 测试和 ESP-IDF 5.5.2 构建。
10. 真实硬件尚未验证时明确标记“待真板复核”，不得把主机测试写成真实 UART 联调成功。

# 输出要求

- 直接修改主线代码和测试，不创建第二套按摩助手、HTTP 跳转或旁路执行链。
- 说明问题的首次断点以及为什么会产生原错误回复；不要只罗列改动文件。
- 列出每条训练原句的期望回复、语义动作和关键参数；相对控制同时说明状态基准。
- 对新增动作说明完整映射：`DeviceCommand -> massage.* -> self.massage.* -> MassageCommandName -> BoardAdapter`。
- 报告实际运行的测试名称、数量和结果；构建失败时给出真实阻塞原因，不能声称通过。
- 若使用历史协议资料，明确引用为历史来源，并列出仍需真板确认的功能码、ACK 或状态语义。
- 不把“能正确回复”当成“设备已执行”；最终回复必须与 `accepted/sent/acknowledged/completed/failed/timeout` 状态一致。

# 成功标准

- 用户提供的所有原始表达均稳定进入同一个正确业务意图，不依赖随机 LLM 输出。
- 不再出现因语义动作、能力声明、mapper 或 MCP 缺口导致的错误“不支持”回复。
- 生成的执行计划只有稳定的 `massage.*` 动作和版本化语义程序，没有岭阳功能码或 UART 原始字节。
- 相对参数基于最新正确状态计算；未知、过期、越界和上限场景有明确且安全的行为。
- 服务端、ESP32 和岭阳适配层职责没有越界，`request_id` 与执行结果链路保持可关联。
- 单轮原句、多轮上下文、mapper、Controller、ACK/状态合并均有回归覆盖。
- 所有相关自动化测试通过；涉及岭阳协议时 Mac 主机测试和 ESP-IDF 5.5.2 构建通过。
- 未经真实硬件验证的协议结论被明确标记，未虚报已烧录、已发 UART 或已完成真板联调。
