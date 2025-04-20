from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import ChatAdminRequired, UserNotParticipant, ChatWriteForbidden
from Opus import app

# Must join both these chats
MUST_JOIN_CHANNEL = "STORM_CORE"   # your group
MUST_JOIN_UPDATES = "STORM_TECHH"  # your channel

@app.on_message(filters.incoming & filters.private, group=-1)
async def must_join_channel_and_group(app: Client, msg: Message):
    if not MUST_JOIN_CHANNEL or not MUST_JOIN_UPDATES:
        return
    
    need_to_join = []
    
    async def check_membership(chat_id):
        try:
            await app.get_chat_member(chat_id, msg.from_user.id)
            return True
        except UserNotParticipant:
            return False
        except ChatAdminRequired:
            print(f"» ᴘʟᴇᴀꜱᴇ ᴍᴀᴋᴇ ᴍᴇ ᴀᴅᴍɪɴ")
            return True  # don't block if bot can't check
    
    # Check both chat memberships
    in_channel = await check_membership(MUST_JOIN_CHANNEL)
    in_updates = await check_membership(MUST_JOIN_UPDATES)

    if not in_channel or not in_updates:
        try:
            # Generate invite links
            channel_link = f"https://t.me/{MUST_JOIN_CHANNEL}" if MUST_JOIN_CHANNEL.isalpha() else (await app.get_chat(MUST_JOIN_CHANNEL)).invite_link
            updates_link = f"https://t.me/{MUST_JOIN_UPDATES}" if MUST_JOIN_UPDATES.isalpha() else (await app.get_chat(MUST_JOIN_UPDATES)).invite_link

            await msg.reply_text(
                text=(
                    "<blockquote><b>» ᴛᴏ ᴜꜱᴇ ᴍʏ ꜰᴇᴀᴛᴜʀᴇꜱ, ʏᴏᴜ ɴᴇᴇᴅ ᴛᴏ ᴊᴏɪɴ ʙᴏᴛʜ ᴏᴜʀ ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ ᴀɴᴅ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ.</b></blockquote>"
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("📢 ᴜᴘᴅᴀᴛᴇs", url=updates_link),
                            InlineKeyboardButton("💬 sᴜᴘᴘᴏʀᴛ", url=channel_link),
                        ]
                    ]
                )
            )
            await msg.stop_propagation()
        except ChatWriteForbidden:
            pass
