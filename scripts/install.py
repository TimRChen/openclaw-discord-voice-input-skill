#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
ASSET_DIR = SKILL_DIR / "assets" / "runtime" / "discord-dm-voice"
VOICE_BLOCK_START = "# >>> openclaw-discord-dm-voice >>>"
VOICE_BLOCK_END = "# <<< openclaw-discord-dm-voice <<<"
MIN_NODE = (22, 16, 0)


def parse_args():
    parser = argparse.ArgumentParser(description="Install the OpenClaw Discord DM voice bridge")
    parser.add_argument("--openclaw-home", default=str(Path.home() / ".openclaw"))
    parser.add_argument("--python", dest="python_bin", default=shutil.which("python3") or sys.executable)
    parser.add_argument("--model", default="base")
    parser.add_argument("--language", default="zh")
    parser.add_argument("--skip-python-install", action="store_true")
    parser.add_argument("--skip-npm-install", action="store_true")
    parser.add_argument("--skip-deploy", action="store_true")
    return parser.parse_args()


def run(cmd, *, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def render_template(template_path: Path, dest_path: Path, replacements: dict[str, str]) -> None:
    content = template_path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        content = content.replace(key, value)
    dest_path.write_text(content, encoding="utf-8")


def patch_openclaw_json(config_path: Path) -> None:
    data = json.loads(config_path.read_text(encoding="utf-8"))
    tools = data.setdefault("tools", {})
    media = tools.setdefault("media", {})
    audio = media.setdefault("audio", {})
    audio["enabled"] = False
    channels = data.setdefault("channels", {})
    discord = channels.setdefault("discord", {})
    dm = discord.setdefault("dm", {})
    dm["enabled"] = False
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def voice_alias_block() -> str:
    return f"""{VOICE_BLOCK_START}
OPENCLAW_HOME="${{OPENCLAW_HOME:-$HOME/.openclaw}}"
OPENCLAW_VOICE_LABEL="gui/$(id -u)/ai.openclaw.discord-dm-voice"

oc-voice-start() {{
  "$OPENCLAW_HOME/runtime/discord-dm-voice/deploy-launchagent.sh"
}}

oc-voice-restart() {{
  launchctl kickstart -k "$OPENCLAW_VOICE_LABEL"
}}

oc-voice-stop() {{
  launchctl bootout "$OPENCLAW_VOICE_LABEL" 2>/dev/null || true
}}

oc-voice-status() {{
  launchctl print "$OPENCLAW_VOICE_LABEL" | sed -n '1,60p'
}}

oc-voice-logs() {{
  tail -n 50 -f \\
    "$OPENCLAW_HOME/logs/discord-dm-voice.log" \\
    "$OPENCLAW_HOME/logs/discord-dm-voice.err.log"
}}
{VOICE_BLOCK_END}
"""


def patch_alias_file(alias_path: Path) -> None:
    alias_path.parent.mkdir(parents=True, exist_ok=True)
    current = alias_path.read_text(encoding="utf-8") if alias_path.exists() else ""
    if VOICE_BLOCK_START in current and VOICE_BLOCK_END in current:
        return
    block = voice_alias_block()
    updated = current.rstrip() + ("\n\n" if current.strip() else "") + block + "\n"
    alias_path.write_text(updated, encoding="utf-8")


def copy_runtime_assets(target_runtime: Path) -> None:
    target_runtime.mkdir(parents=True, exist_ok=True)
    for name in ["voice-bridge.mjs", "transcribe_with_faster_whisper.py", "package.json", "package-lock.json"]:
        shutil.copy2(ASSET_DIR / name, target_runtime / name)
    (target_runtime / "transcribe_with_faster_whisper.py").chmod(0o755)


def ensure_python_dependency(python_bin: str) -> None:
    run([python_bin, "-m", "pip", "install", "--user", "faster-whisper"])
    run([python_bin, "-c", "from faster_whisper import WhisperModel; print('faster-whisper ok')"])


def install_node_deps(target_runtime: Path) -> None:
    run(["npm", "install", "--omit=dev"], cwd=target_runtime)


def parse_node_version(raw: str) -> tuple[int, int, int]:
    value = raw.strip().lstrip("v")
    major, minor, patch = (value.split(".") + ["0", "0"])[:3]
    return int(major), int(minor), int(patch)


def is_supported_node(version: tuple[int, int, int]) -> bool:
    return version >= MIN_NODE


def discover_node_bin(home_dir: Path) -> str:
    nvm_root = home_dir / ".nvm" / "versions" / "node"
    if nvm_root.is_dir():
        candidates = sorted(
            nvm_root.glob("*/bin/node"),
            key=lambda candidate: parse_node_version(candidate.parent.parent.name),
            reverse=True,
        )
        for candidate in candidates:
            if candidate.is_file():
                version = parse_node_version(candidate.parent.parent.name)
                if is_supported_node(version):
                    return str(candidate)
    direct = shutil.which("node")
    if direct:
        version_output = subprocess.run([direct, "-v"], check=True, capture_output=True, text=True).stdout.strip()
        if is_supported_node(parse_node_version(version_output)):
            return direct
    raise FileNotFoundError("Could not find a usable node binary >= 22.16.0. Install Node 22.16+ and retry.")


def main() -> int:
    args = parse_args()
    openclaw_home = Path(args.openclaw_home).expanduser().resolve()
    config_path = openclaw_home / "openclaw.json"
    if not config_path.is_file():
        raise FileNotFoundError(f"OpenClaw config not found: {config_path}")

    home_dir = Path.home().resolve()
    node_bin = discover_node_bin(home_dir)
    target_runtime = openclaw_home / "runtime" / "discord-dm-voice"
    logs_dir = openclaw_home / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    copy_runtime_assets(target_runtime)

    replacements = {
        "__HOME__": str(home_dir),
        "__OPENCLAW_HOME__": str(openclaw_home),
        "__TMPDIR__": os.environ.get("TMPDIR", "/tmp/"),
        "__OPENCLAW_NODE__": node_bin,
        "__OPENCLAW_VOICE_MODEL__": args.model,
        "__OPENCLAW_VOICE_LANGUAGE__": args.language,
        "__OPENCLAW_VOICE_PYTHON__": args.python_bin,
    }

    render_template(
        ASSET_DIR / "ai.openclaw.discord-dm-voice.plist.template",
        target_runtime / "ai.openclaw.discord-dm-voice.plist",
        replacements,
    )
    render_template(
        ASSET_DIR / "deploy-launchagent.sh.template",
        target_runtime / "deploy-launchagent.sh",
        replacements,
    )
    (target_runtime / "deploy-launchagent.sh").chmod(0o755)

    patch_openclaw_json(config_path)

    alias_path = openclaw_home / "runtime" / "agent-safehouse" / "openclaw-aliases.zsh"
    patch_alias_file(alias_path)

    if not args.skip_python_install:
        ensure_python_dependency(args.python_bin)

    if not args.skip_npm_install:
        install_node_deps(target_runtime)

    if not args.skip_deploy:
        run([str(target_runtime / "deploy-launchagent.sh")])

    print(f"Installed Discord DM voice bridge into {target_runtime}")
    print(f"Patched config: {config_path}")
    print(f"Alias file: {alias_path}")
    if args.skip_deploy:
        print("Deployment skipped. Run runtime/discord-dm-voice/deploy-launchagent.sh manually when ready.")
    else:
        print("Deployment complete. Use oc-voice-status and oc-voice-logs to verify.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"install failed: {exc}", file=sys.stderr)
        raise
