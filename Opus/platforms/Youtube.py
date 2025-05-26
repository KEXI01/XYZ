import asyncio
import os
import re
import json
from typing import Union
from functools import lru_cache

import yt_dlp
import aiofiles
import aiohttp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch

from Opus.utils.database import is_on_off
from Opus.utils.formatters import time_to_seconds

import glob
import random
import base64

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        self._api_urls = [
            base64.b64decode("aHR0cHM6Ly9uYXJheWFuLnNpdmVuZHJhc3Rvcm0ud29ya2Vycy5kZXYvYXJ5dG1wMz9kaXJlY3QmaWQ9").decode("utf-8"),
            base64.b64decode("aHR0cHM6Ly9iaWxsYWF4LnNodWtsYWt1c3VtNHEud29ya2Vycy5kZXYvP2lkPQ==").decode("utf-8")
        ]
        self._current_api_index = 0
        self.session = aiohttp.ClientSession()
        self._cookie_file = None

    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    def _get_api_url(self, video_id: str) -> str:
        url = self._api_urls[self._current_api_index] + video_id
        self._current_api_index = (self._current_api_index + 1) % len(self._api_urls)
        return url

    def cookie_txt_file(self):
        if self._cookie_file is None:
            folder_path = f"{os.getcwd()}/cookies"
            txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
            if not txt_files:
                raise FileNotFoundError("No .txt files found in the cookies folder.")
            self._cookie_file = f"cookies/{random.choice(txt_files).split('/')[-1]}"
        return self._cookie_file

    async def check_file_size(self, link):
        async def get_format_info(link):
            proc = await asyncio.create_subprocess_exec(
                "yt-dlp",
                "--cookies", self.cookie_txt_file(),
                "-J",
                link,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                return None
            return json.loads(stdout.decode())

        info = await get_format_info(link)
        if info is None:
            return None
        
        formats = info.get('formats', [])
        if not formats:
            return None
        
        total_size = sum(f.get('filesize', 0) for f in formats)
        return total_size

    async def shell_cmd(self, cmd):
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out, errorz = await proc.communicate()
        if errorz:
            if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
                return out.decode("utf-8")
            return errorz.decode("utf-8")
        return out.decode("utf-8")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
            
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset:entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    @lru_cache(maxsize=100)
    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        results = VideosSearch(link, limit=1)
        result = (await results.next())["result"][0]
        
        title = result["title"]
        duration_min = result["duration"]
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        vidid = result["id"]
        duration_sec = 0 if str(duration_min) == "None" else int(time_to_seconds(duration_min))
        
        return title, duration_min, duration_sec, thumbnail, vidid

    @lru_cache(maxsize=100)
    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        results = VideosSearch(link, limit=1)
        return (await results.next())["result"][0]["title"]

    @lru_cache(maxsize=100)
    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        results = VideosSearch(link, limit=1)
        return (await results.next())["result"][0]["duration"]

    @lru_cache(maxsize=100)
    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        results = VideosSearch(link, limit=1)
        return (await results.next())["result"][0]["thumbnails"][0]["url"].split("?")[0]

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        try:
            proc = await asyncio.create_subprocess_exec(
                "yt-dlp",
                "--cookies", self.cookie_txt_file(),
                "-g",
                "-f",
                "best[height<=?720][width<=?1280]",
                link,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            if stdout:
                return 1, stdout.decode().split("\n")[0]
        except Exception:
            pass
            
        return 0, "Failed to get direct video link"

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
            
        playlist = await self.shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --cookies {self.cookie_txt_file()} "
            f"--playlist-end {limit} --skip-download {link}"
        )
        return [key for key in playlist.split("\n") if key]

    @lru_cache(maxsize=100)
    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        results = VideosSearch(link, limit=1)
        result = (await results.next())["result"][0]
        
        track_details = {
            "title": result["title"],
            "link": result["link"],
            "vidid": result["id"],
            "duration_min": result["duration"],
            "thumb": result["thumbnails"][0]["url"].split("?")[0],
        }
        return track_details, result["id"]

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        ytdl_opts = {"quiet": True, "cookiefile": self.cookie_txt_file()}
        with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
            r = ydl.extract_info(link, download=False)
            formats_available = [
                {
                    "format": f["format"],
                    "filesize": f.get("filesize", 0),
                    "format_id": f["format_id"],
                    "ext": f["ext"],
                    "format_note": f.get("format_note", ""),
                    "yturl": link,
                }
                for f in r["formats"]
                if not "dash" in str(f.get("format", "")).lower()
                and all(k in f for k in ["format", "format_id", "ext"])
            ]
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        results = (await VideosSearch(link, limit=10).next()).get("result")
        result = results[query_type]
        return (
            result["title"],
            result["duration"],
            result["thumbnails"][0]["url"].split("?")[0],
            result["id"],
        )

    async def _download_from_api(self, video_id: str) -> str:
        file_path = os.path.join("downloads", f"{video_id}.mp3")
        if os.path.exists(file_path):
            return file_path

        for attempt in range(2):
            api_url = self._get_api_url(video_id)
            try:
                async with self.session.get(api_url, timeout=30) as response:
                    if response.status == 200:
                        os.makedirs("downloads", exist_ok=True)
                        async with aiofiles.open(file_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        return file_path
            except (aiohttp.ClientError, asyncio.TimeoutError):
                continue
        return None

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link

        # First try API download for audio
        if not (video or songvideo):
            video_id_match = re.search(
                r"(?:v=|youtu\.be/|youtube\.com/(?:embed/|v/|watch\?v=))([0-9A-Za-z_-]{11})", 
                link
            )
            if video_id_match:
                downloaded_file = await self._download_from_api(video_id_match.group(1))
                if downloaded_file:
                    return downloaded_file, False

        # Fall back to regular download methods
        loop = asyncio.get_running_loop()

        if songvideo:
            def song_video_dl():
                ydl_optssx = {
                    "format": f"{format_id}+140",
                    "outtmpl": f"downloads/{title}",
                    "geo_bypass": True,
                    "nocheckcertificate": True,
                    "quiet": True,
                    "no_warnings": True,
                    "cookiefile": self.cookie_txt_file(),
                    "prefer_ffmpeg": True,
                    "merge_output_format": "mp4",
                }
                with yt_dlp.YoutubeDL(ydl_optssx) as ydl:
                    ydl.download([link])

            await loop.run_in_executor(None, song_video_dl)
            return f"downloads/{title}.mp4", True

        elif songaudio:
            def song_audio_dl():
                ydl_optssx = {
                    "format": format_id,
                    "outtmpl": f"downloads/{title}.%(ext)s",
                    "geo_bypass": True,
                    "nocheckcertificate": True,
                    "quiet": True,
                    "no_warnings": True,
                    "cookiefile": self.cookie_txt_file(),
                    "prefer_ffmpeg": True,
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "320",
                    }],
                }
                with yt_dlp.YoutubeDL(ydl_optssx) as ydl:
                    ydl.download([link])

            await loop.run_in_executor(None, song_audio_dl)
            return f"downloads/{title}.mp3", True

        elif video:
            if await is_on_off(1):
                def video_dl():
                    ydl_optssx = {
                        "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                        "outtmpl": "downloads/%(id)s.%(ext)s",
                        "geo_bypass": True,
                        "nocheckcertificate": True,
                        "quiet": True,
                        "cookiefile": self.cookie_txt_file(),
                        "no_warnings": True,
                    }
                    with yt_dlp.YoutubeDL(ydl_optssx) as ydl:
                        info = ydl.extract_info(link, download=False)
                        file_path = os.path.join("downloads", f"{info['id']}.{info['ext']}")
                        if not os.path.exists(file_path):
                            ydl.download([link])
                        return file_path

                downloaded_file = await loop.run_in_executor(None, video_dl)
                return downloaded_file, True
            else:
                proc = await asyncio.create_subprocess_exec(
                    "yt-dlp",
                    "--cookies", self.cookie_txt_file(),
                    "-g",
                    "-f",
                    "best[height<=?720][width<=?1280]",
                    link,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await proc.communicate()
                if stdout:
                    return stdout.decode().split("\n")[0], False
                else:
                    file_size = await self.check_file_size(link)
                    if file_size and (file_size / (1024 * 1024)) <= 250:
                        downloaded_file = await loop.run_in_executor(None, video_dl)
                        return downloaded_file, True
                    return None, False
        else:
            def audio_dl():
                ydl_optssx = {
                    "format": "bestaudio/best",
                    "outtmpl": "downloads/%(id)s.%(ext)s",
                    "geo_bypass": True,
                    "nocheckcertificate": True,
                    "quiet": True,
                    "cookiefile": self.cookie_txt_file(),
                    "no_warnings": True,
                }
                with yt_dlp.YoutubeDL(ydl_optssx) as ydl:
                    info = ydl.extract_info(link, download=False)
                    file_path = os.path.join("downloads", f"{info['id']}.{info['ext']}")
                    if not os.path.exists(file_path):
                        ydl.download([link])
                    return file_path

            downloaded_file = await loop.run_in_executor(None, audio_dl)
            return downloaded_file, True
