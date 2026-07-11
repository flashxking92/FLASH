"""
🎵 ᴀᴜᴅɪᴏ ꜰᴏʀᴡᴀʀᴅᴇʀ ʙᴏᴛ - ᴄᴏᴍᴘʟᴇᴛᴇ ꜰɪxᴇᴅ ᴠᴇʀꜱɪᴏɴ
ᴡɪᴛʜ ꜰᴜʟʟ ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ ᴀɴᴅ ᴘʀᴏᴘᴇʀ ᴇʀʀᴏʀ ʜᴀɴᴅʟɪɴɢ
ᴏɴʟʏ ᴏᴡɴᴇʀ ᴀɴᴅ ᴀᴘᴘʀᴏᴠᴇᴅ ᴜꜱᴇʀꜱ ᴄᴀɴ ᴜꜱᴇ ᴄᴏᴍᴍᴀɴᴅꜱ
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
import numpy as np
import os
import re
from typing import Optional, Tuple, Dict
import json
import logging
import asyncio
import warnings
import time
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Try to import scipy, fallback to basic processing if not available
try:
    from scipy import signal
    SCIPY_AVAILABLE = True
except Exception:
    SCIPY_AVAILABLE = False
    print("⚠️ ꜱᴄɪᴘʏ ʟᴏᴀᴅ ꜰᴀɪʟᴇᴅ - ʙᴀꜱɪᴄ ᴀᴜᴅɪᴏ ᴘʀᴏᴄᴇꜱꜱɪɴɢ ᴏɴʟʏ")

from pyrogram import Client, filters as pyro_filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode, ChatType
from pyrogram.errors import PeerIdInvalid

from pytgcalls import PyTgCalls, idle
from pytgcalls import filters as pytg_filters
from pytgcalls.types import (
    Device,
    Direction,
    ExternalMedia,
    MediaStream,
    RecordStream,
    StreamFrames
)
from pytgcalls.types.raw import AudioParameters
from pytgcalls.exceptions import NoActiveGroupCall

# ==================== ᴄᴏɴꜰɪɢᴜʀᴀᴛɪᴏɴ ====================
# ⚠️ Credentials hardcoded directly (no environment variables).
# Keep this file PRIVATE — anyone with it can control your bot & account.
API_ID = 29177322
API_HASH = "1b8573accde3d0b7c35e43cdbb36e523"
BOT_TOKEN = "8554005804:AAGjW8m_T6e9SrWmzXmLechUKYgANbz-IDs"
OWNER_ID = 8305984975
STRING_SESSION = "BQG9NeoAKgnwMUVxrdLuZqchTSFQaiKJpPuSYhmG29j15hA7BHwFt5-BlIbFOhO4aY6NHKSgdeqp6FmGtIk0_6Aao11efgSUBx23sbDiFj-1Wq2YyZnnUteWe7ao5tienj13NGwYnrxb3pbQpFMeQFwGhtfUzXbVTgiVT4KD3xks7bFfeA_bpkuM50WEs_4yB9KFzsLQZ99oirkxmUXe8r9DDiXKvpkppPKO50Np6gArSQ_MUI7f5sxW9RMNl6YwJYfI837hkPIjFL9ZkgqG2KXV-wCai93e5bR2K_zPS6vh6rZ8RCv_mfjtjaf0hDpsx4Eh7FDgWmWk2VNGcGUdz3ODozAE4QAAAAIJm0jrAA"
RECORD_GROUP = -1003970175858
# ======================================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Disable noisy logs
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("pytgcalls").setLevel(logging.WARNING)

AUDIO_PARAMETERS = AudioParameters(bitrate=48000, channels=2)

# ==================== ᴄʟɪᴇɴᴛꜱ ====================
bot_app = Client("bot_session_v5", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_app = Client("user_session_v5", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
call_py = PyTgCalls(user_app)

# ꜱᴛᴀᴛᴇ
forward_chats = set()
is_muted = False
is_recording = False
RECORD_SOURCE = RECORD_GROUP
processing_lock = asyncio.Lock()
bot_start_time = time.time()

# ᴜꜱᴇʀ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ
approved_users = set()

# ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ ᴄᴏɴꜰɪɢᴜʀᴀᴛɪᴏɴ
audio_config = {
    'volume': 100,
    'bass': 0,
    'treble': 0,
    'gain': 0,
    'compressor': True,
    'limiter': True,
    'highpass': False,
    'lowpass': False
}

# ===== ᴀᴅᴠᴀɴᴄᴇᴅ ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ ᴄᴏɴꜰɪɢ =====
ADVANCED_AUDIO_CONFIG = {
    'ns': 0,           # Noise Suppression (-50 to +50)
    'hpf': 0,          # High Pass Filter (-50 to +50)
    'deesser': 0,      # De-Esser (-50 to +50)
    'presence_eq': 0,  # Presence EQ (-50 to +50)
    'loudness': 0,     # Loudness Normalization (-50 to +50)
    'limiter': 0,      # Look-Ahead Limiter (-50 to +50)
    'noisegate': 0,    # Noise Gate (-50 to +50)
    'dc_offset': 0,    # DC Offset Removal (-50 to +50)
    'saturation': 0,   # Soft Saturation (-50 to +50)
    'stereo_width': 0, # Stereo Width (-50 to +50)
}
# ==================== ᴘᴇʀꜱɪꜱᴛᴇɴᴄᴇ ====================

# 📂 Persistent join request storage
PENDING_JOIN_FILE = "pending_joins.json"
PENDING_JOIN_REQUESTS: Dict[str, Dict] = {}
PENDING_JOIN_MONITORS: Dict[str, asyncio.Task] = {}

STATE_FILE = "bot_state.json"

def save_pending_joins():
    """Persist pending join requests to disk (atomic)."""
    try:
        tmp = f"{PENDING_JOIN_FILE}.tmp"
        with open(tmp, "w") as f:
            json.dump(PENDING_JOIN_REQUESTS, f, indent=2)
        os.replace(tmp, PENDING_JOIN_FILE)
    except Exception as e:
        logger.error(f"Failed to save pending joins: {e}")

def load_pending_joins():
    """Load pending join requests from disk."""
    try:
        with open(PENDING_JOIN_FILE, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            PENDING_JOIN_REQUESTS.update(data)
        logger.info(f"Loaded {len(PENDING_JOIN_REQUESTS)} pending join request(s)")
    except FileNotFoundError:
        logger.info("No pending joins found")
    except Exception as e:
        logger.error(f"Failed to load pending joins: {e}")

async def _run_join_monitor(client, status_msg, invite_hash, original_link, start_time):
    """Run the join monitor and clean up persisted state when done."""
    try:
        await monitor_join_approval(client, status_msg, invite_hash, original_link, start_time)
    finally:
        PENDING_JOIN_REQUESTS.pop(invite_hash, None)
        PENDING_JOIN_MONITORS.pop(invite_hash, None)
        save_pending_joins()

async def resume_pending_joins():
    """Resume monitors for any pending join requests after a restart."""
    if not PENDING_JOIN_REQUESTS:
        return
    for invite_hash, info in list(PENDING_JOIN_REQUESTS.items()):
        try:
            original_link = info.get("original_link", invite_hash)
            start_time = info.get("start_time", time.time())
            chat_id = info.get("chat_id")
            message_id = info.get("message_id")

            status_msg = None
            if chat_id is not None and message_id is not None:
                try:
                    status_msg = await bot_app.get_messages(chat_id, message_id)
                except Exception:
                    status_msg = None
            if status_msg is None and chat_id is not None:
                try:
                    status_msg = await bot_app.send_message(
                        chat_id,
                        f"🔄 Resuming join monitor... 🔗 {original_link}",
                    )
                    info["message_id"] = status_msg.id
                except Exception:
                    status_msg = None
            if status_msg is None:
                continue

            PENDING_JOIN_MONITORS[invite_hash] = asyncio.create_task(
                _run_join_monitor(bot_app, status_msg, invite_hash, original_link, start_time)
            )
        except Exception as e:
            logger.error(f"Failed to resume pending join {invite_hash}: {e}")
    save_pending_joins()


def save_state():
    """ᴘᴇʀꜱɪꜱᴛ ᴀᴘᴘʀᴏᴠᴇᴅ ᴜꜱᴇʀꜱ ᴀɴᴅ ᴀᴜᴅɪᴏ ᴄᴏɴꜰɪɢ ᴛᴏ ᴅɪꜱᴋ"""
    try:
        tmp = f"{STATE_FILE}.tmp"
        with open(tmp, "w") as f:
            json.dump({
                "approved_users": sorted(approved_users),
                "audio_config": audio_config,
                "advanced_audio_config": ADVANCED_AUDIO_CONFIG,  # 👈 ADDED
                "record_source": RECORD_SOURCE,
                "forward_chats": sorted(forward_chats),
            }, f, indent=2)
        os.replace(tmp, STATE_FILE)
    except Exception as e:
        logger.error(f"ꜰᴀɪʟᴇᴅ ᴛᴏ ꜱᴀᴠᴇ ꜱᴛᴀᴛᴇ: {e}")

def load_state():
    """ʟᴏᴀᴅ ᴘᴇʀꜱɪꜱᴛᴇᴅ ꜱᴛᴀᴛᴇ ɪꜰ ᴀᴠᴀɪʟᴀʙʟᴇ"""
    global RECORD_SOURCE  # audio_config is only mutated in place (.update()), no global needed
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
        approved_users.update(int(uid) for uid in data.get("approved_users", []))
        saved_config = data.get("audio_config")
        if isinstance(saved_config, dict):
            audio_config.update(saved_config)
        
        # 👇 ADD THIS - Load advanced audio config
        saved_advanced = data.get("advanced_audio_config")
        if isinstance(saved_advanced, dict):
            ADVANCED_AUDIO_CONFIG.update(saved_advanced)
        
        saved_source = data.get("record_source")
        if saved_source is not None:
            RECORD_SOURCE = saved_source

        saved_forwards = data.get("forward_chats")
        if isinstance(saved_forwards, list):
            forward_chats.update(int(cid) for cid in saved_forwards)
        logger.info(f"ʟᴏᴀᴅᴇᴅ ꜱᴛᴀᴛᴇ: {len(approved_users)} ᴀᴘᴘʀᴏᴠᴇᴅ ᴜꜱᴇʀ(ꜱ), ꜱᴏᴜʀᴄᴇ: {RECORD_SOURCE}")
    except FileNotFoundError:
        logger.info("ɴᴏ ꜱᴀᴠᴇᴅ ꜱᴛᴀᴛᴇ ꜰᴏᴜɴᴅ - ꜱᴛᴀʀᴛɪɴɢ ꜰʀᴇꜱʜ")
    except Exception as e:
        logger.error(f"ꜰᴀɪʟᴇᴅ ᴛᴏ ʟᴏᴀᴅ ꜱᴛᴀᴛᴇ: {e}")

# ==================== ᴀᴜᴛʜᴇɴᴛɪᴄᴀᴛɪᴏɴ ====================

async def _authorized_filter(_, __, message):
    """ᴄʜᴇᴄᴋ ɪꜰ ᴜꜱᴇʀ ɪꜱ ᴏᴡɴᴇʀ ᴏʀ ᴀᴘᴘʀᴏᴠᴇᴅ"""
    user_id = message.from_user.id if message.from_user else None
    if user_id == OWNER_ID or user_id in approved_users:
        return True
    logger.info(f"ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴀᴄᴄᴇꜱꜱ ꜰʀᴏᴍ {user_id} - ɪɢɴᴏʀᴇᴅ")
    return False

def authorized_only():
    """ʀᴇᴛᴜʀɴ ᴀ ᴘʏʀᴏɢʀᴀᴍ ꜰɪʟᴛᴇʀ ᴛʜᴀᴛ ᴀʟʟᴏᴡꜱ ᴏɴʟʏ ᴏᴡɴᴇʀ/ᴀᴘᴘʀᴏᴠᴇᴅ ᴜꜱᴇʀꜱ"""
    return pyro_filters.create(_authorized_filter)

# ==================== ᴜᴛɪʟɪᴛʏ ꜰᴜɴᴄᴛɪᴏɴꜱ ====================

def escape_markdown(text):
    """Escape characters special to Pyrogram's legacy Markdown parser."""
    if not text:
        return ""
    specials = "`*_["
    return "".join("\\" + c if c in specials else c for c in text)

def get_uptime():
    """ɢᴇᴛ ʙᴏᴛ ᴜᴘᴛɪᴍᴇ"""
    uptime_seconds = int(time.time() - bot_start_time)
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    if days > 0:
        return f"{days}ᴅ {hours}ʜ {minutes}ᴍ {seconds}ꜱ"
    elif hours > 0:
        return f"{hours}ʜ {minutes}ᴍ {seconds}ꜱ"
    elif minutes > 0:
        return f"{minutes}ᴍ {seconds}ꜱ"
    else:
        return f"{seconds}ꜱ"

def create_progress_bar(value, max_val, length=12):
    """ᴄʀᴇᴀᴛᴇ ᴀ ᴠɪꜱᴜᴀʟ ᴘʀᴏɢʀᴇꜱꜱ ʙᴀʀ"""
    if not max_val:
        max_val = 1
    filled = int((value / max_val) * length)
    return "█" * filled + "░" * (length - filled)

def get_effect_status(value, max_val):
    """ɢᴇᴛ ꜱᴛᴀᴛᴜꜱ ʙᴀꜱᴇᴅ ᴏɴ ᴠᴀʟᴜᴇ"""
    if not max_val:
        max_val = 1
    percentage = (value / max_val) * 100
    if percentage == 0:
        return "⚪ ᴏꜰꜰ"
    elif percentage <= 30:
        return "🟢 ʟɪɢʜᴛ"
    elif percentage <= 60:
        return "🟡 ᴍᴇᴅɪᴜᴍ"
    elif percentage <= 80:
        return "🟠 ꜱᴛʀᴏɴɢ"
    else:
        return "🔴 ᴇxᴛʀᴇᴍᴇ"


# ==================== ᴀᴜᴅɪᴏ ᴘʀᴏᴄᴇꜱꜱɪɴɢ ====================

def apply_volume_boost(audio_data, level):
    """ᴜʟᴛɪᴍᴀᴛᴇ ᴠᴏʟᴜᴍᴇ - ᴍᴀx ʟᴏᴜᴅɴᴇꜱꜱ ᴡɪᴛʜᴏᴜᴛ ᴄʟɪᴘᴘɪɴɢ"""
    if level == 100:
        return audio_data
    
    audio = audio_data.astype(np.float32)
    
    # ꜱᴍᴀʀᴛ ɢᴀɪɴ ᴍᴀᴘᴘɪɴɢ ꜰᴏʀ ᴍᴀx ʟᴏᴜᴅɴᴇꜱꜱ
    if level <= 100:
        gain_factor = 1.2 + ((level - 100) * 0.0010)
    else:
        gain_factor = 1.2 + ((level - 100) * 0.030)
    
    processed = audio * gain_factor
    
    # ᴀᴄᴛɪᴠᴇ ᴘᴇᴀᴋ ʟɪᴍɪᴛɪɴɢ
    peak = np.max(np.abs(processed))
    if peak > 32000:
        processed = (processed / peak) * 32000
    
    # ᴡᴀʀᴍ ꜱᴀᴛᴜʀᴀᴛɪᴏɴ ꜰᴏʀ ᴘᴜɴᴄʜ
    processed = 32500 * np.tanh(processed / 32500)
    
    return np.clip(processed, -32768, 32767).astype(np.int16)

def apply_bass_boost_basic(audio_data, bass_level):
    """ᴘʀᴏꜰᴇꜱꜱɪᴏɴᴀʟ ʙᴀꜱꜱ - ᴛɪɢʜᴛ, ᴘᴜɴᴄʜʏ, ɴᴏ ꜰᴀᴛ"""
    if bass_level <= 0:
        return audio_data
    
    audio = audio_data.astype(np.float32)
    
    # ᴛɪɢʜᴛ ʙᴀꜱꜱ ᴇxᴛʀᴀᴄᴛɪᴏɴ
    window_size = max(8, int(40 - bass_level * 0.3))
    kernel = np.ones(window_size, dtype=np.float32) / window_size
    low = np.convolve(audio, kernel, mode="same")
    
    # ᴄʟᴇᴀɴ ᴍɪx (ᴄᴏɴᴛʀᴏʟʟᴇᴅ ʙᴀꜱꜱ)
    mix = min(0.35, bass_level / 180.0)
    processed = audio + (low * mix * 1.1)
    
    # ʀᴇᴍᴏᴠᴇ ꜱᴜʙ-ʙᴀꜱꜱ ʀᴜᴍʙʟᴇ (ꜰᴀᴛ ᴋɪʟʟᴇʀ)
    if bass_level > 10:
        hp_kernel = np.array([-0.1, 0.8, -0.1])
        processed = np.convolve(processed, hp_kernel, mode="same")
    
    # ᴘᴜɴᴄʜʏ ᴄʟɪᴘᴘɪɴɢ
    processed = 31500.0 * np.tanh(processed / 31500.0)
    
    return np.clip(processed, -32768, 32767).astype(np.int16)

def apply_bass_boost_advanced(audio_data, bass_level, sample_rate=48000):
    """ᴘʀᴏꜰᴇꜱꜱɪᴏɴᴀʟ ʙᴀꜱꜱ - ꜱᴛᴜᴅɪᴏ Qᴜᴀʟɪᴛʏ"""
    if bass_level == 0:
        return audio_data
    
    try:
        # ʜɪɢʜᴇʀ ꜰʀᴇQ = ᴛɪɢʜᴛᴇʀ ʙᴀꜱꜱ
        f0 = 80 + (bass_level * 0.2)
        Q = 0.85
        gain_db = bass_level / 3.5
        
        w0 = 2 * np.pi * f0 / sample_rate
        A = 10 ** (gain_db / 40)
        cos_w0 = np.cos(w0)
        sin_w0 = np.sin(w0)
        alpha = sin_w0 / (2 * Q)
        
        b0 = A * ((A + 1) + (A - 1) * cos_w0 + 2 * np.sqrt(A) * alpha)
        b1 = -2 * A * ((A - 1) + (A + 1) * cos_w0)
        b2 = A * ((A + 1) + (A - 1) * cos_w0 - 2 * np.sqrt(A) * alpha)
        a0 = (A + 1) - (A - 1) * cos_w0 + 2 * np.sqrt(A) * alpha
        a1 = 2 * ((A - 1) - (A + 1) * cos_w0)
        a2 = (A + 1) - (A - 1) * cos_w0 - 2 * np.sqrt(A) * alpha
        
        b = np.array([b0, b1, b2]) / a0
        a = np.array([1, a1 / a0, a2 / a0])
        
        filtered = signal.lfilter(b, a, audio_data.astype(np.float32))
        
        # ʀᴇᴍᴏᴠᴇ ꜱᴜʙ-ʙᴀꜱꜱ (ɴᴏ ꜰᴀᴛ)
        if bass_level > 10:
            b_hp, a_hp = signal.butter(2, 50 / (sample_rate / 2), btype='high')
            filtered = signal.lfilter(b_hp, a_hp, filtered)
        
        # ᴄʟᴇᴀɴ ᴄʟɪᴘᴘɪɴɢ
        filtered = 32000.0 * np.tanh(filtered / 32000.0)
        
        return np.clip(filtered, -32768, 32767).astype(np.int16)
        
    except Exception as e:
        logger.error(f"ʙᴀꜱꜱ ᴀᴅᴠᴀɴᴄᴇᴅ ᴇʀʀᴏʀ: {e}")
        return apply_bass_boost_basic(audio_data, bass_level)

def apply_treble_boost_basic(audio_data, treble_level):
    """ꜰᴀꜱᴛ ᴛʀᴇʙʟᴇ / ᴘʀᴇꜱᴇɴᴄᴇ ʙᴏᴏꜱᴛ (ɴᴏ ꜱᴄɪᴘʏ)"""

    if treble_level <= 0:
        return audio_data

    audio = audio_data.astype(np.float32)

    # High-frequency extraction (vectorized — no slow per-sample loop)
    window_size = 4
    kernel = np.ones(window_size, dtype=np.float32) / window_size
    low = np.convolve(audio, kernel, mode="same")
    high = audio - low

    # Smooth boost
    mix = min(0.35, treble_level / 160.0)

    processed = audio + (high * mix)

    # Soft limiter
    processed = 30000.0 * np.tanh(processed / 30000.0)

    return np.clip(processed, -32768, 32767).astype(np.int16)

def apply_treble_boost_advanced(audio_data, treble_level, sample_rate=48000):
    """ᴀᴅᴠᴀɴᴄᴇᴅ ᴛʀᴇʙʟᴇ ʙᴏᴏꜱᴛ ᴡɪᴛʜ ꜱᴄɪᴘʏ"""
    if treble_level == 0:
        return audio_data
    try:
        f0 = 3500
        Q = 0.7
        gain_db = treble_level / 4
        w0 = 2 * np.pi * f0 / sample_rate
        A = 10 ** (gain_db / 40)
        cos_w0 = np.cos(w0)
        sin_w0 = np.sin(w0)
        alpha = sin_w0 / (2 * Q)
        b0 = A * ((A + 1) - (A - 1) * cos_w0 + 2 * np.sqrt(A) * alpha)
        b1 = 2 * A * ((A - 1) - (A + 1) * cos_w0)
        b2 = A * ((A + 1) - (A - 1) * cos_w0 - 2 * np.sqrt(A) * alpha)
        a0 = (A + 1) + (A - 1) * cos_w0 + 2 * np.sqrt(A) * alpha
        a1 = -2 * ((A - 1) + (A + 1) * cos_w0)
        a2 = (A + 1) + (A - 1) * cos_w0 - 2 * np.sqrt(A) * alpha
        b = np.array([b0, b1, b2]) / a0
        a = np.array([1, a1 / a0, a2 / a0])
        filtered = signal.lfilter(b, a, audio_data.astype(np.float32))
        return np.clip(filtered, -32768, 32767).astype(np.int16)
    except Exception as e:
        logger.error(f"ᴀᴅᴠᴀɴᴄᴇᴅ ᴛʀᴇʙʟᴇ ᴇʀʀᴏʀ: {e}")
        return apply_treble_boost_basic(audio_data, treble_level)

def apply_soft_gain(audio_data, gain_level):
    """ᴘʀᴏ ᴅʏɴᴀᴍɪᴄꜱ - ᴍᴀx ʟᴏᴜᴅɴᴇꜱꜱ, ᴢᴇʀᴏ ᴅɪꜱᴛᴏʀᴛɪᴏɴ"""
    if gain_level <= 0:
        return audio_data
    
    audio = audio_data.astype(np.float32)
    
    # === ꜱᴛᴀɢᴇ 1: ɪɴᴛᴇʟʟɪɢᴇɴᴛ ᴍᴀᴋᴇᴜᴘ ɢᴀɪɴ ===
    gain_factor = 1.8 + (gain_level / 25.0)
    processed = audio * gain_factor
    
    # === ꜱᴛᴀɢᴇ 2: ᴘʀᴏ ꜱᴏꜰᴛ-ᴋɴᴇᴇ ᴄᴏᴍᴘʀᴇꜱꜱᴏʀ ===
    if audio_config.get("compressor", True):
        threshold = 12000.0 + (gain_level * 40)
        ratio = 2.8 + (gain_level / 35.0)
        knee = 3000.0
        
        abs_processed = np.abs(processed)
        above = abs_processed > (threshold - knee/2)
        
        if np.any(above):
            in_knee = (abs_processed > (threshold - knee/2)) & (abs_processed <= (threshold + knee/2))
            above_knee = abs_processed > (threshold + knee/2)
            
            if np.any(in_knee):
                x = abs_processed[in_knee]
                y = threshold + (x - threshold) / ratio + ((x - threshold)**2) / (2 * knee * ratio)
                processed[in_knee] = np.sign(processed[in_knee]) * y
            
            if np.any(above_knee):
                x = abs_processed[above_knee]
                y = threshold + (x - threshold) / ratio
                processed[above_knee] = np.sign(processed[above_knee]) * y
        
        makeup = 1.3 + (gain_level / 60.0)
        processed = processed * makeup
    
    # === ꜱᴛᴀɢᴇ 3: ᴛʀᴜᴇ ᴘᴇᴀᴋ ʟɪᴍɪᴛᴇʀ ===
    if audio_config.get("limiter", True):
        peak = np.max(np.abs(processed))
        if peak > 31800:
            gain_reduction = 31800 / peak
            processed = processed * gain_reduction
        
        processed = 32200.0 * np.tanh(processed / 32200.0)
    
    # === ꜱᴛᴀɢᴇ 4: ꜰɪɴᴀʟ ꜱᴀꜰᴇᴛʏ ===
    processed = np.clip(processed, -32768, 32767)
    
    return processed.astype(np.int16)

def process_audio(audio_data):
    """ᴀᴘᴘʟʏ ᴀʟʟ ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ ɪɴ ᴄʜᴀɪɴ ɪɴᴄʟᴜᴅɪɴɢ ᴀᴅᴠᴀɴᴄᴇᴅ ᴇꜰꜰᴇᴄᴛꜱ"""

    if audio_data is None or len(audio_data) == 0:
        return audio_data

    try:
        processed = audio_data.copy()
        config = audio_config

        # ===== BASIC EFFECTS =====
        
        # 1. Volume Boost
        if config['volume'] != 100:
            processed = apply_volume_boost(processed, config['volume'])

        # 2. Bass Boost
        if config['bass'] > 0:
            if SCIPY_AVAILABLE:
                processed = apply_bass_boost_advanced(processed, config['bass'])
            else:
                processed = apply_bass_boost_basic(processed, config['bass'])

        # 3. Treble Boost
        if config['treble'] > 0:
            if SCIPY_AVAILABLE:
                processed = apply_treble_boost_advanced(processed, config['treble'])
            else:
                processed = apply_treble_boost_basic(processed, config['treble'])

        # 4. Soft Gain
        if config['gain'] > 0:
            processed = apply_soft_gain(processed, config['gain'])

        # ===== ADVANCED EFFECTS =====
        # Check if any advanced effect is active
        advanced_active = any(
            ADVANCED_AUDIO_CONFIG[key] != 0 
            for key in ADVANCED_AUDIO_CONFIG
        )
        
        if advanced_active:
            processed = apply_advanced_effects(processed)

        # ===== LOWPASS FILTER =====
        if config.get('lowpass', False) and SCIPY_AVAILABLE:
            try:
                b, a = signal.butter(4, 16000 / 24000, btype='low')
                processed = signal.lfilter(b, a, processed.astype(np.float32))
                processed = np.clip(processed, -32768, 32767).astype(np.int16)
            except Exception:
                pass

        # ===== HIGHPASS FILTER =====
        if config.get('highpass', False) and SCIPY_AVAILABLE:
            try:
                b, a = signal.butter(2, 80 / 24000, btype='high')
                processed = signal.lfilter(b, a, processed.astype(np.float32))
                processed = np.clip(processed, -32768, 32767).astype(np.int16)
            except Exception:
                pass

        return processed

    except Exception as e:
        logger.error(f"ᴀᴜᴅɪᴏ ᴘʀᴏᴄᴇꜱꜱɪɴɢ ᴇʀʀᴏʀ: {e}")
        return audio_data

