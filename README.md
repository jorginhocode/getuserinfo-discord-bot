# getuserinfo-discord-bot
Feature for Discord bots that displays detailed profile information of any user.

## Features

- Basic Account Info: Account type, mention, username, global name, ID, and creation date
- Official Badges: Displays all Discord badges the user has earned
- Clan Information: Complete clan and primary guild data with tags and badge assets
- Status & Activities: Real-time presence and custom status messages
- Server Context: Join date and roles when in same server
- Visual Assets: Direct clickable links to avatars, banners, and avatar decorations

## Requirements

System Requirements:
- Python 3.8 or higher
- discord.py library
- python-dotenv
- aiohttp

Bot Configuration:
- Discord Bot Token stored in .env file as DISCORD_TOKEN
- Bot Intents enabled in Discord Developer Portal:
  - Message Content Intent
  - Server Members Intent
  - Presence Intent

Emoji Setup:
- Each Discord badge icon must be uploaded to your server as custom emojis
- Replace the emoji IDs in the code with your server's custom emoji IDs
- Required badge emojis: Staff, Partner, HypeSquad, Bug Hunter, Early Supporter, Developer, Moderator, Active Developer, and HypeSquad Bravery/Brilliance/Balance

![getuserinfo-discord-bot](/preview.png)
