import asyncio
import os
import re
import json
from typing import Union
import glob
import random
import logging
import httpx
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
from Opus.utils.database import is_on_off
from Opus.utils.formatters import time_to_seconds

# API Configuration
API_URL = "http://46.250.243.87:1470/youtube"
API_KEY = "1a873582a7c83342f961cc0a177b2b26"

def cookie_txt_file():
    folder_path = f"{os.getcwd()}/cookies"
    filename = f"{os.getcwd()}/cookies/logs.csv"
    txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
    if not txt_files:
        raise FileNotFoundError("No .txt files found in the specified folder.")
    cookie_txt_file = random.choice(txt_files)
    with open(filename, 'a') as file:
        file.write(f'Choosen File : {cookie_txt_file}\n')
    return f"""cookies/{str(cookie_txt_file).split("/")[-1]}"""

async def check_file_size(link):
    async def get_format_info(link):
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--cookies", cookie_txt_file(),
            "-J",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            print(f'Error:\n{stderr.decode()}')
            return None
        return json.loads(stdout.decode())

    def parse_size(formats):
        total_size = 0
        for format in formats:
            if 'filesize' in format:
                total_size += format['filesize']
        return total_size

    info = await get_format_info(link)
    if info is None:
        return None

    formats = info.get('formats', [])
    if not formats:
        print("No formats found.")
        return None

    total_size = parse_size(formats)
    return total_size

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")

