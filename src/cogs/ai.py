import discord
from discord.ext import commands
from google import genai
import os
import time
from collections import defaultdict
from core.logger_config import logger

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.client = genai.Client(api_key=self.gemini_key) if self.gemini_key else None
        self.user_cooldowns = defaultdict(float)
        self.cooldown_seconds = 10

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        bot_mention = f'<@{self.bot.user.id}>'
        bot_mention_nick = f'<@!{self.bot.user.id}>'
        content = message.content.lower()

        if (message.content.startswith(bot_mention) or message.content.startswith(bot_mention_nick)) and 'hello' in content:
            current_time = time.time()
            if current_time - self.user_cooldowns[message.author.id] < self.cooldown_seconds:
                return

            if not self.client:
                return

            try:
                prompt = message.content.lower().split('hello', 1)[1].strip() or "Halo!"
                async with message.channel.typing():
                    response = self.client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                    await message.reply(response.text)
                self.user_cooldowns[message.author.id] = current_time
            except Exception as e:
                logger.error(f"AI Error: {e}")

async def setup(bot):
    await bot.add_cog(AI(bot))
