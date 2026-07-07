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
import json
import logging
import asyncio
import warnings
import time
warnings.filterwarnings('ignore')

# Try to import scipy, fallback to basic processing if not available
try:
    from scipy import signal
    SCIPY_AVAILABLE = True
except BaseException:
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
# SECURITY: prefer environment variables. Any secrets previously hard-coded
# here have been exposed and should be rotated (new bot token + new session).
API_ID = int(os.getenv("API_ID", "29177322"))
API_HASH = os.getenv("API_HASH", "1b8573accde3d0b7c35e43cdbb36e523")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8554005804:AAGjW8m_T6e9SrWmzXmLechUKYgANbz-IDs")
OWNER_ID = int(os.getenv("OWNER_ID", "8305984975"))
STRING_SESSION = "BQG9NeoAKgnwMUVxrdLuZqchTSFQaiKJpPuSYhmG29j15hA7BHwFt5-BlIbFOhO4aY6NHKSgdeqp6FmGtIk0_6Aao11efgSUBx23sbDiFj-1Wq2YyZnnUteWe7ao5tienj13NGwYnrxb3pbQpFMeQFwGhtfUzXbVTgiVT4KD3xks7bFfeA_bpkuM50WEs_4yB9KFzsLQZ99oirkxmUXe8r9DDiXKvpkppPKO50Np6gArSQ_MUI7f5sxW9RMNl6YwJYfI837hkPIjFL9ZkgqG2KXV-wCai93e5bR2K_zPS6vh6rZ8RCv_mfjtjaf0hDpsx4Eh7FDgWmWk2VNGcGUdz3ODozAE4QAAAAIJm0jrAA"
STRING_SESSION = os.getenv("STRING_SESSION", STRING_SESSION)
RECORD_GROUP = int(os.getenv("RECORD_GROUP", "-1003970175858"))
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

# ==================== ᴘᴇʀꜱɪꜱᴛᴇɴᴄᴇ ====================
STATE_FILE = "bot_state.json"

def save_state():
    """ᴘᴇʀꜱɪꜱᴛ ᴀᴘᴘʀᴏᴠᴇᴅ ᴜꜱᴇʀꜱ ᴀɴᴅ ᴀᴜᴅɪᴏ ᴄᴏɴꜰɪɢ ᴛᴏ ᴅɪꜱᴋ"""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({
                "approved_users": sorted(approved_users),
                "audio_config": audio_config,
                "record_source": RECORD_SOURCE, 
            }, f, indent=2)
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
        
        saved_source = data.get("record_source")
        if saved_source is not None:
            RECORD_SOURCE = saved_source
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
    filled = int((value / max_val) * length)
    return "█" * filled + "░" * (length - filled)

def get_effect_status(value, max_val):
    """ɢᴇᴛ ꜱᴛᴀᴛᴜꜱ ʙᴀꜱᴇᴅ ᴏɴ ᴠᴀʟᴜᴇ"""
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
    """ᴀᴘᴘʟʏ ᴠᴏʟᴜᴍᴇ ʙᴏᴏꜱᴛ (0-200%)"""
    if level == 100:
        return audio_data
    gain_factor = level / 50.0
    return np.clip(audio_data.astype(np.float32) * gain_factor, -32768, 32767).astype(np.int16)

def apply_bass_boost_basic(audio_data, bass_level):
    """ꜰᴀꜱᴛ ʙᴀꜱꜱ ʙᴏᴏꜱᴛ (ɴᴏ ꜱᴄɪᴘʏ)"""

    if bass_level <= 0:
        return audio_data

    audio = audio_data.astype(np.float32)

    # Smooth low-frequency extraction
    window_size = int(48 - min(bass_level, 60) * 0.4)
    window_size = max(12, min(window_size, 48))

    kernel = np.ones(window_size, dtype=np.float32) / window_size
    low = np.convolve(audio, kernel, mode="same")

    # Keep bass controlled
    mix = min(0.25, bass_level / 300.0)

    processed = audio + (low * mix)

    # Remove excessive rumble
    processed -= np.mean(processed)

    # Soft limiter
    processed = 30000.0 * np.tanh(processed / 30000.0)

    return np.clip(processed, -32768, 32767).astype(np.int16)

