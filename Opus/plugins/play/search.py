from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from youtube_search import YoutubeSearch
from Opus import app
from pyrogram import filters
from typing import List, Dict, Optional
import asyncio

BOT_USERNAME = "@STORM_TECHH"

def format_results(results: List[Dict]) -> str:
    formatted = []
    for result in results[:10]:
        formatted.append(
            f"""<blockquote>
<b><a href="https://www.youtube.com{result['url_suffix']}">{result['title']}</a></b>
<b>{result['duration']} | {result['views']}</b>
<b>{result['channel']}</b>
</blockquote>"""
        )
    return "\n".join(formatted)

def create_keyboard(results: List[Dict]) -> InlineKeyboardMarkup:
    buttons = []
    for result in results[:5]:
        title = (result['title'][:35] + '...') if len(result['title']) > 35 else result['title']
        buttons.append(
            [InlineKeyboardButton(
                title, 
                url=f"https://www.youtube.com{result['url_suffix']}"
            )]
        )
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command(["search", f"search@{BOT_USERNAME}"]))
async def ytsearch(_, message: Message):
    try:
        if len(message.command) < 2:
            return await message.reply(
                "<blockquote><b>ʏᴏᴜᴛᴜʙᴇ ꜱᴇᴀʀᴄʜ ʜᴇʟᴘ</b>\n\n"
                "ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ꜱᴇᴀʀᴄʜ Qᴜᴇʀʏ\n"
                "ᴇxᴀᴍᴘʟᴇ: <code>/search jhol</code>\n\n"
                "ᴘʀᴏ ᴛɪᴘ: ᴛʀʏ ꜱᴘᴇᴄɪꜰɪᴄ Qᴜᴇʀɪᴇꜱ ꜰᴏʀ ʙᴇᴛᴛᴇʀ ʀᴇꜱᴜʟᴛꜱ</blockquote>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("ꜱᴜᴘᴘᴏʀᴛ", url="https://t.me/STORM_CORE")
                ]])
            )

        query = message.text.split(None, 1)[1]
        search_msg = await message.reply("✨")

        try:
            results = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: YoutubeSearch(query, max_results=5).to_dict()
                ),
                timeout=12
            )
        except asyncio.TimeoutError:
            return await search_msg.edit(
                "<blockquote><b>⏱️ ꜱᴇᴀʀᴄʜ ᴛɪᴍᴇᴏᴜᴛ</b>\n\n"
                "ʏᴏᴜᴛᴜʙᴇ ᴛᴏᴏᴋ ᴛᴏᴏ ʟᴏɴɢ ᴛᴏ ʀᴇꜱᴘᴏɴᴅ.\n"
                "ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ</blockquote>"
            )

        if not results:
            return await search_msg.edit(
                "<blockquote><b>🔎 ɴᴏ ʀᴇꜱᴜʟᴛꜱ ꜰᴏᴜɴᴅ</b></blockquote>"
            )

        formatted_text = (
            f"<blockquote><b>📌 ʀᴇꜱᴜʟᴛꜱ ꜰᴏʀ: {query}</b></blockquote>\n"
            f"{format_results(results)}\n"
            f"<blockquote><b>⚡ {BOT_USERNAME}</b></blockquote>"
        )

        await search_msg.edit(
            text=formatted_text,
            disable_web_page_preview=True,
            reply_markup=create_keyboard(results)
        )

    except Exception as e:
        error_msg = "<blockquote><b>⚠️ ᴇʀʀᴏʀ: ꜱᴇᴀʀᴄʜ ꜰᴀɪʟᴇᴅ</b></blockquote>"
        if 'search_msg' in locals():
            await search_msg.edit(error_msg)
        else:
            await message.reply(error_msg)
