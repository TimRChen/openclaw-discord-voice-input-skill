import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { Client, GatewayIntentBits, MessageFlags, Partials } from "discord.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = process.env.OPENCLAW_HOME || path.join(os.homedir(), ".openclaw");
const CONFIG_PATH = process.env.OPENCLAW_CONFIG_PATH || path.join(ROOT, "openclaw.json");
const STATE_DIR = path.join(ROOT, "runtime", "discord-dm-voice", "state");
const TMP_DIR = path.join(ROOT, "runtime", "discord-dm-voice", "tmp");
const MODEL_DIR = path.join(ROOT, "runtime", "discord-dm-voice", "models");
const TRANSCRIBE_SCRIPT = path.join(__dirname, "transcribe_with_faster_whisper.py");
const DEFAULT_LANGUAGE = process.env.OPENCLAW_VOICE_LANGUAGE || "zh";
const DEFAULT_MODEL = process.env.OPENCLAW_VOICE_MODEL || "base";
const PYTHON_BIN = process.env.OPENCLAW_VOICE_PYTHON || "python3";
const OPENCLAW_ENTRYPOINT = path.join(process.execPath, "..", "..", "lib", "node_modules", "openclaw", "dist", "index.js");
const CHILD_PROCESS_ENV = {
  KMP_DUPLICATE_LIB_OK: process.env.KMP_DUPLICATE_LIB_OK || "TRUE",
  OMP_NUM_THREADS: process.env.OMP_NUM_THREADS || "1",
  HF_HUB_DISABLE_TELEMETRY: process.env.HF_HUB_DISABLE_TELEMETRY || "1",
  TOKENIZERS_PARALLELISM: process.env.TOKENIZERS_PARALLELISM || "false",
};

const processing = new Set();

function normalizeDiscordUserId(value) {
  return String(value || "")
    .trim()
    .replace(/^<@!?/, "")
    .replace(/>$/, "")
    .replace(/^discord:/i, "")
    .replace(/^user:/i, "")
    .trim();
}

async function ensureDirs() {
  await fs.mkdir(STATE_DIR, { recursive: true });
  await fs.mkdir(TMP_DIR, { recursive: true });
  await fs.mkdir(MODEL_DIR, { recursive: true });
}

async function loadConfig() {
  const raw = await fs.readFile(CONFIG_PATH, "utf8");
  return JSON.parse(raw);
}

function getDiscordToken(config) {
  return process.env.DISCORD_BOT_TOKEN || config?.channels?.discord?.token || "";
}

function getAllowedUsers(config) {
  const list = Array.isArray(config?.channels?.discord?.allowFrom) ? config.channels.discord.allowFrom : [];
  return new Set(list.map(normalizeDiscordUserId).filter(Boolean));
}

function isAudioAttachment(attachment) {
  const contentType = String(attachment.contentType || "").toLowerCase();
  const name = String(attachment.name || "").toLowerCase();
  return (
    contentType.startsWith("audio/") ||
    name.endsWith(".ogg") ||
    name.endsWith(".oga") ||
    name.endsWith(".opus") ||
    name.endsWith(".mp3") ||
    name.endsWith(".m4a") ||
    name.endsWith(".wav") ||
    name.endsWith(".mp4")
  );
}

function isVoiceInputMessage(message) {
  return Boolean(message.flags?.has(MessageFlags.IsVoiceMessage)) || [...message.attachments.values()].some(isAudioAttachment);
}

async function downloadAttachment(attachment, messageId) {
  const url = attachment.url;
  const ext = path.extname(attachment.name || "") || ".ogg";
  const targetPath = path.join(TMP_DIR, `${messageId}${ext}`);
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to download attachment: HTTP ${response.status}`);
  }
  const arrayBuffer = await response.arrayBuffer();
  await fs.writeFile(targetPath, Buffer.from(arrayBuffer));
  return targetPath;
}

function runProcess(command, args, extraEnv = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: ROOT,
      env: {
        ...process.env,
        ...CHILD_PROCESS_ENV,
        OPENCLAW_HOME: ROOT,
        OPENCLAW_VOICE_MODEL_DIR: MODEL_DIR,
        ...extraEnv,
      },
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) {
        resolve({ stdout, stderr });
        return;
      }
      reject(new Error(stderr.trim() || stdout.trim() || `${command} exited with code ${code}`));
    });
  });
}

async function transcribeAudio(inputPath) {
  const { stdout } = await runProcess(PYTHON_BIN, [
    TRANSCRIBE_SCRIPT,
    "--input",
    inputPath,
    "--model",
    DEFAULT_MODEL,
    "--language",
    DEFAULT_LANGUAGE,
  ]);
  const parsed = JSON.parse(stdout);
  return String(parsed.text || "").trim();
}

async function runOpenClawAgent(userId, transcript) {
  const prompt = `[Voice message transcript]\n${transcript}`;
  await runProcess(process.execPath, [
    OPENCLAW_ENTRYPOINT,
    "agent",
    "--channel",
    "discord",
    "--to",
    `user:${userId}`,
    "--message",
    prompt,
    "--deliver",
  ]);
}

async function handleVoiceMessage(message, allowedUsers) {
  if (message.author.bot) return;
  if (message.guildId) return;
  if (allowedUsers.size > 0 && !allowedUsers.has(normalizeDiscordUserId(message.author.id))) return;
  if (!isVoiceInputMessage(message)) return;
  if (processing.has(message.id)) return;

  processing.add(message.id);
  let localPath;
  try {
    await message.channel.sendTyping();
    try {
      await message.react("🎙️");
    } catch {}

    const attachment = [...message.attachments.values()].find(isAudioAttachment);
    if (!attachment) throw new Error("No supported audio attachment found.");

    localPath = await downloadAttachment(attachment, message.id);
    const transcript = await transcribeAudio(localPath);
    if (!transcript) {
      await message.reply("这条语音我没转出有效文字。可以再发一条更清晰一点的语音。");
      return;
    }

    await runOpenClawAgent(message.author.id, transcript);
    try {
      await message.react("✅");
    } catch {}
  } catch (error) {
    console.error(`[voice-bridge] ${message.id}: ${String(error)}`);
    try {
      await message.reply(`语音转写失败：${String(error)}`);
    } catch {}
  } finally {
    processing.delete(message.id);
    if (localPath) {
      await fs.rm(localPath, { force: true }).catch(() => {});
    }
  }
}

async function main() {
  await ensureDirs();
  const config = await loadConfig();
  const token = getDiscordToken(config);
  if (!token) throw new Error("Discord bot token not configured.");
  const allowedUsers = getAllowedUsers(config);

  const client = new Client({
    intents: [GatewayIntentBits.DirectMessages, GatewayIntentBits.MessageContent],
    partials: [Partials.Channel],
  });

  client.once("clientReady", () => {
    console.log(`[voice-bridge] ready as ${client.user?.tag || client.user?.id}`);
  });

  client.on("messageCreate", async (message) => {
    await handleVoiceMessage(message, allowedUsers);
  });

  client.on("error", (error) => {
    console.error(`[voice-bridge] client error: ${String(error)}`);
  });

  await client.login(token);
}

main().catch((error) => {
  console.error(`[voice-bridge] fatal: ${String(error)}`);
  process.exit(1);
});
