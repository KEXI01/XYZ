from pyrogram import Client, filters
from pyrogram.types import Message
from config import LOGGER_ID as LOG_GROUP_ID
from Opus import app
from Opus.utils.database import get_assistant, delete_served_chat

@app.on_message(filters.left_chat_member)
async def on_left_chat_member(_, message: Message):
    try:
        userbot = await get_assistant(message.chat.id)

        left_chat_member = message.left_chat_member
        if left_chat_member and left_chat_member.id == (await app.get_me()).id:
            remove_by = (
                message.from_user.mention if message.from_user else "ᴜɴᴋɴᴏᴡɴ"
            )
            title = message.chat.title
            username = (
                f"@{message.chat.username}" if message.chat.username else "ᴘʀɪᴠᴀᴛᴇ ɢʀᴏᴜᴘ"
            )
            chat_id = message.chat.id
            left = (
                f"<blockquote>● <b>ʟᴇꜰᴛ ɢʀᴏᴜᴘ</b> ●\n\n"
                f"<b>ᴄʜᴀᴛ ᴛɪᴛʟᴇ : {title}</b>\n"
                f"<b>ᴄʜᴀᴛ ɪᴅ : {chat_id}</b>\n"
                f"<b>ʀᴇᴍᴏᴠᴇᴅ ʙʏ : {remove_by}</b></blockquote>"
            )
            await app.send_message(LOG_GROUP_ID, text=left)
            await delete_served_chat(chat_id)
            await userbot.leave_chat(chat_id)
    except Exception as e:
        return
