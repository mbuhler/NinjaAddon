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
        channel = client.get_channel(channel_id)
        if channel:
            # Basic formatting based on type
            if type == "trade_alert":
                embed = discord.Embed(title="Trade Alert", description=content, color=0x00ff00)
            elif type == "agent_override":
                embed = discord.Embed(title="Agent Override", description=content, color=0xffa500)
            elif type == "drawdown_warning":
                embed = discord.Embed(title="Drawdown Warning", description=content, color=0xff0000)
            elif type == "performance_update":
                embed = discord.Embed(title="Performance Update", description=content, color=0x0000ff)
            else:
                embed = discord.Embed(title="General Notification", description=content, color=0x808080)

            await channel.send(embed=embed)
        await client.close()

    try:
        client.run(token)
    except Exception as e:
        print(f"Error sending Discord message: {e}")
