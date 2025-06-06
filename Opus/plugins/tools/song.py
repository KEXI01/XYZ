import os
import requests
from pyrogram import Client, filters
from threading import Timer
from Opus import app

def fetch_song(song_name):
    url = f"https://song-teleservice.vercel.app/song?songName={song_name.replace(' ', '%20')}"
    try:
        response = requests.get(url)
        return response.json() if response.status_code == 200 and "downloadLink" in response.json() else None
    except Exception as e:
        print(f"API Error: {e}")
        return None

def delete_file_after_delay(filename, delay=600): 
    def delete_file():
        try:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"File {filename} deleted after {delay/60} minutes.")
        except Exception as e:
            print(f"Error deleting file {filename}: {e}")
    Timer(delay, delete_file).start()

@app.on_message(filters.command("song"))
async def handle_song(client, message):
    song_name = message.text.split(" ", 1)[1] if len(message.text.split(" ", 1)) > 1 else None
    if not song_name:
        return await message.reply("ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ sᴏɴɢ ɴᴀᴍᴇ ᴀғᴛᴇʀ ᴛʜᴇ /song ᴄᴏᴍᴍᴀɴᴅ..")

    song_info = fetch_song(song_name)
    if not song_info:
        return await message.reply(f"sᴏʀʀʏ, ɪ ᴄᴏᴜʟᴅɴ'ᴛ ғɪɴᴅ ᴛʜᴇ sᴏɴɢ '{song_name}'.")

    filename = f"{song_info['trackName']}.mp3"
    download_url = song_info['downloadLink']

    with requests.get(download_url, stream=True) as r, open(filename, "wb") as file:
        for chunk in r.iter_content(1024):
            if chunk:
                file.write(chunk)

    caption = (f"""sᴏɴɢ ɴᴀᴍᴇ: {song_info['trackName']}\n\nʀᴇʟᴇᴀsᴇ ᴅᴀᴛᴇ: {song_info['releaseDate']}\nʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ: {message.from_user.mention}™""")

    await message.reply_audio(audio=open(filename, "rb"), caption=caption)

    delete_file_after_delay(filename)
