import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import ChatAdminRequired, UserNotParticipant, ChatWriteForbidden
from Opus import app

MUST_JOIN = "STORM_CORE"

@app.on_message(filters.incoming & filters.private, group=-1)
async def must_join_channel(app: Client, msg: Message):
    if not MUST_JOIN:
        return
    try:
        try:
            await app.get_chat_member(MUST_JOIN, msg.from_user.id)
        except UserNotParticipant:
            if MUST_JOIN.isalpha():
                link = "https://t.me/" + MUST_JOIN
            else:
                chat_info = await app.get_chat(MUST_JOIN)
                link = chat_info.invite_link
            try:
                await msg.reply_text(
                    text=(
                        "ʜᴇʏ 🎧\n"
                        "» ʀᴇᴀᴅʏ ᴛᴏ ᴠɪʙᴇ? ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ, ᴊᴏɪɴ ᴜꜱ ᴛᴏ ꜱᴛᴀʀᴛ ᴀɴᴅ ᴜꜱᴇ ᴍʏ ꜰᴇᴀᴛᴜʀᴇꜱ 🚀"
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇ", url="https://t.me/STORM_TECHH"),
                                InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", url="https://t.me/STORM_CORE"),
                            ]
                        ]
                    )
                )
                await msg.stop_propagation()
            except ChatWriteForbidden:
                pass
    except ChatAdminRequired:
        print(f"» ᴘʀᴏᴍᴏᴛᴇ ᴍᴇ ᴀs ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ᴍᴜsᴛ_ᴊᴏɪɴ ᴄʜᴀᴛ ~ {MUST_JOIN}")
