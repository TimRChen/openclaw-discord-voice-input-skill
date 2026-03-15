---
name: openclaw-discord-voice-input-skill
description: Install and maintain a free Discord DM voice-input bridge for an existing OpenClaw home. Use when a user wants Discord private voice messages transcribed locally with faster-whisper and forwarded into OpenClaw without paid APIs, especially on macOS launchd-based setups.
---

# OpenClaw Discord DM Voice

Install the voice bridge by running `scripts/install.py`. Prefer the script over manual patching because it copies the runtime assets, patches `openclaw.json`, installs dependencies, renders the LaunchAgent plist, and deploys the service consistently.

## Quick Start

Run:

```bash
python3 scripts/install.py --openclaw-home ~/.openclaw
```

Use these flags when needed:

- `--python /abs/path/to/python3` to pin the Python interpreter used by `faster-whisper`
- `--model base` to set the default transcription model in the LaunchAgent
- `--language zh` to set the default language hint
- `--skip-deploy` to install files without starting the LaunchAgent
- `--skip-python-install` to skip `pip install --user faster-whisper`

## What The Installer Does

- Copy `assets/runtime/discord-dm-voice/*` into `<openclaw-home>/runtime/discord-dm-voice`
- Install Node dependencies from the bundled `package-lock.json`
- Install `faster-whisper` for the selected Python interpreter unless skipped
- Set `tools.media.audio.enabled=false` in `openclaw.json` so OpenClaw does not race the bridge with its native audio preflight
- Add `oc-voice-start`, `oc-voice-restart`, `oc-voice-stop`, `oc-voice-status`, and `oc-voice-logs` to `runtime/agent-safehouse/openclaw-aliases.zsh` when that file exists
- Render and deploy `ai.openclaw.discord-dm-voice.plist`

## Assumptions

- The target OpenClaw home already exists.
- Discord is already configured in `openclaw.json`, including bot token and allowlists.
- The goal is Discord DM voice messages, not voice channels or server audio.
- The host is macOS with `launchd`.

## Validate After Install

Run:

```bash
oc-voice-status
oc-voice-logs
```

Then send a fresh voice message to the bot in Discord DM. If the user still sees OpenClaw's old "`whisper` not in PATH" reply, re-check `openclaw.json` and confirm `tools.media.audio.enabled` is `false`.

## Assets

- `assets/runtime/discord-dm-voice/voice-bridge.mjs`: Discord DM bridge
- `assets/runtime/discord-dm-voice/transcribe_with_faster_whisper.py`: local transcription entrypoint
- `assets/runtime/discord-dm-voice/*.template`: rendered at install time with user-specific absolute paths
- `scripts/install.py`: canonical installer and updater
