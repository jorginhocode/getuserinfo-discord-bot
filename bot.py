import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import aiohttp
import json
from datetime import datetime, timezone

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Constants
BADGE_EMOJIS = {
    1 << 0: "<:staff:1434657967659155578>",
    1 << 1: "<:partner:1434657966111330335>",
    1 << 2: "<:hypesquad:1434657982653923469>",
    1 << 3: "<:bughunter1:1434657958108725469>",
    1 << 6: "<:bravery:1434657977939267644>",
    1 << 7: "<:brilliance:1434657980212707350>",
    1 << 8: "<:balance:1434657970180067459>",
    1 << 9: "<:earlysupporter:1434657961690665142>",
    1 << 14: "<:bughunter2:1434657959841108050>",
    1 << 17: "<:developer:1434657956108173523>",
    1 << 18: "<:moderator:1434657963913642034>",
    1 << 22: "<:activedeveloper:1434657953453047858>",
}
STATUS_DISPLAY = {
    'online': 'Online',
    'idle': 'Idle',
    'dnd': 'Do Not Disturb',
    'offline': 'Offline'
}

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True
intents.presences = True
intents.reactions = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

def create_footer() -> str:
    """Create standardized footer text."""
    return f"by @potyhx  •  {datetime.now().strftime('Today at %H:%M')}"

def get_user_display_name(user):
    """Get the best display name for a user (global name if available, else username#discriminator)"""
    if hasattr(user, 'global_name') and user.global_name:
        return f"{user.global_name} ({user.name})"
    return f"{user.name}#{user.discriminator}"

def format_date(dt) -> str:
    """Format datetime object to readable string."""
    return dt.strftime("%B %d, %Y %I:%M %p") if dt else "Unknown"

