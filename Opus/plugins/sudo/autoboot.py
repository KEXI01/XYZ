import asyncio
import os
import shutil
from datetime import datetime, timedelta

from pyrogram import filters

from Opus import app
from Opus.misc import SUDOERS
from Opus.utils.database import get_active_chats, remove_active_chat, remove_active_video_chat

async def restart_bot():
    # Notify active chats about the restart
    ac_chats = await get_active_chats()
    for x in ac_chats:
        try:
            await app.send_message(
                chat_id=int(x),
                text=f"<blockquote><b>{app.mention} ɪꜱ ʀᴇʙᴏᴏᴛɪɴɢ ᴛᴏ ᴇɴꜱᴜʀᴇ ꜱᴍᴏᴏᴛʜ ᴘʟᴀʏʙᴀᴄᴋ ᴀꜰᴛᴇʀ ʀᴜɴɴɪɴɢ ꜰᴏʀ ᴏᴠᴇʀ 2 ʜᴏᴜʀꜱ. 🎵\n\nʜᴏʟᴅ ᴏɴ ꜰᴏʀ ᴀʙᴏᴜᴛ 15-20 ꜱᴇᴄᴏɴᴅꜱ, ᴀɴᴅ ʏᴏᴜ’ʟʟ ʙᴇ ʙᴀᴄᴋ ᴛᴏ ᴇɴᴊᴏʏɪɴɢ ʏᴏᴜʀ ᴍᴜꜱɪᴄ ɪɴ ɴᴏ ᴛɪᴍᴇ!</b></blockquote>", # HTML parse mode
            )
            await remove_active_chat(x)
            await remove_active_video_chat(x)
        except:
            pass

    # Clean up directories
    try:
        shutil.rmtree("downloads")
        shutil.rmtree("raw_files")
        shutil.rmtree("cache")
    except:
        pass

    # Restart the bot
    os.system(f"kill -9 {os.getpid()} && bash start")

async def auto_restart():
    while True:
        # Wait for 2 hours
        await asyncio.sleep(2 * 60 * 60)
        
        # Restart the bot
        await restart_bot()

@app.on_message(filters.command(["auto"]) & SUDOERS)
async def start_auto_restart(_, message):
    await message.reply_text(
        "<blockquote><b>ᴀᴜᴛᴏ-ʀᴇꜱᴛᴀʀᴛ ꜱᴛᴀʀᴛᴇᴅ. ᴛʜᴇ ʙᴏᴛ ᴡɪʟʟ ʀᴇꜱᴛᴀʀᴛ ᴀꜰᴛᴇʀ ᴇᴠᴇʀʏ 2 ʜᴏᴜʀꜱ.</b></blockquote>",
    )
    asyncio.create_task(auto_restart())

@app.on_message(filters.command(["stop_auto"]) & SUDOERS)
async def stop_auto_restart(_, message):
    # You can implement a way to stop the auto-restart if needed
    await message.reply_text(
        "<blockquote><b>ᴀᴜᴛᴏ-ʀᴇꜱᴛᴀʀᴛ ꜰᴇᴀᴛᴜʀᴇ ɪꜱ ɴᴏᴛ ꜱᴛᴏᴘᴘᴀʙʟᴇ ɪɴ ᴛʜɪꜱ ɪᴍᴘʟᴇᴍᴇɴᴛᴀᴛɪᴏɴ.</b></blockquote>",
    )
