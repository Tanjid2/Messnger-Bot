import asyncio
from datetime import datetime
import os
import aiohttp
from fbchat_asyncio import Client, Message, ThreadType
import yt_dlp
from google import genai

# পরিবেশক চলক (Environment Variables) থেকে সিক্রেট তথ্যগুলো নেওয়া হবে
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FB_EMAIL = os.environ.get("FB_EMAIL")
FB_PASSWORD = os.environ.get("FB_PASSWORD")
GROUP_THREAD_ID = os.environ.get("GROUP_THREAD_ID", "আপনার_গ্রুপের_আইডি_এখানে_দিন")

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

# সিলেটের আজকের আবহাওয়া আনার ফাংশন
async def get_sylhet_weather():
    try:
        url = "https://wttr.in/Sylhet?format=3"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    return text.strip()
    except Exception:
        pass
    return "আবহাওয়া তথ্য পাওয়া যায়নি।"

# সিলেটের আজানের সঠিক সময় আনার ফাংশন
async def get_sylhet_prayer_times():
    try:
        url = "http://api.aladhan.com/v1/timingsByCity?city=Sylhet&country=Bangladesh&method=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    timings = data['data']['timings']
                    return {
                        "Fajr": timings.get("Fajr"),
                        "Dhuhr": timings.get("Dhuhr"),
                        "Asr": timings.get("Asr"),
                        "Maghrib": timings.get("Maghrib"),
                        "Isha": timings.get("Isha")
                    }
    except Exception:
        pass
    return None

class MessengerBot(Client):
    async def on_people_added(self, added_ids, author_id, thread_id, **kwargs):
        for user_id in added_ids:
            if user_id != self.uid:
                welcome_msg = "🎉 'খাইয়া খাম আছে' গ্রুপে স্বাগতম! এখানে আমরা সবাই ভোজনরসিক আর আড্ডাবাজ। আশা করি আপনিও আমাদের দলের একজন হয়ে উঠবেন। তবে সাবধান! এই গ্রুপে আড্ডা দিতে দিতে হঠাৎ খিদে বেড়ে গেলে কিন্তু আমরা দায়ী না! 😉"
                await self.send(Message(text=welcome_msg), thread_id=thread_id, thread_type=ThreadType.GROUP)

    async def on_people_removed(self, removed_id, author_id, thread_id, **kwargs):
        if removed_id != self.uid:
            leave_msg = "🥺 আপনি আমাদের ছেড়ে চলে যাচ্ছেন শুনে খুব খারাপ লাগছে। 'খাইয়া খাম আছে' গ্রুপটা আপনাকে অনেক মিস করবে। আমাদের আড্ডার টেবিলটা আপনার জন্য আজ একটু খালি হয়ে গেল। যেখানেই যান, ভালো থাকবেন—আমাদের সাথে আপনার দেখা যেন আবার হয়!"
            await self.send(Message(text=leave_msg), thread_id=thread_id, thread_type=ThreadType.GROUP)

    async def on_message(self, author_id, message_object, thread_id, thread_type, **kwargs):
        if author_id == self.uid:
            return
        text = message_object.text
        if not text:
            return

        if text.startswith("!play "):
            song = text.replace("!play ", "")
            await self.send(Message(text=f"🔍 '{song}' গানটি খোঁজা হচ্ছে..."), thread_id=thread_id, thread_type=thread_type)
            url = get_audio_url(song)
            if url:
                await self.send(Message(text=f"🎶 আপনার গান: {url}"), thread_id=thread_id, thread_type=thread_type)
            else:
                await self.send(Message(text="❌ গানটি পাওয়া যায়নি!"), thread_id=thread_id, thread_type=thread_type)
        
        elif text == "!weather":
            weather = await get_sylhet_weather()
            await self.send(Message(text=f"🌤️ সিলেটের বর্তমান আবহাওয়া:\n{weather}"), thread_id=thread_id, thread_type=thread_type)

        elif text == "!namaz":
            times = await get_sylhet_prayer_times()
            if times:
                msg = (
                    f"🕌 সিলেটের আজকের নামাজের সময়সূচি:\n"
                    f"• ফজর: {times['Fajr']}\n"
                    f"• যোহর: {times['Dhuhr']}\n"
                    f"• আসর: {times['Asr']}\n"
                    f"• মাগরিব: {times['Maghrib']}\n"
                    f"• এশা: {times['Isha']}"
                )
                await self.send(Message(text=msg), thread_id=thread_id, thread_type=thread_type)
            else:
                await self.send(Message(text="❌ নামাজের সময়সূচি আনতে সমস্যা হয়েছে।"), thread_id=thread_id, thread_type=thread_type)
        else:
            reply = get_ai_response(text)
            await self.send(Message(text=reply), thread_id=thread_id, thread_type=thread_type)

    async def daily_weather_task(self):
        await self.wait_until_ready()
        sent_today = False
        while not self.is_closed:
            now = datetime.now()
            if now.hour == 10 and now.minute == 0:
                if not sent_today:
                    weather = await get_sylhet_weather()
                    msg = f"🌅 সুপ্রভাত! সিলেটের আজকের সকালের আবহাওয়া আপডেট:\n{weather}\nআজ সারাদিন কেমন যাবে, দেখে নিন!"
                    if GROUP_THREAD_ID != "আপনার_গ্রুপের_আইডি_এখানে_দিন":
                        await self.send(Message(text=msg), thread_id=GROUP_THREAD_ID, thread_type=ThreadType.GROUP)
                    sent_today = True
                    await asyncio.sleep(60)
            else:
                sent_today = False
            await asyncio.sleep(30)

async def main():
    bot = MessengerBot()
    print("বট লগইন হচ্ছে...")
    await bot.login(FB_EMAIL, FB_PASSWORD)
    asyncio.create_task(bot.daily_weather_task())
    print("বট সফলভাবে চালু হয়েছে এবং মেসেজের জন্য প্রস্তুত!")
    await bot.listen()

if __name__ == "__main__":
    asyncio.run(main())
