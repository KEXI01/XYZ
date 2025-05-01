from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.errors import ChatAdminRequired, UserNotParticipant, ChatWriteForbidden
from Opus import app

MUST_JOIN_CHANNEL = "STORM_TECHH"  # your updates channel
SUPPORT_GROUP = "TheVibeVerse"  # your support group

async def check_joined(user_id):
    channel_joined = await app.get_chat_member(MUST_JOIN_CHANNEL, user_id)
    group_joined = await app.get_chat_member(SUPPORT_GROUP, user_id)
    return channel_joined, group_joined

async def generate_buttons():
    # Get invite links
    channel_link = f"https://t.me/{MUST_JOIN_CHANNEL}" if MUST_JOIN_CHANNEL.isalpha() else (await app.get_chat(MUST_JOIN_CHANNEL)).invite_link
    support_link = f"https://t.me/{SUPPORT_GROUP}" if SUPPORT_GROUP.isalpha() else (await app.get_chat(SUPPORT_GROUP)).invite_link
    
    return channel_link, support_link

@app.on_message(filters.private & filters.incoming)
async def force_join(app: Client, msg: Message):
    try:
        channel_joined = group_joined = False
        
        try:
            await app.get_chat_member(MUST_JOIN_CHANNEL, msg.from_user.id)
            channel_joined = True
        except UserNotParticipant:
            pass
            
        try:
            await app.get_chat_member(SUPPORT_GROUP, msg.from_user.id)
            group_joined = True
        except UserNotParticipant:
            pass

        if channel_joined and group_joined:
            return
            
        channel_link, support_link = await generate_buttons()
        buttons = []
        
        if not channel_joined and not group_joined:
            buttons = [
                [InlineKeyboardButton("📢 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=channel_link),
                 InlineKeyboardButton("💬 ᴊᴏɪɴ ɢʀᴏᴜᴘ", url=support_link)],
                [InlineKeyboardButton("🔄", callback_data="refresh_join")]
            ]
        elif not channel_joined:
            buttons = [
                [InlineKeyboardButton("📢 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=channel_link)],
                [InlineKeyboardButton("🔄", callback_data="refresh_join")]
            ]
        elif not group_joined:
            buttons = [
                [InlineKeyboardButton("💬 ᴊᴏɪɴ ɢʀᴏᴜᴘ", url=support_link)],
                [InlineKeyboardButton("🔄", callback_data="refresh_join")]
            ]

        await msg.reply(
            "🔐 ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴛʜᴇ ɢʀᴏᴜᴘ ᴀɴᴅ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
    except ChatAdminRequired:
        print(f"ᴍᴀᴋᴇ ᴍᴇ ᴀᴅᴍɪɴ ɪɴ {MUST_JOIN_CHANNEL} ᴀɴᴅ {SUPPORT_GROUP}")

@app.on_callback_query(filters.regex("^refresh_join$"))
async def refresh_buttons(app: Client, query: CallbackQuery):
    try:
        channel_joined = group_joined = False
        
        try:
            await app.get_chat_member(MUST_JOIN_CHANNEL, query.from_user.id)
            channel_joined = True
        except UserNotParticipant:
            pass
            
        try:
            await app.get_chat_member(SUPPORT_GROUP, query.from_user.id)
            group_joined = True
        except UserNotParticipant:
            pass

        if channel_joined and group_joined:
            await query.message.delete()
            await query.answer("ᴅᴏɴᴇ ✨", show_alert=True)
            return
            
        channel_link, support_link = await generate_buttons()
        buttons = []
        
        if not channel_joined and not group_joined:
            buttons = [
                [InlineKeyboardButton("📢 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=channel_link),
                 InlineKeyboardButton("💬 ᴊᴏɪɴ ɢʀᴏᴜᴘ", url=support_link)],
                [InlineKeyboardButton("🔄", callback_data="refresh_join")]
            ]
        elif not channel_joined:
            buttons = [
                [InlineKeyboardButton("📢 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=channel_link)],
                [InlineKeyboardButton("🔄", callback_data="refresh_join")]
            ]
        elif not group_joined:
            buttons = [
                [InlineKeyboardButton("💬 ᴊᴏɪɴ ɢʀᴏᴜᴘ", url=support_link)],
                [InlineKeyboardButton("🔄", callback_data="refresh_join")]
            ]

        await query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        await query.answer("ꜱᴛᴀᴛᴜꜱ ᴜᴘᴅᴀᴛᴇᴅ ⚡")
        
    except Exception as e:
        await query.answer(f"Error: {str(e)}", show_alert=True)
