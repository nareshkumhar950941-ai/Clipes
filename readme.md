# 🎬 2 GB MTProto Clips Cutter & Remixer Bot

Ye Telegram Bot **Pyrogram MTProto Protocol** par bana hai, jo Telegram ke standard 20MB limit ko cross karke **2,000 MB (2 GB)** tak ki badi video files ko direct download aur upload karta hai.

---

## 🔑 Configured Credentials

Aapke credentials already code me configured hain:
- **API ID**: `31266551`
- **API HASH**: `f2ebfd089cc0958fbedad2088fdc917b`
- **BOT TOKEN**: `@BotFather` se mila token

---

## 🚀 GitHub & Free Hosting Setup (Render / Railway / VPS)

### Option 1: Render.com (24/7 Free Run with Docker)
1. In files (`bot.py`, `requirements.txt`, `Dockerfile`, `README.md`) ko apne GitHub repository me upload karein.
2. [Render.com](https://render.com) par jayein > **New** > **Background Worker**.
3. Apna GitHub repo connect karein.
4. **Environment Variables** me ye add karein:
   - `BOT_TOKEN` = Aapka Telegram bot token
   - `API_ID` = `31266551`
   - `API_HASH` = `f2ebfd089cc0958fbedad2088fdc917b`
5. **Deploy** click karein! Render automatically Dockerfile se FFmpeg aur Python setup karke bot start kar dega.

### Option 2: VPS ya Local PC Par Run Karein
```bash
# 1. FFmpeg install karein
sudo apt update && sudo apt install -y ffmpeg python3-pip

# 2. Dependencies install karein
pip install -r requirements.txt

# 3. Bot Token set karke run karein
export BOT_TOKEN="Aapka_Telegram_Bot_Token"
python bot.py
