import os
import sys
import shutil
import asyncio
import subprocess
import time
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

# Configuration - Credentials provided by user
API_ID = int(os.getenv("API_ID", "31266551"))
API_HASH = os.getenv("API_HASH", "f2ebfd089cc0958fbedad2088fdc917b")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8780259250:AAHecgwTyyywEhlTgKdji1H2uiIcbto--kU")

CLIP_DURATION = 58  # 58 seconds per clip
try:
  loop = asyncio.get_event_loop()
except RuntimeError:
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)

app = Client(
    "clips_cutter_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# User settings memory
user_configs = {}

def get_config(user_id):
    if user_id not in user_configs:
        user_configs[user_id] = {
            "duration": 58,
            "mirror": False,
            "speed": True,       # 1.045x
            "zoom": True,        # 1.06x
            "shorts_916": True,  # 9:16 vertical blur background
            "watermark": ""
        }
    return user_configs[user_id]

def get_keyboard(cfg):
    mirror_status = "✅" if cfg["mirror"] else "❌"
    speed_status = "✅" if cfg["speed"] else "❌"
    zoom_status = "✅" if cfg["zoom"] else "❌"
    shorts_status = "✅" if cfg["shorts_916"] else "❌"

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"Duration: {cfg['duration']}s", callback_data="btn_duration"),
            InlineKeyboardButton(f"9:16 Shorts: {shorts_status}", callback_data="btn_shorts")
        ],
        [
            InlineKeyboardButton(f"Mirror/Flip: {mirror_status}", callback_data="btn_mirror"),
            InlineKeyboardButton(f"Micro Speed (1.045x): {speed_status}", callback_data="btn_speed")
        ],
        [
            InlineKeyboardButton(f"Auto Zoom (1.06x): {zoom_status}", callback_data="btn_zoom"),
            InlineKeyboardButton("Watermark Badlo", callback_data="btn_watermark")
        ]
    ])

