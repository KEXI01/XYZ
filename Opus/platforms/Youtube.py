import os
import asyncio
import re
import json
from typing import Optional, Tuple, Union, List
import glob
import random
import logging
import aiohttp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
from config import URL2 as API_URL2
import yt_dlp

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class YouTubeAPI:

    def __init__(self):
        self.base_url = "https://www.youtube.com/watch?v="
        self.listbase_url = "https://youtube.com/playlist?list="
        self.video_id_pattern = re.compile(r"(?:v=|youtu\.be/|youtube\.com/(?:embed/|v/|watch\?v=))([0-9A-Za-z_-]{11})")
        self.mp3_api_urls = [
            "https://narayan.sivendrastorm.workers.dev/arytmp3",
            "https://billaax.shuklakusum4q.workers.dev/arytmp3"
        ]
        self.video_api_url = API_URL2
        self.session = None
        self.download_dir = "downloads"
        os.makedirs(self.download_dir, exist_ok=True)

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session and not self.session.closed:
            await self.session.close()

    def _get_cookie_file(self) -> str:
        folder_path = os.path.join(os.getcwd(), "cookies")
        txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
        if not txt_files:
            raise FileNotFoundError("No .txt files found in cookies directory.")
        cookie_file = random.choice(txt_files)
        with open(os.path.join(folder_path, "logs.csv"), "a") as f:
            f.write(f"Choosen File: {cookie_file}\n")
        return cookie_file

    async def _run_subprocess(self, cmd: List[str], decode: bool = True) -> str:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            error = stderr.decode("utf-8") if decode else stderr
            logger.error(f"Subprocess error: {error}")
            raise RuntimeError(error)
        return stdout.decode("utf-8") if decode else stdout

    async def _extract_video_id(self, link: str) -> Optional[str]:
        if "&" in link:
            link = link.split("&")[0]
        match = self.video_id_pattern.search(link)
        if not match:
            logger.error(f"Invalid YouTube URL: {link}")
            return None
        return match.group(1)

    async def _download_from_api(self, link: str, is_video: bool, retries: int = 3, backoff: float = 1.0) -> Optional[str]:
        video_id = await self._extract_video_id(link)
        if not video_id:
            return None

        file_ext = "mp4" if is_video else "mp3"
        file_path = os.path.join(self.download_dir, f"{video_id}.{file_ext}")
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            logger.info(f"File {file_path} already exists.")
            return file_path

        api_url = f"{self.video_api_url}{link}&format=480" if is_video else f"{random.choice(self.mp3_api_urls)}?direct&id={video_id}"

        async def try_download(attempt: int) -> Optional[str]:
            session = await self._ensure_session()
            try:
                async with session.get(api_url, timeout=30) as response:
                    if response.status != 200:
                        logger.warning(f"API request failed with status {response.status} for {api_url}")
                        return None
                    if is_video:
                        data = await response.json()
                        if data.get("status") != "success" or not data.get("download_url"):
                            logger.warning(f"Invalid API response: {data}")
                            return None
                        download_url = data["download_url"]
                    else:
                        download_url = api_url

                    async with session.get(download_url, timeout=30) as dl_response:
                        if dl_response.status != 200:
                            logger.warning(f"Download failed with status {dl_response.status}")
                            return None
                        with open(file_path, "wb") as f:
                            async for chunk in dl_response.content.iter_chunked(1024 * 1024):
                                f.write(chunk)
                        if os.path.getsize(file_path) > 0:
                            logger.info(f"Downloaded {file_path}")
                            return file_path
                        os.remove(file_path)
                        logger.warning(f"Empty file downloaded from {download_url}")
                        return None
            except (aiohttp.ClientError, asyncio.TimeoutError, json.JSONDecodeError) as e:
                logger.error(f"API download attempt {attempt} failed: {str(e)}")
                return None

        for attempt in range(retries):
            result = await try_download(attempt + 1)
            if result:
                return result
            if attempt < retries - 1:
                await asyncio.sleep(backoff * (2 ** attempt))
        logger.error(f"All API attempts failed for {link}")
        return None

    async def check_file_size(self, link: str) -> Optional[int]:
        cmd = ["yt-dlp", "--cookies", self._get_cookie_file(), "-J", link]
        try:
            output = await self._run_subprocess(cmd)
            info = json.loads(output)
            return sum(f["filesize"] for f in info.get("formats", []) if "filesize" in f)
        except Exception as e:
            logger.error(f"Failed to check file size: {str(e)}")
            return None

    async def exists(self, link: str, videoid: Optional[str] = None) -> bool:
        if videoid:
            link = self.base_url + videoid
        return bool(self.video_id_pattern.search(link))

    async def url(self, message: Message) -> Optional[str]:
        for msg in (message, message.reply_to_message) if message.reply_to_message else (message,):
            if msg.entities:
                for entity in msg.entities:
                    if entity.type == MessageEntityType.URL:
                        text = msg.text or msg.caption
                        return text[entity.offset:entity.offset + entity.length]
            if msg.caption_entities:
                for entity in msg.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Optional[str] = None) -> Tuple[Optional[str], Optional[str], int, Optional[str], Optional[str]]:
        if videoid:
            link = self.base_url + videoid
        if "&" in link:
            link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=1)
            result = (await results.next())["result"][0]
            title = result["title"]
            duration = result["duration"]
            duration_sec = int(time_to_seconds(duration)) if duration and duration != "None" else 0
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            return title, duration, duration_sec, thumbnail, vidid
        except Exception as e:
            logger.error(f"Failed to fetch details for {link}: {str(e)}")
            return None, None, 0, None, None

    async def title(self, link: str, videoid: Optional[str] = None) -> Optional[str]:
        title, _, _, _, _ = await self.details(link, videoid)
        return title

    async def duration(self, link: str, videoid: Optional[str] = None) -> Optional[str]:
        _, duration, _, _, _ = await self.details(link, videoid)
        return duration

    async def thumbnail(self, link: str, videoid: Optional[str] = None) -> Optional[str]:
        _, _, _, thumbnail, _ = await self.details(link, videoid)
        return thumbnail

    async def video(self, link: str, videoid: Optional[str] = None) -> Tuple[int, Optional[str]]:
        if videoid:
            link = self.base_url + videoid
        if "&" in link:
            link = link.split("&")[0]
        cmd = [
            "yt-dlp",
            "--cookies", self._get_cookie_file(),
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            link
        ]
        try:
            output = await self._run_subprocess(cmd)
            return 1, output.split("\n")[0]
        except Exception as e:
            logger.error(f"Failed to get video stream for {link}: {str(e)}")
            return 0, str(e)

    async def playlist(self, link: str, limit: int, user_id: int, videoid: Optional[str] = None) -> List[str]:
        if videoid:
            link = self.listbase_url + videoid
        if "&" in link:
            link = link.split("&")[0]
        cmd = [
            "yt-dlp",
            "-i",
            "--get-id",
            "--flat-playlist",
            "--cookies", self._get_cookie_file(),
            f"--playlist-end", str(limit),
            "--skip-download",
            link
        ]
        try:
            output = await self._run_subprocess(cmd)
            result = [vid for vid in output.split("\n") if vid]
            return result
        except Exception as e:
            logger.error(f"Failed to fetch playlist for {link}: {str(e)}")
            return []

    async def track(self, link: str, videoid: Optional[str] = None) -> Tuple[dict, Optional[str]]:
        if videoid:
            link = self.base_url + videoid
        if "&" in link:
            link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=1)
            result = (await results.next())["result"][0]
            track_details = {
                "title": result["title"],
                "link": result["link"],
                "vidid": result["id"],
                "duration_min": result["duration"],
                "thumb": result["thumbnails"][0]["url"].split("?")[0]
            }
            return track_details, result["id"]
        except Exception as e:
            logger.error(f"Failed to fetch track details for {link}: {str(e)}")
            return {}, None

    async def formats(self, link: str, videoid: Optional[str] = None) -> Tuple[List[dict], str]:
        if videoid:
            link = self.base_url + videoid
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {"quiet": True, "cookiefile": self._get_cookie_file()}
        try:
            with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
                formats_available = [
                    {
                        "format": f["format"],
                        "filesize": f.get("filesize"),
                        "format_id": f["format_id"],
                        "ext": f["ext"],
                        "format_note": f.get("format_note"),
                        "yturl": link
                    }
                    for f in info.get("formats", [])
                    if "format" in f and "dash" not in f["format"].lower()
                ]
            return formats_available, link
        except Exception as e:
            logger.error(f"Failed to fetch formats for {link}: {str(e)}")
            return [], link

    async def slider(self, link: str, query_type: int, videoid: Optional[str] = None) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        if videoid:
            link = self.base_url + videoid
        if "&" in link:
            link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=10)
            result = (await results.next())["result"][query_type]
            return (
                result["title"],
                result["duration"],
                result["thumbnails"][0]["url"].split("?")[0],
                result["id"]
            )
        except Exception as e:
            logger.error(f"Failed to fetch slider details for {link}: {str(e)}")
            return None, None, None, None

    async def download(
        self,
        link: str,
        mystic,  # Placeholder for compatibility
        video: Optional[bool] = None,
        videoid: Optional[str] = None,
        songaudio: Optional[str] = None,
        songvideo: Optional[str] = None,
        format_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> Tuple[Optional[str], bool]:
        if videoid:
            link = self.base_url + videoid
        if "&" in link:
            link = link.split("&")[0]

        loop = asyncio.get_running_loop()

        def audio_dl() -> str:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(self.download_dir, "%(id)s.%(ext)s"),
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "cookiefile": self._get_cookie_file(),
                "no_warnings": True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
                file_path = os.path.join(self.download_dir, f"{info['id']}.{info['ext']}")
                if os.path.exists(file_path):
                    return file_path
                ydl.download([link])
                return file_path

        def video_dl() -> str:
            ydl_opts = {
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                "outtmpl": os.path.join(self.download_dir, "%(id)s.%(ext)s"),
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "cookiefile": self
._get_cookie_file(),
                "no_warnings": True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
                file_path = os.path.join(self.download_dir, f"{info['id']}.mp4")
                if os.path.exists(file_path):
                    return file_path
                ydl.download([link])
                return file_path

        def song_video_dl() -> None:
            formats = f"{format_id}+140"
            ydl_opts = {
                "format": formats,
                "outtmpl": os.path.join(self.download_dir, title),
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile": self._get_cookie_file(),
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4"
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])

        def song_audio_dl() -> None:
            ydl_opts = {
                "format": format_id,
                "outtmpl": os.path.join(self.download_dir, f"{title}.%(ext)s"),
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile": self._get_cookie_file(),
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "opus",
                        "preferredquality": "192"
                    }
                ]
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])

        try:
            if songvideo:
                await loop.run_in_executor(None, song_video_dl)
                return os.path.join(self.download_dir, f"{title}.mp4"), True
            elif songaudio:
                await loop.run_in_executor(None, song_audio_dl)
                return os.path.join(self.download_dir, f"{title}.opus"), True
            elif video:
                downloaded_file = await self._download_from_api(link, is_video=True)
                if downloaded_file:
                    return downloaded_file, True
                file_size = await self.check_file_size(link)
                if file_size and file_size / (1024 * 1024) > 250:
                    logger.warning(f"File size {file_size / (1024 * 1024):.2f} MB exceeds 250MB limit.")
                    return None, False
                return await loop.run_in_executor(None, video_dl), True
            else:
                downloaded_file = await self._download_from_api(link, is_video=False)
                if downloaded_file:
                    return downloaded_file, True
                return await loop.run_in_executor(None, audio_dl), True
        except Exception as e:
            logger.error(f"Download failed for {link}: {str(e)}")
            return None, False
