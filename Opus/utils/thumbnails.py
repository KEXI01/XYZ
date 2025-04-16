import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from unidecode import unidecode
from youtubesearchpython.__future__ import VideosSearch
from Opus import app
from config import YOUTUBE_IMG_URL

def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage

def truncate(text, max_length=27):
    if len(text) > max_length:
        return text[: max_length - 1] + "…"
    return text

def truncate_channel(text, max_length=18):
    if len(text) > max_length:
        return text[: max_length - 1] + "…"
    return text




def crop_center_circle(img, output_size, border, crop_scale=1.5):
    half_the_width = img.size[0] / 2
    half_the_height = img.size[1] / 2
    larger_size = int(output_size * crop_scale)
    img = img.crop(
        (
            half_the_width - larger_size/2,
            half_the_height - larger_size/2,
            half_the_width + larger_size/2,
            half_the_height + larger_size/2
        )
    )
    
    img = img.resize((output_size - 2*border, output_size - 2*border))
    
    
    final_img = Image.new("RGBA", (output_size, output_size), "white")
    
    
    mask_main = Image.new("L", (output_size - 2*border, output_size - 2*border), 0)
    draw_main = ImageDraw.Draw(mask_main)
    draw_main.ellipse((0, 0, output_size - 2*border, output_size - 2*border), fill=255)
    
    final_img.paste(img, (border, border), mask_main)
    
    
    mask_border = Image.new("L", (output_size, output_size), 0)
    draw_border = ImageDraw.Draw(mask_border)
    draw_border.ellipse((0, 0, output_size, output_size), fill=255)
    
    result = Image.composite(final_img, Image.new("RGBA", final_img.size, (0, 0, 0, 0)), mask_border)
    
    return result


def crop_center_square(img, output_size, crop_scale=1.0):
    half_the_width = img.size[0] / 2
    half_the_height = img.size[1] / 2
    larger_size = int(output_size * crop_scale)

    # Square crop
    img = img.crop((
        half_the_width - larger_size / 2,
        half_the_height - larger_size / 2,
        half_the_width + larger_size / 2,
        half_the_height + larger_size / 2
    ))

    img = img.resize((output_size, output_size))

    # Create a mask with rounded corners
    mask = Image.new("L", (output_size, output_size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, output_size, output_size), radius=10, fill=255)

    # Apply the mask
    rounded_square = Image.new("RGBA", (output_size, output_size), (0, 0, 0, 0))
    rounded_square.paste(img, (0, 0), mask)

    return rounded_square



async def get_thumb(videoid):
    if os.path.isfile(f"cache/{videoid}_v4.png"):
        return f"cache/{videoid}_v4.png"

    url = f"https://www.youtube.com/watch?v={videoid}"
    results = VideosSearch(url, limit=1)
    for result in (await results.next())["result"]:
        try:
            title = result["title"]
            title = re.sub("\W+", " ", title)
            title = title.title()
        except:
            title = "Unsupported Title"
        try:
            duration = result["duration"]
        except:
            duration = "Unknown Mins"
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        try:
            views = result["viewCount"]["short"]
        except:
            views = "Unknown Views"
        try:
            channel = result["channel"]["name"]
        except:
            channel = "Unknown Channel"

    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as resp:
            if resp.status == 200:
                f = await aiofiles.open(f"cache/thumb{videoid}.png", mode="wb")
                await f.write(await resp.read())
                await f.close()

    youtube = Image.open(f"cache/thumb{videoid}.png")
    image1 = changeImageSize(1280, 720, youtube)
    image2 = image1.convert("RGBA")
    background = image2.filter(filter=ImageFilter.BoxBlur(20))
    enhancer = ImageEnhance.Brightness(background)
    background = enhancer.enhance(0.6)
    draw = ImageDraw.Draw(background)

    title_font = ImageFont.truetype("src/assets/semibold.ttf", 28)
    channel_name_font = ImageFont.truetype("src/assets/semibold.ttf", 20)
    duration_font = ImageFont.truetype("src/assets/semibold.ttf", 18)


    # Load your image
    my_image = Image.open("src/assets/bg.png").convert("RGBA")

    # Resize if needed
    my_image = my_image.resize((1280, 720))

    # Calculate center position
    bg_width, bg_height = background.size
    img_width, img_height = my_image.size
    center_x = (bg_width - img_width) // 2
    center_y = (bg_height - img_height) // 2

    # Paste image at center
    background.paste(my_image, (center_x, center_y), my_image)

    square_thumbnail = crop_center_square(youtube, 200)
    square_thumbnail = square_thumbnail.resize((190, 190))
    square_position = (302, 188)
    background.paste(square_thumbnail, square_position, square_thumbnail)

    # Video Title

    text_x_position = 520

    draw.text((text_x_position, 240), truncate(title), font=title_font, fill="white")
    draw.text((text_x_position, 290), truncate_channel(channel), (255, 255, 255), font=channel_name_font)

    
    draw.text((930, 440), f"-{duration}", (174, 174, 174), font=duration_font)

    background = background.convert("RGB")


    try:
        os.remove(f"cache/thumb{videoid}.png")
    except:
        pass
    background.save(f"cache/{videoid}_v4.png")
    return f"cache/{videoid}_v4.png"