async def get_stream_url(query, video=False):
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            params = {"query": query, "video": video, "api_key": API_KEY}
            response = await client.get(API_URL, params=params)
            if response.status_code != 200:
                return ""
            info = response.json()
            return info.get("stream_url")
    except Exception as e:
        logging.error(f"API Error: {e}")
        return ""

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return text[offset:offset + length] if offset else None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            duration_sec = 0 if str(duration_min) == "None" else int(time_to_seconds(duration_min))
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["duration"]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["thumbnails"][0]["url"].split("?")[0]

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        # First try with cookies
        try:
            proc = await asyncio.create_subprocess_exec(
                "yt-dlp",
                "--cookies", cookie_txt_file(),
                "-g",
                "-f",
                "best[height<=?720][width<=?1280]",
                f"{link}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if stdout:
                return 1, stdout.decode().split("\n")[0]
        except Exception as e:
            logging.warning(f"Cookie-based video fetch failed: {e}")
        
        # Fallback to API
        api_url = await get_stream_url(link, True)
        if api_url:
            return 1, api_url
        return 0, "Failed to fetch video URL"

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
            
        # First try with cookies
        try:
            playlist = await shell_cmd(
                f"yt-dlp -i --get-id --flat-playlist --cookies {cookie_txt_file()} --playlist-end {limit} --skip-download {link}"
            )
            result = playlist.split("\n")
            return [key for key in result if key != ""]
        except Exception as e:
            logging.warning(f"Cookie-based playlist fetch failed: {e}")
            return []

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return {
                "title": result["title"],
                "link": result["link"],
                "vidid": result["id"],
                "duration_min": result["duration"],
                "thumb": result["thumbnails"][0]["url"].split("?")[0],
            }, result["id"]

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        formats_available = []
        try:
            ytdl_opts = {"quiet": True, "cookiefile": cookie_txt_file()}
            ydl = yt_dlp.YoutubeDL(ytdl_opts)
            with ydl:
                r = ydl.extract_info(link, download=False)
                for format in r["formats"]:
                    try:
                        if "dash" not in str(format.get("format", "")).lower():
                            formats_available.append({
                                "format": format.get("format"),
                                "filesize": format.get("filesize"),
                                "format_id": format.get("format_id"),
                                "ext": format.get("ext"),
                                "format_note": format.get("format_note"),
                                "yturl": link,
                            })
                    except:
                        continue
        except Exception as e:
            logging.warning(f"Cookie-based formats fetch failed: {e}")
            
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        result = (await VideosSearch(link, limit=10).next()).get("result")
        return (
            result[query_type]["title"],
            result[query_type]["duration"],
            result[query_type]["thumbnails"][0]["url"].split("?")[0],
            result[query_type]["id"],
        )

    async def download(self, link: str, mystic, video: Union[bool, str] = None, 
                     videoid: Union[bool, str] = None, songaudio: Union[bool, str] = None,
                     songvideo: Union[bool, str] = None, format_id: Union[bool, str] = None,
                     title: Union[bool, str] = None) -> str:
        if videoid:
            link = self.base + link
            
        loop = asyncio.get_running_loop()
        
        async def try_cookie_download():
            try:
                if songvideo:
                    def dl():
                        ydl_optssx = {
                            "format": f"{format_id}+140",
                            "outtmpl": f"downloads/{title}",
                            "geo_bypass": True,
                            "cookiefile": cookie_txt_file(),
                            "nocheckcertificate": True,
                            "quiet": True,
                            "no_warnings": True,
                            "prefer_ffmpeg": True,
                            "merge_output_format": "mp4",
                        }
                        yt_dlp.YoutubeDL(ydl_optssx).download([link])
                        return f"downloads/{title}.mp4"
                    
                    return await loop.run_in_executor(None, dl)
                
                elif songaudio:
                    def dl():
                        ydl_optssx = {
                            "format": format_id,
                            "outtmpl": f"downloads/{title}.%(ext)s",
                            "geo_bypass": True,
                            "cookiefile": cookie_txt_file(),
                            "nocheckcertificate": True,
                            "quiet": True,
                            "no_warnings": True,
                            "prefer_ffmpeg": True,
                            "postprocessors": [{
                                "key": "FFmpegExtractAudio",
                                "preferredcodec": "mp3",
                                "preferredquality": "192",
                            }],
                        }
                        yt_dlp.YoutubeDL(ydl_optssx).download([link])
                        return f"downloads/{title}.mp3"
                    
                    return await loop.run_in_executor(None, dl)
                
                elif video:
                    if await is_on_off(1):
                        def dl():
                            ydl_optssx = {
                                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                                "outtmpl": "downloads/%(id)s.%(ext)s",
                                "geo_bypass": True,
                                "cookiefile": cookie_txt_file(),
                                "nocheckcertificate": True,
                                "quiet": True,
                                "no_warnings": True,
                            }
                            x = yt_dlp.YoutubeDL(ydl_optssx)
                            info = x.extract_info(link, False)
                            path = os.path.join("downloads", f"{info['id']}.{info['ext']}")
                            if not os.path.exists(path):
                                x.download([link])
                            return path, True
                        
                        return await loop.run_in_executor(None, dl)
                    else:
                        proc = await asyncio.create_subprocess_exec(
                            "yt-dlp",
                            "--cookies", cookie_txt_file(),
                            "-g",
                            "-f",
                            "best[height<=?720][width<=?1280]",
                            f"{link}",
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                        )
                        stdout, stderr = await proc.communicate()
                        if stdout:
                            return stdout.decode().split("\n")[0], False
                        
                        file_size = await check_file_size(link)
                        if file_size and (file_size / (1024 * 1024)) <= 250:
                            def dl():
                                ydl_optssx = {
                                    "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                                    "outtmpl": "downloads/%(id)s.%(ext)s",
                                    "geo_bypass": True,
                                    "cookiefile": cookie_txt_file(),
                                    "nocheckcertificate": True,
                                    "quiet": True,
                                    "no_warnings": True,
                                }
                                x = yt_dlp.YoutubeDL(ydl_optssx)
                                info = x.extract_info(link, False)
                                path = os.path.join("downloads", f"{info['id']}.{info['ext']}")
                                if not os.path.exists(path):
                                    x.download([link])
                                return path, True
                            
                            return await loop.run_in_executor(None, dl)
                
                else:  # Audio download
                    def dl():
                        ydl_optssx = {
                            "format": "bestaudio/best",
                            "outtmpl": "downloads/%(id)s.%(ext)s",
                            "geo_bypass": True,
                            "cookiefile": cookie_txt_file(),
                            "nocheckcertificate": True,
                            "quiet": True,
                            "no_warnings": True,
                        }
                        x = yt_dlp.YoutubeDL(ydl_optssx)
                        info = x.extract_info(link, False)
                        path = os.path.join("downloads", f"{info['id']}.{info['ext']}")
                        if not os.path.exists(path):
                            x.download([link])
                        return path, True
                    
                    return await loop.run_in_executor(None, dl)
            
            except Exception as e:
                logging.warning(f"Cookie-based download failed: {e}")
                return None
        
        # First try with cookies
        result = await try_cookie_download()
        if result is not None:
            return result
        
        # Fallback to API
        if songvideo:
            return f"downloads/{title}.mp4", True
        elif songaudio:
            return f"downloads/{title}.mp3", True
        else:
            stream_url = await get_stream_url(link, video)
            return stream_url, False if video else None
