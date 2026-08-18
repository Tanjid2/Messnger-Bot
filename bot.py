import asyncio
from datetime import datetime
import os
import aiohttp
from google import genai
import yt_dlp

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
ai_client = genai.Client(api_key=GEMINI_API_KEY)

def get_audio_url(song_name):
    ydl_opts = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{song_name}", download=False)
            if 'entries' in info and len(info['entries']) > 0:
                return info['entries'][0]['url']
    except Exception as e:
        return None

def get_ai_response(prompt):
    try:
        response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return response.text
    except Exception as e:
        return "আমি এখন উত্তর দিতে পারছি না।"

def main():
    print("বট সফলভাবে চালু হয়েছে এবং এআই মোডে প্রস্তুত রয়েছে!")
    # Render সার্ভার যেন বন্ধ না হয়ে যায় সেজন্য লুপ চালিয়ে রাখা হলো
    while True:
        pass

if __name__ == "__main__":
    main()