# ==================== ᴀᴅᴠᴀɴᴄᴇᴅ ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ ====================

def apply_noise_suppression(audio_data, level):
    """ɴᴏɪꜱᴇ ꜱᴜᴘᴘʀᴇꜱꜱɪᴏɴ - ʀᴇᴅᴜᴄᴇꜱ ʙᴀᴄᴋɢʀᴏᴜɴᴅ ʜɪꜱꜱ/ʜᴜᴍ"""
    if level == 0:
        return audio_data
    
    audio = audio_data.astype(np.float32)
    strength = abs(level) / 50.0
    
    threshold = 200 + (strength * 800)
    softness = 0.1 + (strength * 0.4)
    abs_audio = np.abs(audio)
    noise_floor = np.percentile(abs_audio, 10)
    
    gate_factor = 1.0 / (1.0 + np.exp(-softness * (abs_audio - threshold) / (noise_floor + 1)))
    processed = audio * gate_factor
    
    return np.clip(processed, -32768, 32767).astype(np.int16)

def apply_high_pass_filter(audio_data, level, sample_rate=48000):
    """ʜɪɢʜ ᴘᴀꜱꜱ ꜰɪʟᴛᴇʀ - ʀᴇᴍᴏᴠᴇꜱ ʟᴏᴡ ꜰʀᴇQᴜᴇɴᴄʏ ʀᴜᴍʙʟᴇ"""
    if level == 0:
        return audio_data
    
    freq = 40 + (abs(level) * 3)
    
    if SCIPY_AVAILABLE:
        try:
            normalized_freq = freq / (sample_rate / 2)
            if normalized_freq >= 1.0:
                return audio_data
            b, a = signal.butter(3, normalized_freq, btype='high')
            processed = signal.lfilter(b, a, audio_data.astype(np.float32))
            return np.clip(processed, -32768, 32767).astype(np.int16)
        except Exception:
            pass
    
    kernel_size = max(3, int(20 - (abs(level)/50.0) * 15))
    kernel = np.array([-0.5] + [1.0] * (kernel_size - 2) + [-0.5]) / (kernel_size - 1)
    processed = np.convolve(audio_data.astype(np.float32), kernel, mode='same')
    return np.clip(processed, -32768, 32767).astype(np.int16)

def apply_deesser(audio_data, level, sample_rate=48000):
    """ᴅᴇ-ᴇꜱꜱᴇʀ - ʀᴇᴅᴜᴄᴇꜱ ꜱɪʙɪʟᴀɴᴛ ꜱᴏᴜɴᴅꜱ"""
    if level == 0:
        return audio_data
    
    audio = audio_data.astype(np.float32)
    strength = abs(level) / 50.0
    
    if SCIPY_AVAILABLE:
        try:
            low = 4000 / (sample_rate / 2)
            high = 8000 / (sample_rate / 2)
            b, a = signal.butter(3, [low, high], btype='band')
            sibilance = signal.lfilter(b, a, audio)
            sibilance_energy = np.abs(sibilance)
            threshold = np.percentile(sibilance_energy, 70) * (0.3 + strength * 0.4)
            reduction = 1.0 - (strength * 0.7) * np.tanh(sibilance_energy / (threshold + 1))
            reduction = np.clip(reduction, 0.3, 1.0)
            processed = audio - (sibilance * (1.0 - reduction) * 0.5)
            return np.clip(processed, -32768, 32767).astype(np.int16)
        except Exception:
            pass
    
    kernel = np.array([-0.1, 0.3, -0.5, 0.3, -0.1])
    sibilance = np.convolve(audio, kernel, mode='same')
    reduction = 1.0 - strength * 0.5
    processed = audio - (sibilance * (1.0 - reduction))
    return np.clip(processed, -32768, 32767).astype(np.int16)

def apply_presence_eq(audio_data, level, sample_rate=48000):
    """ᴘʀᴇꜱᴇɴᴄᴇ EQ - ʙᴏᴏꜱᴛ/ᴄᴜᴛ ᴛʜᴇ 2-5ᴋʜᴢ ʀᴀɴɢᴇ"""
    if level == 0:
        return audio_data
    
    audio = audio_data.astype(np.float32)
    gain_db = (level / 50.0) * 12
    f0 = 3200
    Q = 0.7
    
    if SCIPY_AVAILABLE:
        try:
            w0 = 2 * np.pi * f0 / sample_rate
            A = 10 ** (gain_db / 40)
            cos_w0 = np.cos(w0)
            sin_w0 = np.sin(w0)
            alpha = sin_w0 / (2 * Q)
            
            b0 = 1 + alpha * A
            b1 = -2 * cos_w0
            b2 = 1 - alpha * A
            a0 = 1 + alpha / A
            a1 = -2 * cos_w0
            a2 = 1 - alpha / A
            
            b = np.array([b0, b1, b2]) / a0
            a = np.array([1, a1 / a0, a2 / a0])
            
            processed = signal.lfilter(b, a, audio)
            return np.clip(processed, -32768, 32767).astype(np.int16)
        except Exception:
            pass
    
    if gain_db > 0:
        kernel = np.array([-0.05, 0.1, 0.8, 0.1, -0.05])
        presence = np.convolve(audio, kernel, mode='same')
        processed = audio + (presence * (gain_db / 20))
    else:
        kernel = np.array([0.05, -0.1, 0.8, -0.1, 0.05])
        presence = np.convolve(audio, kernel, mode='same')
        processed = audio - (audio - presence) * (abs(gain_db) / 20)
    return np.clip(processed, -32768, 32767).astype(np.int16)

def apply_loudness_normalization(audio_data, level):
    """ʟᴏᴜᴅɴᴇꜱꜱ ɴᴏʀᴍᴀʟɪᴢᴀᴛɪᴏɴ (RMS/LUFS)"""
    if level == 0:
        return audio_data
    
    audio = audio_data.astype(np.float32)
    strength = abs(level) / 50.0
    
    rms = np.sqrt(np.mean(audio ** 2))
    if rms < 1:
        return audio_data
    
    target_rms = 2000 + (strength * 6000)
    gain = np.clip(target_rms / rms, 0.1, 10.0)
    processed = audio * gain
    
    if strength > 0.3:
        threshold = target_rms * 0.8
        ratio = 2.0 + (strength * 3.0)
        abs_processed = np.abs(processed)
        above = abs_processed > threshold
        if np.any(above):
            processed[above] = np.sign(processed[above]) * (
                threshold + (abs_processed[above] - threshold) / ratio
            )
        makeup = 1.0 + (strength * 0.3)
        processed = processed * makeup
    
    return np.clip(processed, -32768, 32767).astype(np.int16)

def apply_look_ahead_limiter(audio_data, level):
    """ʟᴏᴏᴋ-ᴀʜᴇᴀᴅ ʟɪᴍɪᴛᴇʀ - ᴘʀᴇᴠᴇɴᴛꜱ ᴄʟɪᴘᴘɪɴɢ"""
    if level == 0:
        return audio_data
    
    audio = audio_data.astype(np.float32)
    look_ahead = int(4 + abs(level) * 0.2)
    release = int(20 + abs(level) * 0.5)
    
    delayed = np.concatenate([audio[look_ahead:], np.zeros(look_ahead)])
    abs_delayed = np.abs(delayed)
    threshold = 15000 + (abs(level) * 150)
    
    gain_reduction = np.ones_like(delayed)
    over_threshold = abs_delayed > threshold
    if np.any(over_threshold):
        reduction = threshold / (abs_delayed[over_threshold] + 1)
        gain_reduction[over_threshold] = reduction
    
    # Vectorized release envelope. The original recurrence simplifies to
    #   s[i] = min(gain_reduction[i], s[i-1] + step),  s[0] = 1.0
    # which equals a sloped cumulative-minimum (no per-sample Python loop).
    step = 1.0 / release
    idx = np.arange(len(gain_reduction), dtype=np.float32)
    c = gain_reduction.astype(np.float32).copy()
    if len(c) > 0:
        c[0] = 1.0
    smoothed_reduction = np.minimum.accumulate(c - idx * step) + idx * step
    
    processed = audio * smoothed_reduction
    processed = 32000.0 * np.tanh(processed / 32000.0)
    return np.clip(processed, -32768, 32767).astype(np.int16)

def apply_noise_gate(audio_data, level):
    """ɴᴏɪꜱᴇ ɢᴀᴛᴇ / ᴇxᴘᴀɴᴅᴇʀ"""
    if level == 0:
        return audio_data
    
    audio = audio_data.astype(np.float32)
    strength = abs(level) / 50.0
    abs_audio = np.abs(audio)
    noise_floor = np.percentile(abs_audio, 5)
    threshold = noise_floor * (1.0 + strength * 2.0)
    ratio = 1.0 + (strength * 4.0)
    knee_width = 200 + (strength * 300)
    
    gate_factor = np.ones_like(audio)
    below = abs_audio < (threshold - knee_width/2)
    in_knee = (abs_audio >= (threshold - knee_width/2)) & (abs_audio <= (threshold + knee_width/2))
    above = abs_audio > (threshold + knee_width/2)
    
    gate_factor[below] = 0.0
    if np.any(in_knee):
        x = (abs_audio[in_knee] - (threshold - knee_width/2)) / knee_width
        gate_factor[in_knee] = x ** 2
    if np.any(above):
        x = (abs_audio[above] - threshold) / (abs_audio[above] + 1)
        gate_factor[above] = 1.0 - (1.0 - 1.0/ratio) * x
    
    processed = audio * gate_factor
    return np.clip(processed, -32768, 32767).astype(np.int16)

def apply_dc_offset_removal(audio_data, level):
    """ᴅᴄ ᴏꜰꜰꜱᴇᴛ ʀᴇᴍᴏᴠᴀʟ"""
    if level == 0:
        return audio_data
    
    audio = audio_data.astype(np.float32)
    dc_offset = np.mean(audio)
    
    if abs(dc_offset) > 1:
        strength = abs(level) / 50.0
        alpha = 0.001 + (strength * 0.02)
        # Vectorized leaky-integrator DC tracker (no slow per-sample loop):
        #   y[i] = (1-alpha)*y[i-1] + alpha*x[i]  ->  IIR filter
        if SCIPY_AVAILABLE:
            dc_estimate = signal.lfilter([alpha], [1.0, -(1.0 - alpha)], audio)
            processed = audio - dc_estimate
        else:
            processed = audio - dc_offset
        return np.clip(processed, -32768, 32767).astype(np.int16)
    
    return audio_data.astype(np.int16)

def apply_soft_saturation(audio_data, level):
    """ꜱᴏꜰᴛ ꜱᴀᴛᴜʀᴀᴛɪᴏɴ / ᴇxᴄɪᴛᴇʀ"""
    if level == 0:
        return audio_data
    
    audio = audio_data.astype(np.float32)
    strength = abs(level) / 50.0
    
    if level > 0:
        positive = audio[audio > 0]
        negative = audio[audio < 0]
        positive_sat = 32000.0 * np.tanh((positive / 32000.0) * (1.0 + strength * 0.3))
        negative_sat = 32000.0 * np.tanh((negative / 32000.0) * (1.0 + strength * 0.2))
        processed = np.zeros_like(audio)
        processed[audio > 0] = positive_sat
        processed[audio < 0] = negative_sat
        if strength > 0.3:
            harmonic = 0.05 * strength * (audio ** 2) * np.sign(audio)
            processed = processed + harmonic
    else:
        processed = 30000.0 * np.tanh(audio / 30000.0)
        harmonic = 0.02 * abs(level) * (audio ** 2) * np.sign(audio)
        processed = processed + harmonic
    
    return np.clip(processed, -32768, 32767).astype(np.int16)

