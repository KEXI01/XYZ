import asyncio
from datetime import datetime

from pyrogram.enums import ChatType

import config
from Opus import app
from Opus.core.call import Anony, autoend
from Opus.utils.database import get_client, is_active_chat, is_autoend


async def auto_leave():
    if config.AUTO_LEAVING_ASSISTANT:
        while True:
            await asyncio.sleep(60) 
            from Opus.core.userbot import assistants

            for num in assistants:
                client = await get_client(num)
                left = 0
                try:
                    async for i in client.get_dialogs():
                        if i.chat.type in [
                            ChatType.SUPERGROUP,
                            ChatType.GROUP,
                            ChatType.CHANNEL,
                        ]:
                            if (
                                i.chat.id != config.LOGGER_ID
                                and i.chat.id != -1001686672798
                                and i.chat.id != -1001549206010
                            ):
                                if left == 20:
                                    continue
                                if not await is_active_chat(i.chat.id):
                                    try:
                                        await client.leave_chat(i.chat.id)
                                        left += 1
                                    except Exception as e:
                                        print(f"Eʀʀᴏʀ ʟᴇᴀᴠɪɴɢ ᴍʏ ᴅᴇsᴛɪɴʏ ᴄʜᴀᴛ {i.chat.id}: {e}")
                                        continue
                except Exception as e:
                    print(f"Eʀʀᴏʀ ɪɴ auto_leave ғᴜɴᴄᴛɪᴏɴ: {e}")
                    pass


async def auto_end():
    while True:
        await asyncio.sleep(52)
        ender = await is_autoend()
        if not ender:
            continue
        for chat_id in autoend:
            timer = autoend.get(chat_id)
            if not timer:
                continue
            if datetime.now() > timer:
                if not await is_active_chat(chat_id):
                    autoend[chat_id] = {}
                    continue
                autoend[chat_id] = {}
                try:
                    await Anony.stop_stream(chat_id)
                except Exception as e:
                    print(f"Eʀʀᴏʀ ᴛᴇʀᴍɪɴᴀᴛɪɴɢ ᴍᴜsɪᴄ ɪɴ ᴄʜᴀᴛ {chat_id}: {e}")
                    continue
                try:
                    await app.send_message(
                        chat_id,
                        "» Sᴛᴏʀᴍ ᴘʟᴀʏᴇʀ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ʟᴇғᴛ ᴠɪᴅᴇᴏᴄʜᴀᴛ ʙᴇᴄᴀᴜsᴇ ɴᴏ ᴏɴᴇ ᴡᴀs ʟɪsᴛᴇɴɪɴɢ ᴏɴ ᴠɪᴅᴇᴏᴄʜᴀᴛ.",
                    )
                except Exception as e:
                    print(f"Eʀʀᴏʀ ᴡʜɪʟᴇ sʜᴀʀɪɴɢ ᴍᴇssᴀɢᴇ ɪɴ ᴄʜᴀᴛ {chat_id}: {e}")
                    continue


async def main():
    task_leave = asyncio.create_task(auto_leave())
    task_end = asyncio.create_task(auto_end())

    try:
        await asyncio.gather(task_leave, task_end)
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    asyncio.run(main())
