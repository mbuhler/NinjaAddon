import discord
import os
from dotenv import load_dotenv

load_dotenv()

def send_discord_message(type: str, content: str):
    if os.getenv("ENABLE_DISCORD_NOTIFICATIONS", "false").lower() != "true":
        return

    token = os.getenv("DISCORD_BOT_TOKEN")
    channel_id = int(os.getenv("DISCORD_CHANNEL_ID"))

    if not token or not channel_id:
        print("Warning: Discord bot token or channel ID not set. Cannot send notification.")
        return

    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'{client.user} has connected to Discord!')

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        if isinstance(message.channel, discord.DMChannel):
            # This is a placeholder for the actual query processing logic.
            # A real implementation would parse the message, query the memory,
            # and generate a response.
            response = f"I received your message: '{message.content}'. I am not yet smart enough to answer your questions."
            await message.channel.send(response)

    # The existing send_discord_message functionality can be moved to a separate
    # function or integrated into the on_ready event. For simplicity, we will
    # leave it as is, but it will not be used in this new implementation.

    try:
        client.run(token)
    except Exception as e:
        print(f"Error sending Discord message: {e}")