def apply_bass_boost_advanced(audio_data, bass_level, sample_rate=48000):
    """ᴀᴅᴠᴀɴᴄᴇᴅ ʙᴀꜱꜱ ʙᴏᴏꜱᴛ ᴡɪᴛʜ ꜱᴄɪᴘʏ"""
    if bass_level == 0:
        return audio_data
    try:
        f0 = 70
        Q = 0.8
        gain_db = bass_level / 3
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
        if audio_config.get('highpass', True):
            b_hp, a_hp = signal.butter(2, 50 / (sample_rate / 2), btype='high')
            filtered = signal.lfilter(b_hp, a_hp, filtered)
        return np.clip(filtered, -32768, 32767).astype(np.int16)
    except Exception as e:
        logger.error(f"ᴀᴅᴠᴀɴᴄᴇᴅ ʙᴀꜱꜱ ᴇʀʀᴏʀ: {e}")
        return apply_bass_boost_basic(audio_data, bass_level)

def apply_treble_boost_basic(audio_data, treble_level):
    """ꜰᴀꜱᴛ ᴛʀᴇʙʟᴇ / ᴘʀᴇꜱᴇɴᴄᴇ ʙᴏᴏꜱᴛ (ɴᴏ ꜱᴄɪᴘʏ)"""

    if treble_level <= 0:
        return audio_data

    audio = audio_data.astype(np.float32)

    # High-frequency extraction
    alpha = 0.92
    high = np.empty_like(audio)
    high[0] = audio[0]

    for i in range(1, len(audio)):
        high[i] = alpha * (high[i - 1] + audio[i] - audio[i - 1])

    # Smooth boost
    mix = min(0.35, treble_level / 180.0)

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
        Q = 0.8
        gain_db = treble_level / 5
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
    """ᴀᴘᴘʟʏ ꜱᴏꜰᴛ ɢᴀɪɴ ᴡɪᴛʜ ᴄᴏᴍᴘʀᴇꜱꜱᴏʀ, ᴍᴀᴋᴇᴜᴘ ɢᴀɪɴ & ꜱᴏꜰᴛ ʟɪᴍɪᴛᴇʀ"""

    if gain_level <= 0:
        return audio_data

    audio = audio_data.astype(np.float32)

    # ==================== Input Gain ====================
    gain_factor = 2.0 + (gain_level / 40.0)
    processed = audio * gain_factor

    # ==================== Compressor ====================
    if audio_config.get("compressor", True):
        threshold = 18000.0
        ratio = 3.5

        abs_processed = np.abs(processed)
        above = abs_processed > threshold

        if np.any(above):
            excess = abs_processed[above] - threshold
            processed[above] = (
                np.sign(processed[above]) *
                (threshold + excess / ratio)
            )

        # Makeup Gain
        processed *= 1.55

    # ==================== Soft Limiter ====================
    if audio_config.get("limiter", True):
        limit = 32700.0
        processed = limit * np.tanh(processed / limit)

    # ==================== Final Safety ====================
    processed = np.clip(processed, -32768, 32767)

    return processed.astype(np.int16)

def process_audio(audio_data):
    """ᴀᴘᴘʟʏ ᴀʟʟ ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ ɪɴ ᴄʜᴀɪɴ"""

    if audio_data is None or len(audio_data) == 0:
        return audio_data

    try:
        processed = audio_data.copy()
        config = audio_config

        if config['volume'] != 100:
            processed = apply_volume_boost(processed, config['volume'])

        if config['bass'] > 0:
            if SCIPY_AVAILABLE:
                processed = apply_bass_boost_advanced(
                    processed,
                    config['bass']
                )
            else:
                processed = apply_bass_boost_basic(
                    processed,
                    config['bass']
                )

        if config['treble'] > 0:
            if SCIPY_AVAILABLE:
                processed = apply_treble_boost_advanced(
                    processed,
                    config['treble']
                )
            else:
                processed = apply_treble_boost_basic(
                    processed,
                    config['treble']
                )

        if config['gain'] > 0:
            processed = apply_soft_gain(
                processed,
                config['gain']
            )

        if config.get('lowpass', False) and SCIPY_AVAILABLE:
            try:
                b, a = signal.butter(
                    4,
                    16000 / 24000,
                    btype='low'
                )

                processed = signal.lfilter(
                    b,
                    a,
                    processed.astype(np.float32)
                )

                processed = np.clip(
                    processed,
                    -32768,
                    32767
                ).astype(np.int16)

            except Exception:
                pass

        return processed

    except Exception as e:
        logger.error(f"ᴀᴜᴅɪᴏ ᴘʀᴏᴄᴇꜱꜱɪɴɢ ᴇʀʀᴏʀ: {e}")
        return audio_data

