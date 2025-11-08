#!/usr/bin/env python3
"""Script to find Discord channel ID by name using bot token"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def find_channel(channel_name: str):
    """Find channel ID by name using Discord API"""
    try:
        import hikari

        token = os.getenv("DISCORD_BOT_TOKEN")
        if not token:
            print("ERROR: DISCORD_BOT_TOKEN not found in .env")
            return None

        # Create REST client
        rest = hikari.RESTApp()

        # Start the REST app
        await rest.start()

        try:
            async with rest.acquire(token, token_type=hikari.TokenType.BOT) as client:
                # Get all guilds the bot is in
                guilds = await client.fetch_my_guilds()

                print(f"\n🔍 Searching for channel: '{channel_name}'")
                print(f"📊 Found {len(guilds)} guild(s)\n")

                for guild in guilds:
                    print(f"Guild: {guild.name} (ID: {guild.id})")

                    # Get all channels in this guild
                    channels = await client.fetch_guild_channels(guild.id)

                    for channel in channels:
                        # Check if it's a text channel and matches name
                        if hasattr(channel, 'name'):
                            if channel.name.lower() == channel_name.lower():
                                print(f"✅ FOUND: #{channel.name}")
                                print(f"   Channel ID: {channel.id}")
                                print(f"   Type: {channel.type}")
                                return channel.id
                            else:
                                # Show all channels for reference
                                print(f"   - #{channel.name} (ID: {channel.id})")

                print(f"\n❌ Channel '{channel_name}' not found in any guild")
                return None
        finally:
            await rest.close()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    channel_name = sys.argv[1] if len(sys.argv) > 1 else "deep-research"
    channel_id = asyncio.run(find_channel(channel_name))

    if channel_id:
        print(f"\n✨ Add this to your .env file:")
        print(f"PLUGIN_DEEP_RESEARCH_CHANNEL_ID={channel_id}")
