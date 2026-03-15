# OpenClaw Discord 语音输入 Skill

[English](./README.md) | [简体中文](./README.zh-CN.md)

![本地转写](https://img.shields.io/badge/local-STT-2da44e?style=flat-square)
![无付费 API](https://img.shields.io/badge/no%20paid-API-0969da?style=flat-square)
![skill-vetter 已审查](https://img.shields.io/badge/skill--vetter-reviewed-8250df?style=flat-square)
![quick_validate 通过](https://img.shields.io/badge/quick__validate-passed-1a7f37?style=flat-square)
![安装冒烟验证](https://img.shields.io/badge/install-smoke--tested-f0883e?style=flat-square)

这个 skill 就是为了解决一个很实际的问题：如果你平时通过 Discord 跟 OpenClaw 交互，老是打字很快就烦了。

装上它之后，你只要在 Discord 私聊窗口里给 OpenClaw bot 发语音，它会在本地用 `faster-whisper` 转成文字，再把文本交给 OpenClaw。

常见的坑我已经提前踩过一轮了，这个仓库也做过 `skill-vetter` 审查、skill 结构校验和安装冒烟验证。

这个仓库本身也是一个合法的 OpenClaw skill 仓库。[`SKILL.md`](./SKILL.md) 是 skill 入口文件，仓库根目录本身就是 skill 根目录。

## 为什么用这套

如果你的目标很简单，就是“我想在 Discord 里跟 OpenClaw 说话，不想一直打字”，那这套就是更省事的做法：

- 在 Discord 私聊窗口里给 bot 发语音
- 本地完成转写
- 把文本交给 OpenClaw
- 在同一个聊天里拿到回复

不用折腾语音频道实时收流，也不用接付费语音 API，更不用把那些安装坑再踩一遍。

## 它会做什么

- 接收发给 Discord bot 的私聊语音消息
- 用本地 `faster-whisper` 转写音频
- 将转写文本转交给 OpenClaw
- 部署一个用于语音桥接的 macOS `launchd` 服务
- 增加 `oc-voice-*` 系列 shell alias 方便管理
- 关闭 OpenClaw 原生的音频附件预处理，避免与桥接流程抢占处理

## 可信信号

- `skill-vetter reviewed`：按 skill-vetter 的思路检查过明显红旗、过宽权限和可疑安装行为
- `quick_validate passed`：仓库结构已通过 OpenClaw skill 校验
- `install smoke-tested`：安装脚本已经在临时 OpenClaw 目录里跑过，确认会正确生成文件、修改配置并产出 launchd 所需文件

这些标识表示“做过审查，也做过冒烟验证”，不表示“这是官方 OpenClaw 发布物”，也不表示“在所有机器上都会完全一样地工作”。

## 仓库结构

```text
SKILL.md
agents/openai.yaml
scripts/install.py
assets/runtime/discord-dm-voice/
README.md
README.zh-CN.md
```

## 安装

```bash
python3 scripts/install.py --openclaw-home ~/.openclaw
```

可选参数：

- `--python /绝对路径/python3`
- `--model base`
- `--language zh`
- `--skip-python-install`
- `--skip-npm-install`
- `--skip-deploy`

## 验证

```bash
oc-voice-status
oc-voice-logs
```

然后在 Discord 私聊窗口里给 bot 发一条新的语音消息。

## 说明

- 目标平台：macOS + `launchd`
- 适用范围：发给 Discord bot 的私聊语音消息
- 前提假设：`~/.openclaw/openclaw.json` 里已经配置好 Discord
- 定位：社区 skill，不是官方 OpenClaw 发布物