def format_bytes(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

async def progress_callback(current, total, status_msg, action_text, last_edit_time):
    now = time.time()
    # Update every 3 seconds to avoid FloodWait
    if now - last_edit_time[0] > 3:
        percentage = (current / total) * 100
        cur_str = format_bytes(current)
        tot_str = format_bytes(total)
        try:
            await status_msg.edit_text(
                f"⏳ *{action_text}*\n"
                f"📊 Progress: `{percentage:.1f}%` ({cur_str} / {tot_str})"
            )
            last_edit_time[0] = now
        except Exception:
            pass

def get_video_duration(filepath):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        filepath
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(res.stdout.strip())
    except:
        return 0

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id
    cfg = get_config(user_id)
    text = (
        "🎬 *2 GB MTProto Video Clips Cutter Bot*\n\n"
        "Ye bot **2,000 MB (2 GB)** tak ki badi videos ko aaram se process karta hai.\n\n"
        "📌 *Features:*\n"
        "• Long video ko **58-second clips** me cut karta hai\n"
        "• **9:16 Shorts / Reels** frame with blurred background\n"
        "• **1.045x Micro speed** & **1.06x Zoom** (Anti-detection)\n"
        "• **Mirror / Flip** option\n"
        "• Custom watermark overlay\n\n"
        "Settings toggle karne ke liye buttons dabayein, ya direct koi bhi video bhejein:"
    )
    await message.reply_text(text, reply_markup=get_keyboard(cfg))

@app.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    cfg = get_config(user_id)
    data = query.data

    if data == "btn_shorts":
        cfg["shorts_916"] = not cfg["shorts_916"]
    elif data == "btn_mirror":
        cfg["mirror"] = not cfg["mirror"]
    elif data == "btn_speed":
        cfg["speed"] = not cfg["speed"]
    elif data == "btn_zoom":
        cfg["zoom"] = not cfg["zoom"]
    elif data == "btn_duration":
        durations = [30, 45, 58, 60]
        cur = durations.index(cfg["duration"]) if cfg["duration"] in durations else 2
        cfg["duration"] = durations[(cur + 1) % len(durations)]
    elif data == "btn_watermark":
        await query.message.reply_text("Watermark set karne ke liye type karein:\n`/watermark @yourchannel`")
        await query.answer()
        return

    await query.message.edit_reply_markup(reply_markup=get_keyboard(cfg))
    await query.answer()

@app.on_message(filters.command("watermark") & filters.private)
async def watermark_handler(client: Client, message: Message):
    user_id = message.from_user.id
    cfg = get_config(user_id)
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        cfg["watermark"] = args[1].strip()
        await message.reply_text(f"✅ Watermark set ho gaya: `{cfg['watermark']}`")
    else:
        cfg["watermark"] = ""
        await message.reply_text("❌ Watermark hata diya gaya.")

@app.on_message((filters.video | filters.document) & filters.private)
async def video_handler(client: Client, message: Message):
    media = message.video or message.document
    if not media:
        return

    # Check MIME type for document
    if message.document and not (message.document.mime_type and message.document.mime_type.startswith("video/")):
        await message.reply_text("Kripya ek valid video file bhejein.")
        return

    user_id = message.from_user.id
    cfg = get_config(user_id)
    work_dir = f"work_{user_id}_{message.id}"
    os.makedirs(work_dir, exist_ok=True)
    input_path = os.path.join(work_dir, "input_video.mp4")

    status = await message.reply_text("🚀 2 GB MTProto Downloader: Video download shuru...")

    try:
        last_edit = [time.time()]
        # MTProto 2GB download with real-time progress
        await client.download_media(
            message=message,
            file_name=input_path,
            progress=progress_callback,
            progress_args=(status, "Video Download Ho Rahi Hai (2 GB Support)", last_edit)
        )

        total_duration = get_video_duration(input_path)
        if total_duration <= 0:
            await status.edit_text("❌ Video ki duration detect nahi ho saki.")
            return

        clip_len = cfg["duration"]
        total_clips = int(total_duration // clip_len) + (1 if (total_duration % clip_len) >= 3 else 0)
        if total_clips == 0:
            total_clips = 1

        await status.edit_text(
            f"✅ *Download Complete!*\n"
            f"⏱️ Video Duration: `{round(total_duration)}s`\n"
            f"✂️ Banenge `{total_clips}` Clips ({clip_len}s each)\n"
            f"⚙️ FFmpeg processing shuru ho rahi hai..."
        )

        cur_start = 0
        clip_idx = 1

        while cur_start < total_duration:
            cur_end = min(cur_start + clip_len, total_duration)
            seg_len = cur_end - cur_start
            if seg_len < 3 and clip_idx > 1:
                break

            out_clip = os.path.join(work_dir, f"clip_{clip_idx}.mp4")
            await status.edit_text(f"🎬 Processing Clip *#{clip_idx} of {total_clips}* ({round(cur_start)}s se {round(cur_end)}s)...")

            # FFmpeg filter building
            vf_steps = []
            if cfg["mirror"]:
                vf_steps.append("hflip")
            if cfg["zoom"]:
                vf_steps.append("scale=iw*1.06:ih*1.06,crop=iw/1.06:ih/1.06")

            pre_vf = ",".join(vf_steps) if vf_steps else "null"

            if cfg["shorts_916"]:
                complex_filter = (
                    f"[0:v]{pre_vf}[base];"
                    f"[base]split=2[fg][bg];"
                    f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bgblur];"
                    f"[fg]scale=1080:-1[fgscaled];"
                    f"[bgblur][fgscaled]overlay=(W-w)/2:(H-h)/2"
                )
            else:
                complex_filter = f"[0:v]{pre_vf}"

            if cfg["watermark"]:
                clean_wm = cfg["watermark"].replace("'", "").replace(":", "")
                complex_filter += f",drawtext=text='{clean_wm}':fontcolor=white@0.7:fontsize=36:x=40:y=h-80"

            audio_filter = "atempo=1.045" if cfg["speed"] else "anull"

            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-ss", str(cur_start),
                "-t", str(seg_len),
                "-i", input_path,
                "-filter_complex", complex_filter,
                "-filter:a", audio_filter,
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "128k",
                out_clip
            ]

            proc = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc.returncode != 0:
                await message.reply_text(f"⚠️ Clip #{clip_idx} render karte waqt error aaya.")
            else:
                upload_edit = [time.time()]
                caption = (
                    f"🎬 *Clip #{clip_idx}* ({round(seg_len)}s)\n"
                    f"✨ 58s Remix • Ready for Shorts/Reels!"
                )
                await client.send_video(
                    chat_id=message.chat.id,
                    video=out_clip,
                    caption=caption,
                    supports_streaming=True,
                    progress=progress_callback,
                    progress_args=(status, f"Clip #{clip_idx} Telegram par upload ho rahi hai", upload_edit)
                )
                if os.path.exists(out_clip):
                    os.remove(out_clip)

            cur_start += clip_len
            clip_idx += 1

        await status.edit_text("🎉 *Sabhi clips 2 GB MTProto Bot ke zariye ready ho kar send ho chuke hain!*")

    except Exception as e:
        await status.edit_text(f"❌ Error aaya: `{str(e)}`")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

if __name__ == "__main__":
    print("🚀 2 GB MTProto Clips Cutter Bot starting...")
    app.run()
