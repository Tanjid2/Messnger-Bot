import asyncio
from datetime import datetime
import os
import aiohttp
from fbchat import Client, Message
import yt_dlp
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FB_EMAIL = os.environ.get("FB_EMAIL")
FB_PASSWORD = os.environ.get("FB_PASSWORD")

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

class MessengerBot(Client):
    def on_message(self, author_id, message_object, thread_id, thread_type, **kwargs):
        if author_id == self.uid:
            return
        text = message_object.text
        if not text:
            return

        if text.startswith("!play "):
            song = text.replace("!play ", "")
            self.send(Message(text=f"🔍 '{song}' গানটি খোঁজা হচ্ছে..."), thread_id=thread_id, thread_type=thread_type)
            url = get_audio_url(song)
            if url:
                self.send(Message(text=f"🎶 আপনার গান: {url}"), thread_id=thread_id, thread_type=thread_type)
            else:
                self.send(Message(text="❌ গানটি পাওয়া যায়নি!"), thread_id=thread_id, thread_type=thread_type)
        else:
            reply = get_ai_response(text)
            self.send(Message(text=reply), thread_id=thread_id, thread_type=thread_type)

def main():
    print("বট লগইন হচ্ছে...")
    # এখানে email= বা password= কিওয়ার্ড বাদ দিয়ে সরাসরি পাস করা হয়েছে
    bot = MessengerBot(FB_EMAIL, FB_PASSWORD)
    print("বট সফলভাবে চালু হয়েছে এবং মেসেজের জন্য প্রস্তুত!")
    bot.listen()

if __name__ == "__main__":
    main()
