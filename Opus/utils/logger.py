from pyrogram.enums import ParseMode

from Opus import app
from Opus.utils.database import is_on_off
from config import LOGGER_ID


async def play_logs(message, streamtype):
    if await is_on_off(2):
        logger_text = f"""
<blockquote><b>ᴄʜᴀᴛ ɪᴅ :</b> <code>{message.chat.id}</code>
<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>
<b>ᴜsᴇʀɴᴀᴍᴇ : <a href='https://t.me/{message.from_user.username}'>ᴜsᴇʀ</a></b></blockquote>

<blockquote><b><u>sᴛʀᴇᴀᴍᴛʏᴘᴇ : {streamtype}</u></b></blockquote>"""
        if message.chat.id != LOGGER_ID:
            try:
                await app.send_message(
                    chat_id=LOGGER_ID,
                    text=logger_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
            except:
                pass
        return
