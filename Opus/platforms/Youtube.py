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

APIS = [
    {"url": "https://sp.ashok.sbs", "key": "3ef99e_3pwgOlZyuZXZL43QdkDzWMxQRe0yk-lB"},
    {"url": "https://sp.ashok.sbs", "key": "11c670_Yr4BHT54qE9HUXblsVBpWXWG9Z-0zuMo"},
    {"url": "https://sp.ashok.sbs", "key": "2b6222_6XK_mvLqkNzgfAaepNeX1f0SBDUan1vK"},
    {"url": "https://sp.ashok.sbs", "key": "34dc78_AbcZpQpBVQLrEAiBsVsLjzSZmAxCe7fj"}
]

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

async def get_stream_url(query, video=False):
    api = random.choice(APIS)  # Randomly select an API
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            params = {"query": query, "video": video, "api_key": api["key"]}
            response = await client.get(api["url"], params=params)
            if response.status_code != 200:
                return ""
            info = response.json()
            return info.get("stream_url", "")
    except Exception as e:
        logging.error(f"API Error with {api['url']}: {e}")
        return ""
        
class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        self.max_retries = 3  # Max retries for any operation
        self.timeout = 30  # Timeout in seconds

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
            
        for attempt in range(self.max_retries):
            try:
                results = VideosSearch(link, limit=1)
                for result in (await results.next())["result"]:
                    title = result["title"]
                    duration_min = result["duration"]
                    thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                    vidid = result["id"]
                    duration_sec = 0 if str(duration_min) == "None" else int(time_to_seconds(duration_min))
                    return title, duration_min, duration_sec, thumbnail, vidid
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logging.error(f"Failed to get details after {self.max_retries} attempts: {e}")
                    return None, None, None, None, None
                await asyncio.sleep(1)

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        for attempt in range(self.max_retries):
            try:
                results = VideosSearch(link, limit=1)
                for result in (await results.next())["result"]:
                    return result["title"]
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logging.error(f"Failed to get title after {self.max_retries} attempts: {e}")
                    return None
                await asyncio.sleep(1)

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        for attempt in range(self.max_retries):
            try:
                results = VideosSearch(link, limit=1)
                for result in (await results.next())["result"]:
                    return result["duration"]
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logging.error(f"Failed to get duration after {self.max_retries} attempts: {e}")
                    return None
                await asyncio.sleep(1)

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        for attempt in range(self.max_retries):
            try:
                results = VideosSearch(link, limit=1)
                for result in (await results.next())["result"]:
                    return result["thumbnails"][0]["url"].split("?")[0]
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logging.error(f"Failed to get thumbnail after {self.max_retries} attempts: {e}")
                    return None
                await asyncio.sleep(1)

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        # Try multiple methods with fallbacks
        methods = [
            self._try_api_video,
            self._try_ytdlp_with_cookies,
            self._try_basic_ytdlp
        ]
        
        for method in methods:
            try:
                result = await method(link)
                if result:
                    return result
            except Exception as e:
                logging.warning(f"Video fetch method {method.__name__} failed: {e}")
                continue
                
        return 0, "Failed to fetch video URL after all attempts"

    async def _try_api_video(self, link):
        """Try getting video URL from API first"""
        api_url = await get_stream_url(link, True)
        if api_url:
            return 1, api_url
        return None

    async def _try_ytdlp_with_cookies(self, link):
        """Try with cookies for premium content"""
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
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
            
            if proc.returncode == 0 and stdout:
                return 1, stdout.decode().split("\n")[0]
        except Exception as e:
            logging.warning(f"Cookie-based video fetch failed: {e}")
        return None

    async def _try_basic_ytdlp(self, link):
        """Fallback to basic yt-dlp without cookies"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "yt-dlp",
                "-g",
                "-f",
                "best[height<=?720][width<=?1280]",
                f"{link}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
            
            if proc.returncode == 0 and stdout:
                return 1, stdout.decode().split("\n")[0]
        except Exception as e:
            logging.warning(f"Basic yt-dlp fetch failed: {e}")
        return None

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
            
        methods = [
            self._try_playlist_with_cookies,
            self._try_basic_playlist
        ]
        
        for method in methods:
            try:
                result = await method(link, limit)
                if result:
                    return result
            except Exception as e:
                logging.warning(f"Playlist fetch method {method.__name__} failed: {e}")
                continue
                
        return []

    async def _try_playlist_with_cookies(self, link, limit):
        """Try fetching playlist with cookies"""
        try:
            playlist = await shell_cmd(
                f"yt-dlp -i --get-id --flat-playlist --cookies {cookie_txt_file()} --playlist-end {limit} --skip-download {link}"
            )
            result = playlist.split("\n")
            return [key for key in result if key != ""]
        except Exception as e:
            logging.warning(f"[PLY] Failed to fetch playlist with cookies: {e}")
            return None

    async def _try_basic_playlist(self, link, limit):
        """Fallback to basic playlist fetch without cookies"""
        try:
            playlist = await shell_cmd(
                f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
            )
            result = playlist.split("\n")
            return [key for key in result if key != ""]
        except Exception as e:
            logging.warning(f"[PLY] Failed to fetch basic playlist: {e}")
            return None

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        for attempt in range(self.max_retries):
            try:
                results = VideosSearch(link, limit=1)
                for result in (await results.next())["result"]:
                    return {
                        "title": result["title"],
                        "link": result["link"],
                        "vidid": result["id"],
                        "duration_min": result["duration"],
                        "thumb": result["thumbnails"][0]["url"].split("?")[0],
                    }, result["id"]
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logging.error(f"Failed to get track info after {self.max_retries} attempts: {e}")
                    return None, None
                await asyncio.sleep(1)

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        formats_available = []
        
        methods = [
            self._try_formats_with_cookies,
            self._try_basic_formats
        ]
        
        for method in methods:
            try:
                result = await method(link)
                if result:
                    return result, link
            except Exception as e:
                logging.warning(f"Formats fetch method {method.__name__} failed: {e}")
                continue
                
        return [], link

    async def _try_formats_with_cookies(self, link):
        """Try getting formats with cookies"""
        try:
            ytdl_opts = {
                "quiet": True,
                "cookiefile": cookie_txt_file(),
                "extract_flat": False
            }
            ydl = yt_dlp.YoutubeDL(ytdl_opts)
            with ydl:
                r = ydl.extract_info(link, download=False)
                return self._process_formats(r)
        except Exception as e:
            logging.warning(f"[FMT] Failed to fetch formats with cookies: {e}")
            return None

    async def _try_basic_formats(self, link):
        """Fallback to basic formats without cookies"""
        try:
            ytdl_opts = {
                "quiet": True,
                "extract_flat": False
            }
            ydl = yt_dlp.YoutubeDL(ytdl_opts)
            with ydl:
                r = ydl.extract_info(link, download=False)
                return self._process_formats(r)
        except Exception as e:
            logging.warning(f"[FMT] Failed to fetch basic formats: {e}")
            return None

    def _process_formats(self, r):
        """Process formats from yt-dlp response"""
        formats_available = []
        for format in r["formats"]:
            try:
                format_note = format.get("format_note", "").lower()
                acodec = format.get("acodec", "").lower()
                
                is_high_quality_audio = (
                    "audio only" in format_note and 
                    acodec in ["opus", "flac", "alac"] or
                    format.get("abr", 0) >= 256
                )
                
                if "audio only" in format_note.lower():
                    formats_available.append({
                        "format": format.get("format"),
                        "filesize": format.get("filesize"),
                        "format_id": format.get("format_id"),
                        "ext": format.get("ext"),
                        "format_note": format.get("format_note"),
                        "abr": format.get("abr", 0),
                        "asr": format.get("asr", 0),
                        "yturl": r["webpage_url"],
                        "is_high_quality": is_high_quality_audio,
                        "acodec": acodec,
                    })
                else:
                    formats_available.append({
                        "format": format.get("format"),
                        "filesize": format.get("filesize"),
                        "format_id": format.get("format_id"),
                        "ext": format.get("ext"),
                        "format_note": format.get("format_note"),
                        "height": format.get("height", 0),
                        "width": format.get("width", 0),
                        "fps": format.get("fps", 0),
                        "yturl": r["webpage_url"],
                    })
            except:
                continue
        
        formats_available.sort(
            key=lambda x: (
                -x.get("is_high_quality", False),
                x.get("height", 0) or x.get("abr", 0),
                x.get("width", 0),
                x.get("fps", 0),
                x.get("asr", 0)
            ),
            reverse=True
        )
        
        return formats_available

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        for attempt in range(self.max_retries):
            try:
                result = (await VideosSearch(link, limit=10).next()).get("result")
                return (
                    result[query_type]["title"],
                    result[query_type]["duration"],
                    result[query_type]["thumbnails"][0]["url"].split("?")[0],
                    result[query_type]["id"],
                )
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logging.error(f"Failed to get slider info after {self.max_retries} attempts: {e}")
                    return None, None, None, None
                await asyncio.sleep(1)

    async def download(self, link: str, mystic, video: Union[bool, str] = None, 
                     videoid: Union[bool, str] = None, songaudio: Union[bool, str] = None,
                     songvideo: Union[bool, str] = None, format_id: Union[bool, str] = None,
                     title: Union[bool, str] = None) -> str:
        if videoid:
            link = self.base + link
            
        loop = asyncio.get_running_loop()
        
        # Define all possible download methods
        methods = [
            lambda: self._try_cookie_download(link, video, songaudio, songvideo, format_id, title, loop),
            lambda: self._try_api_download(link, video, songaudio, songvideo, title),
            lambda: self._try_basic_download(link, video, songaudio, songvideo, format_id, title, loop)
        ]
        
        # Try each method in order until one succeeds
        for method in methods:
            try:
                result = await method()
                if result is not None:
                    return result
            except Exception as e:
                logging.warning(f"[DL] Download method failed: {e}")
                continue
                
        # Final fallback
        if songvideo:
            return f"downloads/{title}.mp4", True
        elif songaudio:
            return f"downloads/{title}.mp3", True
        else:
            return None

    async def _try_cookie_download(self, link, video, songaudio, songvideo, format_id, title, loop):
        """Try download with cookies first"""
        try:
            if songvideo:
                def dl():
                    ydl_optssx = {
                        "format": f"{format_id}+bestaudio[acodec=opus]/best",
                        "outtmpl": f"downloads/{title}",
                        "geo_bypass": True,
                        "cookiefile": cookie_txt_file(),
                        "nocheckcertificate": True,
                        "quiet": True,
                        "no_warnings": True,
                        "prefer_ffmpeg": True,
                        "merge_output_format": "mp4",
                        "postprocessors": [{
                            "key": "FFmpegVideoConvertor",
                            "preferedformat": "mp4"
                        }],
                        "ffmpeg_location": "/usr/bin/ffmpeg"
                    }
                    yt_dlp.YoutubeDL(ydl_optssx).download([link])
                    return f"downloads/{title}.mp4"
                
                return await loop.run_in_executor(None, dl), True
            
            elif songaudio:
                def dl():
                    # First try highest quality audio formats
                    try:
                        ydl_optssx = {
                            "format": "bestaudio[acodec=opus]/bestaudio[ext=webm]/bestaudio[abr>=320]/bestaudio/best",
                            "outtmpl": f"downloads/{title}.%(ext)s",
                            "geo_bypass": True,
                            "cookiefile": cookie_txt_file(),
                            "nocheckcertificate": True,
                            "quiet": True,
                            "no_warnings": True,
                            "prefer_ffmpeg": True,
                            "postprocessors": [{
                                "key": "FFmpegExtractAudio",
                                "preferredcodec": "opus",
                                "preferredquality": "0",
                            }],
                            "ffmpeg_location": "/usr/bin/ffmpeg",
                        }
                        ydl = yt_dlp.YoutubeDL(ydl_optssx)
                        info = ydl.extract_info(link, download=False)
                        
                        # Check for Opus (highest quality)
                        if any(f.get('acodec', '').lower() == 'opus' for f in info.get('formats', [])):
                            path = os.path.join("downloads", f"{title}.opus")
                            if not os.path.exists(path):
                                ydl.download([link])
                            return path
                        
                        # Fallback to 320kbps MP3
                        ydl_optssx["postprocessors"][0]["preferredcodec"] = "mp3"
                        ydl_optssx["postprocessors"][0]["preferredquality"] = "320"
                        ydl = yt_dlp.YoutubeDL(ydl_optssx)
                        path = os.path.join("downloads", f"{title}.mp3")
                        if not os.path.exists(path):
                            ydl.download([link])
                        return path
                    except Exception as e:
                        logging.warning(f"[AUDIO] Failed to get high quality audio: {e}")
                        # Final fallback
                        ydl_optssx = {
                            "format": "bestaudio/best",
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
                            "ffmpeg_location": "/usr/bin/ffmpeg"
                        }
                        yt_dlp.YoutubeDL(ydl_optssx).download([link])
                        return f"downloads/{title}.mp3"
                
                return await loop.run_in_executor(None, dl), True
            
            elif video:
                if await is_on_off(1):
                    def dl():
                        ydl_optssx = {
                            "format": "bestvideo[height<=480][ext=mp4]+bestaudio[acodec=opus]/bestvideo[height<=480]+bestaudio/best",
                            "outtmpl": "downloads/%(id)s.%(ext)s",
                            "geo_bypass": True,
                            "cookiefile": cookie_txt_file(),
                            "nocheckcertificate": True,
                            "quiet": True,
                            "no_warnings": True,
                            "ffmpeg_location": "/usr/bin/ffmpeg",
                            "merge_output_format": "mp4"
                        }
                        x = yt_dlp.YoutubeDL(ydl_optssx)
                        info = x.extract_info(link, False)
                        path = os.path.join("downloads", f"{info['id']}.{info['ext']}")
                        if not os.path.exists(path):
                            x.download([link])
                        return path
                    
                    return await loop.run_in_executor(None, dl), True
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
                                "format": "bestvideo[height<=480][ext=mp4]+bestaudio/best",
                                "outtmpl": "downloads/%(id)s.%(ext)s",
                                "geo_bypass": True,
                                "cookiefile": cookie_txt_file(),
                                "nocheckcertificate": True,
                                "quiet": True,
                                "no_warnings": True,
                                "ffmpeg_location": "/usr/bin/ffmpeg"
                            }
                            x = yt_dlp.YoutubeDL(ydl_optssx)
                            info = x.extract_info(link, False)
                            path = os.path.join("downloads", f"{info['id']}.{info['ext']}")
                            if not os.path.exists(path):
                                x.download([link])
                            return path
                        
                        return await loop.run_in_executor(None, dl), True
            
            else: 
                def dl():
                    # Audio-only download with highest quality priority
                    try:
                        ydl_optssx = {
                            "format": "bestaudio[acodec=opus]/bestaudio[ext=webm]/bestaudio[abr>=320]/bestaudio/best",
                            "outtmpl": "downloads/%(id)s.%(ext)s",
                            "geo_bypass": True,
                            "cookiefile": cookie_txt_file(),
                            "nocheckcertificate": True,
                            "quiet": True,
                            "no_warnings": True,
                            "postprocessors": [{
                                "key": "FFmpegExtractAudio",
                                "preferredcodec": "opus",
                                "preferredquality": "0",
                            }],
                            "ffmpeg_location": "/usr/bin/ffmpeg",
                        }
                        ydl = yt_dlp.YoutubeDL(ydl_optssx)
                        info = ydl.extract_info(link, download=False)
                        
                        # Check for Opus (highest quality)
                        if any(f.get('acodec', '').lower() == 'opus' for f in info.get('formats', [])):
                            path = os.path.join("downloads", f"{info['id']}.opus")
                            if not os.path.exists(path):
                                ydl.download([link])
                            return path
                        
                        # Fallback to 320kbps MP3
                        ydl_optssx["postprocessors"][0]["preferredcodec"] = "mp3"
                        ydl_optssx["postprocessors"][0]["preferredquality"] = "320"
                        ydl = yt_dlp.YoutubeDL(ydl_optssx)
                        path = os.path.join("downloads", f"{info['id']}.mp3")
                        if not os.path.exists(path):
                            ydl.download([link])
                        return path
                    except Exception as e:
                        logging.warning(f"[AUDIO] Failed to get high quality audio: {e}")
                        # Final fallback
                        ydl_optssx = {
                            "format": "bestaudio/best",
                            "outtmpl": "downloads/%(id)s.%(ext)s",
                            "geo_bypass": True,
                            "cookiefile": cookie_txt_file(),
                            "nocheckcertificate": True,
                            "quiet": True,
                            "no_warnings": True,
                            "postprocessors": [{
                                "key": "FFmpegExtractAudio",
                                "preferredcodec": "mp3",
                                "preferredquality": "192",
                            }],
                            "ffmpeg_location": "/usr/bin/ffmpeg"
                        }
                        x = yt_dlp.YoutubeDL(ydl_optssx)
                        info = x.extract_info(link, False)
                        path = os.path.join("downloads", f"{info['id']}.mp3")
                        if not os.path.exists(path):
                            x.download([link])
                        return path
                
                return await loop.run_in_executor(None, dl), True
        
        except Exception as e:
            logging.warning(f"[DL] Cookie-based download failed: {e}")
            return None

    async def _try_api_download(self, link, video, songaudio, songvideo, title):
        """Try getting download URL from API"""
        try:
            stream_url = await get_stream_url(link, video)
            if stream_url:
                if songvideo:
                    return f"downloads/{title}.mp4", True
                elif songaudio:
                    return f"downloads/{title}.mp3", True
                else:
                    return stream_url, False if video else None
        except Exception as e:
            logging.warning(f"[DL] API download failed: {e}")
            return None

    async def _try_basic_download(self, link, video, songaudio, songvideo, format_id, title, loop):
        """Fallback to basic download without cookies"""
        try:
            if songvideo:
                def dl():
                    ydl_optssx = {
                        "format": f"{format_id}+bestaudio/best",
                        "outtmpl": f"downloads/{title}",
                        "geo_bypass": True,
                        "nocheckcertificate": True,
                        "quiet": True,
                        "no_warnings": True,
                        "prefer_ffmpeg": True,
                        "merge_output_format": "mp4",
                        "postprocessors": [{
                            "key": "FFmpegVideoConvertor",
                            "preferedformat": "mp4"
                        }],
                        "ffmpeg_location": "/usr/bin/ffmpeg"
                    }
                    yt_dlp.YoutubeDL(ydl_optssx).download([link])
                    return f"downloads/{title}.mp4"
                
                return await loop.run_in_executor(None, dl), True
            
            elif songaudio:
                def dl():
                    ydl_optssx = {
                        "format": "bestaudio/best",
                        "outtmpl": f"downloads/{title}.%(ext)s",
                        "geo_bypass": True,
                        "nocheckcertificate": True,
                        "quiet": True,
                        "no_warnings": True,
                        "prefer_ffmpeg": True,
                        "postprocessors": [{
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }],
                        "ffmpeg_location": "/usr/bin/ffmpeg"
                    }
                    yt_dlp.YoutubeDL(ydl_optssx).download([link])
                    return f"downloads/{title}.mp3"
                
                return await loop.run_in_executor(None, dl), True
            
            elif video:
                proc = await asyncio.create_subprocess_exec(
                    "yt-dlp",
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
            else:
                def dl():
                    ydl_optssx = {
                        "format": "bestaudio/best",
                        "outtmpl": "downloads/%(id)s.%(ext)s",
                        "geo_bypass": True,
                        "nocheckcertificate": True,
                        "quiet": True,
                        "no_warnings": True,
                        "postprocessors": [{
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }],
                        "ffmpeg_location": "/usr/bin/ffmpeg"
                    }
                    x = yt_dlp.YoutubeDL(ydl_optssx)
                    info = x.extract_info(link, False)
                    path = os.path.join("downloads", f"{info['id']}.mp3")
                    if not os.path.exists(path):
                        x.download([link])
                    return path
                
                return await loop.run_in_executor(None, dl), True
                
        except Exception as e:
            logging.warning(f"[DL] Basic download failed: {e}")
            return None
