import asyncio
import os
import shutil
from pyrogram import filters
from Opus import app
from Opus.misc import SUDOERS
from datetime import datetime


CLEAN_INTERVAL = 1800  
TARGET_DIRS = ["downloads", "cache"]  
LOG_FILE = "cleaner.log"  

async def log_activity(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as log:
        log.write(f"[{timestamp}] {message}\n")

async def nuke_directories():
    while True:
        try:
            for dir_path in TARGET_DIRS:
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path) 
                    os.makedirs(dir_path)  
                    await log_activity(f"☢️ ɴᴜᴋᴇᴅ: {dir_path}")
                    print(f"☢️ ᴅᴇʟᴇᴛᴇᴅ: {dir_path}")

            print("✅ ᴀᴜᴛᴏ-ᴄʟᴇᴀɴ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!")
        except Exception as e:
            await log_activity(f"💥 ᴇʀʀᴏʀ: {str(e)}")
            print(f"⚠️ ᴄʟᴇᴀɴᴇʀ �ᴇʀʀᴏʀ: {e}")

        await asyncio.sleep(CLEAN_INTERVAL)


@app.on_message(filters.command("start_cleaner") & SUDOERS)
async def start_nuker(_, message):
    asyncio.create_task(nuke_directories())
    await message.reply_text(
        "<blockquote>🛁 <b>ꜱᴛᴀʀᴛᴇᴅ ᴘᴀꜱꜱɪᴠᴇ ᴄʟᴇᴀɴᴇʀ</b></blockquote>\n\n"
        f"<blockquote>• <b>ᴛᴀʀɢᴇᴛꜱ:</b> <code>{', '.join(TARGET_DIRS)}</code>\n"
        f"• <b>ꜰʀᴇqᴜᴇɴᴄʏ:</b> <code>{CLEAN_INTERVAL//60} ᴍɪɴᴜᴛᴇꜱ</code>\n"
        "• <b>ᴍᴏᴅᴇ:</b> <code>ɴᴏ ᴇxᴄᴇᴘᴛɪᴏɴꜱ, ꜰᴜʟʟ ᴡɪᴘᴇ</code></blockquote>"
    )

@app.on_message(filters.command("clean_now") & SUDOERS)
async def trigger_nuke(_, message):
    try:
        for dir_path in TARGET_DIRS:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                os.makedirs(dir_path)
        await message.reply_text("<blockquote>💥 <b>ᴍᴀɴᴜᴀʟ ᴄʟᴇᴀɴᴜᴘ ᴄᴏᴍᴘʟᴇᴛᴇ!</b></blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>❌ <b>ꜰᴀɪʟᴇᴅ:</b> <code>{e}</code></blockquote>")

@app.on_message(filters.command("cleaner_status") & SUDOERS)
async def nuker_status(_, message):
    await message.reply_text(
        "<blockquote>📊 <b>ᴄʟᴇᴀɴᴇʀ ꜱᴛᴀᴛᴜꜱ</b></blockquote>\n\n"
        f"<blockquote>• <b>ʀᴜɴɴɪɴɢ:</b> <code>ʏᴇꜱ</code>\n"
        f"• <b>ɴᴇxᴛ ᴄʟᴇᴀɴ ɪɴ:</b> <code>{CLEAN_INTERVAL//60} ᴍɪɴᴜᴛᴇꜱ</code>\n"
        f"• <b>ᴛᴀʀɢᴇᴛꜱ:</b> <code>{', '.join(TARGET_DIRS)}</code></blockquote>\n"
        "<blockquote>• <b>ᴡᴀʀɴɪɴɢ:</b> <code>ᴛʜɪꜱ ᴡɪʟʟ ᴅᴇʟᴇᴛᴇ ᴇᴠᴇʀʏᴛʜɪɴɢ ɪɴ ᴛᴀʀɢᴇᴛ ꜰᴏʟᴅᴇʀꜱ!</code></blockquote>"
    )

@app.on_message(filters.command("clear") & SUDOERS)
async def clear_terminal(_, message):
    os.system('cls' if os.name == 'nt' else 'clear')
    await message.reply_text(
        "<blockquote><b>✅ ᴛᴇʀᴍɪɴᴀʟ ʟᴏɢꜱ ᴄʟᴇᴀʀᴇᴅ. ᴀᴜᴛᴏ ᴄʟᴇᴀʀɪɴɢ ᴇᴠᴇʀʏ 15 ꜱᴇᴄᴏɴᴅꜱ.</b></blockquote>",
    )

    while True:
        await asyncio.sleep(10)  # Wait for 5 seconds
        os.system('cls' if os.name == 'nt' else 'clear')
        print("🔄 Terminal logs cleared automatically.")