# ==================== ᴀᴜᴅɪᴏ ʜᴀɴᴅʟᴇʀ ====================

@call_py.on_update(pytg_filters.stream_frame(Direction.INCOMING, Device.MICROPHONE))
async def audio_forwarder(_, update: StreamFrames):
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
            processed_output = process_audio(mixed_output)
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

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
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
    """ʜᴀɴᴅʟᴇ ᴀʟʟ ɴᴏɴ-ᴘᴀɴᴇʟ ᴄᴀʟʟʙᴀᴄᴋ Qᴜᴇʀɪᴇꜱ (ꜱᴇᴇ panel_callbacks ꜰᴏʀ panel_* ᴅᴀᴛᴀ)"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if user_id != OWNER_ID and user_id not in approved_users:
        await callback_query.answer("⛔ ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ!", show_alert=True)
        return
    
    await callback_query.answer()
    
    if data == "refresh_userlist":
        if not approved_users:
            keyboard = build_keyboard([
                ("➕ ᴀᴘᴘʀᴏᴠᴇ", "help_info", ButtonStyle.SUCCESS),
                ("🏠 ʜᴏᴍᴇ", "back_start", ButtonStyle.PRIMARY)
            ], row_width=2)
            await callback_query.edit_message_text(
                "📭 **ɴᴏ ᴜꜱᴇʀꜱ ᴀʀᴇ ᴀᴘᴘʀᴏᴠᴇᴅ ʏᴇᴛ.**",
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
    
    elif data == "back_userlist":
        if not approved_users:
            keyboard = build_keyboard([
                ("➕ ᴀᴘᴘʀᴏᴠᴇ", "help_info", ButtonStyle.SUCCESS),
                ("🏠 ʜᴏᴍᴇ", "back_start", ButtonStyle.PRIMARY)
            ], row_width=2)
            await callback_query.edit_message_text(
                "📭 **ɴᴏ ᴜꜱᴇʀꜱ ᴀᴘᴘʀᴏᴠᴇᴅ**\n\nᴜꜱᴇ `/approve` ᴛᴏ ᴀᴅᴅ",
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
    
    elif data == "help_info":
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
📊 **ᴜᴛɪʟɪᴛʏ**
/ping - ᴄʜᴇᴄᴋ ʙᴏᴛ
/stats - ʙᴏᴛ ꜱᴛᴀᴛꜱ
/status - ꜱʏꜱᴛᴇᴍ ꜱᴛᴀᴛᴜꜱ
/list - ꜰᴏʀᴡᴀʀᴅɪɴɢ ʟɪꜱᴛ
/id - ɢᴇᴛ ᴄʜᴀᴛ ɪᴅ
/panel - ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ (ʙᴜᴛᴛᴏɴꜱ)
────────────────────
👤 **ᴜꜱᴇʀ ᴍɢᴍᴛ** (ᴏᴡɴᴇʀ)
/approve - ᴀᴅᴅ ᴜꜱᴇʀ
/disapprove - ʀᴇᴍᴏᴠᴇ
/userlist - ʟɪꜱᴛ ᴜꜱᴇʀꜱ
/setrecordgroup <ɪᴅ> - ᴄʜᴀɴɢᴇ ꜱᴏᴜʀᴄᴇ
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
    
    elif data == "owner":
        keyboard = build_keyboard([
            ("🏠 ʜᴏᴍᴇ", "back_start", ButtonStyle.SUCCESS)
        ], row_width=1)
        await callback_query.edit_message_text(
            "👤 **ᴏᴡɴᴇʀ**\n\n"
            "📌 @Why_not_ZarKo\n"
            "🔗 [ᴛᴇʟᴇɢʀᴀᴍ](t.me/Why_not_ZarKo)",
            reply_markup=keyboard,
            disable_web_page_preview=True
        )


# ===== ꜱᴛᴀʀᴛ ᴄᴏᴍᴍᴀɴᴅ =====

@bot_app.on_message(pyro_filters.command("start"))
async def cmd_start(client, message):
    """ꜱᴛᴀʀᴛ ᴄᴏᴍᴍᴀɴᴅ ᴡɪᴛʜ ʙᴜᴛᴛᴏɴꜱ"""
    user_id = message.from_user.id if message.from_user else None
    
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
📊 **ᴜᴛɪʟɪᴛʏ**
/ping - ᴄʜᴇᴄᴋ ʙᴏᴛ
/stats - ʙᴏᴛ ꜱᴛᴀᴛꜱ
/status - ꜱʏꜱᴛᴇᴍ ꜱᴛᴀᴛᴜꜱ
/list - ꜰᴏʀᴡᴀʀᴅɪɴɢ ʟɪꜱᴛ
/id - ɢᴇᴛ ᴄʜᴀᴛ ɪᴅ
/panel - ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ (ʙᴜᴛᴛᴏɴꜱ)
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

# ===== ᴜᴛɪʟɪᴛʏ ᴄᴏᴍᴍᴀɴᴅꜱ =====

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
────────────────────

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
                f"💡 ᴜꜱᴇ ᴀ ɴᴜᴍᴇʀɪᴄ ɪᴅ (ᴇ.ɢ., `-1003929100976`)"
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

🔊 **ɴᴏ ᴀᴜᴅɪᴏ ɪꜱ ʙᴇɪɴɢ ꜰᴏʀᴡᴀʀᴅᴇᴅ ʀɪɢʜᴛ ɴᴏ���!**
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
            f"📊 **ᴄᴜʀʀᴇɴ��:** `{current}%`\n"
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

        
@bot_app.on_message(pyro_filters.command("reset") & authorized_only())
async def cmd_reset(client, message):
    """ʀᴇꜱᴇᴛ ᴀʟʟ ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ"""
    global audio_config
    old_config = audio_config.copy()
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
    reset_msg = f"""
