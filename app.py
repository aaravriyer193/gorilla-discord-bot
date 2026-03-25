import os
import discord
import aiohttp
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = "openai/gpt-oss-120b:free" 

SIGNATURE = """

---
*Note: This bot was made by Gor://a Builder's team to assist people with code bugs and share the power of AI agents with the world. https://gorillabuilder.dev will be launching soon, for more information, read https://forum-bot.gorillabuilder.dev. if you would like to become a beta tester for the product or have any queries, mail support@gorillabuilder.dev, and we will give you the necessary details.*"""

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

async def generate_answer(question: str) -> str:
    """Passes the Discord question via OpenRouter asynchronously."""
    system_prompt = (
        "You are an expert, highly helpful senior web developer called Gor://a made by a small team building a top secret AI coding agent that will release soon. "
        "A user in a Discord server is asking a programming question or posting a bug. "
        "Provide a direct, highly accurate, and friendly answer. "
        "Include code snippets in markdown if relevant. Do NOT add any promotional text yourself."
    )
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://gorillabuilder.dev",
        "X-Title": "Gorilla Discord Agent",
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "temperature": 0.4
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data["choices"][0]["message"]["content"]
            else:
                error_text = await response.text()
                print(f"❌ OpenRouter Error: {error_text}")
                return "I am temporarily overloaded and I couldn't process that. Try again in a minute!"

@client.event
async def on_ready():
    print(f"🚀 {client.user} has connected to Discord! Proactive listening is ON.")

@client.event
async def on_message(message):
    # 1. Ignore the bot's own messages
    if message.author == client.user:
        return

    content_lower = message.content.lower()

    # 2. Check for Direct Triggers (@mention or plain text "Gorilla Helper")
    is_mentioned = client.user in message.mentions
    is_named = "gorilla helper" in content_lower
    
    # 3. Check for Passive Triggers (Finding threads on its own)
    # We require BOTH a "help" phrase AND a "tech" phrase so it doesn't spam gamers.
    help_phrases = ["how do i fix", "getting an error", "this bug", "help me with", "why is my code"]
    
    is_asking_for_help = any(hp in content_lower for hp in help_phrases)

    # 4. If any condition is met, execute the swarm
    if is_mentioned or is_named or is_asking_for_help:
        
        # Clean the prompt (remove bot ID if they @mentioned it)
        clean_question = message.content.replace(f'<@{client.user.id}>', '').strip()
        
        # Determine why it triggered for the terminal log
        trigger_reason = "Directly Asked" if (is_mentioned or is_named) else "Found Thread"
        print(f"\n🔔 [{trigger_reason}] Question from {message.author.name} in #{message.channel.name}")
        
        async with message.channel.typing():
            try:
                # Add a tiny artificial delay if it found the thread passively, 
                # so it doesn't feel like a creepy instant auto-reply
                if trigger_reason == "Found Thread":
                    await asyncio.sleep(0.1)

                ai_response = await generate_answer(clean_question)
                final_reply = ai_response + SIGNATURE
                
                # Discord 2000 character limit safety net
                if len(final_reply) > 2000:
                    await message.reply(final_reply[:1990] + "...") 
                else:
                    await message.reply(final_reply)
                    
                print(f"✅ Successfully replied to {message.author.name}")
                
            except Exception as e:
                print(f"❌ Error replying to message: {e}")

# Start the bot
client.run(DISCORD_TOKEN)
