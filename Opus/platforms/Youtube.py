import asyncio
import os
import re
import json
from typing import Union
import glob
import random
import logging
import aiohttp
import base64
from functools import lru_cache
from contextlib import asynccontextmanager

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch

from Opus.utils.database import is_on_off
from Opus.utils.formatters import time_to_seconds

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cookie_txt_file():
    folder_path = f"{os.getcwd()}/cookies"
    filename = f"{os.getcwd()}/cookies/logs.csv"
    txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
    if not txt_files:
        raise FileNotFoundError("No .txt files found in the specified folder.")
    cookie_file = random.choice(txt_files)
    with open(filename, 'a') as file:
        file.write(f'Chosen File: {cookie_file}\n')
    return f"cookies/{os.path.basename(cookie_file)}"

async def check_file_size(link: str) -> Union[int, None]:
    async def get_format_info(link: str) -> Union[dict, None]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "yt-dlp", "--cookies", cookie_txt_file(), "-J", link,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                logger.error(f"yt-dlp error: {stderr.decode()}")
                return None
            return json.loads(stdout.decode())
        except Exception as e:
            logger.error(f"Error fetching format info: {e}")
            return None

    def parse_size(formats: list) -> int:
        return sum(format.get('filesize', 0) for format in formats)

    info = await get_format_info(link)
    if not info:
        return None
    formats = info.get('formats', [])
    if not formats:
        logger.warning("No formats found.")
        return None
    return parse_size(formats)

