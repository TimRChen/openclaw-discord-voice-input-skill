# OpenClaw Discord DM Voice Skill

This repository packages a reusable OpenClaw skill for adding **Discord DM voice input** with **local `faster-whisper` transcription**.

The actual skill lives in [`openclaw-discord-dm-voice/`](./openclaw-discord-dm-voice).

## What It Installs

- A Discord DM voice bridge for OpenClaw
- Local `faster-whisper` transcription
- A macOS `launchd` service for the bridge
- `oc-voice-*` shell aliases
- An `openclaw.json` patch that disables OpenClaw's native audio attachment preflight to avoid racing the bridge

## Skill Layout

```text
openclaw-discord-dm-voice/
├── SKILL.md
├── agents/openai.yaml
├── scripts/install.py
└── assets/runtime/discord-dm-voice/
```

## Install Into An Existing OpenClaw Home

```bash
python3 openclaw-discord-dm-voice/scripts/install.py --openclaw-home ~/.openclaw
```

Optional flags:

- `--python /abs/path/to/python3`
- `--model base`
- `--language zh`
- `--skip-python-install`
- `--skip-npm-install`
- `--skip-deploy`

## Validate

After installation:

```bash
oc-voice-status
oc-voice-logs
```

Then send a fresh voice message to the bot in a Discord DM.

## Notes

- Target platform: macOS with `launchd`
- Scope: Discord private voice messages only
- Assumption: Discord is already configured in `~/.openclaw/openclaw.json`
