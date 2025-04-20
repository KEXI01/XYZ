from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import ChatAdminRequired, UserNotParticipant, ChatWriteForbidden
from Opus import app

MUST_JOIN_CHANNEL = "STORM_TECHH"

@app.on_message(filters.incoming & group=-1)
async def must_join_channel(app: Client, msg: Message):
    if not MUST_JOIN_CHANNEL:
        return
    try:
        try:
            await app.get_chat_member(MUST_JOIN_CHANNEL, msg.from_user.id)
        except UserNotParticipant:
            if MUST_JOIN_CHANNEL.isalpha():
                invite_link = f"https://t.me/{MUST_JOIN_CHANNEL}"
            else:
                chat_info = await app.get_chat(MUST_JOIN_CHANNEL)
                invite_link = chat_info.invite_link

            try:
                await msg.reply_text(
                    text=(
                        "<blockquote><b>» ᴛᴏ ᴜꜱᴇ ᴍʏ ꜰᴇᴀᴛᴜʀᴇꜱ, ʏᴏᴜ ᴍᴜꜱᴛ ᴊᴏɪɴ ᴏᴜʀ ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ ғɪʀꜱᴛ.</b></blockquote>"
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("📢 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=invite_link),
                            ]
                        ]
                    )
                )
                await msg.stop_propagation()
            except ChatWriteForbidden:
                pass
    except ChatAdminRequired:
        print(f"» ᴘʀᴏᴍᴏᴛᴇ ᴍᴇ ᴀꜱ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ~ {MUST_JOIN_CHANNEL}")