def apply_stereo_width(audio_data, level):
    """
    ᴜꜰᴇʀᴇᴏ ᴡɪᴅᴛʜ / ᴍᴏɴᴏ ᴏᴘᴛɪᴍɪᴢᴀᴛɪᴏɴ - ꜰʀᴀᴍᴇ-ꜱɪᴢᴇ ꜱᴀꜰᴇ
    (ᴏᴜᴛᴘᴜᴛ ꜱᴀᴍᴘʟᴇ ᴄᴏᴜɴᴛ ᴀʟᴡᴀʏꜱ = ɪɴᴘᴜᴛ)
    """
    if level == 0 or audio_data is None or len(audio_data) == 0:
        return audio_data

    audio = audio_data.astype(np.float32)
    strength = min(abs(level) / 50.0, 1.0)
    n = len(audio)

    # Frames from PyTgCalls are interleaved stereo (even length). We MUST keep
    # the output the same number of samples as the input, otherwise the frame
    # sent via send_frame() gets the wrong size and audio breaks.
    if n % 2 == 0 and n >= 4:
        left = audio[0::2]
        right = audio[1::2]

        mid = (left + right) / 2.0
        side = (left - right) / 2.0

        if level > 0:
            side_gain = 1.0 + strength * 1.5      # widen
        else:
            side_gain = max(0.0, 1.0 - strength)  # narrow toward mono

        left_new = mid + side * side_gain
        right_new = mid - side * side_gain

        # Subtle Haas-style widening, still without changing length
        if level < 0 and strength > 0.3:
            delay = min(int(2 + strength * 4), max(1, len(left) // 4))
            left_new = left_new - np.roll(left_new, delay) * strength * 0.15
            right_new = right_new + np.roll(right_new, delay) * strength * 0.15

        processed = np.empty(n, dtype=np.float32)
        processed[0::2] = left_new
        processed[1::2] = right_new
    else:
        # Odd-length / true mono buffer: keep length identical (safe no-op)
        processed = audio.copy()

    peak = np.max(np.abs(processed))
    if peak > 32000:
        processed = (processed / peak) * 32000

    return np.clip(processed, -32768, 32767).astype(np.int16)


def apply_advanced_effects(audio_data):
    """ᴀᴘᴘʟʏ ᴀʟʟ ᴀᴅᴠᴀɴᴄᴇᴅ ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ ɪɴ ᴄʜᴀɪɴ"""
    if audio_data is None or len(audio_data) == 0:
        return audio_data
    
    try:
        config = ADVANCED_AUDIO_CONFIG
        processed = audio_data.copy()
        
        # 1. DC Offset Removal (first in chain)
        if config['dc_offset'] != 0:
            processed = apply_dc_offset_removal(processed, config['dc_offset'])
        
        # 2. Noise Gate
        if config['noisegate'] != 0:
            processed = apply_noise_gate(processed, config['noisegate'])
        
        # 3. High Pass Filter
        if config['hpf'] != 0:
            processed = apply_high_pass_filter(processed, config['hpf'])
        
        # 4. Noise Suppression
        if config['ns'] != 0:
            processed = apply_noise_suppression(processed, config['ns'])
        
        # 5. De-Esser
        if config['deesser'] != 0:
            processed = apply_deesser(processed, config['deesser'])
        
        # 6. Presence EQ
        if config['presence_eq'] != 0:
            processed = apply_presence_eq(processed, config['presence_eq'])
        
        # 7. Soft Saturation
        if config['saturation'] != 0:
            processed = apply_soft_saturation(processed, config['saturation'])
        
        # 8. Loudness Normalization
        if config['loudness'] != 0:
            processed = apply_loudness_normalization(processed, config['loudness'])
        
        # 9. Look-Ahead Limiter
        if config['limiter'] != 0:
            processed = apply_look_ahead_limiter(processed, config['limiter'])
        
        # 10. Stereo Width (final)
        if config['stereo_width'] != 0:
            processed = apply_stereo_width(processed, config['stereo_width'])
        
        return processed
        
    except Exception as e:
        logger.error(f"ᴀᴅᴠᴀɴᴄᴇᴅ ᴀᴜᴅɪᴏ ᴘʀᴏᴄᴇꜱꜱɪɴɢ ᴇʀʀᴏʀ: {e}")
        return audio_data
        
        
# ==================== ᴀᴜᴅɪᴏ ʜᴀɴᴅʟᴇʀ ====================

async def _forward_incoming_frames(update):
    if is_muted or update.chat_id != RECORD_SOURCE or not forward_chats:
        return
    async with processing_lock:
        try:
            if not update.frames:
                return
            frame_length = len(update.frames[0].frame) // 2
            # ᴀᴄᴄᴜᴍᴜʟᴀᴛᴇ ɪɴ ɪɴᴛ32 ᴛᴏ ᴀᴠᴏɪᴅ ɪɴᴛ16 ᴏᴠᴇʀꜰʟᴏᴡ ᴡʜᴇɴ ᴍɪxɪɴɢ ꜰʀᴀᴍᴇꜱ
            mixed_acc = np.zeros(frame_length, dtype=np.int32)
            valid_frames = 0
            for frame_data in update.frames:
                try:
                    source_samples = np.frombuffer(frame_data.frame, dtype=np.int16)
                    if len(source_samples) == frame_length:
                        mixed_acc += source_samples.astype(np.int32)
                        valid_frames += 1
                except Exception:
                    continue
            if valid_frames == 0:
                return
            mixed_acc //= valid_frames
            mixed_output = np.clip(mixed_acc, -32768, 32767).astype(np.int16)
            loop = asyncio.get_running_loop()
            processed_output = await loop.run_in_executor(None, process_audio, mixed_output)
            mixed_bytes = processed_output.tobytes()
            for chat_id in list(forward_chats):
                try:
                    await call_py.send_frame(chat_id, Device.MICROPHONE, mixed_bytes)
                except Exception as e:
                    logger.debug(f"ꜱᴇɴᴅ ᴇʀʀᴏʀ ᴛᴏ {chat_id}: {e}")
                    if "not found" in str(e).lower() or "invalid" in str(e).lower():
                        forward_chats.discard(chat_id)
                        logger.warning(f"ʀᴇᴍᴏᴠᴇᴅ {chat_id} ꜰʀᴏᴍ ꜰᴏʀᴡᴀʀᴅɪɴɢ ʟɪꜱᴛ")
        except Exception as e:
            logger.error(f"ᴀᴜᴅɪᴏ ʜᴀɴᴅʟᴇʀ ᴇʀʀᴏʀ: {e}")

# ==================== ᴄʜᴀᴛ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ ====================

@call_py.on_update(pytg_filters.stream_frame(Direction.INCOMING, Device.MICROPHONE))
async def audio_forwarder(_, update: StreamFrames):
    await _forward_incoming_frames(update)


async def cache_chat_info(chat_id):
    """ᴄᴀᴄʜᴇ ᴄʜᴀᴛ ɪɴꜰᴏ ᴡɪᴛʜ ᴘʀᴏᴘᴇʀ ᴇʀʀᴏʀ ʜᴀɴᴅʟɪɴɢ"""
    try:
        logger.info(f"ᴄᴀᴄʜɪɴɢ ᴄʜᴀᴛ ɪɴꜰᴏ ꜰᴏʀ {chat_id}...")
        try:
            chat = await user_app.get_chat(chat_id)
            chat_title = chat.title if hasattr(chat, 'title') else str(chat_id)
            logger.info(f"✅ ᴄᴀᴄʜᴇᴅ: {chat_id} - {chat_title}")
            return True
        except (PeerIdInvalid, ValueError) as e:
            logger.debug(f"ᴅɪʀᴇᴄᴛ ɢᴇᴛ_ᴄʜᴀᴛ ꜰᴀɪʟᴇᴅ: {e}")
            try:
                async for dialog in user_app.get_dialogs(limit=50):
                    if dialog.chat.id == chat_id:
                        logger.info(f"✅ ꜰᴏᴜɴᴅ ɪɴ ᴅɪᴀʟᴏɢꜱ: {chat_id}")
                        return True
            except Exception:
                pass
            logger.error(f"❌ ᴄᴀɴɴᴏᴛ ꜰɪɴᴅ ᴄʜᴀᴛ: {chat_id}")
            return False
    except Exception as e:
        logger.error(f"ᴄᴀᴄʜᴇ ᴇʀʀᴏʀ ꜰᴏʀ {chat_id}: {e}")
        return False

async def join_call_safe(chat_id):
    """ꜱᴀꜰᴇʟʏ ᴊᴏɪɴ ᴄᴀʟʟ ᴡɪᴛʜ ᴘʀᴏᴘᴇʀ ᴇʀʀᴏʀ ʜᴀɴᴅʟɪɴɢ"""
    try:
        if not await cache_chat_info(chat_id):
            return False, "ᴄʜᴀᴛ ɴᴏᴛ ꜰᴏᴜɴᴅ ᴏʀ ɪɴᴀᴄᴄᴇꜱꜱɪʙʟᴇ"
        try:
            await call_py.play(
                chat_id,
                MediaStream(ExternalMedia.AUDIO, AUDIO_PARAMETERS),
            )
            return True, None
        except NoActiveGroupCall:
            return False, "ɴᴏ ᴀᴄᴛɪᴠᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ"
        except Exception as e:
            error_msg = str(e)
            if "already participating" in error_msg.lower():
                return True, None
            return False, error_msg
    except Exception as e:
        return False, str(e)

# ==================== ᴄᴏᴍᴍᴀɴᴅꜱ ====================

# ===== ᴜꜱᴇʀ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ ᴄᴏᴍᴍᴀɴᴅꜱ =====

@bot_app.on_message(pyro_filters.command("approve") & pyro_filters.user(OWNER_ID))
async def cmd_approve(client, message):
    """ᴀᴘᴘʀᴏᴠᴇ ᴀ ᴜꜱᴇʀ ᴛᴏ ᴜꜱᴇ ᴛʜᴇ ʙᴏᴛ"""
    try:
        user_id = None
        user_mention = None
        username = None
        first_name = None
        if message.reply_to_message:
            user = message.reply_to_message.from_user
            user_id = user.id
            user_mention = user.mention
            username = user.username or "ɴᴏ ᴜꜱᴇʀɴᴀᴍᴇ"
            first_name = user.first_name or "ᴜɴᴋɴᴏᴡɴ"
        else:
            parts = message.text.split()
            if len(parts) < 2:
                await message.reply(
                    "❌ **ᴜꜱᴀɢᴇ:** `/approve` (ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ)\n"
                    "ᴏʀ: `/approve <ᴜꜱᴇʀ_ɪᴅ>`"
                )
                return
            try:
                user_id = int(parts[1])
                try:
                    user = await client.get_users(user_id)
                    user_mention = user.mention
                    username = user.username or "ɴᴏ ᴜꜱᴇʀɴᴀᴍᴇ"
                    first_name = user.first_name or "ᴜɴᴋɴᴏᴡɴ"
                except Exception:
                    user_mention = f"ᴜꜱᴇʀ {user_id}"
                    username = "ᴜɴᴋɴᴏᴡɴ"
                    first_name = "ᴜɴᴋɴᴏᴡɴ"
            except ValueError:
                await message.reply("❌ **ɪɴᴠᴀʟɪᴅ ᴜꜱᴇʀ ɪᴅ ꜰᴏʀᴍᴀᴛ!**")
                return
        if user_id in approved_users:
            await message.reply(
                f"ℹ️ **ᴜꜱᴇʀ ᴀʟʀᴇᴀᴅʏ ᴀᴘᴘʀᴏᴠᴇᴅ!**\n\n"
                f"👤 {user_mention}\n"
                f"🔢 `{user_id}`"
            )
            return
        approved_users.add(user_id)
        save_state()
        approve_msg = f"""
✅ **ᴜꜱᴇʀ ᴀᴘᴘʀᴏᴠᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**

────────────────────
👤 **ɴᴀᴍᴇ:** {first_name} ({user_mention})
🔢 **ɪᴅ:** `{user_id}`
📝 **ᴜꜱᴇʀɴᴀᴍᴇ:** @{username}
📊 **ꜱᴛᴀᴛᴜꜱ:** 🟢 ᴀᴘᴘʀᴏᴠᴇᴅ
────────────────────

🎯 **ᴛʜᴇʏ ᴄᴀɴ ɴᴏᴡ ᴜꜱᴇ ᴛʜᴇ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅꜱ!**
"""
        await message.reply(approve_msg)
        logger.info(f"ᴜꜱᴇʀ {user_id} ᴀᴘᴘʀᴏᴠᴇᴅ ʙʏ ᴏᴡɴᴇʀ")
    except Exception as e:
        await message.reply(f"❌ **ᴇʀʀᴏʀ:** `{str(e)}`")

@bot_app.on_message(pyro_filters.command("disapprove") & pyro_filters.user(OWNER_ID))
async def cmd_disapprove(client, message):
    """ʀᴇᴍᴏᴠᴇ ᴜꜱᴇʀ ᴀᴘᴘʀᴏᴠᴀʟ"""
    try:
        user_id = None
        user_mention = None
        if message.reply_to_message:
            user = message.reply_to_message.from_user
            user_id = user.id
            user_mention = user.mention
        else:
            parts = message.text.split()
            if len(parts) < 2:
                await message.reply(
                    "❌ **ᴜꜱᴀɢᴇ:** `/disapprove` (ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ)\n"
                    "ᴏʀ: `/disapprove <ᴜꜱᴇʀ_ɪᴅ>`"
                )
                return
            try:
                user_id = int(parts[1])
                try:
                    user = await client.get_users(user_id)
                    user_mention = user.mention
                except Exception:
                    user_mention = f"ᴜꜱᴇʀ {user_id}"
            except ValueError:
                await message.reply("❌ **ɪɴᴠᴀʟɪᴅ ᴜꜱᴇʀ ɪᴅ ꜰᴏʀᴍᴀᴛ!**")
                return
        if user_id not in approved_users:
            await message.reply(
                f"ℹ️ **ᴜꜱᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ ɪɴ ᴀᴘᴘʀᴏᴠᴇᴅ ʟɪꜱᴛ!**\n\n"
                f"👤 {user_mention}\n"
                f"🔢 `{user_id}`"
            )
            return
        approved_users.discard(user_id)
        save_state()
        disapprove_msg = f"""
❌ **ᴜꜱᴇʀ ᴅɪꜱᴀᴘᴘʀᴏᴠᴇᴅ!**

────────────────────
👤 **ɴᴀᴍᴇ:** {user_mention}
🔢 **ɪᴅ:** `{user_id}`
📊 **ꜱᴛᴀᴛᴜꜱ:** 🔴 ʀᴇᴍᴏᴠᴇᴅ
────────────────────

🚫 **ᴛʜᴇʏ ᴄᴀɴ ɴᴏ ʟᴏɴɢᴇʀ ᴜꜱᴇ ᴛʜᴇ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅꜱ!**
"""
        await message.reply(disapprove_msg)
        logger.info(f"ᴜꜱᴇʀ {user_id} ᴅɪꜱᴀᴘᴘʀᴏᴠᴇᴅ ʙʏ ᴏᴡɴᴇʀ")
    except Exception as e:
        await message.reply(f"❌ **ᴇʀʀᴏʀ:** `{str(e)}`")

@bot_app.on_message(pyro_filters.command("userlist") & pyro_filters.user(OWNER_ID))
async def cmd_userlist(client, message):
    """ꜱʜᴏᴡ ʟɪꜱᴛ ᴏꜰ ᴀᴘᴘʀᴏᴠᴇᴅ ᴜꜱᴇʀꜱ"""
    try:
        if not approved_users:
            await message.reply(
                "📭 **ɴᴏ ᴜꜱᴇʀꜱ ᴀʀᴇ ᴀᴘᴘʀᴏᴠᴇᴅ ʏᴇᴛ.**\n\n"
                "ᴜꜱᴇ `/approve` ᴛᴏ ᴀᴅᴅ ᴜꜱᴇʀꜱ."
            )
            return
        user_list = []
        total = len(approved_users)
        processed = 0
        for user_id in approved_users:
            processed += 1
            try:
                user = await client.get_users(user_id)
                username = f"@{user.username}" if user.username else "ɴᴏ ᴜꜱᴇʀɴᴀᴍᴇ"
                mention = user.mention
                user_list.append(f"• {mention}\n  🔢 `{user_id}` | {username}")
            except Exception:
                user_list.append(f"• ᴜꜱᴇʀ `{user_id}` (⚠️ ᴄᴏᴜʟᴅ ɴᴏᴛ ꜰᴇᴛᴄʜ)")
        response = f"""
🔥 **ᴀᴘᴘʀᴏᴠᴇᴅ ᴜꜱᴇʀꜱ**

────────────────────
📊 **ᴛᴏᴛᴀʟ:** {total} ᴜꜱᴇʀꜱ
📌 **ᴘʀᴏᴄᴇꜱꜱɪɴɢ:** {processed}/{total}
────────────────────

"""
        response += "\n\n".join(user_list)
        response += f"\n\n────────────────────\n✅ **ᴛᴏᴛᴀʟ:** {total}"
        buttons = build_keyboard([
            ("🔄 ʀᴇꜰʀᴇꜱʜ", "refresh_userlist", ButtonStyle.PRIMARY),
            ("📊 ꜱᴛᴀᴛꜱ", "userlist_stats", ButtonStyle.PRIMARY),
            ("⬅️ ʙᴀᴄᴋ", "back_start", ButtonStyle.SUCCESS)
        ], row_width=2)
        if len(response) > 4000:
            parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    await message.reply(part, reply_markup=buttons)
                else:
                    await message.reply(part)
        else:
            await message.reply(response, reply_markup=buttons)
    except Exception as e:
        await message.reply(f"❌ **ᴇʀʀᴏʀ:** `{str(e)}`")

# ==================== ᴄᴜꜱᴛᴏᴍ ʙᴜᴛᴛᴏɴ ꜱᴛʏʟɪɴɢ ====================

from io import BytesIO
from pyrogram.raw.core import TLObject
from pyrogram.raw.base import KeyboardButton
from pyrogram.raw.core.primitives import Int, Bytes, String

class RawKeyboardButtonStyle(TLObject):
    ID = 0x4fdd3430
    QUALNAME = "types.KeyboardButtonStyle"
    def __init__(self, bg_primary=False, bg_danger=False, bg_success=False):
        self.bg_primary = bg_primary
        self.bg_danger = bg_danger
        self.bg_success = bg_success
    def write(self, *args):
        b = BytesIO()
        b.write(Int(self.ID, False))
        flags = 0
        if self.bg_primary: flags |= (1 << 0)
        if self.bg_danger: flags |= (1 << 1)
        if self.bg_success: flags |= (1 << 2)
        b.write(Int(flags))
        return b.getvalue()

class RawKeyboardButtonCallback(KeyboardButton, TLObject):
    ID = 0xe62bc960
    QUALNAME = "types.KeyboardButtonCallback"
    def __init__(self, text, data, requires_password, style):
        self.text = text
        self.data = data
        self.requires_password = requires_password
        self.style = style
    def write(self, *args):
        b = BytesIO()
        b.write(Int(self.ID, False))
        flags = 0
        if self.requires_password: flags |= (1 << 0)
        if self.style is not None: flags |= (1 << 10)
        b.write(Int(flags))
        if self.style is not None:
            b.write(self.style.write())
        b.write(String(self.text))
        b.write(Bytes(self.data))
        return b.getvalue()

class RawKeyboardButtonUrl(KeyboardButton, TLObject):
    ID = 0xd80c25ec
    QUALNAME = "types.KeyboardButtonUrl"
    def __init__(self, text, url, style):
        self.text = text
        self.url = url
        self.style = style
    def write(self, *args):
        b = BytesIO()
        b.write(Int(self.ID, False))
        flags = 0
        if self.style is not None: flags |= (1 << 10)
        b.write(Int(flags))
        if self.style is not None:
            b.write(self.style.write())
        b.write(String(self.text))
        b.write(String(self.url))
        return b.getvalue()

class StyledInlineKeyboardButton(InlineKeyboardButton):
    def __init__(self, text: str, callback_data: str = None, url: str = None, style: str = None, **kwargs):
        super().__init__(text=text, callback_data=callback_data, url=url, **kwargs)
        self.style = style

    async def write(self, client: "pyrogram.Client"):
        if not self.style:
            return await super().write(client)
            
        style_str = self.style
        if style_str.startswith("bg_"):
            style_str = style_str[3:]
            
        if style_str not in ["primary", "danger", "success"]:
            return await super().write(client)
            
        bg_primary = (style_str == "primary")
        bg_danger = (style_str == "danger")
        bg_success = (style_str == "success")
        style_obj = RawKeyboardButtonStyle(bg_primary=bg_primary, bg_danger=bg_danger, bg_success=bg_success)
        
        if self.callback_data is not None:
            data_bytes = bytes(self.callback_data, "utf-8") if isinstance(self.callback_data, str) else self.callback_data
            # FIXED: Use getattr with default False for requires_password
            requires_password = getattr(self, 'requires_password', False)
            return RawKeyboardButtonCallback(
                text=self.text,
                data=data_bytes,
                requires_password=requires_password,
                style=style_obj
            )
            
        if self.url is not None:
            return RawKeyboardButtonUrl(
                text=self.text,
                url=self.url,
                style=style_obj
            )
            
        return await super().write(client)

class ButtonStyle:
    PRIMARY = "bg_primary"
    SUCCESS = "bg_success"
    DANGER = "bg_danger"

def styled_button(text: str, callback_data: str = None, url: str = None, style: str = ButtonStyle.PRIMARY) -> InlineKeyboardButton:
    """ᴄʀᴇᴀᴛᴇ ᴀ ʙᴜᴛᴛᴏɴ ᴀɴᴅ ɪɴᴊᴇᴄᴛ ᴛᴇʟᴇɢʀᴀᴍ ʙᴀᴄᴋᴇɴᴅ ᴄᴏʟᴏʀ ꜱᴛʏʟᴇ"""
    return StyledInlineKeyboardButton(text=text, callback_data=callback_data, url=url, style=style)

def build_keyboard(buttons: list, row_width: int = 2) -> InlineKeyboardMarkup:
    """ʙᴜɪʟᴅ ᴋᴇʏʙᴏᴀʀᴅ ꜰʀᴏᴍ ʙᴜᴛᴛᴏɴ ᴅᴀᴛᴀ (ᴄᴏʟᴏʀ ꜱᴜᴘᴘᴏʀᴛᴇᴅ)"""
    rows, row = [], []
    
    for btn in buttons:
        if len(btn) == 4:
            text, callback, style, url = btn
            if style not in [ButtonStyle.PRIMARY, ButtonStyle.SUCCESS, ButtonStyle.DANGER]:
                style = ButtonStyle.PRIMARY
            row.append(styled_button(text, callback_data=callback, url=url, style=style))
        elif len(btn) == 3:
            text, callback, style = btn
            if style not in [ButtonStyle.PRIMARY, ButtonStyle.SUCCESS, ButtonStyle.DANGER]:
                style = ButtonStyle.PRIMARY
            row.append(styled_button(text, callback_data=callback, style=style))
        else:
            text, callback = btn[0], btn[1]
            row.append(styled_button(text, callback_data=callback, style=ButtonStyle.PRIMARY))
        
        if len(row) >= row_width:
            rows.append(row)
            row = []
    
    if row:
        rows.append(row)
    
    return InlineKeyboardMarkup(rows)

# ==================== ᴄᴀʟʟʙᴀᴄᴋ ʜᴀɴᴅʟᴇʀꜱ ====================

@bot_app.on_callback_query(~pyro_filters.regex(r"^panel_"))
async def handle_callbacks(client, callback_query: CallbackQuery):
    """ʜᴀɴᴅʟᴇ ᴀʟʟ ɴᴏɴ-ᴘᴀɴᴇʟ ᴄᴀʟʟʙᴀᴄᴋ Qᴜᴇʀɪᴇꜱ"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    # 🔐 ᴀᴜᴛʜᴇɴᴛɪᴄᴀᴛɪᴏɴ ᴄʜᴇᴄᴋ
    if user_id != OWNER_ID and user_id not in approved_users:
        await callback_query.answer("⛔ ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ!", show_alert=True)
        return
    
    await callback_query.answer()
    
    # ──────────────────────────────────────────────────────
    # ʀᴇꜰʀᴇꜱʜ ᴜꜱᴇʀʟɪꜱᴛ
    # ──────────────────────────────────────────────────────
    if data == "refresh_userlist":
        if not approved_users:
            keyboard = build_keyboard([
                ("➕ ᴀᴘᴘʀᴏᴠᴇ", "help_info", ButtonStyle.SUCCESS),
                ("🏠 ʜᴏᴍᴇ", "back_start", ButtonStyle.PRIMARY)
            ], row_width=2)
            await callback_query.edit_message_text(
                "📭 **ɴᴏ ᴜꜱᴇʀꜱ ᴀʀᴇ ᴀᴘᴘʀᴏᴠᴇᴅ ʏᴇᴛ.**\n\n"
                "💡 ᴜꜱᴇ `/ᴀᴘᴘʀᴏᴠᴇ` ᴛᴏ ᴀᴅᴅ ᴜꜱᴇʀꜱ",
                reply_markup=keyboard
            )
            return
        
        user_list = []
        for uid in approved_users:
            try:
                user = await client.get_users(uid)
                username = f"@{user.username}" if user.username else "ɴᴏ ᴜꜱᴇʀɴᴀᴍᴇ"
                mention = user.mention
                user_list.append(f"• {mention}\n  🔢 `{uid}` | {username}")
            except Exception:
                user_list.append(f"• ᴜꜱᴇʀ `{uid}` (⚠️ ᴄᴏᴜʟᴅ ɴᴏᴛ ꜰᴇᴛᴄʜ)")
        
        response = f"""
🔥 **ᴀᴘᴘʀᴏᴠᴇᴅ ᴜꜱᴇʀꜱ** (🔄 ʀᴇꜰʀᴇꜱʜᴇᴅ)
────────────────────
📊 **ᴛᴏᴛᴀʟ:** {len(approved_users)} ᴜꜱᴇʀꜱ
────────────────────
"""
        response += "\n\n".join(user_list)
        response += f"\n\n────────────────────\n✅ **ᴛᴏᴛᴀʟ:** {len(approved_users)}"
        
        keyboard = build_keyboard([
            ("🔄 ʀᴇꜰʀᴇꜱʜ", "refresh_userlist", ButtonStyle.PRIMARY),
            ("📊 ꜱᴛᴀᴛꜱ", "userlist_stats", ButtonStyle.PRIMARY),
            ("🏠 ʜᴏᴍᴇ", "back_start", ButtonStyle.SUCCESS)
        ], row_width=2)
        
        await callback_query.edit_message_text(response, reply_markup=keyboard)
    
    # ──────────────────────────────────────────────────────
    # ᴜꜱᴇʀʟɪꜱᴛ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ
    # ──────────────────────────────────────────────────────
    elif data == "userlist_stats":
        total = len(approved_users)
        stats_msg = f"""
📊 **ᴜꜱᴇʀ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ**
────────────────────
🔥 **ᴛᴏᴛᴀʟ:** {total}
📌 **ꜱᴛᴀᴛᴜꜱ:** {'🟢 ᴀᴄᴛɪᴠᴇ' if total > 0 else '🔴 ᴇᴍᴘᴛʏ'}
────────────────────
📈 **ᴘʀᴏɢʀᴇꜱꜱ**
{('█' * min(total, 10)) + ('░' * (10 - min(total, 10))) if total > 0 else '░░░░░░░░░░'}
⚡ **ᴜꜱᴀɢᴇ:** {'ɢᴏᴏᴅ' if total < 50 else 'ʜᴇᴀᴠʏ' if total < 100 else 'ᴍᴀx'}
"""
        keyboard = build_keyboard([
            ("⬅️ ʙᴀᴄᴋ", "back_userlist", ButtonStyle.PRIMARY)
        ], row_width=1)
        await callback_query.edit_message_text(stats_msg, reply_markup=keyboard)
    
    # ──────────────────────────────────────────────────────
    # ʙᴀᴄᴋ ᴛᴏ ᴜꜱᴇʀʟɪꜱᴛ
    # ──────────────────────────────────────────────────────
    elif data == "back_userlist":
        if not approved_users:
            keyboard = build_keyboard([
                ("➕ ᴀᴘᴘʀᴏᴠᴇ", "help_info", ButtonStyle.SUCCESS),
                ("🏠 ʜᴏᴍᴇ", "back_start", ButtonStyle.PRIMARY)
            ], row_width=2)
            await callback_query.edit_message_text(
                "📭 **ɴᴏ ᴜꜱᴇʀꜱ ᴀᴘᴘʀᴏᴠᴇᴅ**\n\n"
                "💡 ᴜꜱᴇ `/ᴀᴘᴘʀᴏᴠᴇ` ᴛᴏ ᴀᴅᴅ",
                reply_markup=keyboard
            )
            return
        
        user_list = []
        for uid in approved_users:
            try:
                user = await client.get_users(uid)
                username = f"@{user.username}" if user.username else "ɴᴏ ᴜꜱᴇʀɴᴀᴍᴇ"
                mention = user.mention
                user_list.append(f"• {mention}\n  🔢 `{uid}` | {username}")
            except Exception:
                user_list.append(f"• ᴜꜱᴇʀ `{uid}` (⚠️ ᴄᴏᴜʟᴅ ɴᴏᴛ ꜰᴇᴛᴄʜ)")
        
        response = f"""
🔥 **ᴀᴘᴘʀᴏᴠᴇᴅ ᴜꜱᴇʀꜱ**
────────────────────
📊 **ᴛᴏᴛᴀʟ:** {len(approved_users)}
────────────────────
"""
        response += "\n\n".join(user_list)
        response += f"\n\n────────────────────\n✅ **ᴛᴏᴛᴀʟ:** {len(approved_users)}"
        
        keyboard = build_keyboard([
            ("🔄 ʀᴇꜰʀᴇꜱʜ", "refresh_userlist", ButtonStyle.PRIMARY),
            ("📊 ꜱᴛᴀᴛꜱ", "userlist_stats", ButtonStyle.PRIMARY),
            ("🏠 ʜᴏᴍᴇ", "back_start", ButtonStyle.SUCCESS)
        ], row_width=2)
        
        await callback_query.edit_message_text(response, reply_markup=keyboard)
    
    # ──────────────────────────────────────────────────────
    # ʜᴇʟᴘ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ
    # ──────────────────────────────────────────────────────
    elif data == "help_info":
        help_text = """
📖 **ʜᴇʟᴘ ᴍᴇɴᴜ**
────────────────────
🎵 **ᴀᴜᴅɪᴏ ᴄᴏɴᴛʀᴏʟ**
/record - ꜱᴛᴀʀᴛ ʀᴇᴄᴏʀᴅɪɴɢ
/join <ɪᴅ> - ꜰᴏʀᴡᴀʀᴅ ᴛᴏ ᴄʜᴀᴛ
/joinlink <ʟɪɴᴋ> - ᴊᴏɪɴ ᴠɪᴀ ɪɴᴠɪᴛᴇ
/rejoin - ʀᴇᴄᴏɴɴᴇᴄᴛ ᴀʟʟ
/leave <ɪᴅ> - ꜱᴛᴏᴘ ꜰᴏʀᴡᴀʀᴅɪɴɢ
/leaveall - ꜱᴛᴏᴘ ᴀʟʟ
/leaverecord - ʟᴇᴀᴠᴇ ꜱᴏᴜʀᴄᴇ
/mute - ᴍᴜᴛᴇ
/unmute - ᴜɴᴍᴜᴛᴇ
────────────────────
🎛️ **ᴇꜰꜰᴇᴄᴛꜱ**
/level <0-200> - ᴠᴏʟᴜᴍᴇ
/bass <0-60> - ʙᴀꜱꜱ
/treble <0-60> - ᴛʀᴇʙʟᴇ
/gain <0-60> - ɢᴀɪɴ
/effects - ꜱʜᴏᴡ ᴄᴜʀʀᴇɴᴛ
/reset - ʀᴇꜱᴇᴛ ᴀʟʟ
────────────────────
⚡ **ᴀᴅᴠᴀɴᴄᴇᴅ ᴇꜰꜰᴇᴄᴛꜱ**
/a1 - ᴀᴅᴠᴀɴᴄᴇᴅ ᴄᴏɴᴛʀᴏʟ
────────────────────
📊 **ᴜᴛɪʟɪᴛʏ**
/ping - ᴄʜᴇᴄᴋ ʙᴏᴛ
/stats - ʙᴏᴛ ꜱᴛᴀᴛꜱ
/status - ꜱʏꜱᴛᴇᴍ ꜱᴛᴀᴛᴜꜱ
/list - ꜰᴏʀᴡᴀʀᴅɪɴɢ ʟɪꜱᴛ
/id - ɢᴇᴛ ᴄʜᴀᴛ ɪᴅ
/panel - ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ
────────────────────
👤 **ᴜꜱᴇʀ ᴍɢᴍᴛ** (ᴏᴡɴᴇʀ)
/approve - ᴀᴅᴅ ᴜꜱᴇʀ
/disapprove - ʀᴇᴍᴏᴠᴇ
/userlist - ʟɪꜱᴛ ᴜꜱᴇʀꜱ
/setrecordgroup - ᴄʜᴀɴɢᴇ ꜱᴏᴜʀᴄᴇ
/restart - ʀᴇꜱᴛᴀʀᴛ ʙᴏᴛ
"""
        keyboard = build_keyboard([
            ("🏠 ʜᴏᴍᴇ", "back_start", ButtonStyle.SUCCESS)
        ], row_width=1)
        await callback_query.edit_message_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
    
    # ──────────────────────────────────────────────────────
    # ʙᴀᴄᴋ ᴛᴏ ꜱᴛᴀʀᴛ
    # ──────────────────────────────────────────────────────
    elif data == "back_start":
        user = callback_query.from_user
        first_name = escape_markdown(user.first_name or "ᴜꜱᴇʀ")
        last_name = escape_markdown(user.last_name or "")
        username = f"@{user.username}" if user.username else ""
        
        welcome_text = f"""
✨ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴀᴜᴅɪᴏ ꜰᴏʀᴡᴀʀᴅᴇʀ** ✨
────────────────────
👋 **ʜᴇʟʟᴏ, {first_name}!**
{last_name}
{username}
────────────────────
🎵 **ʀᴇᴀʟ-ᴛɪᴍᴇ ᴀᴜᴅɪᴏ ꜰᴏʀᴡᴀʀᴅɪɴɢ**
📊 **ꜱʏꜱᴛᴇᴍ:** ██████████ 100% ✅
⚡ **ꜰᴇᴀᴛᴜʀᴇꜱ:**
• ʀᴇᴀʟ-ᴛɪᴍᴇ ꜰᴏʀᴡᴀʀᴅɪɴɢ
• ᴀᴅᴠᴀɴᴄᴇᴅ ᴇꜰꜰᴇᴄᴛꜱ
• ᴠᴏʟᴜᴍᴇ ᴄᴏɴᴛʀᴏʟ
• ᴍᴜʟᴛɪ-ᴄʜᴀᴛ ꜰᴏʀᴡᴀʀᴅɪɴɢ
────────────────────
📌 **ᴜꜱᴇ /ʜᴇʟᴘ ꜰᴏʀ ᴄᴏᴍᴍᴀɴᴅꜱ**
"""
        keyboard = build_keyboard([
            ("👤 ᴏᴡɴᴇʀ", "owner", ButtonStyle.PRIMARY),
            ("📖 ʜᴇʟᴘ", "help_info", ButtonStyle.PRIMARY)
        ], row_width=2)
        
        try:
            photos = []
            async for photo in client.get_chat_photos(user.id, limit=1):
                photos.append(photo)
            
            if photos:
                photo = photos[0]
                await callback_query.edit_message_media(
                    media=photo.file_id,
                    caption=welcome_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard
                )
            else:
                await callback_query.edit_message_text(
                    welcome_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard
                )
        except Exception as e:
            logger.error(f"ʙᴀᴄᴋ_ꜱᴛᴀʀᴛ ᴇʀʀᴏʀ: {e}")
            if "MESSAGE_NOT_MODIFIED" not in str(e):
                try:
                    await callback_query.edit_message_text(
                        welcome_text,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=keyboard
                    )
                except Exception:
                    pass
    
    # ──────────────────────────────────────────────────────
    # ᴏᴡɴᴇʀ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ
    # ──────────────────────────────────────────────────────
    elif data == "owner":
        keyboard = build_keyboard([
            ("🏠 ʜᴏᴍᴇ", "back_start", ButtonStyle.SUCCESS)
        ], row_width=1)
        await callback_query.edit_message_text(
            "👤 **ᴏᴡɴᴇʀ**\n\n"
            "📌 **ᴛᴇʟᴇɢʀᴀᴍ:** @Why_not_ZarKo\n"
            "🔗 [ᴘʀᴏꜰɪʟᴇ ʟɪɴᴋ](t.me/Why_not_ZarKo)\n\n"
            "💡 **ꜰᴏʀ ꜱᴜᴘᴘᴏʀᴛ ᴏʀ Qᴜᴇʀɪᴇꜱ:**\n"
            "• ᴅᴍ ᴏɴ ᴛᴇʟᴇɢʀᴀᴍ\n"
            "• ᴜꜱᴇ /ʜᴇʟᴘ ꜰᴏʀ ᴄᴏᴍᴍᴀɴᴅꜱ",
            reply_markup=keyboard,
            disable_web_page_preview=True
        )


# ===== ꜱᴛᴀʀᴛ ᴄᴏᴍᴍᴀɴᴅ =====

@bot_app.on_message(pyro_filters.command("start"))
async def cmd_start(client, message):
    """ꜱᴛᴀʀᴛ ᴄᴏᴍᴍᴀɴᴅ ᴡɪᴛʜ ʙᴜᴛᴛᴏɴꜱ"""
    user_id = message.from_user.id if message.from_user else None
    
    # 🔐 ᴀᴜᴛʜᴇɴᴛɪᴄᴀᴛɪᴏɴ - ꜱɪʟᴇɴᴛ ɪɢɴᴏʀᴇ
    if user_id != OWNER_ID and user_id not in approved_users:
        logger.info(f"ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ /ꜱᴛᴀʀᴛ ꜰʀᴏᴍ {user_id}")
        return
    
    user = message.from_user
    first_name = escape_markdown(user.first_name or "ᴜꜱᴇʀ")
    last_name = escape_markdown(user.last_name or "")
    username = f"@{user.username}" if user.username else ""
    
    welcome_text = f"""
✨ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴀᴜᴅɪᴏ ꜰᴏʀᴡᴀʀᴅᴇʀ** ✨
────────────────────
👋 **ʜᴇʟʟᴏ, {first_name}!**
{last_name}
{username}
────────────────────
🎵 **ʀᴇᴀʟ-ᴛɪᴍᴇ ᴀᴜᴅɪᴏ ꜰᴏʀᴡᴀʀᴅɪɴɢ**
📊 **ꜱʏꜱᴛᴇᴍ:** ██████████ 100% ✅
⚡ **ꜰᴇᴀᴛᴜʀᴇꜱ:**
• ʀᴇᴀʟ-ᴛɪᴍᴇ ꜰᴏʀᴡᴀʀᴅɪɴɢ
• ᴀᴅᴠᴀɴᴄᴇᴅ ᴇꜰꜰᴇᴄᴛꜱ
• ᴠᴏʟᴜᴍᴇ ᴄᴏɴᴛʀᴏʟ
• ᴍᴜʟᴛɪ-ᴄʜᴀᴛ ꜰᴏʀᴡᴀʀᴅɪɴɢ
────────────────────
📌 **ᴜꜱᴇ /ʜᴇʟᴘ ꜰᴏʀ ᴄᴏᴍᴍᴀɴᴅꜱ**
"""
    
    keyboard = build_keyboard([
        ("👤 ᴏᴡɴᴇʀ", "owner", ButtonStyle.PRIMARY),
        ("📖 ʜᴇʟᴘ", "help_info", ButtonStyle.PRIMARY)
    ], row_width=2)
    
    try:
        photos = []
        async for photo in client.get_chat_photos(user.id, limit=1):
            photos.append(photo)
        
        if photos:
            photo = photos[0]
            await message.reply_photo(
                photo=photo.file_id,
                caption=welcome_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
            return
    except Exception as e:
        logger.debug(f"ᴄᴏᴜʟᴅ ɴᴏᴛ ɢᴇᴛ ᴘʀᴏꜰɪʟᴇ ᴘʜᴏᴛᴏ: {e}")
    
    await message.reply(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

# ===== ʜᴇʟᴘ ᴄᴏᴍᴍᴀɴᴅ =====

@bot_app.on_message(pyro_filters.command("help") & authorized_only())
async def cmd_help(client, message):
    """ꜱʜᴏᴡ ʜᴇʟᴘ ᴍᴇɴᴜ ᴡɪᴛʜ ʙᴜᴛᴛᴏɴꜱ"""
    help_text = """
📖 **ʜᴇʟᴘ ᴍᴇɴᴜ**
────────────────────
🎵 **ᴀᴜᴅɪᴏ ᴄᴏɴᴛʀᴏʟ**
/record - ꜱᴛᴀʀᴛ ʀᴇᴄᴏʀᴅɪɴɢ
/join <ɪᴅ> - ꜰᴏʀᴡᴀʀᴅ ᴛᴏ ᴄʜᴀᴛ
/rejoin - ʀᴇᴄᴏɴɴᴇᴄᴛ ᴀʟʟ
/leave <ɪᴅ> - ꜱᴛᴏᴘ ꜰᴏʀᴡᴀʀᴅɪɴɢ
/leaveall - ꜱᴛᴏᴘ ᴀʟʟ
/leaverecord - ʟᴇᴀᴠᴇ ꜱᴏᴜʀᴄᴇ
/mute - ᴍᴜᴛᴇ
/unmute - ᴜɴᴍᴜᴛᴇ
────────────────────
🎛️ **ᴇꜰꜰᴇᴄᴛꜱ**
/level <0-200> - ᴠᴏʟᴜᴍᴇ
/bass <0-60> - ʙᴀꜱꜱ
/treble <0-60> - ᴛʀᴇʙʟᴇ
/gain <0-60> - ɢᴀɪɴ
/effects - ꜱʜᴏᴡ ᴄᴜʀʀᴇɴᴛ
/reset - ʀᴇꜱᴇᴛ ᴀʟʟ
────────────────────
⚡ **ᴀᴅᴠᴀɴᴄᴇᴅ ᴇꜰꜰᴇᴄᴛꜱ**
/a1 - ᴀᴅᴠᴀɴᴄᴇᴅ ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ
────────────────────
📊 **ᴜᴛɪʟɪᴛʏ**
/ping - ᴄʜᴇᴄᴋ ʙᴏᴛ
/stats - ʙᴏᴛ ꜱᴛᴀᴛꜱ
/status - ꜱʏꜱᴛᴇᴍ ꜱᴛᴀᴛᴜꜱ
/list - ꜰᴏʀᴡᴀʀᴅɪɴɢ ʟɪꜱᴛ
/id - ɢᴇᴛ ᴄʜᴀᴛ ɪᴅ
/panel - ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ (ʙᴜᴛᴛᴏɴꜱ)
/joinlink - ᴊᴏɪɴ ᴠɪᴀ ɪɴᴠɪᴛᴇ ʟɪɴᴋ
────────────────────
👤 **ᴜꜱᴇʀ ᴍɢᴍᴛ** (ᴏᴡɴᴇʀ)
/approve - ᴀᴅᴅ ᴜꜱᴇʀ
/disapprove - ʀᴇᴍᴏᴠᴇ
/userlist - ʟɪꜱᴛ ᴜꜱᴇʀꜱ
/setrecordgroup <ɪᴅ> - ᴄʜᴀɴɢᴇ ꜱᴏᴜʀᴄᴇ
/restart - ʀᴇꜱᴛᴀʀᴛ ʙᴏᴛ
"""
    keyboard = build_keyboard([
        ("🏠 ʜᴏᴍᴇ", "back_start", ButtonStyle.SUCCESS),
        ("👤 ᴏᴡɴᴇʀ", "owner", ButtonStyle.PRIMARY)
    ], row_width=2)
    
    await message.reply(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

# ===== ᴜᴛɪʟɪᴛʏ Coᴍᴍᴀɴᴅꜱ =====

@bot_app.on_message(pyro_filters.command("id") & pyro_filters.user(OWNER_ID))
async def cmd_id(client, message):
    """ɢᴇᴛ ᴄʜᴀᴛ ɪᴅ"""
    chat_type = "ɢʀᴏᴜᴘ" if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP) else "ᴘʀɪᴠᴀᴛᴇ"
    id_msg = f"""
📱 **ᴄʜᴀᴛ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ**

────────────────────
🔢 **ᴄʜᴀᴛ ɪᴅ:** `{message.chat.id}`
📌 **ᴛʏᴘᴇ:** {chat_type}
📝 **ᴛɪᴛʟᴇ:** {message.chat.title or 'ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ'}
───────────────────

✅ **ᴄᴏᴘʏ ᴛʜɪꜱ ɪᴅ ꜰᴏʀ ᴜꜱᴇ ɪɴ ᴄᴏᴍᴍᴀɴᴅꜱ**
"""
    await message.reply(id_msg)

@bot_app.on_message(pyro_filters.command("ping") & authorized_only())
async def cmd_ping(client, message):
    """ᴄʜᴇᴄᴋ ʙᴏᴛ ᴘɪɴɢ"""
    start = time.time()
    msg = await message.reply("🏓 ᴘɪɴɢ...")
    end = time.time()
    ping = round((end - start) * 1000)
    await msg.edit_text(
        f"🏓 **ᴘᴏɴɢ!**\n\n"
        f"📡 **ᴘɪɴɢ:** `{ping}ᴍꜱ`\n"
        f"⏱️ **ᴜᴘᴛɪᴍᴇ:** `{get_uptime()}`"
    )

@bot_app.on_message(pyro_filters.command("stats") & pyro_filters.user(OWNER_ID))
async def cmd_stats(client, message):
    """ꜱʜᴏᴡ ʙᴏᴛ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ"""
    stats_msg = f"""
📊 **ʙᴏᴛ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ**

────────────────────
⏱️ **ᴜᴘᴛɪᴍᴇ:** `{get_uptime()}`
👥 **ᴀᴘᴘʀᴏᴠᴇᴅ ᴜꜱᴇʀꜱ:** {len(approved_users)}
📤 **ᴀᴄᴛɪᴠᴇ ꜰᴏʀᴡᴀʀᴅꜱ:** {len(forward_chats)}
📡 **ꜱᴏᴜʀᴄᴇ:** `{RECORD_SOURCE}`
🔊 **ᴀᴜᴅɪᴏ:** {'🔇 ᴍᴜᴛᴇᴅ' if is_muted else '🔊 ʟɪᴠᴇ'}
🎵 **ʀᴇᴄᴏʀᴅɪɴɢ:** {'🟢 ᴏɴ' if is_recording else '🔴 ᴏꜰꜰ'}
────────────────────

🎛️ **ᴀᴄᴛɪᴠᴇ ᴇꜰꜰᴇᴄᴛꜱ**
• ᴠᴏʟᴜᴍᴇ: `{audio_config['volume']}%`
• ʙᴀꜱꜱ: `{audio_config['bass']}`
• ᴛʀᴇʙʟᴇ: `{audio_config['treble']}`
• ɢᴀɪɴ: `{audio_config['gain']}`
"""
    await message.reply(stats_msg)

# ===== ᴀᴜᴅɪᴏ ᴄᴏɴᴛʀᴏʟ ᴄᴏᴍᴍᴀɴᴅꜱ =====

@bot_app.on_message(pyro_filters.command("record") & authorized_only())
async def cmd_record(client, message):
    """ꜱᴛᴀʀᴛ ʀᴇᴄᴏʀᴅɪɴɢ ꜰʀᴏᴍ ꜱᴏᴜʀᴄᴇ ɢʀᴏᴜᴘ"""
    global is_recording
    if is_recording:
        await message.reply(
            "⚠️ **ᴀʟʀᴇᴀᴅʏ ʀᴇᴄᴏʀᴅɪɴɢ!**\n\n"
            f"📡 **ꜱᴏᴜʀᴄᴇ:** `{RECORD_SOURCE}`\n"
            f"📤 **ꜰᴏʀᴡᴀʀᴅɪɴɢ:** {len(forward_chats)} ᴄʜᴀᴛꜱ"
        )
        return
    try:
        status_msg = await message.reply(
            "🔄 **ꜱᴛᴀʀᴛɪɴɢ ʀᴇᴄᴏʀᴅɪɴɢ...**\n\n"
            "📡 ᴄᴏɴɴᴇᴄᴛɪɴɢ ᴛᴏ ꜱᴏᴜʀᴄᴇ..."
        )
        success, error = await join_call_safe(RECORD_SOURCE)
        if success:
            await call_py.record(RECORD_SOURCE, RecordStream(True, AUDIO_PARAMETERS))
            is_recording = True
            record_msg = f"""
✅ **ʀᴇᴄᴏʀᴅɪɴɢ ꜱᴛᴀʀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**

────────────────────
📡 **ꜱᴏᴜʀᴄᴇ:** `{RECORD_SOURCE}`
📤 **ꜰᴏʀᴡᴀʀᴅɪɴɢ:** {len(forward_chats)} ᴄʜᴀᴛꜱ
📊 **ꜱᴛᴀᴛᴜꜱ:** 🟢 ʟɪᴠᴇ
────────────────────

🎵 **ᴀᴜᴅɪᴏ ɪꜱ ɴᴏᴡ ꜰʟᴏᴡɪɴɢ!**
"""
            await status_msg.edit_text(record_msg)
            logger.info("ʀᴇᴄᴏʀᴅɪɴɢ ꜱᴛᴀʀᴛᴇᴅ")
        else:
            await status_msg.edit_text(
                f"❌ **ꜰᴀɪʟᴇᴅ ᴛᴏ ꜱᴛᴀʀᴛ ʀᴇᴄᴏʀᴅɪɴɢ!**\n\n"
                f"⚠️ **ᴇʀʀᴏʀ:** `{error}`\n\n"
                f"💡 ᴍᴀᴋᴇ ꜱᴜʀᴇ ᴄʜᴀᴛ ɪꜱ ᴀᴄᴛɪᴠᴇ"
            )
    except Exception as e:
        await message.reply(f"❌ **ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!**\n\n⚠️ `{str(e)}`")

@bot_app.on_message(pyro_filters.command("join") & authorized_only())
async def cmd_join(client, message):
    """ꜰᴏʀᴡᴀʀᴅ ᴀᴜᴅɪᴏ ᴛᴏ ᴀ ᴄʜᴀᴛ"""
    parts = message.text.split()
    if len(parts) < 2:
        join_help = """
❌ **ᴜꜱᴀɢᴇ:** `/join <ᴄʜᴀᴛ_ɪᴅ>`

────────────────────
📌 **ᴇxᴀᴍᴘʟᴇ:**
`/join -1003929100976`

💡 **ʜᴏᴡ ᴛᴏ ɢᴇᴛ ᴄʜᴀᴛ ɪᴅ:**
• ꜰᴏʀᴡᴀʀᴅ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ @ꜱᴛᴀᴛᴜꜱʀᴏʙᴏᴛ
• ᴏʀ ᴜꜱᴇ `/ɪᴅ` ɪɴ ᴛʜᴇ ᴄʜᴀᴛ (ᴏᴡɴᴇʀ)
────────────────────

⚠️ **ɴᴏᴛᴇ:** ᴄʜᴀᴛ ɪᴅ ᴍᴜꜱᴛ ʙᴇ ɴᴜᴍᴇʀɪᴄ
"""
        await message.reply(join_help)
        return
    chat_id_str = re.sub(r'[^\d-]', '', parts[1])
    try:
        chat_id = int(chat_id_str)
        if chat_id in forward_chats:
            await message.reply(
                f"⚠️ **ᴀʟʀᴇᴀᴅʏ ꜰᴏʀᴡᴀʀᴅɪɴɢ ᴛᴏ ᴛʜɪꜱ ᴄʜᴀᴛ!**\n\n"
                f"🎯 `{chat_id}`\n"
                f"📤 **ᴛᴏᴛᴀʟ:** {len(forward_chats)} ᴄʜᴀᴛꜱ"
            )
            return
        if chat_id == RECORD_SOURCE:
            await message.reply(
                "⚠️ **ᴄᴀɴɴᴏᴛ ꜰᴏʀᴡᴀʀᴅ ᴛᴏ ꜱᴏᴜʀᴄᴇ ᴄʜᴀᴛ!**\n\n"
                f"📡 **ꜱᴏᴜʀᴄᴇ:** `{RECORD_SOURCE}`\n"
                "💡 ᴜꜱᴇ ᴀ ᴅɪꜰꜰᴇʀᴇɴᴛ ᴄʜᴀᴛ ꜰᴏʀ ꜰᴏʀᴡᴀʀᴅɪɴɢ"
            )
            return
        status_msg = await message.reply(
            f"🔄 **ᴄᴏɴɴᴇᴄᴛɪɴɢ ᴛᴏ `{chat_id}`...**\n\n"
            "📡 ᴇꜱᴛᴀʙʟɪꜱʜɪɴɢ ᴀᴜᴅɪᴏ ꜰᴏʀᴡᴀʀᴅɪɴɢ..."
        )
        success, error = await join_call_safe(chat_id)
        if success:
            forward_chats.add(chat_id)
            save_state()
            join_msg = f"""
✅ **ꜰᴏʀᴡᴀʀᴅɪɴɢ ꜱᴛᴀʀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**

────────────────────
🎯 **ᴛᴀʀɢᴇᴛ:** `{chat_id}`
📤 **ᴛᴏᴛᴀʟ ᴅᴇꜱᴛɪɴᴀᴛɪᴏɴꜱ:** {len(forward_chats)}
📊 **ꜱᴛᴀᴛᴜꜱ:** 🟢 ᴄᴏɴɴᴇᴄᴛᴇᴅ
────────────────────

🎵 **ᴀᴜᴅɪᴏ ɪꜱ ɴᴏᴡ ꜰᴏʀᴡᴀʀᴅɪɴɢ ᴛᴏ ᴛʜɪꜱ ᴄʜᴀᴛ!**
"""
            await status_msg.edit_text(join_msg)
            logger.info(f"ᴊᴏɪɴᴇᴅ {chat_id}")
        else:
            await status_msg.edit_text(
                f"❌ **ꜰᴀɪʟᴇᴅ ᴛᴏ ᴊᴏɪɴ ᴄʜᴀᴛ!**\n\n"
                f"⚠️ **ᴇʀʀᴏʀ:** `{error}`\n\n"
                f"💡 **ᴛʀᴏᴜʙʟᴇꜱʜᴏᴏᴛɪɴɢ:**\n"
                f"• ᴇɴꜱᴜʀᴇ ᴄʜᴀᴛ ɪꜱ ᴀᴄᴛɪᴠᴇ\n"
                f"• ᴄʜᴇᴄᴋ ɪꜰ ʙᴏᴛ ɪꜱ ᴀᴅᴍɪɴ\n"
                f"• ᴠᴇʀɪꜰʏ ᴄʜᴀᴛ ɪᴅ ɪꜱ ᴄᴏʀʀᴇᴄᴛ"
            )
    except ValueError:
        await message.reply(
            f"❌ **ɪɴᴠᴀʟɪᴅ ᴄʜᴀᴛ ɪᴅ ꜰᴏʀᴍᴀᴛ!**\n\n"
            f"📌 **ʏᴏᴜ ᴇɴᴛᴇʀᴇᴅ:** `{parts[1]}`\n"
            f"💡 ᴜꜱᴇ ᴀ ɴᴜᴍᴇʀɪᴄ ɪᴅ (ᴇ.ɢ., `-1003929100976`)"
        )
    except Exception as e:
        await message.reply(f"❌ **ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!**\n\n⚠️ `{str(e)}`")

# ===== ʀᴇᴊᴏɪɴ ᴄᴏᴍᴍᴀɴᴅ =====

@bot_app.on_message(pyro_filters.command("rejoin") & authorized_only())
async def cmd_rejoin(client, message):
    """ʟᴇᴀᴠᴇ ᴀɴᴅ ᴊᴏɪɴ ᴀʟʟ ᴄʜᴀᴛꜱ ᴀɢᴀɪɴ (ʀᴇᴄᴏᴠᴇʀ ꜰʀᴏᴍ ɴᴇᴛᴡᴏʀᴋ ɪꜱꜱᴜᴇꜱ)"""
    global is_recording
    
    status_msg = await message.reply(
        "🔄 **ʀᴇᴊᴏɪɴɪɴɢ ᴀʟʟ ᴄʜᴀᴛꜱ...**\n\n"
        "📡 ᴅɪꜱᴄᴏɴɴᴇᴄᴛɪɴɢ ᴀɴᴅ ʀᴇᴄᴏɴɴᴇᴄᴛɪɴɢ ᴀʟʟ ᴄᴏɴɴᴇᴄᴛɪᴏɴꜱ..."
    )
    
    # Track status
    rejoin_results = {
        "source": {"status": "❌", "error": None},
        "forwards": {"total": 0, "success": 0, "failed": 0, "errors": []}
    }
    
    # 1. Leave and rejoin source (if recording)
    was_recording = is_recording
    source_chat = RECORD_SOURCE
    
    if was_recording:
        try:
            # Leave source
            await call_py.leave_call(source_chat)
            logger.info(f"ʟᴇꜰᴛ ꜱᴏᴜʀᴄᴇ {source_chat} ꜰᴏʀ ʀᴇᴊᴏɪɴ")
            await asyncio.sleep(1)  # Small delay for cleanup
        except Exception as e:
            logger.warning(f"ᴄᴏᴜʟᴅ ɴᴏᴛ ʟᴇᴀᴠᴇ ꜱᴏᴜʀᴄᴇ: {e}")
        
        # Rejoin source
        try:
            success, error = await join_call_safe(source_chat)
            if success:
                await call_py.record(source_chat, RecordStream(True, AUDIO_PARAMETERS))
                is_recording = True
                rejoin_results["source"]["status"] = "✅"
                logger.info(f"ʀᴇᴊᴏɪɴᴇᴅ ꜱᴏᴜʀᴄᴇ {source_chat} ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ")
            else:
                is_recording = False
                rejoin_results["source"]["status"] = "❌"
                rejoin_results["source"]["error"] = error
                logger.error(f"ꜰᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴊᴏɪɴ ꜱᴏᴜʀᴄᴇ: {error}")
        except Exception as e:
            is_recording = False
            rejoin_results["source"]["status"] = "❌"
            rejoin_results["source"]["error"] = str(e)
            logger.error(f"ᴇʀʀᴏʀ ʀᴇᴊᴏɪɴɪɴɢ ꜱᴏᴜʀᴄᴇ: {e}")
    else:
        rejoin_results["source"]["status"] = "⏸️"
        rejoin_results["source"]["error"] = "ɴᴏᴛ ʀᴇᴄᴏʀᴅɪɴɢ"
    
    # 2. Rejoin all forward chats
    forward_list = list(forward_chats)
    rejoin_results["forwards"]["total"] = len(forward_list)
    
    if forward_list:
        # Leave all forward chats
        for chat_id in forward_list:
            try:
                await call_py.leave_call(chat_id)
                logger.info(f"ʟᴇꜰᴛ ꜰᴏʀᴡᴀʀᴅ ᴄʜᴀᴛ {chat_id} ꜰᴏʀ ʀᴇᴊᴏɪɴ")
            except Exception as e:
                logger.debug(f"ᴄᴏᴜʟᴅ ɴᴏᴛ ʟᴇᴀᴠᴇ {chat_id}: {e}")
        
        await asyncio.sleep(1.5)  # Give time for cleanup
        
        # Rejoin all forward chats
        for chat_id in forward_list:
            try:
                success, error = await join_call_safe(chat_id)
                if success:
                    rejoin_results["forwards"]["success"] += 1
                    logger.info(f"ʀᴇᴊᴏɪɴᴇᴅ ꜰᴏʀᴡᴀʀᴅ ᴄʜᴀᴛ {chat_id} ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ")
                else:
                    rejoin_results["forwards"]["failed"] += 1
                    rejoin_results["forwards"]["errors"].append(f"`{chat_id}`: {error[:50]}")
                    logger.error(f"ꜰᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴊᴏɪɴ {chat_id}: {error}")
                    # Remove failed chats from forward list
                    forward_chats.discard(chat_id)
            except Exception as e:
                rejoin_results["forwards"]["failed"] += 1
                rejoin_results["forwards"]["errors"].append(f"`{chat_id}`: {str(e)[:50]}")
                forward_chats.discard(chat_id)
                logger.error(f"ᴇʀʀᴏʀ ʀᴇᴊᴏɪɴɪɴɢ {chat_id}: {e}")
    else:
        rejoin_results["forwards"]["status"] = "⏸️"
        rejoin_results["forwards"]["error"] = "ɴᴏ ꜰᴏʀᴡᴀʀᴅ ᴄʜᴀᴛꜱ"
    
    save_state()

    # Build response message
    response = f"""
🔄 **ʀᴇᴊᴏɪɴ ᴄᴏᴍᴘʟᴇᴛᴇ!**

────────────────────
📡 **ꜱᴏᴜʀᴄᴇ ɢʀᴏᴜᴘ:** `{source_chat}`
{'✅ ʀᴇᴄᴏɴɴᴇᴄᴛᴇᴅ' if rejoin_results['source']['status'] == '✅' else '❌ ꜰᴀɪʟᴇᴅ' if rejoin_results['source']['status'] == '❌' else '⏸️ ɴᴏᴛ ᴀᴄᴛɪᴠᴇ'}
"""
    
    if rejoin_results['source']['error']:
        response += f"⚠️ **ᴇʀʀᴏʀ:** `{rejoin_results['source']['error']}`\n"
    
    response += f"""
────────────────────
📤 **ꜰᴏʀᴡᴀʀᴅ ꜱᴛᴀᴛᴜꜱ:**
• **ᴛᴏᴛᴀʟ:** {rejoin_results['forwards']['total']}
• **✅ ꜱᴜᴄᴄᴇꜱꜱ:** {rejoin_results['forwards']['success']}
• **❌ ꜰᴀɪʟᴇᴅ:** {rejoin_results['forwards']['failed']}
"""
    
    if rejoin_results['forwards']['errors']:
        response += "\n⚠️ **ꜰᴀɪʟᴇᴅ ᴄʜᴀᴛꜱ:**\n"
        for err in rejoin_results['forwards']['errors'][:5]:
            response += f"• {err}\n"
        if len(rejoin_results['forwards']['errors']) > 5:
            response += f"• ... ᴀɴᴅ {len(rejoin_results['forwards']['errors'])-5} ᴍᴏʀᴇ\n"
    
    response += f"""
────────────────────
📊 **ꜰɪɴᴀʟ ꜱᴛᴀᴛᴜꜱ:**
• **ʀᴇᴄᴏʀᴅɪɴɢ:** {'🟢 ᴀᴄᴛɪᴠᴇ' if is_recording else '🔴 ɪɴᴀᴄᴛɪᴠᴇ'}
• **ꜰᴏʀᴡᴀʀᴅɪɴɢ:** {len(forward_chats)} ᴄʜᴀᴛꜱ
• **ᴀᴜᴅɪᴏ:** {'🔇 ᴍᴜᴛᴇᴅ' if is_muted else '🔊 ʟɪᴠᴇ'}
────────────────────

💡 **ɴᴏᴛᴇ:** ꜰᴀɪʟᴇᴅ ᴄʜᴀᴛꜱ ᴡᴇʀᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ꜰᴏʀᴡᴀʀᴅɪɴɢ ʟɪꜱᴛ
"""
    
    await status_msg.edit_text(response)
    logger.info(f"ʀᴇᴊᴏɪɴ ᴄᴏᴍᴘʟᴇᴛᴇᴅ: ꜱᴏᴜʀᴄᴇ={rejoin_results['source']['status']}, ꜰᴏʀᴡᴀʀᴅꜱ={rejoin_results['forwards']['success']}/{rejoin_results['forwards']['total']}")

# ===== ʟᴇᴀᴠᴇ ᴄᴏᴍᴍᴀɴᴅꜱ =====

@bot_app.on_message(pyro_filters.command("leaverecord") & authorized_only())
async def cmd_leaverecord(client, message):
    """ʟᴇᴀᴠᴇ ᴛʜᴇ ꜱᴏᴜʀᴄᴇ ʀᴇᴄᴏʀᴅɪɴɢ ɢʀᴏᴜᴘ"""
    global is_recording
    try:
        status_msg = await message.reply("🔄 **ʟᴇᴀᴠɪɴɢ ꜱᴏᴜʀᴄᴇ ɢʀᴏᴜᴘ...**")
        await call_py.leave_call(RECORD_SOURCE)
        is_recording = False
        leave_msg = f"""
✅ **ʟᴇꜰᴛ ꜱᴏᴜʀᴄᴇ ɢʀᴏᴜᴘ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**

────────────────────
📡 **ꜱᴏᴜʀᴄᴇ:** `{RECORD_SOURCE}`
📊 **ꜱᴛᴀᴛᴜꜱ:** 🔴 ᴅɪꜱᴄᴏɴɴᴇᴄᴛᴇᴅ
📤 **ᴀᴄᴛɪᴠᴇ ꜰᴏʀᴡᴀʀᴅɪɴɢ:** {len(forward_chats)}
────────────────────

🎵 **ʀᴇᴄᴏʀᴅɪɴɢ ʜᴀꜱ ʙᴇᴇɴ ꜱᴛᴏᴘᴘᴇᴅ!**
"""
        await status_msg.edit_text(leave_msg)
        logger.info("ʟᴇꜰᴛ ʀᴇᴄᴏʀᴅ ɢʀᴏᴜᴘ")
    except Exception as e:
        await message.reply(f"❌ **ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!**\n\n⚠️ `{str(e)}`")

@bot_app.on_message(pyro_filters.command("leave") & authorized_only())
async def cmd_leave(client, message):
    """ʟᴇᴀᴠᴇ ᴀ ꜱᴘᴇᴄɪꜰɪᴄ ᴄʜᴀᴛ ᴏʀ ᴀʟʟ ᴄʜᴀᴛꜱ"""
    parts = message.text.split()
    if len(parts) >= 2:
        chat_id_str = re.sub(r'[^\d-]', '', parts[1])
        try:
            chat_id = int(chat_id_str)
        except ValueError:
            await message.reply(
                f"❌ **ɪɴᴠᴀʟɪᴅ ᴄʜᴀᴛ ɪᴅ!**\n\n"
                f"📌 **ʏᴏᴜ ᴇɴᴛᴇʀᴇᴅ:** `{parts[1]}`\n"
                f"💡 ᴜꜱᴇ ᴀ ɴuᴍᴇʀɪᴄ ɪᴅ (ᴇ.ɢ., `-1003929100976`)"
            )
            return
        if chat_id not in forward_chats:
            await message.reply(
                f"⚠️ **ɴᴏᴛ ꜰᴏʀᴡᴀʀᴅɪɴɢ ᴛᴏ ᴛʜɪꜱ ᴄʜᴀᴛ!**\n\n🎯 `{chat_id}`"
            )
            return
        try:
            status_msg = await message.reply(f"🔄 **ʟᴇᴀᴠɪɴɢ `{chat_id}`...**")
            await call_py.leave_call(chat_id)
            forward_chats.discard(chat_id)
            save_state()
            leave_msg = f"""
✅ **ʟᴇꜰᴛ ᴄʜᴀᴛ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**

────────────────────
🎯 **ᴄʜᴀᴛ:** `{chat_id}`
📤 **ʀᴇᴍᴀɪɴɪɴɢ ꜰᴏʀᴡᴀʀᴅɪɴɢ:** {len(forward_chats)}
📊 **ꜱᴛᴀᴛᴜꜱ:** 🔴 ᴅɪꜱᴄᴏɴɴᴇᴄᴛᴇᴅ
────────────────────

📌 **ᴀᴜᴅɪᴏ ɴᴏ ʟᴏɴɢᴇʀ ꜰʟᴏᴡꜱ ᴛᴏ ᴛʜɪꜱ ᴄʜᴀᴛ!**
"""
            await status_msg.edit_text(leave_msg)
            logger.info(f"ʟᴇꜰᴛ ᴄʜᴀᴛ {chat_id}")
        except Exception as e:
            logger.error(f"ᴄᴍᴅ_ʟᴇᴀᴠᴇ ᴇʀʀᴏʀ ꜰᴏʀ {chat_id}: {e}")
            await message.reply(f"❌ **ᴇʀʀᴏʀ ʟᴇᴀᴠɪɴɢ ᴄʜᴀᴛ!**\n\n⚠️ `{str(e)}`")
    else:
        if not forward_chats:
            await message.reply(
                "📭 **ɴᴏ ᴄʜᴀᴛꜱ ᴛᴏ ʟᴇᴀᴠᴇ!**\n\n💡 ᴜꜱᴇ `/ᴊᴏɪɴ` ᴛᴏ ꜱᴛᴀʀᴛ ꜰᴏʀᴡᴀʀᴅɪɴɢ"
            )
            return
        count = len(forward_chats)
        status_msg = await message.reply(f"🔄 **ʟᴇᴀᴠɪɴɢ ᴀʟʟ {count} ᴄʜᴀᴛꜱ...**")
        left_count = 0
        for cid in list(forward_chats):
            try:
                await call_py.leave_call(cid)
                left_count += 1
            except Exception:
                pass
        forward_chats.clear()
        save_state()
        leave_msg = f"""
✅ **ʟᴇꜰᴛ ᴀʟʟ ᴄʜᴀᴛꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**

────────────────────
📤 **ᴛᴏᴛᴀʟ ʟᴇꜰᴛ:** {left_count}/{count} ᴄʜᴀᴛꜱ
📊 **ꜱᴛᴀᴛᴜꜱ:** 🔴 ᴀʟʟ ᴅɪꜱᴄᴏɴɴᴇᴄᴛᴇᴅ
📡 **ꜱᴏᴜʀᴄᴇ:** {'🟢 ᴀᴄᴛɪᴠᴇ' if is_recording else '🔴 ɪɴᴀᴄᴛɪᴠᴇ'}
────────────────────

🎵 **ᴀʟʟ ᴀᴜᴅɪᴏ ꜰᴏʀᴡᴀʀᴅɪɴɢ ʜᴀꜱ ꜱᴛᴏᴘᴘᴇᴅ!**
"""
        await status_msg.edit_text(leave_msg)

@bot_app.on_message(pyro_filters.command("leaveall") & authorized_only())
async def cmd_leaveall(client, message):
    """ʟᴇᴀᴠᴇ ᴀʟʟ ᴄʜᴀᴛꜱ ɪɴᴄʟᴜᴅɪɴɢ ꜱᴏᴜʀᴄᴇ"""
    global is_recording
    total_forward = len(forward_chats)
    status_msg = await message.reply(
        "🔄 **ᴅɪꜱᴄᴏɴɴᴇᴄᴛɪɴɢ ᴀʟʟ ᴄʜᴀᴛꜱ...**\n\n📡 ᴄʟᴇᴀɴɪɴɢ ᴜᴘ ᴀʟʟ ᴄᴏɴɴᴇᴄᴛɪᴏɴꜱ..."
    )
    try:
        await call_py.leave_call(RECORD_SOURCE)
        is_recording = False
    except Exception:
        pass
    left_count = 0
    for cid in list(forward_chats):
        try:
            await call_py.leave_call(cid)
            left_count += 1
        except Exception:
            pass
    forward_chats.clear()
    save_state()
    leaveall_msg = f"""
✅ **ᴀʟʟ ᴄʜᴀᴛꜱ ᴅɪꜱᴄᴏɴɴᴇᴄᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**

────────────────────
📡 **ꜱᴏᴜʀᴄᴇ:** ✅ ʟᴇꜰᴛ
📤 **ꜰᴏʀᴡᴀʀᴅɪɴɢ:** {left_count}/{total_forward} ʟᴇꜰᴛ
📊 **ꜱᴛᴀᴛᴜꜱ:** 🔴 ᴀʟʟ ᴅɪꜱᴄᴏɴɴᴇᴄᴛᴇᴅ
────────────────────

🎵 **ᴇᴠᴇʀʏᴛʜɪɴɢ ʜᴀꜱ ʙᴇᴇɴ ᴄʟᴇᴀɴᴇᴅ ᴜᴘ!**
"""
    await status_msg.edit_text(leaveall_msg)
    logger.info("ʟᴇꜰᴛ ᴀʟʟ ᴄʜᴀᴛꜱ")

# ===== ᴍᴜᴛᴇ/ᴜɴᴍᴜᴛᴇ ᴄᴏᴍᴍᴀɴᴅꜱ =====

@bot_app.on_message(pyro_filters.command("mute") & authorized_only())
async def cmd_mute(client, message):
    """ᴍᴜᴛᴇ ᴀᴜᴅɪᴏ ꜰᴏʀᴡᴀʀᴅɪɴɢ"""
    global is_muted
    if is_muted:
        await message.reply(
            "🔇 **ᴀʟʀᴇᴀᴅʏ ᴍᴜᴛᴇᴅ!**\n\n"
            f"📤 **ᴀᴄᴛɪᴠᴇ ꜰᴏʀᴡᴀʀᴅɪɴɢ:** {len(forward_chats)}\n"
            "💡 ᴜꜱᴇ `/ᴜɴᴍᴜᴛᴇ` ᴛᴏ ʀᴇꜱᴜᴍᴇ"
        )
        return
    is_muted = True
    mute_msg = f"""
🔇 **ᴀᴜᴅɪᴏ ᴍᴜᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**

────────────────────
📊 **ꜱᴛᴀᴛᴜꜱ:** 🔇 ᴍᴜᴛᴇᴅ
📤 **ᴀᴄᴛɪᴠᴇ ꜰᴏʀᴡᴀʀᴅɪɴɢ:** {len(forward_chats)}
📡 **ꜱᴏᴜʀᴄᴇ:** {'🟢 ᴀᴄᴛɪᴠᴇ' if is_recording else '🔴 ɪɴᴀᴄᴛɪᴠᴇ'}
────────────────────

🔊 **ɴᴏ ᴀᴜᴅɪᴏ ɪꜱ ʙᴇɪɴɢ ꜰᴏʀᴡᴀʀᴅᴇᴅ ʀɪɢʜᴛ ɴᴏ!**
"""
    await message.reply(mute_msg)
    logger.info("ᴀᴜᴅɪᴏ ᴍᴜᴛᴇᴅ")

@bot_app.on_message(pyro_filters.command("unmute") & authorized_only())
async def cmd_unmute(client, message):
    """ᴜɴᴍᴜᴛᴇ ᴀᴜᴅɪᴏ ꜰᴏʀᴡᴀʀᴅɪɴɢ"""
    global is_muted
    if not is_muted:
        await message.reply(
            "🔊 **ɴᴏᴛ ᴍᴜᴛᴇᴅ!**\n\n"
            f"📤 **ᴀᴄᴛɪᴠᴇ ꜰᴏʀᴡᴀʀᴅɪɴɢ:** {len(forward_chats)}\n"
            "💡 ᴀᴜᴅɪᴏ ɪꜱ ᴀʟʀᴇᴀᴅʏ ꜰʟᴏᴡɪɴɢ"
        )
        return
    is_muted = False
    unmute_msg = f"""
🔊 **ᴀᴜᴅɪᴏ ᴜɴᴍᴜᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**

────────────────────
📊 **ꜱᴛᴀᴛᴜꜱ:** 🟢 ʟɪᴠᴇ
📤 **ᴀᴄᴛɪᴠᴇ ꜰᴏʀᴡᴀʀᴅɪɴɢ:** {len(forward_chats)}
📡 **ꜱᴏᴜʀᴄᴇ:** {'🟢 ᴀᴄᴛɪᴠᴇ' if is_recording else '🔴 ɪɴᴀᴄᴛɪᴠᴇ'}
────────────────────

🎵 **ᴀᴜᴅɪᴏ ɪꜱ ɴᴏᴡ ꜰʟᴏᴡɪɴɢ ᴛᴏ ᴀʟʟ ᴄʜᴀᴛꜱ!**
"""
    await message.reply(unmute_msg)
    logger.info("ᴀᴜᴅɪᴏ ᴜɴᴍᴜᴛᴇᴅ")

# ===== ᴇꜰꜰᴇᴄᴛꜱ ᴄᴏᴍᴍᴀɴᴅꜱ =====

@bot_app.on_message(pyro_filters.command("level") & authorized_only())
async def cmd_level(client, message):
    """ꜱᴇᴛ ᴠᴏʟᴜᴍᴇ ʟᴇᴠᴇʟ"""
    parts = message.text.split()
    current = audio_config['volume']
    if len(parts) < 2:
        bar = create_progress_bar(current, 200)
        await message.reply(
            f"🔊 **ᴠᴏʟᴜᴍᴇ ᴄᴏɴᴛʀᴏʟ**\n\n"
            f"📊 **ᴄᴜʀʀᴇɴᴛ:** `{current}%`\n"
            f"📈 {bar} `{current}%`\n"
            f"📌 **ꜱᴛᴀᴛᴜꜱ:** {get_effect_status(current, 200)}\n\n"
            f"💡 **ᴜꜱᴀɢᴇ:** `/level <0-200>`"
        )
        return
    try:
        level = int(parts[1])
        if 0 <= level <= 200:
            audio_config['volume'] = level
            save_state()
            bar = create_progress_bar(level, 200)
            await message.reply(
                f"✅ **ᴠᴏʟᴜᴍᴇ ᴜᴘᴅᴀᴛᴇᴅ!**\n\n"
                f"📊 **ɴᴇᴡ:** `{level}%`\n"
                f"📈 {bar} `{level}%`\n"
                f"📌 **ꜱᴛᴀᴛᴜꜱ:** {get_effect_status(level, 200)}\n\n"
                f"🎯 **ᴘʀᴇᴠɪᴏᴜꜱ:** `{current}%` → **ɴᴇᴡ:** `{level}%`"
            )
        else:
            await message.reply(
                f"❌ **ɪɴᴠᴀʟɪᴅ ʀᴀɴɢᴇ!**\n\n"
                f"📌 **ᴀʟʟᴏᴡᴇᴅ:** `0-200`\n"
                f"📊 **ʏᴏᴜ ᴇɴᴛᴇʀᴇᴅ:** `{level}`"
            )
    except ValueError:
        await message.reply(
            f"❌ **ɪɴᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ!**\n\n"
            f"📌 **ʏᴏᴜ ᴇɴᴛᴇʀᴇᴅ:** `{parts[1]}`\n"
            f"💡 ᴘʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ ɴᴜᴍᴇʀɪᴄ ᴠᴀʟᴜᴇ"
        )

@bot_app.on_message(pyro_filters.command("bass") & authorized_only())
async def cmd_bass(client, message):
    """ꜱᴇᴛ ʙᴀꜱꜱ ʙᴏᴏꜱᴛ"""
    parts = message.text.split()
    current = audio_config['bass']
    if len(parts) < 2:
        bar = create_progress_bar(current, 60)
        await message.reply(
            f"🎸 **ʙᴀꜱꜱ ʙᴏᴏꜱᴛ**\n\n"
            f"📊 **ᴄᴜʀʀᴇɴᴛ:** `{current}`\n"
            f"📈 {bar} `{current}/60`\n"
            f"📌 **ꜱᴛᴀᴛᴜꜱ:** {get_effect_status(current, 60)}\n"
            f"🔊 **ʜɪɢʜᴘᴀꜱꜱ:** {'✅ ᴏɴ' if audio_config['highpass'] else '❌ ᴏꜰꜰ'}\n\n"
            f"💡 **ᴜꜱᴀɢᴇ:** `/bass <0-60>`"
        )
        return
    try:
        level = int(parts[1])
        if 0 <= level <= 60:
            audio_config['bass'] = level
            audio_config['highpass'] = level > 0
            save_state()
            bar = create_progress_bar(level, 60)
            await message.reply(
                f"✅ **ʙᴀꜱꜱ ʙᴏᴏꜱᴛ ᴜᴘᴅᴀᴛᴇᴅ!**\n\n"
                f"📊 **ɴᴇᴡ:** `{level}`\n"
                f"📈 {bar} `{level}/60`\n"
                f"📌 **ꜱᴛᴀᴛᴜꜱ:** {get_effect_status(level, 60)}\n"
                f"🔊 **ʜɪɢʜᴘᴀꜱꜱ:** {'✅ ᴇɴᴀʙʟᴇᴅ' if level > 0 else '❌ ᴅɪꜱᴀʙʟᴇᴅ'}\n\n"
                f"🎯 **ᴘʀᴇᴠɪᴏᴜꜱ:** `{current}` → **ɴᴇᴡ:** `{level}`"
            )
        else:
            await message.reply(
                f"❌ **ɪɴᴠᴀʟɪᴅ ʀᴀɴɢᴇ!**\n\n"
                f"📌 **ᴀʟʟᴏᴡᴇᴅ:** `0-60`\n"
                f"📊 **ʏᴏᴜ ᴇɴᴛᴇʀᴇᴅ:** `{level}`"
            )
    except ValueError:
        await message.reply(
            f"❌ **ɪɴᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ!**\n\n"
            f"📌 **ʏᴏᴜ ᴇɴᴛᴇʀᴇᴅ:** `{parts[1]}`\n"
            f"💡 ᴘʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ ɴᴜᴍᴇʀɪᴄ ᴠᴀʟᴜᴇ"
        )

@bot_app.on_message(pyro_filters.command("treble") & authorized_only())
async def cmd_treble(client, message):
    """ꜱᴇᴛ ᴛʀᴇʙʟᴇ ʙᴏᴏꜱᴛ"""
    parts = message.text.split()
    current = audio_config['treble']
    if len(parts) < 2:
        bar = create_progress_bar(current, 60)
        await message.reply(
            f"🎵 **ᴛʀᴇʙʟᴇ ʙᴏᴏꜱᴛ**\n\n"
            f"📊 **ᴄᴜʀʀᴇɴᴛ:** `{current}`\n"
            f"📈 {bar} `{current}/60`\n"
            f"📌 **ꜱᴛᴀᴛᴜꜱ:** {get_effect_status(current, 60)}\n\n"
            f"💡 **ᴜꜱᴀɢᴇ:** `/treble <0-60>`"
        )
        return
    try:
        level = int(parts[1])
        if 0 <= level <= 60:
            audio_config['treble'] = level
            save_state()
            bar = create_progress_bar(level, 60)
            await message.reply(
                f"✅ **ᴛʀᴇʙʟᴇ ʙᴏᴏꜱᴛ ᴜᴘᴅᴀᴛᴇᴅ!**\n\n"
                f"📊 **ɴᴇᴡ:** `{level}`\n"
                f"📈 {bar} `{level}/60`\n"
                f"📌 **ꜱᴛᴀᴛᴜꜱ:** {get_effect_status(level, 60)}\n\n"
                f"🎯 **ᴘʀᴇᴠɪᴏᴜꜱ:** `{current}` → **ɴᴇᴡ:** `{level}`"
            )
        else:
            await message.reply(
                f"❌ **ɪɴᴠᴀʟɪᴅ ʀᴀɴɢᴇ!**\n\n"
                f"📌 **ᴀʟʟᴏᴡᴇᴅ:** `0-60`\n"
                f"📊 **ʏᴏᴜ ᴇɴᴛᴇʀᴇᴅ:** `{level}`"
            )
    except ValueError:
        await message.reply(
            f"❌ **ɪɴᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ!**\n\n"
            f"📌 **ʏᴏᴜ ᴇɴᴛᴇʀᴇᴅ:** `{parts[1]}`\n"
            f"💡 ᴘʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ ɴᴜᴍᴇʀɪᴄ ᴠᴀʟᴜᴇ"
        )


@bot_app.on_message(pyro_filters.command("gain") & authorized_only())
async def cmd_gain(client, message):
    """ꜱᴇᴛ ɢᴀɪɴ"""
    parts = message.text.split()
    current = audio_config['gain']
    if len(parts) < 2:
        bar = create_progress_bar(current, 60)
        await message.reply(
            f"📈 **ꜱᴏꜰᴛ ɢᴀɪɴ**\n\n"
            f"📊 **ᴄᴜʀʀᴇɴᴛ:** `{current}`\n"
            f"📈 {bar} `{current}/60`\n"
            f"📌 **ꜱᴛᴀᴛᴜꜱ:** {get_effect_status(current, 60)}\n\n"
            f"💡 **ᴜꜱᴀɢᴇ:** `/gain <0-60>`"
        )
        return
    try:
        level = int(parts[1])
        if 0 <= level <= 60:
            audio_config['gain'] = level
            save_state()
            bar = create_progress_bar(level, 60)
            await message.reply(
                f"✅ **ꜱᴏꜰᴛ ɢᴀɪɴ ᴜᴘᴅᴀᴛᴇᴅ!**\n\n"
                f"📊 **ɴᴇᴡ:** `{level}`\n"
                f"📈 {bar} `{level}/60`\n"
                f"📌 **ꜱᴛᴀᴛᴜꜱ:** {get_effect_status(level, 60)}\n\n"
                f"🎯 **ᴘʀᴇᴠɪᴏᴜꜱ:** `{current}` → **ɴᴇᴡ:** `{level}`"
            )
        else:
            await message.reply(
                f"❌ **ɪɴᴠᴀʟɪᴅ ʀᴀɴɢᴇ!**\n\n"
                f"📌 **ᴀʟʟᴏᴡᴇᴅ:** `0-60`\n"
                f"📊 **ʏᴏᴜ ᴇɴᴛᴇʀᴇᴅ:** `{level}`"
            )
    except ValueError:
        await message.reply(
            f"❌ **ɪɴᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ!**\n\n"
            f"📌 **ʏᴏᴜ ᴇɴᴛᴇʀᴇᴅ:** `{parts[1]}`\n"
            f"💡 ᴘʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ ɴᴜᴍᴇʀɪᴄ ᴠᴀʟᴜᴇ"
        )

@bot_app.on_message(pyro_filters.command("a1") & authorized_only())
async def cmd_advanced(client, message):
    """ᴀᴅᴠᴀɴᴄᴇᴅ ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ ᴄᴏɴᴛʀᴏʟ"""
    parts = message.text.split()
    
    if len(parts) < 2:
        # Show current status with visual indicators
        adv = ADVANCED_AUDIO_CONFIG
        
        # Create status bars for each effect
        def get_bar(val):
            normalized = (val + 50) / 100
            filled = int(normalized * 10)
            return "█" * filled + "░" * (10 - filled)
        
        def get_status(val):
            if val == 0:
                return "⚪ ᴏꜰꜰ"
            elif val > 0:
                return "🟢 ᴇɴʜᴀɴᴄᴇᴅ"
            else:
                return "🔵 ʀᴇᴅᴜᴄᴇᴅ"
        
        status_msg = f"""
🎛️ **ᴀᴅᴠᴀɴᴄᴇᴅ ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ**

────────────────────
**ᴄᴜʀʀᴇɴᴛ ꜱᴇᴛᴛɪɴɢꜱ:**

• **ɴꜱ** (ɴᴏɪꜱᴇ ꜱᴜᴘᴘʀᴇꜱꜱɪᴏɴ): `{adv['ns']:+.0f}` {get_bar(adv['ns'])} {get_status(adv['ns'])}
• **ʜᴘꜰ** (ʜɪɢʜ ᴘᴀꜱꜱ ꜰɪʟᴛᴇʀ): `{adv['hpf']:+.0f}` {get_bar(adv['hpf'])} {get_status(adv['hpf'])}
• **ᴅᴇ** (ᴅᴇ-ᴇꜱꜱᴇʀ): `{adv['deesser']:+.0f}` {get_bar(adv['deesser'])} {get_status(adv['deesser'])}
• **ᴇQ** (ᴘʀᴇꜱᴇɴᴄᴇ ᴇQ): `{adv['presence_eq']:+.0f}` {get_bar(adv['presence_eq'])} {get_status(adv['presence_eq'])}
• **ʟᴏᴜᴅ** (ʟᴏᴜᴅɴᴇꜱꜱ ɴᴏʀᴍ): `{adv['loudness']:+.0f}` {get_bar(adv['loudness'])} {get_status(adv['loudness'])}
• **ʟɪᴍ** (ʟᴏᴏᴋ-ᴀʜᴇᴀᴅ ʟɪᴍɪᴛᴇʀ): `{adv['limiter']:+.0f}` {get_bar(adv['limiter'])} {get_status(adv['limiter'])}
• **ɢᴀᴛᴇ** (ɴᴏɪꜱᴇ ɢᴀᴛᴇ): `{adv['noisegate']:+.0f}` {get_bar(adv['noisegate'])} {get_status(adv['noisegate'])}
• **ᴅᴄ** (ᴅᴄ ᴏꜰꜰꜱᴇᴛ): `{adv['dc_offset']:+.0f}` {get_bar(adv['dc_offset'])} {get_status(adv['dc_offset'])}
• **ꜱᴀᴛ** (ꜱᴏꜰᴛ ꜱᴀᴛᴜʀᴀᴛɪᴏɴ): `{adv['saturation']:+.0f}` {get_bar(adv['saturation'])} {get_status(adv['saturation'])}
• **ꜱᴛ** (ꜱᴛᴇʀᴇᴏ ᴡɪᴅᴛʜ): `{adv['stereo_width']:+.0f}` {get_bar(adv['stereo_width'])} {get_status(adv['stereo_width'])}

────────────────────
📌 **ᴜꜱᴀɢᴇ:** `/a1 <ᴇꜰꜰᴇᴄᴛ> <ᴠᴀʟᴜᴇ>`

**ᴇꜰꜰᴇᴄᴛꜱ:**
• `ns`   - ɴᴏɪꜱᴇ ꜱᴜᴘᴘʀᴇꜱꜱɪᴏɴ (-50 ᴛᴏ +50)
• `hpf`  - ʜɪɢʜ ᴘᴀꜱꜱ ꜰɪʟᴛᴇʀ (-50 ᴛᴏ +50)
• `de`   - ᴅᴇ-ᴇꜱꜱᴇʀ (-50 ᴛᴏ +50)
• `eq`   - ᴘʀᴇꜱᴇɴᴄᴇ ᴇQ (-50 ᴛᴏ +50)
• `loud` - ʟᴏᴜᴅɴᴇꜱꜱ ɴᴏʀᴍ (-50 ᴛᴏ +50)
• `lim`  - ʟɪᴍɪᴛᴇʀ (-50 ᴛᴏ +50)
• `gate` - ɴᴏɪꜱᴇ ɢᴀᴛᴇ (-50 ᴛᴏ +50)
• `dc`   - ᴅᴄ ᴏꜰꜰꜱᴇᴛ (-50 ᴛᴏ +50)
• `sat`  - ꜱᴀᴛᴜʀᴀᴛɪᴏɴ (-50 ᴛᴏ +50)
• `st`   - ꜱᴛᴇʀᴇᴏ ᴡɪᴅᴛʜ (-50 ᴛᴏ +50)

**ᴇxᴀᴍᴘʟᴇꜱ:**
• `/a1 ns 30` - ɴᴏɪꜱᴇ ꜱᴜᴘᴘʀᴇꜱꜱɪᴏɴ +30
• `/a1 eq -15` - ᴘʀᴇꜱᴇɴᴄᴇ ᴇQ -15
• `/a1 loud 40` - ʟᴏᴜᴅɴᴇꜱꜱ ɴᴏʀᴍ +40
• `/a1 reset` - ʀᴇꜱᴇᴛ ᴀʟʟ ᴀᴅᴠᴀɴᴄᴇᴅ ᴇꜰꜰᴇᴄᴛꜱ
"""
        await message.reply(status_msg)
        return
    
    command = parts[1].lower()
    
    # Handle reset
    if command == "reset":
        old_advanced = ADVANCED_AUDIO_CONFIG.copy()
        for key in ADVANCED_AUDIO_CONFIG:
            ADVANCED_AUDIO_CONFIG[key] = 0
        save_state()
        
        reset_msg = f"""
🔄 **ᴀᴅᴠᴀɴᴄᴇᴅ ᴇꜰꜰᴇᴄᴛꜱ ʀᴇꜱᴇᴛ!**

────────────────────
📊 **ᴀʟʟ ᴀᴅᴠᴀɴᴄᴇᴅ ᴇꜰꜰᴇᴄᴛꜱ ꜱᴇᴛ ᴛᴏ `0`**

✅ ɴᴏɪꜱᴇ ꜱᴜᴘᴘʀᴇꜱꜱɪᴏɴ: `{old_advanced['ns']:+.0f}` → `0`
✅ ʜɪɢʜ ᴘᴀꜱꜱ ꜰɪʟᴛᴇʀ: `{old_advanced['hpf']:+.0f}` → `0`
✅ ᴅᴇ-ᴇꜱꜱᴇʀ: `{old_advanced['deesser']:+.0f}` → `0`
✅ ᴘʀᴇꜱᴇɴᴄᴇ ᴇQ: `{old_advanced['presence_eq']:+.0f}` → `0`
✅ ʟᴏᴜᴅɴᴇꜱꜱ ɴᴏʀᴍ: `{old_advanced['loudness']:+.0f}` → `0`
✅ ʟɪᴍɪᴛᴇʀ: `{old_advanced['limiter']:+.0f}` → `0`
✅ ɴᴏɪꜱᴇ ɢᴀᴛᴇ: `{old_advanced['noisegate']:+.0f}` → `0`
✅ ᴅᴄ ᴏꜰꜰꜱᴇᴛ: `{old_advanced['dc_offset']:+.0f}` → `0`
✅ ꜱᴀᴛᴜʀᴀᴛɪᴏɴ: `{old_advanced['saturation']:+.0f}` → `0`
✅ ꜱᴛᴇʀᴇᴏ ᴡɪᴅᴛʜ: `{old_advanced['stereo_width']:+.0f}` → `0`

────────────────────
💡 **ᴛɪᴘ:** ᴜꜱᴇ `/ʀᴇꜱᴇᴛ` ꜰᴏʀ ᴄᴏᴍᴘʟᴇᴛᴇ ʀᴇꜱᴇᴛ (ʙᴀꜱɪᴄ + ᴀᴅᴠᴀɴᴄᴇᴅ)
"""
        await message.reply(reset_msg)
        return
    
    # Check if value is provided
    if len(parts) < 3:
        await message.reply(
            f"❌ **ᴜꜱᴀɢᴇ:** `/a1 {command} <ᴠᴀʟᴜᴇ>`\n\n"
            f"📌 **ᴠᴀʟᴜᴇ ʀᴀɴɢᴇ:** `-50` ᴛᴏ `+50`\n"
            f"💡 **ᴇxᴀᴍᴘʟᴇ:** `/a1 {command} 30`"
        )
        return
    
    try:
        value = int(parts[2])
        if value < -50 or value > 50:
            await message.reply(
                f"❌ **ɪɴᴠᴀʟɪᴅ ᴠᴀʟᴜᴇ!**\n\n"
                f"📌 **ʀᴀɴɢᴇ:** `-50` ᴛᴏ `+50`\n"
                f"📊 **ʏᴏᴜ ᴇɴᴛᴇʀᴇᴅ:** `{value}`"
            )
            return
        
        # Effect mapping
        effect_map = {
            'ns': 'ns',
            'hpf': 'hpf',
            'de': 'deesser',
            'eq': 'presence_eq',
            'loud': 'loudness',
            'lim': 'limiter',
            'gate': 'noisegate',
            'dc': 'dc_offset',
            'sat': 'saturation',
            'st': 'stereo_width'
        }
        
        if command not in effect_map:
            await message.reply(
                f"❌ **ᴜɴᴋɴᴏᴡɴ ᴇꜰꜰᴇᴄᴛ!**\n\n"
                f"📌 **ᴀᴠᴀɪʟᴀʙʟᴇ:** `ns`, `hpf`, `de`, `eq`, `loud`, `lim`, `gate`, `dc`, `sat`, `st`"
            )
            return
        
        key = effect_map[command]
        old_value = ADVANCED_AUDIO_CONFIG[key]
        ADVANCED_AUDIO_CONFIG[key] = value
        save_state()
        
        # Effect names for display
        effect_names = {
            'ns': 'ɴᴏɪꜱᴇ ꜱᴜᴘᴘʀᴇꜱꜱɪᴏɴ',
            'hpf': 'ʜɪɢʜ ᴘᴀꜱꜱ ꜰɪʟᴛᴇʀ',
            'deesser': 'ᴅᴇ-ᴇꜱꜱᴇʀ',
            'presence_eq': 'ᴘʀᴇꜱᴇɴᴄᴇ ᴇQ',
            'loudness': 'ʟᴏᴜᴅɴᴇꜱꜱ ɴᴏʀᴍᴀʟɪᴢᴀᴛɪᴏɴ',
            'limiter': 'ʟᴏᴏᴋ-ᴀʜᴇᴀᴅ ʟɪᴍɪᴛᴇʀ',
            'noisegate': 'ɴᴏɪꜱᴇ ɢᴀᴛᴇ / ᴇxᴘᴀɴᴅᴇʀ',
            'dc_offset': 'ᴅᴄ ᴏꜰꜰꜱᴇᴛ ʀᴇᴍᴏᴠᴀʟ',
            'saturation': 'ꜱᴏꜰᴛ ꜱᴀᴛᴜʀᴀᴛɪᴏɴ / ᴇxᴄɪᴛᴇʀ',
            'stereo_width': 'ꜱᴛᴇʀᴇᴏ ᴡɪᴅᴛʜ / ᴍᴏɴᴏ ᴏᴘᴛɪᴍɪᴢᴀᴛɪᴏɴ'
        }
        
        # Create visual bar
        bar_length = 10
        normalized = (value + 50) / 100
        filled = int(normalized * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        # Status text
        if value == 0:
            status = "⚪ ᴏꜰꜰ"
            emoji = "⚪"
        elif value > 0:
            status = "🟢 ᴇɴʜᴀɴᴄᴇᴅ"
            emoji = "🟢"
        else:
            status = "🔵 ʀᴇᴅᴜᴄᴇᴅ"
            emoji = "🔵"
        
        # Response message
        response = f"""
✅ **ᴀᴅᴠᴀɴᴄᴇᴅ ᴇꜰꜰᴇᴄᴛ ᴜᴘᴅᴀᴛᴇᴅ!**

────────────────────
🎛️ **ᴇꜰꜰᴇᴄᴛ:** {effect_names[key]}
📊 **ᴏʟᴅ:** `{old_value:+.0f}` → **ɴᴇᴡ:** `{value:+.0f}`
📈 **ʟᴇᴠᴇʟ:** {bar} `{value:+.0f}`
📌 **ꜱᴛᴀᴛᴜꜱ:** {status}

────────────────────
💡 **ᴜꜱᴇ `/a1` ᴛᴏ ꜱʜᴏᴡ ᴀʟʟ ꜱᴇᴛᴛɪɴɢꜱ**
"""
        await message.reply(response)
        
    except ValueError:
        await message.reply(
            f"❌ **ɪɴᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ!**\n\n"
            f"📌 **ʏᴏᴜ ᴇɴᴛᴇʀᴇᴅ:** `{parts[2]}`\n"
            f"💡 ᴘʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ ɴᴜᴍᴇʀɪᴄ ᴠᴀʟᴜᴇ (-50 ᴛᴏ +50)"
        )
        
@bot_app.on_message(pyro_filters.command("reset") & authorized_only())
async def cmd_reset(client, message):
    """ʀᴇꜱᴇᴛ ᴀʟʟ ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ (ʙᴀꜱɪᴄ + ᴀᴅᴠᴀɴᴄᴇᴅ)"""
    global audio_config
    
    # Save old configs for comparison
    old_config = audio_config.copy()
    old_advanced = ADVANCED_AUDIO_CONFIG.copy()
    
    # Reset basic audio config
    audio_config = {
        'volume': 100,
        'bass': 0,
        'treble': 0,
        'gain': 0,
        'compressor': True,
        'limiter': True,
        'highpass': False,
        'lowpass': False
    }
    
    # Reset advanced audio config (all to 0)
    for key in ADVANCED_AUDIO_CONFIG:
        ADVANCED_AUDIO_CONFIG[key] = 0
    
    save_state()
    
    # Check if advanced effects were active
    advanced_was_active = any(old_advanced[key] != 0 for key in old_advanced)
    
    reset_msg = f"""
✅ **ᴀʟʟ ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ ʀᴇꜱᴇᴛ!**

────────────────────
🔊 **ᴠᴏʟᴜᴍᴇ:** `{old_config['volume']}%` → `{audio_config['volume']}%` ✅
🎸 **ʙᴀꜱꜱ:** `{old_config['bass']}` → `{audio_config['bass']}` ✅
🎵 **ᴛʀᴇʙʟᴇ:** `{old_config['treble']}` → `{audio_config['treble']}` ✅
📈 **ɢᴀɪɴ:** `{old_config['gain']}` → `{audio_config['gain']}` ✅

────────────────────
⚙️ **ᴀᴅᴠᴀɴᴄᴇᴅ ᴇꜰꜰᴇᴄᴛꜱ:** {'🟢 ᴄʟᴇᴀʀᴇᴅ' if advanced_was_active else '⚪ ᴡᴇʀᴇ ᴀʟʀᴇᴀᴅʏ ᴏꜰꜰ'}
• **ɴꜱ:** `{old_advanced['ns']:+.0f}` → `0` ✅
• **ʜᴘꜰ:** `{old_advanced['hpf']:+.0f}` → `0` ✅
• **ᴅᴇ-ᴇꜱꜱᴇʀ:** `{old_advanced['deesser']:+.0f}` → `0` ✅
• **ᴘʀᴇꜱᴇɴᴄᴇ ᴇQ:** `{old_advanced['presence_eq']:+.0f}` → `0` ✅
• **ʟᴏᴜᴅɴᴇꜱꜱ:** `{old_advanced['loudness']:+.0f}` → `0` ✅
• **ʟɪᴍɪᴛᴇʀ:** `{old_advanced['limiter']:+.0f}` → `0` ✅
• **ɴᴏɪꜱᴇ ɢᴀᴛᴇ:** `{old_advanced['noisegate']:+.0f}` → `0` ✅
• **ᴅᴄ ᴏꜰꜰꜱᴇᴛ:** `{old_advanced['dc_offset']:+.0f}` → `0` ✅
• **ꜱᴀᴛᴜʀᴀᴛɪᴏɴ:** `{old_advanced['saturation']:+.0f}` → `0` ✅
• **ꜱᴛᴇʀᴇᴏ ᴡɪᴅᴛʜ:** `{old_advanced['stereo_width']:+.0f}` → `0` ✅

────────────────────
📊 **ꜱᴛᴀᴛᴜꜱ:** 🟢 ꜰᴀᴄᴛᴏʀʏ ᴅᴇꜰᴀᴜʟᴛ ʀᴇꜱᴛᴏʀᴇᴅ
🎯 **ᴇꜰꜰᴇᴄᴛꜱ:** ᴀʟʟ ʙᴀꜱɪᴄ + ᴀᴅᴠᴀɴᴄᴇᴅ ᴄʟᴇᴀʀᴇᴅ
💡 **ᴛɪᴘ:** ᴜꜱᴇ `/a1` ᴛᴏ ꜱᴇᴛ ᴀᴅᴠᴀɴᴄᴇᴅ ᴇꜰꜰᴇᴄᴛꜱ
"""
    await message.reply(reset_msg)
    logger.info("ᴀʟʟ ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ (ʙᴀꜱɪᴄ + ᴀᴅᴠᴀɴᴄᴇᴅ) ʀᴇꜱᴇᴛ ᴛᴏ ᴅᴇꜰᴀᴜʟᴛ")


@bot_app.on_message(pyro_filters.command("effects") & authorized_only())
async def cmd_effects(client, message):
    """ꜱʜᴏᴡ ᴄᴜʀʀᴇɴᴛ ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ ɪɴᴄʟᴜᴅɪɴɢ ᴀᴅᴠᴀɴᴄᴇᴅ"""
    config = audio_config
    adv_config = ADVANCED_AUDIO_CONFIG
    scipy_status = "✅ ᴀᴅᴠᴀɴᴄᴇᴅ ᴀᴠᴀɪʟᴀʙʟᴇ" if SCIPY_AVAILABLE else "❌ ʙᴀꜱɪᴄ ᴏɴʟʏ"
    
    vol_bar = create_progress_bar(config['volume'], 200)
    bass_bar = create_progress_bar(config['bass'], 60)
    treble_bar = create_progress_bar(config['treble'], 60)
    gain_bar = create_progress_bar(config['gain'], 60)
    
    advanced_active = any(adv_config[key] != 0 for key in adv_config)
    
    effects_msg = f"""
🎛️ **ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ ᴅᴀꜱʜʙᴏᴀʀᴅ**

────────────────────
🔊 **ᴠᴏʟᴜᴍᴇ:** `{config['volume']}%`
{vol_bar} `{config['volume']}%`

🎸 **ʙᴀꜱꜱ:** `{config['bass']}/60`
{bass_bar} `{config['bass']}/60`

🎵 **ᴛʀᴇʙʟᴇ:** `{config['treble']}/60`
{treble_bar} `{config['treble']}/60`

📈 **ɢᴀɪɴ:** `{config['gain']}/60`
{gain_bar} `{config['gain']}/60`

────────────────────
⚙️ **ᴀᴅᴠᴀɴᴄᴇᴅ ᴇꜰꜰᴇᴄᴛꜱ** {'🟢 ᴀᴄᴛɪᴠᴇ' if advanced_active else '⚪ ɪɴᴀᴄᴛɪᴠᴇ'}
• **ɴꜱ:** `{adv_config['ns']:+.0f}`
• **ʜᴘꜰ:** `{adv_config['hpf']:+.0f}`
• **ᴅᴇ-ᴇꜱꜱᴇʀ:** `{adv_config['deesser']:+.0f}`
• **ᴘʀᴇꜱᴇɴᴄᴇ ᴇQ:** `{adv_config['presence_eq']:+.0f}`
• **ʟᴏᴜᴅɴᴇꜱꜱ:** `{adv_config['loudness']:+.0f}`
• **ʟɪᴍɪᴛᴇʀ:** `{adv_config['limiter']:+.0f}`
• **ɴᴏɪꜱᴇ ɢᴀᴛᴇ:** `{adv_config['noisegate']:+.0f}`
• **ᴅᴄ ᴏꜰꜰꜱᴇᴛ:** `{adv_config['dc_offset']:+.0f}`
• **ꜱᴀᴛᴜʀᴀᴛɪᴏɴ:** `{adv_config['saturation']:+.0f}`
• **ꜱᴛᴇʀᴇᴏ ᴡɪᴅᴛʜ:** `{adv_config['stereo_width']:+.0f}`

────────────────────
⚙️ **ꜰᴇᴀᴛᴜʀᴇꜱ**
• ᴄᴏᴍᴘʀᴇꜱꜱᴏʀ: {'✅ ᴇɴᴀʙʟᴇᴅ' if config['compressor'] else '❌ ᴅɪꜱᴀʙʟᴇᴅ'}
• ʟɪᴍɪᴛᴇʀ: {'✅ ᴇɴᴀʙʟᴇᴅ' if config['limiter'] else '❌ ᴅɪꜱᴀʙʟᴇᴅ'}
• ʜɪɢʜᴘᴀꜱꜱ: {'✅ ᴇɴᴀʙʟᴇᴅ' if config['highpass'] else '❌ ᴅɪꜱᴀʙʟᴇᴅ'}
• ʟᴏᴡᴘᴀꜱꜱ: {'✅ ᴇɴᴀʙʟᴇᴅ' if config['lowpass'] else '❌ ᴅɪꜱᴀʙʟᴇᴅ'}

📦 **ꜱᴄɪᴘʏ:** {scipy_status}

💡 **ᴜꜱᴇ `/a1` ꜰᴏʀ ᴀᴅᴠᴀɴᴄᴇᴅ ᴇꜰꜰᴇᴄᴛꜱ ᴄᴏɴᴛʀᴏʟ**
"""
    await message.reply(effects_msg)

@bot_app.on_message(pyro_filters.command("status") & authorized_only())
async def cmd_status(client, message):
    """ꜱʜᴏᴡ ᴄᴏᴍᴘʟᴇᴛᴇ ʙᴏᴛ ꜱᴛᴀᴛᴜꜱ"""
    recording_status = "🟢 ᴀᴄᴛɪᴠᴇ" if is_recording else "🔴 ɪɴᴀᴄᴛɪᴠᴇ"
    audio_status = "🔇 ᴍᴜᴛᴇᴅ" if is_muted else "🔊 ʟɪᴠᴇ"
    forward_count = len(forward_chats)
    forward_list = ""
    if forward_chats:
        forward_list = "\n".join(f"• `{c}`" for c in list(forward_chats)[:10])
        if len(forward_chats) > 10:
            forward_list += f"\n• ... ᴀɴᴅ {len(forward_chats)-10} ᴍᴏʀᴇ"
    else:
        forward_list = "• ɴᴏɴᴇ"
    status_msg = f"""
📊 **ʙᴏᴛ ꜱᴛᴀᴛᴜꜱ ᴅᴀꜱʜʙᴏᴀʀᴅ**

────────────────────
🔴 **ʀᴇᴄᴏʀᴅɪɴɢ:** {recording_status}
📡 **ꜱᴏᴜʀᴄᴇ:** `{RECORD_SOURCE}`
🔊 **ᴀᴜᴅɪᴏ:** {audio_status}
📤 **ꜰᴏʀᴡᴀʀᴅɪɴɢ:** {forward_count} ᴄʜᴀᴛꜱ
⏱️ **ᴜᴘᴛɪᴍᴇ:** `{get_uptime()}`
────────────────────

📤 **ᴀᴄᴛɪᴠᴇ ꜰᴏʀᴡᴀʀᴅɪɴɢ:**
{forward_list}

────────────────────
🎵 **ᴀᴄᴛɪᴠᴇ ᴇꜰꜰᴇᴄᴛꜱ:**
• ᴠᴏʟᴜᴍᴇ: `{audio_config['volume']}%`
• ʙᴀꜱꜱ: `{audio_config['bass']}`
• ᴛʀᴇʙʟᴇ: `{audio_config['treble']}`
• ɢᴀɪɴ: `{audio_config['gain']}`

📊 **ꜱʏꜱᴛᴇᴍ:** {'🟢 ꜱᴛᴀʙʟᴇ' if is_recording else '🟡 ꜱᴛᴀɴᴅʙʏ'}
"""
    await message.reply(status_msg)

@bot_app.on_message(pyro_filters.command("list") & authorized_only())
async def cmd_list(client, message):
    """ꜱʜᴏᴡ ʟɪꜱᴛ ᴏꜰ ꜰᴏʀᴡᴀʀᴅᴇᴅ ᴄʜᴀᴛꜱ"""
    if not forward_chats:
        await message.reply(
            "📭 **ɴᴏ ᴀᴄᴛɪᴠᴇ ꜰᴏʀᴡᴀʀᴅɪɴɢ**\n\n"
            "💡 ᴜꜱᴇ `/ᴊᴏɪɴ <ᴄʜᴀᴛ_ɪᴅ>` ᴛᴏ ꜱᴛᴀʀᴛ\n"
            "📌 ᴇxᴀᴍᴘʟᴇ: `/ᴊᴏɪɴ -1003929100976`"
        )
        return
    chat_list = []
    for idx, cid in enumerate(forward_chats, 1):
        chat_list.append(f"`{idx}.` `{cid}`")
    list_msg = f"""
📤 **ꜰᴏʀᴡᴀʀᴅɪɴɢ ᴄʜᴀᴛꜱ ʟɪꜱᴛ**

────────────────────
📊 **ᴛᴏᴛᴀʟ:** {len(forward_chats)} ᴄʜᴀᴛꜱ
────────────────────

{chr(10).join(chat_list)}

────────────────────
💡 **ᴛɪᴘꜱ:**
• ᴜꜱᴇ `/ʟᴇᴀᴠᴇ <ɪᴅ>` ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴀ ᴄʜᴀᴛ
• ᴜꜱᴇ `/ʟᴇᴀᴠᴇᴀʟʟ` ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴀʟʟ
"""
    await message.reply(list_msg)

# ===== ꜱᴇᴛ ʀᴇᴄᴏʀᴅ ɢʀᴏᴜᴘ ᴄᴏᴍᴍᴀɴᴅ =====

@bot_app.on_message(pyro_filters.command("setrecordgroup") & pyro_filters.user(OWNER_ID))
async def cmd_setrecordgroup(client, message):
    """ꜱᴇᴛ ᴛʜᴇ ꜱᴏᴜʀᴄᴇ ʀᴇᴄᴏʀᴅɪɴɢ ɢʀᴏᴜᴘ (OWNER ONLY)"""
    global RECORD_SOURCE, is_recording
    
    parts = message.text.split()
    
    if len(parts) < 2:
        await message.reply(
            f"❌ **ᴜꜱᴀɢᴇ:** `/setrecordgroup <ᴄʜᴀᴛ_ɪᴅ>`\n\n"
            f"📌 **ᴇxᴀᴍᴘʟᴇ:** `/setrecordgroup -1003970175858`\n\n"
            f"📊 **ᴄᴜʀʀᴇɴᴛ ꜱᴏᴜʀᴄᴇ:** `{RECORD_SOURCE}`"
        )
        return
    
    chat_id_str = re.sub(r'[^\d-]', '', parts[1])
    
    try:
        new_source = int(chat_id_str)
        old_source = RECORD_SOURCE
        
        if new_source == old_source:
            await message.reply(f"ℹ️ **ᴛʜɪꜱ ɪꜱ ᴀʟʀᴇᴀᴅʏ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ꜱᴏᴜʀᴄᴇ ɢʀᴏᴜᴘ!**\n\n📡 **ᴄᴜʀʀᴇɴᴛ ꜱᴏᴜʀᴄᴇ:** `{new_source}`")
            return
        
        status_msg = await message.reply(f"🔄 **ᴄʜᴀɴɢɪɴɢ ꜱᴏᴜʀᴄᴇ ꜰʀᴏᴍ `{old_source}` ᴛᴏ `{new_source}`...**")
        
        # Agar recording active hai toh stop karein
        if is_recording:
            try:
                await call_py.leave_call(old_source)
                is_recording = False
                logger.info(f"ʟᴇꜰᴛ ᴏʟᴅ ꜱᴏᴜʀᴄᴇ: {old_source}")
            except Exception as e:
                logger.warning(f"ᴄᴏᴜʟᴅ ɴᴏᴛ ʟᴇᴀᴠᴇ ᴏʟᴅ ꜱᴏᴜʀᴄᴇ: {e}")
        
        # Update source
        RECORD_SOURCE = new_source
        save_state()
        
        # Agar recording active thi toh naye source mein join karein
        if is_recording:
            success, error = await join_call_safe(new_source)
            if success:
                await call_py.record(new_source, RecordStream(True, AUDIO_PARAMETERS))
                is_recording = True
                await status_msg.edit_text(
                    f"✅ **ꜱᴏᴜʀᴄᴇ ᴄʜᴀɴɢᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**\n\n"
                    f"📡 **ᴏʟᴅ:** `{old_source}`\n"
                    f"🎯 **ɴᴇᴡ:** `{new_source}`\n"
                    f"📊 **ꜱᴛᴀᴛᴜꜱ:** 🟢 ʀᴇᴄᴏʀᴅɪɴɢ"
                )
            else:
                is_recording = False
                await status_msg.edit_text(
                    f"⚠️ **ꜱᴏᴜʀᴄᴇ ᴄʜᴀɴɢᴇᴅ ʙᴜᴛ ꜰᴀɪʟᴇᴅ ᴛᴏ ᴊᴏɪɴ!**\n\n"
                    f"📡 **ɴᴇᴡ ꜱᴏᴜʀᴄᴇ:** `{new_source}`\n"
                    f"⚠️ **ᴇʀʀᴏʀ:** `{error}`\n"
                    f"💡 ᴜꜱᴇ `/ʀᴇᴄᴏʀᴅ` ᴛᴏ ᴛʀʏ ᴀɢᴀɪɴ"
                )
        else:
            await status_msg.edit_text(
                f"✅ **ꜱᴏᴜʀᴄᴇ ᴄʜᴀɴɢᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**\n\n"
                f"📡 **ᴏʟᴅ:** `{old_source}`\n"
                f"🎯 **ɴᴇᴡ:** `{new_source}`\n"
                f"📊 **ꜱᴛᴀᴛᴜꜱ:** 🔴 ꜱᴛᴀɴᴅʙʏ\n\n"
                f"💡 ᴜꜱᴇ `/ʀᴇᴄᴏʀᴅ` ᴛᴏ ꜱᴛᴀʀᴛ"
            )
        
        logger.info(f"ꜱᴏᴜʀᴄᴇ ᴄʜᴀɴɢᴇᴅ ꜰʀᴏᴍ {old_source} ᴛᴏ {new_source} ʙʏ ᴏᴡɴᴇʀ")
        
    except ValueError:
        await message.reply(f"❌ **ɪɴᴠᴀʟɪᴅ ᴄʜᴀᴛ ɪᴅ!**\n\n📌 **ʏᴏᴜ ᴇɴᴛᴇʀᴇᴅ:** `{parts[1]}`")
    except Exception as e:
        await message.reply(f"❌ **ᴇʀʀᴏʀ:** `{str(e)}`")
        
# ==================== ʀᴇꜱᴛᴀʀᴛ ᴄᴏᴍᴍᴀɴᴅ ====================

@bot_app.on_message(pyro_filters.command("restart") & pyro_filters.user(OWNER_ID))
async def cmd_restart(client, message):
    """ʀᴇꜱᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ - ᴄʟᴇᴀɴ ᴀɴᴅ ʀᴇᴄᴏɴɴᴇᴄᴛ"""
    global is_recording, is_muted, call_py, forward_chats
    
    try:
        status_msg = await message.reply(
            "🔄 **ʀᴇꜱᴛᴀʀᴛɪɴɢ ʙᴏᴛ...**\n\n"
            "📡 ᴄʟᴇᴀɴɪɴɢ ᴜᴘ ᴀʟʟ ᴄᴏɴɴᴇᴄᴛɪᴏɴꜱ..."
        )
        
        # ===== 1. SAVE STATE =====
        save_state()
        logger.info("💾 ꜱᴛᴀᴛᴇ ꜱᴀᴠᴇᴅ")
        
        # ===== 2. LEAVE ALL CALLS =====
        left_count = 0
        failed_count = 0
        
        # Leave source
        try:
            await call_py.leave_call(RECORD_SOURCE)
            left_count += 1
            logger.info(f"ʟᴇꜰᴛ ꜱᴏᴜʀᴄᴇ: {RECORD_SOURCE}")
        except Exception as e:
            failed_count += 1
            logger.debug(f"ᴄᴏᴜʟᴅ ɴᴏᴛ ʟᴇᴀᴠᴇ ꜱᴏᴜʀᴄᴇ: {e}")
        
        # Leave all forward chats
        for chat_id in list(forward_chats):
            try:
                await call_py.leave_call(chat_id)
                left_count += 1
                logger.info(f"ʟᴇꜰᴛ ꜰᴏʀᴡᴀʀᴅ ᴄʜᴀᴛ: {chat_id}")
            except Exception as e:
                failed_count += 1
                logger.debug(f"ᴄᴏᴜʟᴅ ɴᴏᴛ ʟᴇᴀᴠᴇ {chat_id}: {e}")
        
        # ===== 3. REMEMBER STATE (preserve forwarding list for rejoin) =====
        saved_forwards = list(forward_chats)
        was_recording = is_recording
        is_recording = False
        logger.info("🧹 ʀᴜɴᴛɪᴍᴇ ꜱᴛᴀᴛᴇ ᴄʟᴇᴀʀᴇᴅ")
        
        # ===== 4. STOP PYTGCALLS =====
        stop_success = False
        try:
            await call_py.stop()
            stop_success = True
            logger.info("🛑 ᴘʏᴛɢᴄᴀʟʟꜱ ꜱᴛᴏᴘᴘᴇᴅ")
        except Exception as e:
            logger.debug(f"ᴘʏᴛɢᴄᴀʟʟꜱ ꜱᴛᴏᴘ ᴇʀʀᴏʀ: {e}")
        
        # ===== 5. WAIT FOR CLEANUP =====
        await asyncio.sleep(2)  # Increased wait time for proper cleanup
        
        # ===== 6. RESTART PYTGCALLS =====
        restart_success = False
        try:
            # Create new PyTgCalls instance
            call_py = PyTgCalls(user_app)
            
            # Re-register the microphone stream handler
            @call_py.on_update(pytg_filters.stream_frame(Direction.INCOMING, Device.MICROPHONE))
            async def audio_forwarder_handler(_, update: StreamFrames):
                """registered audio handler"""
                await _forward_incoming_frames(update)
            # Start PyTgCalls
            await call_py.start()

            # Rejoin source + forward chats after restart (no data loss)
            if was_recording:
                ok, _ = await join_call_safe(RECORD_SOURCE)
                if ok:
                    await call_py.record(RECORD_SOURCE, RecordStream(True, AUDIO_PARAMETERS))
                    is_recording = True
            for _cid in saved_forwards:
                try:
                    ok, _ = await join_call_safe(_cid)
                    if not ok:
                        forward_chats.discard(_cid)
                except Exception:
                    forward_chats.discard(_cid)
            save_state()

            restart_success = True
            logger.info("🔄 ᴘʏᴛɢᴄᴀʟʟꜱ ʀᴇꜱᴛᴀʀᴛᴇᴅ")
            
        except Exception as e:
            logger.error(f"ᴀꜰᴛᴇʀ ʀᴇꜱᴛᴀʀᴛ ᴘʏᴛɢᴄᴀʟʟꜱ ꜰᴀɪʟᴇᴅ: {e}")
            restart_success = False
        
        # ===== 7. UPDATE STATUS =====
        if restart_success:
            await status_msg.edit_text(
                f"✅ **ʙᴏᴛ ʀᴇꜱᴛᴀʀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**\n\n"
                f"📊 **ᴄʟᴇᴀɴᴇᴅ:** {left_count} ᴄʜᴀᴛꜱ\n"
                f"⚠️ **ꜰᴀɪʟᴇᴅ:** {failed_count} ᴄʜᴀᴛꜱ\n"
                f"📡 **ꜱᴏᴜʀᴄᴇ:** `{RECORD_SOURCE}`\n"
                f"📤 **ᴀᴄᴛɪᴠᴇ ꜰᴏʀᴡᴀʀᴅꜱ:** {len(forward_chats)}\n"
                f"🔊 **ᴀᴜᴅɪᴏ:** {'🔇 ᴍᴜᴛᴇᴅ' if is_muted else '🔊 ʟɪᴠᴇ'}\n"
                f"📊 **ꜱᴛᴀᴛᴜꜱ:** 🟢 ʀᴇᴀᴅʏ\n\n"
                f"💡 **ᴜꜱᴇ `/ʀᴇᴄᴏʀᴅ` ᴛᴏ ꜱᴛᴀʀᴛ ᴀɢᴀɪɴ**"
            )
        else:
            await status_msg.edit_text(
                f"⚠️ **ᴘᴀʀᴛɪᴀʟ ʀᴇꜱᴛᴀʀᴛ - ᴄʜᴇᴄᴋ ʟᴏɢꜱ!**\n\n"
                f"📊 **ᴄʟᴇᴀɴᴇᴅ:** {left_count} ᴄʜᴀᴛꜱ\n"
                f"⚠️ **ꜰᴀɪʟᴇᴅ:** {failed_count} ᴄʜᴀᴛꜱ\n"
                f"🛑 **ᴘʏᴛɢᴄᴀʟʟꜱ:** {'✅ ꜱᴛᴏᴘᴘᴇᴅ' if stop_success else '❌ ꜰᴀɪʟᴇᴅ'}\n"
                f"🔄 **ʀᴇꜱᴛᴀʀᴛ:** {'✅ ꜱᴜᴄᴄᴇꜱꜱ' if restart_success else '❌ ꜰᴀɪʟᴇᴅ'}\n\n"
                f"💡 ᴍᴀɴᴜᴀʟʟʏ ᴄʜᴇᴄᴋ ᴛʜᴇ ʙᴏᴛ ꜱᴛᴀᴛᴜꜱ"
            )
        
        logger.info("✅ ʀᴇꜱᴛᴀʀᴛ ᴄᴏᴍᴘʟᴇᴛᴇ")
        
    except Exception as e:
        logger.error(f"ʀᴇꜱᴛᴀʀᴛ ᴇʀʀᴏʀ: {e}")
        try:
            await message.reply(
                f"❌ **ʀᴇꜱᴛᴀʀᴛ ꜰᴀɪʟᴇᴅ!**\n\n"
                f"⚠️ **ᴇʀʀᴏʀ:** `{str(e)}`\n\n"
                f"💡 ᴍᴀɴᴜᴀʟʟʏ ʀᴇꜱᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ"
            )
        except Exception:
            logger.error("ᴄᴏᴜʟᴅ ɴᴏᴛ ꜱᴇɴᴅ ᴇʀʀᴏʀ ᴍᴇꜱꜱᴀɢᴇ")

# ==================== ʀᴇꜱᴛᴀʀᴛ ᴄᴏᴍᴍᴀɴᴅ ᴇɴᴅꜱ ====================        

# ==================== ᴇɴʜᴀɴᴄᴇᴅ ᴇxᴄᴇᴘᴛɪᴏɴ ʜᴀɴᴅʟɪɴɢ ====================

from pyrogram.errors import (
    FloodWait,
    InviteHashExpired,
    InviteHashInvalid,
    UserAlreadyParticipant,
    ChannelPrivate,
    RPCError,
    PeerIdInvalid,
    UsernameNotOccupied,
    UserBannedInChannel,
    ChatAdminRequired,
    InviteRequestSent,
)

async def handle_pyrogram_error(e, input_text, status_msg):
    """🎯 Handle all Pyrogram errors with specific messages"""
    
    error_msg = str(e).lower()
    
    # ===== FLOOD WAIT =====
    if isinstance(e, FloodWait) or "flood" in error_msg:
        wait_time = getattr(e, 'value', None)
        if not wait_time:
            wait_match = re.search(r'wait\s*(\d+)', error_msg)
            wait_time = int(wait_match.group(1)) if wait_match else 30
        await status_msg.edit_text(
            f"🚫 **ʀᴀᴛᴇ ʟɪᴍɪᴛᴇᴅ!** (ꜰʟᴏᴏᴅᴡᴀɪᴛ)\n\n"
            f"⏳ ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ **{wait_time} ꜱᴇᴄᴏɴᴅꜱ** ʙᴇꜰᴏʀᴇ ᴛʀʏɪɴɢ ᴀɢᴀɪɴ.\n"
            f"🔗 **ʟɪɴᴋ:** `{input_text}`"
        )
        return True
    
    # ===== INVITE HASH EXPIRED =====
    if isinstance(e, InviteHashExpired) or "expired" in error_msg:
        await status_msg.edit_text(
            f"⛔ **ɪɴᴠɪᴛᴇ ʟɪɴᴋ ᴇxᴘɪʀᴇᴅ!**\n\n"
            f"🔗 **ʟɪɴᴋ:** `{input_text}`\n"
            f"💡 ʀᴇQᴜᴇꜱᴛ ᴀ ɴᴇᴡ ʟɪɴᴋ ꜰʀᴏᴍ ᴛʜᴇ ᴀᴅᴍɪɴ."
        )
        return True
    
    # ===== INVITE HASH INVALID =====
    if isinstance(e, InviteHashInvalid) or "invalid" in error_msg:
        await status_msg.edit_text(
            f"❌ **ɪɴᴠᴀʟɪᴅ ɪɴᴠɪᴛᴇ ʜᴀꜱʜ!**\n\n"
            f"🔗 **ʟɪɴᴋ:** `{input_text}`\n"
            f"💡 ᴍᴀᴋᴇ ꜱᴜʀᴇ ʏᴏᴜ ᴄᴏᴘɪᴇᴅ ᴛʜᴇ ᴇɴᴛɪʀᴇ ʟɪɴᴋ ᴄᴏʀʀᴇᴄᴛʟʏ."
        )
        return True
    
    # ===== USER ALREADY PARTICIPANT =====
    if isinstance(e, UserAlreadyParticipant) or "already" in error_msg or "participant" in error_msg:
        await status_msg.edit_text(
            f"ℹ️ **ᴀʟʀᴇᴀᴅʏ ᴀ ᴍᴇᴍʙᴇʀ!** 👋\n\n"
            f"🔗 **ʟɪɴᴋ:** `{input_text}`\n\n"
            f"✅ ᴛʜᴇ ᴜꜱᴇʀ ɪꜱ ᴀʟʀᴇᴀᴅʏ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ.\n\n"
            f"💡 ᴜꜱᴇ `/join <ɪᴅ>` ᴛᴏ ꜱᴛᴀʀᴛ ꜰᴏʀᴡᴀʀᴅɪɴɢ"
        )
        return True
    
    # ===== CHANNEL PRIVATE =====
    if isinstance(e, ChannelPrivate) or "private" in error_msg:
        await status_msg.edit_text(
            f"🔒 **ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀɴɴᴇʟ!**\n\n"
            f"🔗 **ʟɪɴᴋ:** `{input_text}`\n"
            f"💡 ʏᴏᴜ ɴᴇᴇᴅ ᴀɴ ɪɴᴠɪᴛᴇ ʟɪɴᴋ ꜰʀᴏᴍ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ᴀᴅᴍɪɴ."
        )
        return True
    
    # ===== USER BANNED =====
    if isinstance(e, UserBannedInChannel) or "banned" in error_msg:
        await status_msg.edit_text(
            f"🚫 **ʏᴏᴜ'ʀᴇ ʙᴀɴɴᴇᴅ!**\n\n"
            f"🔗 **ʟɪɴᴋ:** `{input_text}`\n"
            f"💡 ʏᴏᴜ ᴄᴀɴɴᴏᴛ ᴊᴏɪɴ ᴅᴜᴇ ᴛᴏ ʙᴀɴ."
        )
        return True
    
    # ===== USERNAME NOT OCCUPIED =====
    if isinstance(e, UsernameNotOccupied) or "username_not_occupied" in error_msg:
        await status_msg.edit_text(
            f"❌ **ᴜꜱᴇʀɴᴀᴍᴇ ᴅᴏᴇꜱɴ'ᴛ ᴇxɪꜱᴛ!**\n\n"
            f"📛 **ᴜꜱᴇʀɴᴀᴍᴇ:** `{input_text}`\n"
            f"💡 ᴍᴀᴋᴇ ꜱᴜʀᴇ ᴛʜᴇ ᴜꜱᴇʀɴᴀᴍᴇ ɪꜱ ᴄᴏʀʀᴇᴄᴛ."
        )
        return True
    
    # ===== CHAT ADMIN REQUIRED =====
    if isinstance(e, ChatAdminRequired) or "not enough rights" in error_msg:
        await status_msg.edit_text(
            f"⚠️ **ɪɴꜱᴜꜰꜰɪᴄɪᴇɴᴛ ᴘᴇʀᴍɪꜱꜱɪᴏɴꜱ!** 🔒\n\n"
            f"🔗 **ʟɪɴᴋ:** `{input_text}`\n\n"
            f"❌ ʙᴏᴛ ɴᴇᴇᴅꜱ ᴘᴇʀᴍɪꜱꜱɪᴏɴ ᴛᴏ ᴊᴏɪɴ.\n"
            f"💡 ᴍᴀᴋᴇ ʙᴏᴛ ᴀ ᴍᴇᴍʙᴇʀ ᴏʀ ᴀᴅᴍɪɴ."
        )
        return True
    
    # ===== PEER ID INVALID =====
    if isinstance(e, PeerIdInvalid) or "chat not found" in error_msg:
        await status_msg.edit_text(
            f"❌ **ᴄʜᴀᴛ ɴᴏᴛ ꜰᴏᴜɴᴅ!** 🔍\n\n"
            f"🔗 **ʟɪɴᴋ:** `{input_text}`\n\n"
            f"⚠️ **ᴘᴏꜱꜱɪʙʟᴇ ʀᴇᴀꜱᴏɴꜱ:**\n"
            f"• ɪɴᴠᴀʟɪᴅ/ᴇxᴘɪʀᴇᴅ ʟɪɴᴋ\n"
            f"• ᴄʜᴀᴛ ᴡᴀꜱ ᴅᴇʟᴇᴛᴇᴅ\n"
            f"• ʙᴏᴛ ɪꜱ ʙʟᴏᴄᴋᴇᴅ"
        )
        return True
    
    # ===== INVITE REQUEST SENT (Pending Approval) =====
    if isinstance(e, InviteRequestSent) or "request" in error_msg or "join request" in error_msg:
        return False
    
    # ===== GENERIC RPC ERROR =====
    if isinstance(e, RPCError):
        await status_msg.edit_text(
            f"❌ **ʀᴘᴄ ᴇʀʀᴏʀ!** ⚠️\n\n"
            f"🔗 **ʟɪɴᴋ:** `{input_text}`\n"
            f"⚠️ **ᴇʀʀᴏʀ:** `{str(e)[:200]}`\n\n"
            f"💡 **ᴛʀᴏᴜʙʟᴇꜱʜᴏᴏᴛɪɴɢ:**\n"
            f"• ᴠᴇʀɪꜰʏ ᴛʜᴇ ʟɪɴᴋ\n"
            f"• ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ\n"
            f"• ᴜꜱᴇ: `/join <ɪᴅ>`"
        )
        return True
    
    return False


# ==================== ᴊᴏɪɴ ʟɪɴᴋ ᴄᴏᴍᴍᴀɴᴅ ====================

def parse_invite_link(link: str) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    """🎯 Smart link parser - detects invite hashes, usernames & chat IDs"""
    link = link.strip()
    
    if any(x in link for x in ["t.me/", "telegram.me/", "telegram.dog/"]):
        path = re.split(r't\.me/|telegram\.me/|telegram\.dog/', link)[-1]
        path = path.split("?")[0].split("#")[0]
        
        patterns = [
            (r'^\+([a-zA-Z0-9_-]+)$', 'hash'),
            (r'^joinchat/([a-zA-Z0-9_-]+)$', 'hash'),
            (r'^c/(\d+)$', 'id'),
            (r'^@?([a-zA-Z][a-zA-Z0-9_]{4,})$', 'user'),
            (r'^([a-zA-Z0-9_-]{8,})$', 'hash'),
            (r'^(-?\d+)$', 'id'),
        ]
        
        for pattern, ptype in patterns:
            match = re.match(pattern, path)
            if match:
                if ptype == 'hash':
                    return match.group(1), None, None
                elif ptype == 'user':
                    return None, f"@{match.group(1)}", None
                elif ptype == 'id':
                    val = int(match.group(1))
                    if val > 0:
                        return None, None, val
                    return None, None, int(f"-100{abs(val)}")
    
    patterns = [
        (r'^@?([a-zA-Z][a-zA-Z0-9_]{4,})$', 'user'),
        (r'^([a-zA-Z0-9_-]{8,})$', 'hash'),
        (r'^(-?\d+)$', 'id'),
    ]
    
    for pattern, ptype in patterns:
        match = re.match(pattern, link)
        if match:
            if ptype == 'hash':
                return match.group(1), None, None
            elif ptype == 'user':
                return None, f"@{match.group(1)}", None
            elif ptype == 'id':
                val = int(match.group(1))
                if val > 0:
                    return None, None, val
                return None, None, int(f"-100{abs(val)}")
    
    return None, None, None


async def check_existing_join(username: str, chat_id: int, invite_hash: str):
    """🔍 Check if already joined without calling join_chat()"""
    try:
        async for dialog in user_app.get_dialogs(limit=200):
            dialog_username = getattr(dialog.chat, 'username', None)
            dialog_id = dialog.chat.id
            
            if username and dialog_username and dialog_username.lower() == username.lstrip('@').lower():
                return dialog.chat
            if chat_id is not None and dialog_id == chat_id:
                return dialog.chat
            if invite_hash:
                try:
                    check = await user_app.get_chat(invite_hash)
                    if check:
                        return check
                except Exception:
                    pass
    except Exception:
        pass
    return None


@bot_app.on_message(pyro_filters.command("joinlink") & authorized_only())
async def cmd_joinlink(client, message):
    """ᴊᴏɪɴ ᴀ ɢʀᴏᴜᴘ ᴠɪᴀ ɪɴᴠɪᴛᴇ ʟɪɴᴋ - ғɪxᴇᴅ ᴠᴇʀsɪᴏɴ"""
    parts = message.text.split()
    
    if len(parts) < 2:
        await message.reply(
            f"❌ **ᴜꜱᴀɢᴇ:** `/joinlink <ʟɪɴᴋ>`\n\n"
            f"📌 **ᴇxᴀᴍᴘʟᴇꜱ:**\n"
            f"┌─────────────────────────────────────┐\n"
            f"│ • `/joinlink https://t.me/+xyz`    │\n"
            f"│ • `/joinlink https://t.me/joinchat`│\n"
            f"│ • `/joinlink @mygroup`             │\n"
            f"│ • `/joinlink mygroup`              │\n"
            f"└─────────────────────────────────────┘\n\n"
            f"💡 **ꜱᴜᴘᴘᴏʀᴛꜱ:**\n"
            f"🔐 ᴘʀɪᴠᴀᴛᴇ ɪɴᴠɪᴛᴇ ʟɪɴᴋꜱ (+ʜᴀꜱʜ)\n"
            f"🌐 ᴘᴜʙʟɪᴄ ɢʀᴏᴜᴘ ᴜꜱᴇʀɴᴀᴍᴇꜱ\n"
            f"🔢 ᴄʜᴀᴛ ɪᴅꜱ\n"
            f"⏳ ʀᴇQᴜᴇꜱᴛ-ᴊᴏɪɴ ʟɪɴᴋꜱ (ᴀᴜᴛᴏ-ᴍᴏɴɪᴛᴏʀꜱ)"
        )
        return
    
    input_text = parts[1].strip()
    status_msg = await message.reply("🔄 **ᴘʀᴏᴄᴇꜱꜱɪɴɢ ʏᴏᴜʀ ʀᴇQᴜᴇꜱᴛ...**")
    
    try:
        # 🔍 Parse link using smart parser
        invite_hash, username, chat_id = parse_invite_link(input_text)
        
        if not any([invite_hash, username, chat_id]):
            await status_msg.edit_text(
                f"❌ **ɪɴᴠᴀʟɪᴅ ɪɴᴠɪᴛᴇ ʟɪɴᴋ!**\n\n"
                f"🔗 **ɪɴᴘᴜᴛ:** `{input_text}`\n\n"
                f"💡 **ᴛɪᴘꜱ:**\n"
                f"• ᴠᴇʀɪꜰʏ ᴛʜᴇ ʟɪɴᴋ ɪꜱ ᴄᴏᴍᴘʟᴇᴛᴇ\n"
                f"• ᴄʜᴇᴄᴋ ɪꜰ ᴛʜᴇ ʟɪɴᴋ ʜᴀꜱ ᴇxᴘɪʀᴇᴅ\n"
                f"• ᴇɴꜱᴜʀᴇ ʏᴏᴜ ʜᴀᴠᴇ ᴘʀᴏᴘᴇʀ ᴘᴇʀᴍɪꜱꜱɪᴏɴꜱ\n\n"
                f"📌 **ᴛʀʏ:** `/joinlink https://t.me/+Vcpn1Nt8D0gwMjFl`"
            )
            return
        
        # 🔍 Check if already joined (optimized)
        chat_info = await check_existing_join(username, chat_id, invite_hash)
        if chat_info:
            chat_id_show = chat_info.id
            chat_title = getattr(chat_info, 'title', str(chat_id_show))
            chat_username = getattr(chat_info, 'username', None)
            username_str = f"@{chat_username}" if chat_username else "ɴᴏɴᴇ"
            member_count = getattr(chat_info, 'members_count', 'ɴ/ᴀ')
            
            await status_msg.edit_text(
                f"ℹ️ **ᴀʟʀᴇᴀᴅʏ ᴀ ᴍᴇᴍʙᴇʀ!** 👋\n\n"
                f"┌─────────────────────────────────────┐\n"
                f"│ 📝 **ɴᴀᴍᴇ:** {chat_title}              │\n"
                f"│ 🔢 **ɪᴅ:** `{chat_id_show}`              │\n"
                f"│ 👥 **ᴍᴇᴍʙᴇʀꜱ:** {member_count}          │\n"
                f"│ 📛 **ᴜꜱᴇʀɴᴀᴍᴇ:** {username_str}         │\n"
                f"└─────────────────────────────────────┘\n\n"
                f"💡 **ɴᴇxᴛ ꜱᴛᴇᴘꜱ:**\n"
                f"• `/join {chat_id_show}` → ꜱᴛᴀʀᴛ ꜰᴏʀᴡᴀʀᴅɪɴɢ\n"
                f"• `/leave {chat_id_show}` → ꜱᴛᴏᴘ ꜰᴏʀᴡᴀʀᴅɪɴɢ"
            )
            return
        
        # 🎯 Join based on link type
        if invite_hash:
            try:
                chat_info = await user_app.join_chat(invite_hash)
                join_method = "ᴘʀɪᴠᴀᴛᴇ ʟɪɴᴋ"
                
            except Exception as e:
                error_str = str(e).lower()
                
                # 🎯 Check if it's a request-join link
                if "request" in error_str or "join request" in error_str:
                    await status_msg.edit_text(
                        f"📨 **ᴊᴏɪɴ ʀᴇQᴜᴇꜱᴛ ꜱᴇɴᴛ!**\n\n"
                        f"┌─────────────────────────────────────┐\n"
                        f"│ 🔗 **ʟɪɴᴋ:** `{input_text}`      │\n"
                        f"│ ⏳ **ꜱᴛᴀᴛᴜꜱ:** ⏰ ᴘᴇɴᴅɪɴɢ ᴀᴘᴘʀᴏᴠᴀʟ   │\n"
                        f"│ 📌 **ᴍᴏɴɪᴛᴏʀ:** 24 ʜᴏᴜʀꜱ ᴍᴀx        │\n"
                        f"│ 🔄 **ᴄʜᴇᴄᴋ:** ᴇᴠᴇʀʏ 60 ꜱᴇᴄᴏɴᴅꜱ      │\n"
                        f"└─────────────────────────────────────┘\n\n"
                        f"💡 ʏᴏᴜ'ʟʟ ʙᴇ ɴᴏᴛɪꜰɪᴇᴅ ᴡʜᴇɴ ᴀᴘᴘʀᴏᴠᴇᴅ!\n"
                        f"⏱️ ꜱᴛᴀʀᴛᴇᴅ ᴍᴏɴɪᴛᴏʀɪɴɢ..."
                    )
                    
                    _start_time = time.time()
                    PENDING_JOIN_REQUESTS[invite_hash] = {
                        "invite_hash": invite_hash,
                        "original_link": input_text,
                        "start_time": _start_time,
                        "chat_id": message.chat.id,
                        "message_id": status_msg.id,
                    }
                    save_pending_joins()
                    PENDING_JOIN_MONITORS[invite_hash] = asyncio.create_task(
                        _run_join_monitor(client, status_msg, invite_hash, input_text, _start_time)
                    )
                    return
                
                # 🎯 Use enhanced error handler
                if await handle_pyrogram_error(e, input_text, status_msg):
                    return
                
                # 🎯 If still not handled, re-raise
                raise e
        
        elif username:
            try:
                chat_info = await user_app.join_chat(username)
                join_method = "ᴘᴜʙʟɪᴄ ᴜꜱᴇʀɴᴀᴍᴇ"
            except Exception as e:
                if await handle_pyrogram_error(e, input_text, status_msg):
                    return
                raise e
        
        elif chat_id is not None:
            try:
                chat_info = await user_app.join_chat(chat_id)
                join_method = "ᴄʜᴀᴛ ɪᴅ"
            except Exception as e:
                if await handle_pyrogram_error(e, input_text, status_msg):
                    return
                raise e
        
        # ===== CHECK IF JOIN SUCCESSFUL =====
        if chat_info:
            chat_id_show = chat_info.id
            chat_title = getattr(chat_info, 'title', str(chat_id_show))
            
            chat_type_obj = getattr(chat_info, 'type', None)
            if chat_type_obj == ChatType.CHANNEL:
                chat_type = "ᴄʜᴀɴɴᴇʟ"
            elif chat_type_obj in (ChatType.GROUP, ChatType.SUPERGROUP):
                chat_type = "ɢʀᴏᴜᴘ"
            else:
                chat_type = "ᴄʜᴀᴛ"
            
            chat_username = getattr(chat_info, 'username', None)
            username_str = f"@{chat_username}" if chat_username else "ɴᴏɴᴇ"
            member_count = getattr(chat_info, 'members_count', 'ɴ/ᴀ')
            
            success_msg = f"""
✅ **ᴄʜᴀᴛ ᴊᴏɪɴᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!** 🎉

┌─────────────────────────────────────┐
│ 📝 **ɴᴀᴍᴇ:** {chat_title}              │
│ 🔢 **ɪᴅ:** `{chat_id_show}`              │
│ 📌 **ᴛʏᴘᴇ:** {chat_type}               │
│ 👥 **ᴍᴇᴍʙᴇʀꜱ:** {member_count}          │
│ 📛 **ᴜꜱᴇʀɴᴀᴍᴇ:** {username_str}         │
│ 🔗 **ᴍᴇᴛʜᴏᴅ:** {join_method}            │
└─────────────────────────────────────┘

💡 **ɴᴇxᴛ ꜱᴛᴇᴘꜱ:**
• `/join {chat_id_show}` - ꜱᴛᴀʀᴛ ꜰᴏʀᴡᴀʀᴅɪɴɢ
• `/leave {chat_id_show}` - ꜱᴛᴏᴘ ꜰᴏʀᴡᴀʀᴅɪɴɢ
• `/list` - ꜱᴇᴇ ᴀʟʟ ᴀᴄᴛɪᴠᴇ
"""
            
            await status_msg.edit_text(success_msg)
            logger.info(f"✅ ᴊᴏɪɴᴇᴅ {chat_id_show} ᴠɪᴀ: {input_text}")
            return
            
        else:
            await status_msg.edit_text(
                f"❌ **ꜰᴀɪʟᴇᴅ ᴛᴏ ᴊᴏɪɴ ᴄʜᴀᴛ!**\n\n"
                f"🔗 **ʟɪɴᴋ:** `{input_text}`\n\n"
                f"⚠️ **ᴘᴏꜱꜱɪʙʟᴇ ʀᴇᴀꜱᴏɴꜱ:**\n"
                f"• ɪɴᴠᴀʟɪᴅ/ᴇxᴘɪʀᴇᴅ ʟɪɴᴋ\n"
                f"• ʙᴏᴛ ɪꜱ ʙʟᴏᴄᴋᴇᴅ\n"
                f"• ᴄʜᴀᴛ ᴡᴀꜱ ᴅᴇʟᴇᴛᴇᴅ\n\n"
                f"💡 ᴛʀʏ: `/join <ɪᴅ>` ᴅɪʀᴇᴄᴛʟʏ"
            )
            
    except Exception as e:
        # 🎯 Final fallback error handler
        if not await handle_pyrogram_error(e, input_text, status_msg):
            logger.error(f"ᴊᴏɪɴʟɪɴᴋ ᴇʀʀᴏʀ: {e}")
            await status_msg.edit_text(
                f"❌ **ᴜɴʜᴀɴᴅʟᴇᴅ ᴇʀʀᴏʀ!** ⚠️\n\n"
                f"🔗 **ʟɪɴᴋ:** `{input_text}`\n"
                f"⚠️ **ᴇʀʀᴏʀ:** `{str(e)[:200]}`\n\n"
                f"💡 ᴘʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ ᴏʀ ᴄᴏɴᴛᴀᴄᴛ ꜱᴜᴘᴘᴏʀᴛ."
            )


async def monitor_join_approval(client, status_msg, invite_hash, original_link, start_time):
    """ᴍᴏɴɪᴛᴏʀ ᴊᴏɪɴ ʀᴇQᴜᴇꜱᴛ ꜱᴛᴀᴛᴜꜱ ꜰᴏʀ 24 ʜᴏᴜʀꜱ"""
    
    check_count = 0
    max_checks = 1440
    
    try:
        while check_count < max_checks:
            await asyncio.sleep(60)
            check_count += 1
            elapsed = int(time.time() - start_time)
            
            if check_count % 5 == 0:
                hours = elapsed // 3600
                minutes = (elapsed % 3600) // 60
                seconds = elapsed % 60
                
                try:
                    await status_msg.edit_text(
                        f"⏳ **ᴊᴏɪɴ ʀᴇQᴜᴇꜱᴛ ᴘᴇɴᴅɪɴɢ...**\n\n"
                        f"┌─────────────────────────────────────┐\n"
                        f"│ 🔗 **ʟɪɴᴋ:** `{original_link}`      │\n"
                        f"│ ⏱️ **ᴇʟᴀᴘꜱᴇᴅ:** {hours}ʜ {minutes}ᴍ {seconds}ꜱ │\n"
                        f"│ 🔄 **ᴄʜᴇᴄᴋ #:** {check_count}/{max_checks} │\n"
                        f"└─────────────────────────────────────┘\n\n"
                        f"💡 ᴡɪʟʟ ᴀᴜᴛᴏ-ᴅᴇᴛᴇᴄᴛ ᴡʜᴇɴ ᴀᴅᴍɪɴ ᴀᴘᴘʀᴏᴠᴇꜱ"
                    )
                except Exception:
                    pass
            
            try:
                chat_info = await user_app.join_chat(invite_hash)
                
                chat_id_show = chat_info.id
                chat_title = getattr(chat_info, 'title', str(chat_id_show))
                chat_username = getattr(chat_info, 'username', None)
                username_str = f"@{chat_username}" if chat_username else "ɴᴏɴᴇ"
                member_count = getattr(chat_info, 'members_count', 'ɴ/ᴀ')
                elapsed_total = int(time.time() - start_time)
                hours = elapsed_total // 3600
                minutes = (elapsed_total % 3600) // 60
                seconds = elapsed_total % 60
                
                await status_msg.edit_text(
                    f"✅ **ᴊᴏɪɴ ʀᴇQᴜᴇꜱᴛ ᴀᴘᴘʀᴏᴠᴇᴅ!** 🎉\n\n"
                    f"┌─────────────────────────────────────┐\n"
                    f"│ 📝 **ɴᴀᴍᴇ:** {chat_title}              │\n"
                    f"│ 🔢 **ɪᴅ:** `{chat_id_show}`              │\n"
                    f"│ 👥 **ᴍᴇᴍʙᴇʀꜱ:** {member_count}          │\n"
                    f"│ 📛 **ᴜꜱᴇʀɴᴀᴍᴇ:** {username_str}         │\n"
                    f"│ ⏱️ **ᴛɪᴍᴇ ᴛᴀᴋᴇɴ:** {hours}ʜ {minutes}ᴍ {seconds}ꜱ │\n"
                    f"└─────────────────────────────────────┘\n\n"
                    f"💡 **ɴᴇxᴛ ꜱᴛᴇᴘꜱ:**\n"
                    f"• `/join {chat_id_show}` - ꜱᴛᴀʀᴛ ꜰᴏʀᴡᴀʀᴅɪɴɢ\n"
                    f"• `/leave {chat_id_show}` - ꜱᴛᴏᴘ ꜰᴏʀᴡᴀʀᴅɪɴɢ"
                )
                logger.info(f"✅ ᴊᴏɪɴ ʀᴇQᴜᴇꜱᴛ ᴀᴘᴘʀᴏᴠᴇᴅ ꜰᴏʀ: {original_link}")
                return
                
            except Exception as e:
                error_str = str(e).lower()
                
                # 🎯 Check for specific errors during monitoring
                if "expired" in error_str or "invalid" in error_str:
                    await status_msg.edit_text(
                        f"⛔ **ɪɴᴠɪᴛᴇ ʟɪɴᴋ ᴇxᴘɪʀᴇᴅ/ɪɴᴠᴀʟɪᴅ!**\n\n"
                        f"🔗 **ʟɪɴᴋ:** `{original_link}`\n"
                        f"💡 ᴘʟᴇᴀꜱᴇ ʀᴇQᴜᴇꜱᴛ ᴀ ɴᴇᴡ ʟɪɴᴋ."
                    )
                    return
                elif "banned" in error_str:
                    await status_msg.edit_text(
                        f"🚫 **ʏᴏᴜ ᴡᴇʀᴇ ʙᴀɴɴᴇᴅ ꜰʀᴏᴍ ᴛʜɪꜱ ᴄʜᴀᴛ!**\n\n"
                        f"🔗 **ʟɪɴᴋ:** `{original_link}`"
                    )
                    return
                elif "flood" in error_str:
                    # Continue monitoring, flood might be temporary
                    pass
                # Otherwise continue monitoring
            
            if elapsed > 86400:
                await status_msg.edit_text(
                    f"⏰ **ᴛɪᴍᴇ ᴏᴜᴛ! 24 ʜᴏᴜʀꜱ ᴘᴀꜱꜱᴇᴅ**\n\n"
                    f"┌─────────────────────────────────────┐\n"
                    f"│ 📨 **ꜱᴛᴀᴛᴜꜱ:** ʀᴇQᴜᴇꜱᴛ ᴇxᴘɪʀᴇᴅ    │\n"
                    f"│ 🔗 **ʟɪɴᴋ:** `{original_link}`      │\n"
                    f"│ ⏱️ **ᴡᴀɪᴛᴇᴅ:** 24+ ʜᴏᴜʀꜱ            │\n"
                    f"└─────────────────────────────────────┘\n\n"
                    f"💡 **ᴡʜᴀᴛ ᴛᴏ ᴅᴏ?**\n"
                    f"• ᴀᴅᴍɪɴ ᴅɪᴅɴ'ᴛ ᴀᴘᴘʀᴏᴠᴇ\n"
                    f"• ᴛʀʏ ᴀ ɴᴇᴡ ʟɪɴᴋ\n"
                    f"• ᴜꜱᴇ: `/join <ɪᴅ>` ɪꜰ ᴀʟʀᴇᴀᴅʏ ᴀ ᴍᴇᴍʙᴇʀ"
                )
                return
                
    except asyncio.CancelledError:
        logger.info(f"ᴊᴏɪɴ ᴍᴏɴɪᴛᴏʀ ᴄᴀɴᴄᴇʟʟᴇᴅ ꜰᴏʀ: {original_link}")
    except Exception as e:
        logger.error(f"ᴊᴏɪɴ ᴍᴏɴɪᴛᴏʀ ᴇʀʀᴏʀ: {e}")

# ==================== ᴊᴏɪɴ ʟɪɴᴋ ᴄᴏᴍᴍᴀɴᴅ ᴇɴᴅꜱ ====================

# ==================== ᴘᴀɴᴇʟ ᴄᴏᴍᴍᴀɴᴅ ====================

@bot_app.on_message(pyro_filters.command("panel") & authorized_only())
async def cmd_panel(client, message):
    """ꜱʜᴏᴡ ᴄᴏᴍᴘʟᴇᴛᴇ ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ ᴡɪᴛʜ ʙᴜᴛᴛᴏɴꜱ"""
    
    # Get current stats
    recording_status = "🟢 ᴀᴄᴛɪᴠᴇ" if is_recording else "🔴 ɪɴᴀᴄᴛɪᴠᴇ"
    audio_status = "🔇 ᴍᴜᴛᴇᴅ" if is_muted else "🔊 ʟɪᴠᴇ"
    forward_count = len(forward_chats)
    uptime = get_uptime()
    
    # Create status bar
    vol_bar = create_progress_bar(audio_config['volume'], 200)
    bass_bar = create_progress_bar(audio_config['bass'], 60)
    treble_bar = create_progress_bar(audio_config['treble'], 60)
    gain_bar = create_progress_bar(audio_config['gain'], 60)
    
    panel_text = f"""
🎛️ **ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ**

────────────────────
📊 **ꜱʏꜱᴛᴇᴍ ꜱᴛᴀᴛᴜꜱ**
• **ʀᴇᴄᴏʀᴅɪɴɢ:** {recording_status}
• **ᴀᴜᴅɪᴏ:** {audio_status}
• **ꜰᴏʀᴡᴀʀᴅɪɴɢ:** {forward_count} ᴄʜᴀᴛꜱ
• **ᴜᴘᴛɪᴍᴇ:** {uptime}
• **ꜱᴏᴜʀᴄᴇ:** `{RECORD_SOURCE}`

────────────────────
🎵 **ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ**
• **ᴠᴏʟᴜᴍᴇ:** `{audio_config['volume']}%` {vol_bar}
• **ʙᴀꜱꜱ:** `{audio_config['bass']}/60` {bass_bar}
• **ᴛʀᴇʙʟᴇ:** `{audio_config['treble']}/60` {treble_bar}
• **ɢᴀɪɴ:** `{audio_config['gain']}/60` {gain_bar}

────────────────────
📌 **ᴜꜱᴇ ʙᴜᴛᴛᴏɴꜱ ʙᴇʟᴏᴡ ᴛᴏ ᴄᴏɴᴛʀᴏʟ**
"""
    
    # ===== BUILD KEYBOARD WITH ONLY 3 AVAILABLE STYLES =====
    keyboard = build_keyboard([
        # Row 1: Audio Controls
        ("🔇 ᴍᴜᴛᴇ", "panel_mute", ButtonStyle.DANGER),   # Red
        ("🔊 ᴜɴᴍᴜᴛᴇ", "panel_unmute", ButtonStyle.DANGER), # red
        
        # Row 2: Volume Controls
        ("🔉 ᴠᴏʟᴜᴍᴇ -", "panel_vol_down", ButtonStyle.SUCCESS),  # Dark Blue
        ("🔊 ᴠᴏʟᴜᴍᴇ +", "panel_vol_up", ButtonStyle.SUCCESS),    # Dark Blue
        
        # Row 3: Bass Controls
        ("⬇️ ʙᴀꜱꜱ -", "panel_bass_down", ButtonStyle.PRIMARY),  # Dark Blue
        ("⬆️ ʙᴀꜱꜱ +", "panel_bass_up", ButtonStyle.PRIMARY),    # Dark Blue
        
        # Row 4: Treble Controls
        ("⬇️ ᴛʀᴇʙʟᴇ -", "panel_treble_down", ButtonStyle.DANGER), # Dark Blue
        ("⬆️ ᴛʀᴇʙʟᴇ +", "panel_treble_up", ButtonStyle.DANGER),   # Dark Blue
        
        # Row 5: Gain Controls
        ("⬇️ ɢᴀɪɴ -", "panel_gain_down", ButtonStyle.SUCCESS),  # Dark Blue
        ("⬆️ ɢᴀɪɴ +", "panel_gain_up", ButtonStyle.SUCCESS),    # Dark Blue
        
        # Row 6: Utility
        ("🔄 ʀᴇꜱᴇᴛ", "panel_reset", ButtonStyle.DANGER),  # Red
        ("📋 ʟɪꜱᴛ", "panel_list", ButtonStyle.DANGER),   # Dark Blue
        
        # Row 7: Close
        ("❌ ᴄʟᴏꜱᴇ", "panel_close", ButtonStyle.DANGER),  # Red
    ], row_width=2)
    
    await message.reply(
        panel_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )


# ==================== ᴘᴀɴᴇʟ ᴄᴀʟʟʙᴀᴄᴋ ʜᴀɴᴅʟᴇʀꜱ ====================

@bot_app.on_callback_query(pyro_filters.regex(r"^panel_"))
async def panel_callbacks(client, callback_query: CallbackQuery):
    """ʜᴀɴᴅʟᴇ ᴀʟʟ panel_* ᴄᴀʟʟʙᴀᴄᴋ Qᴜᴇʀɪᴇꜱ ꜰʀᴏᴍ /panel"""
    global is_muted, audio_config, RECORD_SOURCE  
    
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    # Check authorization
    if user_id != OWNER_ID and user_id not in approved_users:
        await callback_query.answer("⛔ ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ!", show_alert=True)
        return
    
    await callback_query.answer()
    
    # ===== PANEL MUTE =====
    if data == "panel_mute":
        if is_muted:
            await callback_query.answer("🔇 ᴀʟʀᴇᴀᴅʏ ᴍᴜᴛᴇᴅ!", show_alert=True)
            return
        is_muted = True
        await callback_query.answer("🔇 ᴀᴜᴅɪᴏ ᴍᴜᴛᴇᴅ!", show_alert=True)
        await refresh_panel(client, callback_query)
    
    # ===== PANEL UNMUTE =====
    elif data == "panel_unmute":
        if not is_muted:
            await callback_query.answer("🔊 ᴀʟʀᴇᴀᴅʏ ᴜɴᴍᴜᴛᴇᴅ!", show_alert=True)
            return
        is_muted = False
        await callback_query.answer("🔊 ᴀᴜᴅɪᴏ ᴜɴᴍᴜᴛᴇᴅ!", show_alert=True)
        await refresh_panel(client, callback_query)
    
    # ===== VOLUME CONTROLS =====
    elif data == "panel_vol_up":
        audio_config['volume'] = min(200, audio_config['volume'] + 10)
        save_state()
        await callback_query.answer(f"🔊 ᴠᴏʟᴜᴍᴇ: {audio_config['volume']}%", show_alert=True)
        await refresh_panel(client, callback_query)
    
    elif data == "panel_vol_down":
        audio_config['volume'] = max(0, audio_config['volume'] - 10)
        save_state()
        await callback_query.answer(f"🔉 ᴠᴏʟᴜᴍᴇ: {audio_config['volume']}%", show_alert=True)
        await refresh_panel(client, callback_query)
    
    # ===== BASS CONTROLS =====
    elif data == "panel_bass_up":
        audio_config['bass'] = min(60, audio_config['bass'] + 5)
        audio_config['highpass'] = audio_config['bass'] > 0
        save_state()
        await callback_query.answer(f"🎸 ʙᴀꜱꜱ: {audio_config['bass']}/60", show_alert=True)
        await refresh_panel(client, callback_query)
    
    elif data == "panel_bass_down":
        audio_config['bass'] = max(0, audio_config['bass'] - 5)
        audio_config['highpass'] = audio_config['bass'] > 0
        save_state()
        await callback_query.answer(f"🎸 ʙᴀꜱꜱ: {audio_config['bass']}/60", show_alert=True)
        await refresh_panel(client, callback_query)
    
    # ===== TREBLE CONTROLS =====
    elif data == "panel_treble_up":
        audio_config['treble'] = min(60, audio_config['treble'] + 5)
        save_state()
        await callback_query.answer(f"🎵 ᴛʀᴇʙʟᴇ: {audio_config['treble']}/60", show_alert=True)
        await refresh_panel(client, callback_query)
    
    elif data == "panel_treble_down":
        audio_config['treble'] = max(0, audio_config['treble'] - 5)
        save_state()
        await callback_query.answer(f"🎵 ᴛʀᴇʙʟᴇ: {audio_config['treble']}/60", show_alert=True)
        await refresh_panel(client, callback_query)
    
    # ===== GAIN CONTROLS =====
    elif data == "panel_gain_up":
        audio_config['gain'] = min(60, audio_config['gain'] + 5)
        save_state()
        await callback_query.answer(f"📈 ɢᴀɪɴ: {audio_config['gain']}/60", show_alert=True)
        await refresh_panel(client, callback_query)
    
    elif data == "panel_gain_down":
        audio_config['gain'] = max(0, audio_config['gain'] - 5)
        save_state()
        await callback_query.answer(f"📈 ɢᴀɪɴ: {audio_config['gain']}/60", show_alert=True)
        await refresh_panel(client, callback_query)
    
    # ===== PANEL RESET =====
    elif data == "panel_reset":
        audio_config = {
            'volume': 100,
            'bass': 0,
            'treble': 0,
            'gain': 0,
            'compressor': True,
            'limiter': True,
            'highpass': False,
            'lowpass': False
        }
        save_state()
        await callback_query.answer("🔄 ᴀʟʟ ᴇꜰꜰᴇᴄᴛꜱ ʀᴇꜱᴇᴛ!", show_alert=True)
        await refresh_panel(client, callback_query)
    
    # ===== PANEL LIST =====
    elif data == "panel_list":
        if not forward_chats:
            list_text = "📭 **ɴᴏ ᴀᴄᴛɪᴠᴇ ꜰᴏʀᴡᴀʀᴅɪɴɢ**"
        else:
            chat_list = "\n".join(f"• `{c}`" for c in list(forward_chats)[:15])
            if len(forward_chats) > 15:
                chat_list += f"\n• ... ᴀɴᴅ {len(forward_chats)-15} ᴍᴏʀᴇ"
            list_text = f"""
📤 **ꜰᴏʀᴡᴀʀᴅɪɴɢ ᴄʜᴀᴛꜱ**

────────────────────
📊 **ᴛᴏᴛᴀʟ:** {len(forward_chats)}
────────────────────
{chat_list}
"""
        keyboard = build_keyboard([
            ("⬅️ ʙᴀᴄᴋ", "panel_back", ButtonStyle.PRIMARY)
        ], row_width=1)
        await callback_query.edit_message_text(
            list_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
    
    # ===== PANEL BACK =====
    elif data == "panel_back":
        await refresh_panel(client, callback_query)
    
    # ===== PANEL CLOSE =====
    elif data == "panel_close":
        try:
            await callback_query.message.delete()
            await callback_query.answer("✅ ᴘᴀɴᴇʟ ᴄʟᴏꜱᴇᴅ!", show_alert=True)
        except Exception:
            await callback_query.answer("⚠️ ᴄᴏᴜʟᴅ ɴᴏᴛ ᴄʟᴏꜱᴇ", show_alert=True)


# ==================== ʀᴇꜰʀᴇꜱʜ ᴘᴀɴᴇʟ ꜰᴜɴᴄᴛɪᴏɴ ====================

async def refresh_panel(client, callback_query: CallbackQuery):
    """ʀᴇꜰʀᴇꜱʜ ᴛʜᴇ ᴘᴀɴᴇʟ ᴡɪᴛʜ ᴄᴜʀʀᴇɴᴛ ꜱᴛᴀᴛᴜꜱ"""
    
    # Get current stats
    recording_status = "🟢 ᴀᴄᴛɪᴠᴇ" if is_recording else "🔴 ɪɴᴀᴄᴛɪᴠᴇ"
    audio_status = "🔇 ᴍᴜᴛᴇᴅ" if is_muted else "🔊 ʟɪᴠᴇ"
    forward_count = len(forward_chats)
    uptime = get_uptime()
    
    # Create status bars
    vol_bar = create_progress_bar(audio_config['volume'], 200)
    bass_bar = create_progress_bar(audio_config['bass'], 60)
    treble_bar = create_progress_bar(audio_config['treble'], 60)
    gain_bar = create_progress_bar(audio_config['gain'], 60)
    
    panel_text = f"""
🎛️ **ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ** (🔄 ʀᴇꜰʀᴇꜱʜᴇᴅ)

────────────────────
📊 **ꜱʏꜱᴛᴇᴍ ꜱᴛᴀᴛᴜꜱ**
• **ʀᴇᴄᴏʀᴅɪɴɢ:** {recording_status}
• **ᴀᴜᴅɪᴏ:** {audio_status}
• **ꜰᴏʀᴡᴀʀᴅɪɴɢ:** {forward_count} ᴄʜᴀᴛꜱ
• **ᴜᴘᴛɪᴍᴇ:** {uptime}
• **ꜱᴏᴜʀᴄᴇ:** `{RECORD_SOURCE}`

────────────────────
🎵 **ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ**
• **ᴠᴏʟᴜᴍᴇ:** `{audio_config['volume']}%` {vol_bar}
• **ʙᴀꜱꜱ:** `{audio_config['bass']}/60` {bass_bar}
• **ᴛʀᴇʙʟᴇ:** `{audio_config['treble']}/60` {treble_bar}
• **ɢᴀɪɴ:** `{audio_config['gain']}/60` {gain_bar}

────────────────────
📌 **ᴜꜱᴇ ʙᴜᴛᴛᴏɴꜱ ʙᴇʟᴏᴡ ᴛᴏ ᴄᴏɴᴛʀᴏʟ**
"""
    
    # ===== BUILD KEYBOARD WITH ONLY 3 AVAILABLE STYLES =====
    keyboard = build_keyboard([
        # Row 1: Audio Controls
        ("🔇 ᴍᴜᴛᴇ", "panel_mute", ButtonStyle.DANGER),   # Red
        ("🔊 ᴜɴᴍᴜᴛᴇ", "panel_unmute", ButtonStyle.DANGER), # red
        
        # Row 2: Volume Controls
        ("🔉 ᴠᴏʟᴜᴍᴇ -", "panel_vol_down", ButtonStyle.SUCCESS),  # green
        ("🔊 ᴠᴏʟᴜᴍᴇ +", "panel_vol_up", ButtonStyle.SUCCESS),    # Green
        
        # Row 3: Bass Controls
        ("⬇️ ʙᴀꜱꜱ -", "panel_bass_down", ButtonStyle.PRIMARY),  # Dark Blue
        ("⬆️ ʙᴀꜱꜱ +", "panel_bass_up", ButtonStyle.PRIMARY),    # Dark Blue
        
        # Row 4: Treble Controls
        ("⬇️ ᴛʀᴇʙʟᴇ -", "panel_treble_down", ButtonStyle.DANGER), # red
        ("⬆️ ᴛʀᴇʙʟᴇ +", "panel_treble_up", ButtonStyle.DANGER),   # red
        
        # Row 5: Gain Controls
        ("⬇️ ɢᴀɪɴ -", "panel_gain_down", ButtonStyle.SUCCESS),  # Green 
        ("⬆️ ɢᴀɪɴ +", "panel_gain_up", ButtonStyle.SUCCESS),    # green
        
        # Row 6: Utility
        ("🔄 ʀᴇꜱᴇᴛ", "panel_reset", ButtonStyle.DANGER),  # Red
        ("📋 ʟɪꜱᴛ", "panel_list", ButtonStyle.DANGER),   # red
        
        # Row 7: Close
        ("❌ ᴄʟᴏꜱᴇ", "panel_close", ButtonStyle.DANGER),  # Red
    ], row_width=2)
    
    try:
        await callback_query.edit_message_text(
            panel_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.debug(f"ʀᴇꜰʀᴇꜱʜ_ᴘᴀɴᴇʟ ᴇᴅɪᴛ ꜰᴀɪʟᴇᴅ, ʀᴇꜱᴇɴᴅɪɴɢ: {e}")
        try:
            await callback_query.message.delete()
            await callback_query.message.reply_text(
                panel_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        except Exception:
            pass

# ==================== ᴘᴀɴᴇʟ ᴄᴏᴍᴍᴀɴᴅ ᴇɴᴅꜱ ====================
        
# ==================== MAIN ====================

async def main():
    """Start clients, resume monitors, and idle until stopped."""
    load_state()
    load_pending_joins()

    print("🎵 Audio Forwarder v5 - complete fixed version")
    print(f"📂 Pending joins: {len(PENDING_JOIN_REQUESTS)}")
    if SCIPY_AVAILABLE:
        print("✅ scipy available - full audio processing")
    else:
        print("⚠️ scipy not available - basic audio processing only")

    await bot_app.start()
    print("✅ Bot started successfully")

    try:
        await call_py.start()
        print("✅ PyTgCalls started successfully")
    except Exception as e:
        print(f"⚠️ PyTgCalls start failed (user session error): {e}")
        print("   Bot will still run for bot commands!")

    # Running loop exists here, so this is safe now.
    asyncio.create_task(resume_pending_joins())
    print("🔄 Pending join monitors resumed")

    print("\n✅ Online! Use /record then /join")
    print("📌 Owner: /approve, /disapprove, /userlist, /restart")
    print("📌 Audio: /level, /bass, /treble, /gain, /effects")
    print("📌 Extra: /ping, /stats, /joinlink\n")

    _idle = idle()
    if asyncio.iscoroutine(_idle):
        await _idle


async def _shutdown():
    """Leave calls, stop clients, and save state."""
    print("🔄 Cleaning up calls...")
    for chat in list(forward_chats):
        try:
            await call_py.leave_call(chat)
            print(f"   ✅ Left chat: {chat}")
        except Exception as e:
            print(f"   ⚠️ Couldn't leave {chat}: {e}")
    try:
        await call_py.leave_call(RECORD_SOURCE)
        print(f"   ✅ Left source: {RECORD_SOURCE}")
    except Exception as e:
        print(f"   ⚠️ Couldn't leave source: {e}")
    try:
        await call_py.stop()
        print("   ✅ PyTgCalls stopped")
    except Exception as e:
        print(f"   ⚠️ PyTgCalls stop error: {e}")
    try:
        if getattr(bot_app, "is_connected", False):
            await bot_app.stop()
        print("   ✅ Bot stopped")
    except Exception as e:
        print(f"   ⚠️ Bot stop error: {e}")
    save_state()
    save_pending_joins()
    print("   ✅ State saved")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        try:
            loop.run_until_complete(_shutdown())
        except Exception as e:
            print(f"   ❌ Cleanup error: {e}")
        finally:
            try:
                loop.close()
            except Exception:
                pass