✅ **ᴀʟʟ ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ ʀᴇꜱᴇᴛ!**

────────────────────
🔊 **ᴠᴏʟᴜᴍᴇ:** `{old_config['volume']}%` → `{audio_config['volume']}%` ✅
🎸 **ʙᴀꜱꜱ:** `{old_config['bass']}` → `{audio_config['bass']}` ✅
🎵 **ᴛʀᴇʙʟᴇ:** `{old_config['treble']}` → `{audio_config['treble']}` ✅
📈 **ɢᴀɪɴ:** `{old_config['gain']}` → `{audio_config['gain']}` ✅
────────────────────

📊 **ꜱᴛᴀᴛᴜꜱ:** 🟢 ꜰᴀᴄᴛᴏʀʏ ᴅᴇꜰᴀᴜʟᴛ ʀᴇꜱᴛᴏʀᴇᴅ
🎯 **ᴇꜰꜰᴇᴄᴛꜱ:** ᴀʟʟ ᴄʟᴇᴀʀᴇᴅ
"""
    await message.reply(reset_msg)
    logger.info("ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ ʀᴇꜱᴇᴛ ᴛᴏ ᴅᴇꜰᴀᴜʟᴛ")

@bot_app.on_message(pyro_filters.command("effects") & authorized_only())
async def cmd_effects(client, message):
    """ꜱʜᴏᴡ ᴄᴜʀʀᴇɴᴛ ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ"""
    config = audio_config
    scipy_status = "✅ ᴀᴅᴠᴀɴᴄᴇᴅ ᴀᴠᴀɪʟᴀʙʟᴇ" if SCIPY_AVAILABLE else "❌ ʙᴀꜱɪᴄ ᴏɴʟʏ"
    vol_bar = create_progress_bar(config['volume'], 200)
    bass_bar = create_progress_bar(config['bass'], 60)
    treble_bar = create_progress_bar(config['treble'], 60)
    gain_bar = create_progress_bar(config['gain'], 60)
    
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

⚙️ **ꜰᴇᴀᴛᴜʀᴇꜱ**
• ᴄᴏᴍᴘʀᴇꜱꜱᴏʀ: {'✅ ᴇɴᴀʙʟᴇᴅ' if config['compressor'] else '❌ ᴅɪꜱᴀʙʟᴇᴅ'}
• ʟɪᴍɪᴛᴇʀ: {'✅ ᴇɴᴀʙʟᴇᴅ' if config['limiter'] else '❌ ᴅɪꜱᴀʙʟᴇᴅ'}
• ʜɪɢʜᴘᴀꜱꜱ: {'✅ ᴇɴᴀʙʟᴇᴅ' if config['highpass'] else '❌ ᴅɪꜱᴀʙʟᴇᴅ'}
• ʟᴏᴡᴘᴀꜱꜱ: {'✅ ᴇɴᴀʙʟᴇᴅ' if config['lowpass'] else '❌ ᴅɪꜱᴀʙʟᴇᴅ'}

📦 **ꜱᴄɪᴘʏ:** {scipy_status}
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
        
        # ===== 3. CLEAR STATE =====
        forward_chats = set()  # Reassign instead of clear
        is_recording = False
        is_muted = False
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
                """ʀᴇɢɪꜱᴛᴇʀᴇᴅ ᴀᴜᴅɪᴏ ʜᴀɴᴅʟᴇʀ"""
                if is_muted or update.chat_id != RECORD_SOURCE or not forward_chats:
                    return
                async with processing_lock:
                    try:
                        if not update.frames:
                            return
                        frame_length = len(update.frames[0].frame) // 2
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
                        processed_output = process_audio(mixed_output)
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
            
            # Start PyTgCalls
            await call_py.start()
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
        ("🔊 ᴜɴᴍᴜᴛᴇ", "panel_unmute", ButtonStyle.SUCCESS), # Green
        
        # Row 2: Volume Controls
        ("🔉 ᴠᴏʟᴜᴍᴇ -", "panel_vol_down", ButtonStyle.PRIMARY),  # Dark Blue
        ("🔊 ᴠᴏʟᴜᴍᴇ +", "panel_vol_up", ButtonStyle.PRIMARY),    # Dark Blue
        
        # Row 3: Bass Controls
        ("⬇️ ʙᴀꜱꜱ -", "panel_bass_down", ButtonStyle.PRIMARY),  # Dark Blue
        ("⬆️ ʙᴀꜱꜱ +", "panel_bass_up", ButtonStyle.PRIMARY),    # Dark Blue
        
        # Row 4: Treble Controls
        ("⬇️ ᴛʀᴇʙʟᴇ -", "panel_treble_down", ButtonStyle.PRIMARY), # Dark Blue
        ("⬆️ ᴛʀᴇʙʟᴇ +", "panel_treble_up", ButtonStyle.PRIMARY),   # Dark Blue
        
        # Row 5: Gain Controls
        ("⬇️ ɢᴀɪɴ -", "panel_gain_down", ButtonStyle.PRIMARY),  # Dark Blue
        ("⬆️ ɢᴀɪɴ +", "panel_gain_up", ButtonStyle.PRIMARY),    # Dark Blue
        
        # Row 6: Utility
        ("🔄 ʀᴇꜱᴇᴛ", "panel_reset", ButtonStyle.DANGER),  # Red
        ("📋 ʟɪꜱᴛ", "panel_list", ButtonStyle.PRIMARY),   # Dark Blue
        
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
    global is_muted, audio_config
    
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
        audio_config['volume'] = 200
        save_state()
        await callback_query.answer("🔊 ᴠᴏʟᴜᴍᴇ: ᴍᴀx (200%)", show_alert=True)
        await refresh_panel(client, callback_query)
    
    elif data == "panel_vol_down":
        audio_config['volume'] = 100
        save_state()
        await callback_query.answer("🔉 ᴠᴏʟᴜᴍᴇ: 100%", show_alert=True)
        await refresh_panel(client, callback_query)
    
    # ===== BASS CONTROLS =====
    elif data == "panel_bass_up":
        audio_config['bass'] = 60
        audio_config['highpass'] = True
        save_state()
        await callback_query.answer("🎸 ʙᴀꜱꜱ: ᴍᴀx (60/60)", show_alert=True)
        await refresh_panel(client, callback_query)
    
    elif data == "panel_bass_down":
        audio_config['bass'] = 0
        audio_config['highpass'] = False
        save_state()
        await callback_query.answer("🎸 ʙᴀꜱꜱ: ᴏꜰꜰ (0/60)", show_alert=True)
        await refresh_panel(client, callback_query)
    
    # ===== TREBLE CONTROLS =====
    elif data == "panel_treble_up":
        audio_config['treble'] = 60
        save_state()
        await callback_query.answer("🎵 ᴛʀᴇʙʟᴇ: ᴍᴀx (60/60)", show_alert=True)
        await refresh_panel(client, callback_query)
    
    elif data == "panel_treble_down":
        audio_config['treble'] = 0
        save_state()
        await callback_query.answer("🎵 ᴛʀᴇʙʟᴇ: ᴏꜰꜰ (0/60)", show_alert=True)
        await refresh_panel(client, callback_query)
    
    # ===== GAIN CONTROLS =====
    elif data == "panel_gain_up":
        audio_config['gain'] = 60
        save_state()
        await callback_query.answer("📈 ɢᴀɪɴ: ᴍᴀx (60/60)", show_alert=True)
        await refresh_panel(client, callback_query)
    
    elif data == "panel_gain_down":
        audio_config['gain'] = 0
        save_state()
        await callback_query.answer("📈 ɢᴀɪɴ: ᴏꜰꜰ (0/60)", show_alert=True)
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
        ("🔊 ᴜɴᴍᴜᴛᴇ", "panel_unmute", ButtonStyle.SUCCESS), # Green
        
        # Row 2: Volume Controls
        ("🔉 ᴠᴏʟᴜᴍᴇ -", "panel_vol_down", ButtonStyle.PRIMARY),  # Dark Blue
        ("🔊 ᴠᴏʟᴜᴍᴇ +", "panel_vol_up", ButtonStyle.PRIMARY),    # Dark Blue
        
        # Row 3: Bass Controls
        ("⬇️ ʙᴀꜱꜱ -", "panel_bass_down", ButtonStyle.PRIMARY),  # Dark Blue
        ("⬆️ ʙᴀꜱꜱ +", "panel_bass_up", ButtonStyle.PRIMARY),    # Dark Blue
        
        # Row 4: Treble Controls
        ("⬇️ ᴛʀᴇʙʟᴇ -", "panel_treble_down", ButtonStyle.PRIMARY), # Dark Blue
        ("⬆️ ᴛʀᴇʙʟᴇ +", "panel_treble_up", ButtonStyle.PRIMARY),   # Dark Blue
        
        # Row 5: Gain Controls
        ("⬇️ ɢᴀɪɴ -", "panel_gain_down", ButtonStyle.PRIMARY),  # Dark Blue
        ("⬆️ ɢᴀɪɴ +", "panel_gain_up", ButtonStyle.PRIMARY),    # Dark Blue
        
        # Row 6: Utility
        ("🔄 ʀᴇꜱᴇᴛ", "panel_reset", ButtonStyle.DANGER),  # Red
        ("📋 ʟɪꜱᴛ", "panel_list", ButtonStyle.PRIMARY),   # Dark Blue
        
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
        
# ==================== ᴍᴀɪɴ ====================

if __name__ == "__main__":
    load_state()
    print("🎵 ᴀᴜᴅɪᴏ ꜰᴏʀᴡᴀʀᴅᴇʀ ᴠ5 - ᴄᴏᴍᴘʟᴇᴛᴇ ꜰɪxᴇᴅ ᴠᴇʀꜱɪᴏɴ")
    print("✅ ᴄᴀᴄʜᴇ-ꜰɪʀꜱᴛ ᴀᴘᴘʀᴏᴀᴄʜ ᴡɪᴛʜ ᴇʀʀᴏʀ ʜᴀɴᴅʟɪɴɢ")
    print("✅ ꜰᴜʟʟ ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛꜱ ꜱᴜᴘᴘᴏʀᴛ")
    print("✅ ᴜꜱᴇʀ ᴀᴘᴘʀᴏᴠᴀʟ ꜱʏꜱᴛᴇᴍ - ꜱɪʟᴇɴᴛ ɪɢɴᴏʀᴇ ꜰᴏʀ ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜꜱᴇʀꜱ\n")
    
    if SCIPY_AVAILABLE:
        print("✅ ꜱᴄɪᴘʏ ᴀᴠᴀɪʟᴀʙʟᴇ - ꜰᴜʟʟ ᴀᴜᴅɪᴏ ᴘʀᴏᴄᴇꜱꜱɪɴɢ")
    else:
        print("⚠️ ꜱᴄɪᴘʏ ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ - ʙᴀꜱɪᴄ ᴀᴜᴅɪᴏ ᴘʀᴏᴄᴇꜱꜱɪɴɢ ᴏɴʟʏ")
        print("   ɪɴꜱᴛᴀʟʟ ᴡɪᴛʜ: ᴘɪᴘ ɪɴꜱᴛᴀʟʟ ꜱᴄɪᴘʏ\n")
    
    try:
        bot_app.start()
        try:
            call_py.start()
        except Exception as e:
            print(f"⚠️ ᴘʏᴛɢᴄᴀʟʟꜱ ꜱᴛᴀʀᴛ ꜰᴀɪʟᴇᴅ (User session error): {e}")
            print("   ʙᴏᴛ ᴡɪʟʟ ꜱᴛɪʟʟ ʀᴜɴ ꜰᴏʀ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅꜱ!\n")
        
        print("✅ ᴏɴʟɪɴᴇ! ᴜꜱᴇ /ʀᴇᴄᴏʀᴅ ᴛʜᴇɴ /ᴊᴏɪɴ")
        print("📌 ᴏᴡɴᴇʀ ᴄᴏᴍᴍᴀɴᴅꜱ: /ᴀᴘᴘʀᴏᴠᴇ, /ᴅɪꜱᴀᴘᴘʀᴏᴠᴇ, /ᴜꜱᴇʀʟɪꜱᴛ, /ʀᴇꜱᴛᴀʀᴛ")
        print("📌 ᴀᴜᴅɪᴏ ᴄᴏᴍᴍᴀɴᴅꜱ: /ʟᴇᴠᴇʟ, /ʙᴀꜱꜱ, /ᴛʀᴇʙʟᴇ, /ɢᴀɪɴ, /ᴇꜰꜰᴇᴄᴛꜱ")
        print("📌 ᴇxᴛʀᴀ ᴄᴏᴍᴍᴀɴᴅꜱ: /ᴘɪɴɢ, /ꜱᴛᴀᴛꜱ")
        print("⚠️ ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜꜱᴇʀꜱ ɢᴇᴛ ɴᴏ ʀᴇꜱᴘᴏɴꜱᴇ (ꜱɪʟᴇɴᴛ ɪɢɴᴏʀᴇ)\n")
        
        idle()
        
    except KeyboardInterrupt:
        print("\n🛑 ꜱʜᴜᴛᴛɪɴɢ ᴅᴏᴡɴ...")
    except Exception as e:
        print(f"❌ ꜰᴀᴛᴀʟ ᴇʀʀᴏʀ: {e}")
    finally:
        try:
            # Leave all calls
            for chat in list(forward_chats):
                try:
                    call_py.leave_call(chat)
                except Exception:
                    pass
            
            # Leave source
            try:
                call_py.leave_call(RECORD_SOURCE)
            except Exception:
                pass
            
            # Stop PyTgCalls
            try:
                call_py.stop()
            except Exception:
                pass
            
            # Stop Bot
            try:
                bot_app.stop()
            except Exception:
                pass
                
        except Exception:
            pass
        
        print("✅ ᴄʟᴇᴀɴᴜᴘ ᴄᴏᴍᴘʟᴇᴛᴇ")