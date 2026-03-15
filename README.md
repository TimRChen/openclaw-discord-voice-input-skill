# OpenClaw Discord DM Voice Skill

[English](./README.md) | [简体中文](./README.zh-CN.md)

![Local STT](https://img.shields.io/badge/local-STT-2da44e?style=flat-square)
![No Paid API](https://img.shields.io/badge/no%20paid-API-0969da?style=flat-square)
![skill-vetter reviewed](https://img.shields.io/badge/skill--vetter-reviewed-8250df?style=flat-square)
![quick validate passed](https://img.shields.io/badge/quick__validate-passed-1a7f37?style=flat-square)
![install smoke tested](https://img.shields.io/badge/install-smoke--tested-f0883e?style=flat-square)

Add voice input to OpenClaw through Discord DMs, using local `faster-whisper` transcription and no paid speech API.

This repository is also a valid OpenClaw skill repository. [`SKILL.md`](./SKILL.md) is the skill entrypoint, and the repository root is the skill root.

## Why This Skill

If you want voice input without building a full live-audio stack, this skill takes the simpler route:

- DM the bot a Discord voice message
- Transcribe it locally
- Feed the transcript into OpenClaw
- Get the reply back in the same chat

It is easier to install, cheaper to run, and much easier to keep stable over time.

## What It Does

- Receives Discord private voice messages
- Transcribes audio locally with `faster-whisper`
- Forwards the transcript into OpenClaw
- Deploys a macOS `launchd` service for the voice bridge
- Adds `oc-voice-*` shell aliases for lifecycle management
- Disables OpenClaw's native audio attachment preflight to avoid racing the bridge

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

Then send a fresh voice message to the bot in a Discord DM.

## Notes

- Target platform: macOS with `launchd`
- Scope: Discord DM voice messages only
- Assumption: Discord is already configured in `~/.openclaw/openclaw.json`
- Positioning: community skill, not an official OpenClaw release
