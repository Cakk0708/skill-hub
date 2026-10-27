---
name: ai-massage-protocol-ci1302
description: |
  涉及到“ci1302”协议部分时触发
  分析 CI1302 UART 协议，解析十六进制帧、日志中的 RX/TX 报文、功能码、键值。
---


## 协议文档

- **接收协议表**: 
  - path: `references/rx-commands.md`
  - description: 接收协议指令表，用于 esp32 端 rx 口被动接收 ci1302 指令清单。
- **发送协议表**: 
  - path: `references/tx-commands.md`
  - description: 发送协议指令表，用于 esp32 端 tx 口主动向 ci1302 发去指令清单。
- **网络流媒体播放交互时序**: 
  - path: `references/streaming-playback-sequence.md`
  - description: 用于澄清 esp32 与 ci1302 音频播放交互关系。

## 功能介绍

CI1302 与 ESP32 通过 UART1 沟通以实现离线指令命中、在线人声 PCM 对话

### 离线

ESP32 未能连接 WIFI 网络时使用离线对话指令音频

ESP32 处于离线模式时，通过 CI1302 UART1 TX 发送 `A5 A5 5A 5A 00 00 10 04 01 00 00 01 78 56 34 12 00`（消息类型 `0x0410`，负载 `0`）告知 CI1302 当前网络不可用。该通知在启动时发送、CI1302 报告就绪后重新同步，并在联网状态变化时更新。

离线模式词条命中后

### 在线

ESP32 成功连接 WIFI 后使用完整对话录音投送 PCM 音频内容的在线逻辑

ESP32 处于在线模式时，通过 CI1302 UART1 TX 发送 `A5 A5 5A 5A 01 00 10 04 01 00 00 01 78 56 34 12 01`（消息类型 `0x0410`，负载 `1`）告知 CI1302 当前网络可用。

### 答复音频

#### 在线

### 离线

离线音频的答复句必须遵循协议文档列“播报语句”内容使用`firmware/esp32-s3/boards/l01-iot-ci1302/assets/`下的合适音频做答复


### `rx-commands`文档列介绍：

- **code**: 定义语意序号
- **command**: ci1302 发来的命中命令
- **content**: 被 CI1302 唤醒的命令词
- **reply text**: CI1302 命令词命中后答复语句，一般用于 ESP32 发送岭阳按摩主板按摩指令 UART0 RX 响应成功后将储存对应答复音频提取后转发给 CI1302 实现播放音频形成播报语句
- **send command**: 对应命令最终产生的岭阳主板指令参考。ESP32 必须先将 CI1302 命中映射为语义动作并交给 `MassageController`，再由 `BoardAdapter` 编码；接收层不得原样直发此字段中的裸帧。