async def get_user_complete_info_api(user_id: int) -> dict:
    """Get complete user information via direct API call."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://discord.com/api/v10/users/{user_id}",
                headers={"Authorization": f"Bot {TOKEN}"}
            ) as response:
                return await response.json() if response.status == 200 else {}
    except Exception as e:
        print(f"Error fetching user info via API: {e}")
        return {}

async def get_user_badges_with_emojis(public_flags: int) -> str:
    """Get user badges with custom emojis displayed horizontally."""
    if not public_flags:
        return "**No badges**"
    user_badges = [
        emoji for flag, emoji in BADGE_EMOJIS.items() 
        if public_flags & flag
    ]
    return f">>> {''.join(user_badges)}" if user_badges else "**No badges**"

async def get_member_info(interaction: discord.Interaction, target_user: discord.User) -> tuple:
    """Get server-specific member information."""
    if not interaction.guild:
        return None, None
    target_member = interaction.guild.get_member(target_user.id)
    if not target_member:
        return None, None
    joined_date = format_date(target_member.joined_at)
    roles = [role.name for role in target_member.roles[1:]]
    roles_text = ", ".join(roles) if roles else "None"
    server_text = (
        f">>> **Found in Server:** {interaction.guild.name}\n"
        f"**Joined Server:** `{joined_date}`\n"
        f"**Roles:** {roles_text}"
    )
    return server_text, target_member

async def get_status_activity(target_member: discord.Member) -> str:
    """Get member status and custom activity."""
    if not target_member:
        return ""
    status_text = STATUS_DISPLAY.get(str(target_member.status), 'Offline')
    custom_status = next(
        (activity.name for activity in target_member.activities 
         if isinstance(activity, discord.CustomActivity)),
        None
    )
    status_activity_text = f">>> **Status:** {status_text}\n"
    if custom_status:
        status_activity_text += f"**Custom Status:** {custom_status}"
    return status_activity_text

async def get_decorative_items(api_data: dict, target_user: discord.User) -> tuple:
    """Get avatar, banner and decoration links."""
    avatar_hash = api_data.get('avatar')
    avatar_url = (f"https://cdn.discordapp.com/avatars/{target_user.id}/{avatar_hash}.png?size=1024" 
                 if avatar_hash else target_user.display_avatar.url)
    avatar_link = f"[**Avatar**]({avatar_url})"
    banner_hash = api_data.get('banner')
    banner_url = f"https://cdn.discordapp.com/banners/{target_user.id}/{banner_hash}.png?size=1024" if banner_hash else None
    banner_link = f"[**Banner**]({banner_url})" if banner_url else "**No banner**"
    decoration_data = api_data.get('avatar_decoration_data')
    decoration_link = "**No avatar decoration**"
    if decoration_data and decoration_data.get('asset'):
        decoration_asset = decoration_data['asset']
        decoration_url = f"https://cdn.discordapp.com/avatar-decorations/{target_user.id}/{decoration_asset}.png"
        decoration_link = f"[**Avatar Decoration**]({decoration_url})"
    return avatar_link, banner_link, decoration_link, avatar_url, banner_url

async def get_clan_info(api_data: dict) -> str:
    """Get clan information from API data."""
    clan_data = api_data.get('clan') or api_data.get('primary_guild')
    if not clan_data:
        return "**No Clan Tag**"
    clan_info_parts = []
    if clan_tag := clan_data.get('tag'):
        clan_info_parts.append(f"> **Tag:** {clan_tag}")
    if guild_id := clan_data.get('identity_guild_id'):
        clan_info_parts.append(f"> **Server ID:** `{guild_id}`")
    if badge_hash := clan_data.get('badge'):
        if guild_id:
            badge_url = f"https://cdn.discordapp.com/clan-badges/{guild_id}/{badge_hash}.png"
            clan_info_parts.append(f"> **[Badge]({badge_url})**")
        else:
            clan_info_parts.append(f"> **Badge Hash:** {badge_hash}")
    return "\n".join(clan_info_parts) if clan_info_parts else "**No Clan Tag**"

@bot.tree.command(name="getuserinfo", description="Get detailed information about a user.")
async def getuserinfo(interaction: discord.Interaction, user: discord.User = None):
    target_user = user or interaction.user
    api_data = await get_user_complete_info_api(target_user.id)
    if not api_data:
        await interaction.response.send_message("Error: Could not fetch user data.", ephemeral=True)
        return
    
    # Basic user info
    account_type = "Bot Account" if target_user.bot else "User Account"
    discriminator_text = f"**Discriminator:** `#{target_user.discriminator}`\n" if hasattr(target_user, 'discriminator') and target_user.discriminator != '0' else ""
    global_name = api_data.get('global_name')
    global_name = "None" if not global_name or global_name == target_user.name else global_name
    info_text = (
        f">>> **Type:** {account_type}\n"
        f"**Mention:** {target_user.mention}\n"
        f"**Username:** {target_user.name}\n"
        f"{discriminator_text}"
        f"**Global Name:** {global_name}\n"
        f"**User ID:** `{target_user.id}`\n"
        f"**Account Created:** `{format_date(target_user.created_at)}`"
    )
    
    # Get additional information
    server_text, target_member = await get_member_info(interaction, target_user)
    status_activity_text = await get_status_activity(target_member)
    avatar_link, banner_link, decoration_link, avatar_url, banner_url = await get_decorative_items(api_data, target_user)
    badges_text = await get_user_badges_with_emojis(api_data.get('public_flags', 0))
    clan_text = await get_clan_info(api_data)
    decorative_text = f">>> {avatar_link}\n{banner_link}\n{decoration_link}"
    
    # Create embed
    embed = discord.Embed(title="User Information", color=discord.Color.from_rgb(88, 101, 242))
    # Add fields conditionally
    embed.add_field(name="General Info", value=info_text, inline=False)
    if badges_text != "**No badges**":
        embed.add_field(name="Badges", value=badges_text, inline=False)
    if clan_text != "**No Clan Tag**":
        embed.add_field(name="Clan Info", value=clan_text, inline=False)
    if status_activity_text.strip():
        embed.add_field(name="Status & Activities", value=status_activity_text, inline=False)
    if server_text:
        embed.add_field(name="Server Info", value=server_text, inline=False)
    embed.add_field(name="Decorative Items", value=decorative_text, inline=False)
    
    # Set images and footer
    embed.set_thumbnail(url=avatar_url)
    if banner_url:
        embed.set_image(url=banner_url)
    embed.set_footer(text=create_footer(), icon_url=bot.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    print("Synchronizing commands...")
    try:
        synced = await bot.tree.sync()
        print(f"Synchronized {len(synced)} commands:")
        for cmd in synced:
            print(f" - /{cmd.name}")
    except Exception as e:
        print(f"Error synchronizing: {e}")
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.custom,
            name="Custom Status",
            state="/getuserinfo"
        ),
        status=discord.Status.online
    )
    print(f"Bot connected as {bot.user}")

bot.run(TOKEN)