async def shell_cmd(cmd: str) -> str:
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        out, err = await proc.communicate()
        output = out.decode("utf-8") if out else err.decode("utf-8")
        if "unavailable videos are hidden" in output.lower():
            return out.decode("utf-8")
        return output
    except Exception as e:
        logger.error(f"Shell command error: {e}")
        return ""

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.listbase = "https://youtube.com/playlist?list="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self._api_urls = [
            base64.b64decode("aHR0cHM6Ly9uYXJheWFuLnNpdmVuZHJhc3Rvcm0ud29ya2Vycy5kZXYvYXJ5dG1wMz9kaXJlY3QmaWQ9").decode("utf-8"),
            base64.b64decode("aHR0cHM6Ly9iaWxsYWF4LnNodWtsYWt1c3VtNHEud29ya2Vycy5kZXYvP2lkPQ==").decode("utf-8")
        ]
        self._current_api_index = 0
        self._session = None  # Lazy initialization of ClientSession

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self._session

    async def __aenter__(self):
        await self._get_session()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._session and not self._session.closed:
            await self._session.close()

    def _get_api_url(self, video_id: str) -> str:
        url = self._api_urls[self._current_api_index] + video_id
        self._current_api_index = (self._current_api_index + 1) % len(self._api_urls)
        return url

    @lru_cache(maxsize=1000)
    async def exists(self, link: str, videoid: Union[bool, str] = None) -> bool:
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1, message_1.reply_to_message] if message_1.reply_to_message else [message_1]
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset:entity.offset + entity.length]
            if message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    @lru_cache(maxsize=1000)
    async def details(self, link: str, videoid: Union[bool, str] = None) -> tuple:
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        result = (await results.next())["result"][0]
        title = result["title"]
        duration_min = result["duration"] or "0:00"
        duration_sec = int(time_to_seconds(duration_min)) if duration_min != "0:00" else 0
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        vidid = result["id"]
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None) -> str:
        title, _, _, _, _ = await self.details(link, videoid)
        return title

    async def duration(self, link: str, videoid: Union[bool, str] = None) -> str:
        _, duration_min, _, _, _ = await self.details(link, videoid)
        return duration_min

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None) -> str:
        _, _, _, thumbnail, _ = await self.details(link, videoid)
        return thumbnail

    async def video(self, link: str, videoid: Union[bool, str] = None) -> tuple:
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            proc = await asyncio.create_subprocess_exec(
                "yt-dlp", "--cookies", cookie_txt_file(), "-g", "-f", "best[height<=?720][width<=?1280]", link,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if stdout:
                return 1, stdout.decode().split("\n")[0]
            return 0, stderr.decode()
        except Exception as e:
            logger.error(f"Video fetch error: {e}")
            return 0, str(e)

    async def playlist(self, link: str, limit: int, user_id: int, videoid: Union[bool, str] = None) -> list:
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        cmd = f"yt-dlp -i --get-id --flat-playlist --cookies {cookie_txt_file()} --playlist-end {limit} --skip-download {link}"
        result = await shell_cmd(cmd)
        return [x for x in result.split("\n") if x]

    async def track(self, link: str, videoid: Union[bool, str] = None) -> tuple:
        title, duration_min, _, thumbnail, vidid = await self.details(link, videoid)
        return {
            "title": title,
            "link": link,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None) -> tuple:
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {"quiet": True, "cookiefile": cookie_txt_file()}
        try:
            with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                r = ydl.extract_info(link, download=False)
                formats_available = [
                    {
                        "format": f["format"],
                        "filesize": f.get("filesize"),
                        "format_id": f["format_id"],
                        "ext": f["ext"],
                        "format_note": f.get("format_note"),
                        "yturl": link,
                    }
                    for f in r["formats"]
                    if "dash" not in f["format"].lower() and all(k in f for k in ["format", "format_id", "ext"])
                ]
            return formats_available, link
        except Exception as e:
            logger.error(f"Formats fetch error: {e}")
            return [], link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None) -> tuple:
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=10)
        result = (await results.next())["result"][query_type]
        return (
            result["title"],
            result["duration"] or "0:00",
            result["thumbnails"][0]["url"].split("?")[0],
            result["id"]
        )

    async def _download_from_api(self, video_id: str) -> Union[str, None]:
        file_path = os.path.join("downloads", f"{video_id}.mp3")
        if os.path.exists(file_path):
            logger.info(f"{file_path} already exists. Skipping download.")
            return file_path

        async with self._get_session() as session:
            for attempt in range(2):
                api_url = self._get_api_url(video_id)
                try:
                    async with session.get(api_url) as response:
                        if response.status == 200:
                            os.makedirs("downloads", exist_ok=True)
                            with open(file_path, 'wb') as f:
                                async for chunk in response.content.iter_chunked(8192):
                                    f.write(chunk)
                            logger.info(f"Successfully downloaded from API: {file_path}")
                            return file_path
                        logger.warning(f"API request failed with status {response.status}")
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    logger.error(f"API download attempt {attempt + 1} failed: {e}")
            logger.error("All API attempts failed")
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
    ) -> tuple:
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        loop = asyncio.get_running_loop()

        async def audio_dl() -> str:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "cookiefile": cookie_txt_file(),
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
                xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
                if os.path.exists(xyz):
                    return xyz
                ydl.download([link])
                return xyz

        async def video_dl() -> str:
            ydl_opts = {
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "cookiefile": cookie_txt_file(),
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
                xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
                if os.path.exists(xyz):
                    return xyz
                ydl.download([link])
                return xyz

        async def song_video_dl() -> str:
            ydl_opts = {
                "format": f"{format_id}+140",
                "outtmpl": f"downloads/{title}",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "cookiefile": cookie_txt_file(),
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4",
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
            return f"downloads/{title}.mp4"

        async def song_audio_dl() -> str:
            ydl_opts = {
                "format": format_id,
                "outtmpl": f"downloads/{title}.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "cookiefile": cookie_txt_file(),
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "320",
                    }
                ],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
            return f"downloads/{title}.mp3"

        try:
            if songvideo:
                return await song_video_dl(), True
            elif songaudio:
                return await song_audio_dl(), True
            elif video:
                if await is_on_off(1):
                    return await video_dl(), True
                file_size = await check_file_size(link)
                if not file_size:
                    logger.error("Failed to retrieve file size")
                    return None, False
                if file_size / (1024 * 1024) > 250:
                    logger.error(f"File size {file_size / (1024 * 1024):.2f} MB exceeds 250MB limit")
                    return None, False
                return await video_dl(), True
            else:
                video_id_pattern = r"(?:v=|youtu\.be/|youtube\.com/(?:embed/|v/|watch\?v=))([0-9A-Za-z_-]{11})"
                match = re.search(video_id_pattern, link)
                if match:
                    downloaded_file = await self._download_from_api(match.group(1))
                    if downloaded_file:
                        return downloaded_file, True
                return await audio_dl(), True
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None, False
