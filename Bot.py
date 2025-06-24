import asyncio
import logging
import os
import tempfile
import random
from io import BytesIO
import aiohttp
import aiofiles
import edge_tts
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, TextClip
from PIL import Image, ImageDraw, ImageFont
import requests
import json

# Налаштування
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN", "YOUR_HUGGINGFACE_TOKEN_HERE")

# API endpoints
STABLE_DIFFUSION_API = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
TEXT_GENERATION_API = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"

# Ініціалізація бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Налаштування логування
logging.basicConfig(level=logging.INFO)

class HorrorVideoGenerator:
    def __init__(self):
        self.horror_prompts = [
            "A dark abandoned house at midnight with glowing windows",
            "Creepy forest with twisted trees and fog",
            "Old cemetery with weathered tombstones and mist",
            "Haunted mansion with broken windows and ivy",
            "Dark alley with flickering streetlight",
            "Abandoned hospital corridor with flickering lights",
            "Old church at night with storm clouds",
            "Foggy swamp with dead trees"
        ]
        
        self.horror_stories_templates = [
            "В старому будинку на краю міста...",
            "Минулої ночі я почув дивні звуки...", 
            "Коли я зайшов у покинуту лікарню...",
            "На цвинтарі о півночі...",
            "У темному лісі я побачив...",
            "Старий дзеркало в антикварній крамниці...",
            "Телефонний дзвінок о 3:33 ранку...",
            "Підвал старого будинку приховував..."
        ]

    async def generate_horror_story(self):
        """Генерує страшну історію"""
        template = random.choice(self.horror_stories_templates)
        
        # Простий генератор історій (можна замінити на ШІ)
        story_parts = [
            "темнота огортала все навкруги",
            "раптово почулися кроки за спиною", 
            "холодний вітер пронизав до кісток",
            "тіні почали рухатися самі по собі",
            "дзеркало відображало не те, що мало",
            "двері почали скриплячи відчинятися",
            "очі спостерігали з темряви",
            "час ніби зупинився"
        ]
        
        story = template + " " + ". ".join(random.sample(story_parts, 3)) + "."
        return story

    async def generate_image(self, prompt):
        """Генерує зображення через Hugging Face API"""
        headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}
        
        # Додаємо horror стиль до промпту
        enhanced_prompt = f"horror, scary, dark, {prompt}, cinematic lighting, detailed"
        
        payload = {"inputs": enhanced_prompt}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(STABLE_DIFFUSION_API, headers=headers, json=payload) as response:
                if response.status == 200:
                    image_bytes = await response.read()
                    return Image.open(BytesIO(image_bytes))
                else:
                    # Fallback - створюємо просте темне зображення
                    return self.create_fallback_image()

    def create_fallback_image(self):
        """Створює fallback зображення якщо API недоступне"""
        img = Image.new('RGB', (1024, 1024), color='black')
        draw = ImageDraw.Draw(img)
        
        # Додаємо простий scary текст
        try:
            font = ImageFont.truetype("arial.ttf", 60)
        except:
            font = ImageFont.load_default()
            
        draw.text((512, 512), "HORROR", fill='red', anchor='mm', font=font)
        return img

    async def text_to_speech(self, text, output_path):
        """Перетворює текст в мову через Edge-TTS"""
        # Використовуємо українську мову з похмурим голосом
        voice = "uk-UA-OstapNeural"  # або "uk-UA-PolinaNeural"
        
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

    async def create_video(self, image_path, audio_path, story_text, output_path):
        """Створює відео з зображення, аудіо та тексту"""
        try:
            # Завантажуємо компоненти
            image_clip = ImageClip(image_path)
            audio_clip = AudioFileClip(audio_path)
            
            # Встановлюємо тривалість відео за аудіо
            video_duration = audio_clip.duration
            image_clip = image_clip.set_duration(video_duration)
            
            # Додаємо текст як субтитри
            txt_clip = TextClip(story_text, 
                              fontsize=30, 
                              color='white', 
                              stroke_color='black',
                              stroke_width=2,
                              size=(800, None),
                              method='caption').set_position('center').set_duration(video_duration)
            
            # Створюємо фінальну композицію
            video = CompositeVideoClip([image_clip, txt_clip])
            video = video.set_audio(audio_clip)
            
            # Експортуємо відео
            video.write_videofile(output_path, 
                                fps=24, 
                                codec='libx264',
                                audio_codec='aac',
                                temp_audiofile='temp-audio.m4a',
                                remove_temp=True)
            
            # Очищуємо пам'ять
            video.close()
            audio_clip.close()
            
        except Exception as e:
            logging.error(f"Error creating video: {e}")
            raise

# Ініціалізуємо генератор
generator = HorrorVideoGenerator()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "👻 Привіт! Я бот для створення страшних відео для TikTok!\n\n"
        "Команди:\n"
        "/horror - створити страшне відео\n"
        "/help - допомога"
    )

@dp.message(Command("help"))
async def help_handler(message: types.Message):
    await message.answer(
        "🎬 Як користуватися ботом:\n\n"
        "1. Натисни /horror для створення відео\n"
        "2. Зачекай кілька хвилин поки я створю твоє страшне відео\n"
        "3. Отримай готове відео для TikTok!\n\n"
        "⚠️ Створення може зайняти 1-3 хвилини"
    )

@dp.message(Command("horror"))
async def create_horror_video(message: types.Message):
    status_msg = await message.answer("🎬 Починаю створення страшного відео...")
    
    try:
        # 1. Генеруємо історію
        await status_msg.edit_text("📝 Генерую страшну історію...")
        story = await generator.generate_horror_story()
        
        # 2. Генеруємо зображення
        await status_msg.edit_text("🖼️ Створюю страшне зображення...")
        prompt = random.choice(generator.horror_prompts)
        image = await generator.generate_image(prompt)
        
        # 3. Створюємо тимчасові файли
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = os.path.join(temp_dir, "horror_image.png")
            audio_path = os.path.join(temp_dir, "horror_audio.wav")
            video_path = os.path.join(temp_dir, "horror_video.mp4")
            
            # Зберігаємо зображення
            image.save(image_path)
            
            # 4. Генеруємо аудіо
            await status_msg.edit_text("🎤 Озвучую історію...")
            await generator.text_to_speech(story, audio_path)
            
            # 5. Створюємо відео
            await status_msg.edit_text("🎞️ Монтую відео...")
            await generator.create_video(image_path, audio_path, story, video_path)
            
            # 6. Надсилаємо готове відео
            await status_msg.edit_text("📤 Надсилаю готове відео...")
            
            async with aiofiles.open(video_path, 'rb') as video_file:
                video_data = await video_file.read()
                
            await message.answer_video(
                video=types.BufferedInputFile(video_data, filename="horror_video.mp4"),
                caption=f"👻 Твоє страшне відео готове!\n\n📖 Історія: {story[:100]}..."
            )
            
    except Exception as e:
        logging.error(f"Error creating horror video: {e}")
        await message.answer("❌ Помилка при створенні відео. Спробуй ще раз!")
    
    finally:
        await status_msg.delete()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
