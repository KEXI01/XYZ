from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import ChatAdminRequired, UserNotParticipant, ChatWriteForbidden
from Opus import app

MUST_JOIN_CHANNEL = "STORM_TECHH"  # your updates channel
SUPPORT_GROUP = "TheVibeVerse"  # your support group

@app.on_message(filters.incoming & filters.private, group=-1)
async def must_join_channel(app: Client, msg: Message):
    if not MUST_JOIN_CHANNEL:
        return
    try:
        try:
            await app.get_chat_member(MUST_JOIN_CHANNEL, msg.from_user.id)
        except UserNotParticipant:
            # Get the invite links
            if MUST_JOIN_CHANNEL.isalpha():
                channel_link = f"https://t.me/{MUST_JOIN_CHANNEL}"
            else:
                channel_info = await app.get_chat(MUST_JOIN_CHANNEL)
                channel_link = channel_info.invite_link
            
            if SUPPORT_GROUP.isalpha():
                support_link = f"https://t.me/{SUPPORT_GROUP}"
            else:
                support_info = await app.get_chat(SUPPORT_GROUP)
                support_link = support_info.invite_link

            try:
                await msg.reply_text(
                    text=(
                        "<blockquote><b>» ᴛᴏ ᴜꜱᴇ ᴍʏ ꜰᴇᴀᴛᴜʀᴇꜱ, ʏᴏᴜ ᴍᴜꜱᴛ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ᴀɴᴅ ɢʀᴏᴜᴘ</b></blockquote>"
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("📢 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=channel_link),
                                InlineKeyboardButton("💬 ꜱᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", url=support_link)
                            ],
                            [
                                InlineKeyboardButton("🔄 ᴛʀʏ ᴀɢᴀɪɴ", callback_data="check_joined")
                            ]
                        ]
                    )
                )
                await msg.stop_propagation()
            except ChatWriteForbidden:
                pass
    except ChatAdminRequired:
        print(f"» ᴘʀᴏᴍᴏᴛᴇ ᴍᴇ ᴀꜱ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ~ {MUST_JOIN_CHANNEL}")
