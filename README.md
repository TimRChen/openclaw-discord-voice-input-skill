# OpenClaw Discord Voice Input Skill

[English](./README.md) | [简体中文](./README.zh-CN.md)

![Local STT](https://img.shields.io/badge/local-STT-2da44e?style=flat-square)
![No Paid API](https://img.shields.io/badge/no%20paid-API-0969da?style=flat-square)
![skill-vetter reviewed](https://img.shields.io/badge/skill--vetter-reviewed-8250df?style=flat-square)
![quick validate passed](https://img.shields.io/badge/quick__validate-passed-1a7f37?style=flat-square)
![install smoke tested](https://img.shields.io/badge/install-smoke--tested-f0883e?style=flat-square)

Built for one very practical reason: if you use OpenClaw through Discord, typing every prompt gets old fast.

This skill fixes that. Send your OpenClaw bot a private voice message on Discord, transcribe it locally with `faster-whisper`, and pass the transcript straight into OpenClaw.

Most of the annoying setup pitfalls have already been worked through, and the repository has been reviewed with `skill-vetter`, validated as a proper skill, and smoke-tested against a temporary OpenClaw home.

This repository is also a valid OpenClaw skill repository. [`SKILL.md`](./SKILL.md) is the skill entrypoint, and the repository root is the skill root.

## Why This Skill

If your goal is simply "I want to talk to OpenClaw in Discord instead of typing all the time", this is the lightweight way to do it:

- Send the bot a voice message in a Discord private chat
- Transcribe it locally
- Feed the transcript into OpenClaw
- Get the reply back in the same chat

No voice channel plumbing. No paid speech API. No need to re-discover the same setup issues from scratch.

## What It Does

- Receives private voice messages sent to your Discord bot
- Becomes the single DM ingress path for Discord private chats, so voice and text do not split into separate sessions
- Transcribes audio locally with `faster-whisper`
- Forwards the transcript into OpenClaw
- Deploys a macOS `launchd` service for the voice bridge
- Adds `oc-voice-*` shell aliases for lifecycle management
- Disables OpenClaw's native audio attachment preflight to avoid racing the bridge
- Disables native Discord DM intake so raw voice attachments do not create duplicate sessions

## Trust Signals

- `skill-vetter reviewed`: checked for obvious red flags, excessive scope, and suspicious install behavior
- `quick_validate passed`: the repository validates cleanly as an OpenClaw skill
- `install smoke-tested`: the installer was run against a temporary OpenClaw home to verify file generation, config patching, and launchd setup

These badges mean the repository was reviewed and smoke-tested. They do not mean this is an official OpenClaw release, or that it is guaranteed to behave the same way on every machine.

## Repository Layout

```text
SKILL.md
agents/openai.yaml
scripts/install.py
assets/runtime/discord-dm-voice/
README.md
README.zh-CN.md
```

## Install

```bash
python3 scripts/install.py --openclaw-home ~/.openclaw
```

Optional flags:

- `--python /abs/path/to/python3`
- `--model base`
- `--language zh`
- `--skip-python-install`
- `--skip-npm-install`
- `--skip-deploy`

## Validate

```bash
oc-voice-status
oc-voice-logs
```

Then send a fresh voice message to the bot in a Discord private chat.

## Notes

- Target platform: macOS with `launchd`
- Scope: private voice messages sent to a Discord bot
- Assumption: Discord is already configured in `~/.openclaw/openclaw.json`
- Positioning: community skill, not an official OpenClaw release
