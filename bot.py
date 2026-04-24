import discord
from discord import app_commands
import json
import os
import random
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.invites = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

def load_data():
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

def has_role(interaction, roles):
    return any(role.name in roles for role in interaction.user.roles)

def get_balance(data, user_id):
    user_id = str(user_id)
    if "economy" not in data:
        data["economy"] = {}
    if user_id not in data["economy"]:
        data["economy"][user_id] = {"coins": 0, "inventory": [], "message_count": 0}
    return data["economy"][user_id]["coins"]

def add_coins(data, user_id, amount):
    user_id = str(user_id)
    if "economy" not in data:
        data["economy"] = {}
    if user_id not in data["economy"]:
        data["economy"][user_id] = {"coins": 0, "inventory": [], "message_count": 0}
    data["economy"][user_id]["coins"] += amount

def remove_coins(data, user_id, amount):
    user_id = str(user_id)
    if "economy" not in data:
        data["economy"] = {}
    if user_id not in data["economy"]:
        data["economy"][user_id] = {"coins": 0, "inventory": [], "message_count": 0}
    data["economy"][user_id]["coins"] = max(0, data["economy"][user_id]["coins"] - amount)

OWNER = ["Owner"]
CO_OWNER = ["Owner", "Co Owner"]
EMBED_ROLES = ["Owner", "Co Owner", "Trial Co Owner", "Chief Manager"]
REMOVE_VOUCH_ROLES = ["Owner", "Co Owner", "Trial Co Owner", "Chief Manager", "Head Manager"]
MANAGER = ["Owner", "Co Owner", "Trial Co Owner", "Chief Manager", "Head Manager", "Senior Manager", "Manager", "Trial Manager"]
ADMIN = ["Owner", "Co Owner", "Trial Co Owner", "Chief Manager", "Head Manager", "Senior Manager", "Manager", "Trial Manager", "Chief Admin", "Head Admin", "Senior Admin", "Admin", "Trial Admin"]

ROLE_HIERARCHY = [
    "Community Member", "Trial Staff", "Staff Team", "Trial Support",
    "Support Team", "Head Of Support", "Chief Of Support", "Trial Moderator",
    "Moderator", "Senior Moderator", "Head Moderator", "Chief Moderator",
    "Trial Admin", "Admin", "Senior Admin", "Head Admin", "Chief Admin",
    "Trial Manager", "Manager", "Senior Manager", "Head Manager", "Chief Manager",
    "Trial Co Owner", "Co Owner", "Owner"
]

SHOP_ITEMS = [
    {"id": "100m_brainrot", "name": "100m Brainrot", "price": 700},
    {"id": "125m_brainrot", "name": "125m Brainrot", "price": 1000},
    {"id": "150m_brainrot", "name": "150m Brainrot", "price": 1500},
    {"id": "175m_brainrot", "name": "175m Brainrot", "price": 1750},
    {"id": "200m_brainrot", "name": "200m Brainrot", "price": 2000},
    {"id": "200m_plus_brainrot", "name": "200m+ Brainrot", "price": 2500},
    {"id": "rare_brainrot", "name": "Rare Brainrot", "price": 4000},
]

CLAIMS_CHANNEL = "📂｜𝑪𝒍𝒂𝒊𝒎 𝑹𝒆𝒒𝒖𝒆𝒔𝒕 𝑳𝒐𝒈𝒔"
REMOVE_VOUCH_LOG = "📂｜𝑹𝒆𝒎𝒐𝒗𝒆 𝑽𝒐𝒖𝒄𝒉𝒆𝒔 𝑳𝒐𝒈𝒔"

# ============ EVENTS ============

@client.event
async def on_ready():
    guild = discord.Object(id=1483171842251297052)
    tree.copy_global_to(guild=guild)
    try:
        synced = await tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands!")
    except Exception as e:
        print(f"Error: {e}")
    print(f"Launchly is online! Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return
    data = load_data()
    user_id = str(message.author.id)
    if "economy" not in data:
        data["economy"] = {}
    if user_id not in data["economy"]:
        data["economy"][user_id] = {"coins": 0, "inventory": [], "message_count": 0}
    if "message_count" not in data["economy"][user_id]:
        data["economy"][user_id]["message_count"] = 0
    data["economy"][user_id]["message_count"] += 1
    if data["economy"][user_id]["message_count"] >= 10:
        data["economy"][user_id]["coins"] += 1
        data["economy"][user_id]["message_count"] = 0
    save_data(data)

@client.event
async def on_member_join(member):
    data = load_data()
    invites_after = await member.guild.invites()
    if "invites" not in data:
        data["invites"] = {}
    for invite in invites_after:
        old_uses = data["invites"].get(str(invite.code), 0)
        if invite.uses > old_uses:
            add_coins(data, invite.inviter.id, 10)
            data["invites"][str(invite.code)] = invite.uses
            break
    save_data(data)

# ============ BUTTONS ============

class ClaimButton(discord.ui.View):
    def __init__(self, claimer: discord.Member, item_name: str):
        super().__init__(timeout=None)
        self.claimer = claimer
        self.item_name = item_name

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.green, emoji="🎟️")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.name in ["Owner", "Co Owner"] for role in interaction.user.roles):
            await interaction.response.send_message("❌ Only Owners can open tickets!", ephemeral=True)
            return
        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            self.claimer: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        for role in guild.roles:
            if role.name in ["Owner", "Co Owner"]:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        ticket_channel = await guild.create_text_channel(
            f"claim-{self.claimer.name}",
            overwrites=overwrites
        )
        embed = discord.Embed(title="🎟️ Claim Ticket", color=discord.Color.orange())
        embed.add_field(name="User", value=self.claimer.mention)
        embed.add_field(name="Item", value=self.item_name)
        embed.set_footer(text="An admin will be with you shortly!")
        await ticket_channel.send(embed=embed)
        button.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"✅ Ticket opened! {ticket_channel.mention}", ephemeral=True)

class VouchListButton(discord.ui.View):
    def __init__(self, member: discord.Member, vouchers: list):
        super().__init__(timeout=60)
        self.member = member
        self.vouchers = vouchers

    @discord.ui.button(label="Show List", style=discord.ButtonStyle.blurple, emoji="📋")
    async def show_list(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.vouchers:
            await interaction.response.send_message("❌ No vouches found!", ephemeral=True)
            return
        list_text = "\n".join([f"{i+1}. <@{v}>" for i, v in enumerate(self.vouchers)])
        embed = discord.Embed(title=f"📋 {self.member.display_name}'s Vouch List", color=discord.Color.gold())
        embed.description = list_text
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ============ MODERATION ============

@tree.command(name="ping", description="Test command")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! Launchly is working!")

@tree.command(name="kick", description="Kick a member")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not has_role(interaction, MANAGER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ You can't kick someone with a higher or equal role!", ephemeral=True)
        return
    dm_embed = discord.Embed(title="👢 You have been kicked", color=discord.Color.red())
    dm_embed.add_field(name="Server", value=interaction.guild.name, inline=False)
    dm_embed.add_field(name="Reason", value=reason, inline=False)
    dm_embed.add_field(name="Moderator", value=str(interaction.user), inline=False)
    try:
        await member.send(embed=dm_embed)
    except:
        pass
    await member.kick(reason=reason)
    embed = discord.Embed(title="👢 Member Kicked", color=discord.Color.red())
    embed.add_field(name="Member", value=member.mention, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="ban", description="Ban a member")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not has_role(interaction, CO_OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ You can't ban someone with a higher or equal role!", ephemeral=True)
        return
    dm_embed = discord.Embed(title="🔨 You have been banned", color=discord.Color.dark_red())
    dm_embed.add_field(name="Server", value=interaction.guild.name, inline=False)
    dm_embed.add_field(name="Reason", value=reason, inline=False)
    dm_embed.add_field(name="Moderator", value=str(interaction.user), inline=False)
    try:
        await member.send(embed=dm_embed)
    except:
        pass
    await member.ban(reason=reason)
    embed = discord.Embed(title="🔨 Member Banned", color=discord.Color.dark_red())
    embed.add_field(name="Member", value=member.mention, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="unban", description="Unban a user by ID")
async def unban(interaction: discord.Interaction, user_id: str):
    if not has_role(interaction, CO_OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    user = await client.fetch_user(int(user_id))
    await interaction.guild.unban(user)
    embed = discord.Embed(title="✅ Member Unbanned", color=discord.Color.green())
    embed.add_field(name="User", value=str(user), inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="mute", description="Mute a member")
async def mute(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not has_role(interaction, ADMIN):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    dm_embed = discord.Embed(title="🔇 You have been muted", color=discord.Color.orange())
    dm_embed.add_field(name="Server", value=interaction.guild.name, inline=False)
    dm_embed.add_field(name="Reason", value=reason, inline=False)
    dm_embed.add_field(name="Moderator", value=str(interaction.user), inline=False)
    try:
        await member.send(embed=dm_embed)
    except:
        pass
    role = discord.utils.get(interaction.guild.roles, name="Muted")
    await member.add_roles(role)
    embed = discord.Embed(title="🔇 Member Muted", color=discord.Color.orange())
    embed.add_field(name="Member", value=member.mention, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="unmute", description="Unmute a member")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    if not has_role(interaction, ADMIN):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    role = discord.utils.get(interaction.guild.roles, name="Muted")
    await member.remove_roles(role)
    embed = discord.Embed(title="🔊 Member Unmuted", color=discord.Color.green())
    embed.add_field(name="Member", value=member.mention, inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="warn", description="Warn a member")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    if not has_role(interaction, ADMIN):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    data = load_data()
    if "warns" not in data:
        data["warns"] = {}
    user_id = str(member.id)
    if user_id not in data["warns"]:
        data["warns"][user_id] = []
    data["warns"][user_id].append(reason)
    save_data(data)
    total = len(data["warns"][user_id])
    dm_embed = discord.Embed(title="⚠️ You have been warned", color=discord.Color.yellow())
    dm_embed.add_field(name="Server", value=interaction.guild.name, inline=False)
    dm_embed.add_field(name="Reason", value=reason, inline=False)
    dm_embed.add_field(name="Moderator", value=str(interaction.user), inline=False)
    dm_embed.add_field(name="Total Warnings", value=str(total), inline=False)
    try:
        await member.send(embed=dm_embed)
    except:
        pass
    embed = discord.Embed(title="⚠️ Member Warned", color=discord.Color.yellow())
    embed.add_field(name="Member", value=member.mention, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
    embed.add_field(name="Total Warnings", value=str(total), inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="unwarn", description="Remove last warn from a member")
async def unwarn(interaction: discord.Interaction, member: discord.Member):
    if not has_role(interaction, ADMIN):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    data = load_data()
    user_id = str(member.id)
    if "warns" not in data or user_id not in data["warns"] or not data["warns"][user_id]:
        await interaction.response.send_message(f"❌ {member.mention} has no warnings!")
        return
    data["warns"][user_id].pop()
    save_data(data)
    embed = discord.Embed(title="✅ Warning Removed", color=discord.Color.green())
    embed.add_field(name="Member", value=member.mention, inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="clearwarns", description="Clear all warns from a member")
async def clearwarns(interaction: discord.Interaction, member: discord.Member):
    if not has_role(interaction, ADMIN):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    data = load_data()
    user_id = str(member.id)
    if "warns" in data and user_id in data["warns"]:
        data["warns"][user_id] = []
        save_data(data)
    embed = discord.Embed(title="✅ Warnings Cleared", color=discord.Color.green())
    embed.add_field(name="Member", value=member.mention, inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="lock", description="Lock a channel")
async def lock(interaction: discord.Interaction, channel: discord.TextChannel = None):
    if not has_role(interaction, MANAGER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    channel = channel or interaction.channel
    await channel.set_permissions(interaction.guild.default_role, send_messages=False)
    embed = discord.Embed(title="🔒 Channel Locked", color=discord.Color.red())
    embed.add_field(name="Channel", value=channel.mention, inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="unlock", description="Unlock a channel")
async def unlock(interaction: discord.Interaction, channel: discord.TextChannel = None):
    if not has_role(interaction, MANAGER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    channel = channel or interaction.channel
    await channel.set_permissions(interaction.guild.default_role, send_messages=True)
    embed = discord.Embed(title="🔓 Channel Unlocked", color=discord.Color.green())
    embed.add_field(name="Channel", value=channel.mention, inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="lockall", description="Lock all channels")
async def lockall(interaction: discord.Interaction):
    if not has_role(interaction, MANAGER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    for channel in interaction.guild.text_channels:
        await channel.set_permissions(interaction.guild.default_role, send_messages=False)
    embed = discord.Embed(title="🔒 All Channels Locked", color=discord.Color.red())
    await interaction.response.send_message(embed=embed)

@tree.command(name="unlockall", description="Unlock all channels")
async def unlockall(interaction: discord.Interaction):
    if not has_role(interaction, MANAGER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    for channel in interaction.guild.text_channels:
        await channel.set_permissions(interaction.guild.default_role, send_messages=True)
    embed = discord.Embed(title="🔓 All Channels Unlocked", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@tree.command(name="slowmode", description="Set slowmode for a channel")
async def slowmode(interaction: discord.Interaction, seconds: int, channel: discord.TextChannel = None):
    if not has_role(interaction, ADMIN):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    target = channel or interaction.channel
    await interaction.response.defer()
    await target.edit(slowmode_delay=seconds)
    embed = discord.Embed(title="⏱️ Slowmode Set", color=discord.Color.blue())
    embed.add_field(name="Channel", value=target.mention, inline=False)
    embed.add_field(name="Slowmode", value=f"{seconds} seconds", inline=False)
    await interaction.followup.send(embed=embed)

@tree.command(name="changenickname", description="Change a member's nickname")
async def changenickname(interaction: discord.Interaction, member: discord.Member, nickname: str):
    if not has_role(interaction, ADMIN):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    await member.edit(nick=nickname)
    embed = discord.Embed(title="✏️ Nickname Changed", color=discord.Color.blue())
    embed.add_field(name="Member", value=member.mention, inline=False)
    embed.add_field(name="New Nickname", value=nickname, inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="setlogchannel", description="Set the log channel")
async def setlogchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not has_role(interaction, CO_OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    data = load_data()
    data["log_channel"] = channel.id
    save_data(data)
    embed = discord.Embed(title="📋 Log Channel Set", color=discord.Color.blue())
    embed.add_field(name="Channel", value=channel.mention, inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="grantaccess", description="Grant tester access to a user")
async def grantaccess(interaction: discord.Interaction, member: discord.Member):
    if not has_role(interaction, OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    role = discord.utils.get(interaction.guild.roles, name="Tester")
    await member.add_roles(role)
    embed = discord.Embed(title="✅ Tester Access Granted", color=discord.Color.green())
    embed.add_field(name="Member", value=member.mention, inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="revokeaccess", description="Revoke tester access from a user")
async def revokeaccess(interaction: discord.Interaction, member: discord.Member):
    if not has_role(interaction, OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    role = discord.utils.get(interaction.guild.roles, name="Tester")
    await member.remove_roles(role)
    embed = discord.Embed(title="❌ Tester Access Revoked", color=discord.Color.red())
    embed.add_field(name="Member", value=member.mention, inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="promote", description="Promote a member to the next role")
async def promote(interaction: discord.Interaction, member: discord.Member):
    if not has_role(interaction, OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    member_roles = [role.name for role in member.roles]
    current_index = -1
    for i, role_name in enumerate(ROLE_HIERARCHY):
        if role_name in member_roles:
            current_index = i
    if current_index == -1 or current_index >= len(ROLE_HIERARCHY) - 1:
        await interaction.response.send_message("❌ Can't promote this member!", ephemeral=True)
        return
    next_role_name = ROLE_HIERARCHY[current_index + 1]
    next_role = discord.utils.get(interaction.guild.roles, name=next_role_name)
    current_role = discord.utils.get(interaction.guild.roles, name=ROLE_HIERARCHY[current_index])
    if next_role and current_role:
        await member.remove_roles(current_role)
        await member.add_roles(next_role)
        embed = discord.Embed(title="⬆️ Member Promoted", color=discord.Color.green())
        embed.add_field(name="Member", value=member.mention, inline=False)
        embed.add_field(name="New Role", value=next_role_name, inline=False)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ Role not found!", ephemeral=True)

@tree.command(name="demote", description="Demote a member to the previous role")
async def demote(interaction: discord.Interaction, member: discord.Member):
    if not has_role(interaction, OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    member_roles = [role.name for role in member.roles]
    current_index = -1
    for i, role_name in enumerate(ROLE_HIERARCHY):
        if role_name in member_roles:
            current_index = i
    if current_index <= 0:
        await interaction.response.send_message("❌ Can't demote this member!", ephemeral=True)
        return
    prev_role_name = ROLE_HIERARCHY[current_index - 1]
    prev_role = discord.utils.get(interaction.guild.roles, name=prev_role_name)
    current_role = discord.utils.get(interaction.guild.roles, name=ROLE_HIERARCHY[current_index])
    if prev_role and current_role:
        await member.remove_roles(current_role)
        await member.add_roles(prev_role)
        embed = discord.Embed(title="⬇️ Member Demoted", color=discord.Color.red())
        embed.add_field(name="Member", value=member.mention, inline=False)
        embed.add_field(name="New Role", value=prev_role_name, inline=False)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ Role not found!", ephemeral=True)

# ============ ECONOMY ============

@tree.command(name="balance", description="Check your coin balance")
async def balance(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    data = load_data()
    coins = get_balance(data, member.id)
    embed = discord.Embed(title=f"💰 {member.display_name}'s Balance", color=discord.Color.gold())
    embed.add_field(name="Coins", value=f"{coins} 🪙")
    await interaction.response.send_message(embed=embed)

@tree.command(name="givecoin", description="Give coins to a member")
async def givecoin(interaction: discord.Interaction, member: discord.Member, amount: int):
    if not has_role(interaction, CO_OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    data = load_data()
    add_coins(data, member.id, amount)
    save_data(data)
    embed = discord.Embed(title="🪙 Coins Given", color=discord.Color.gold())
    embed.add_field(name="Member", value=member.mention, inline=False)
    embed.add_field(name="Amount", value=f"{amount} 🪙", inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="takecoins", description="Take coins from a member")
async def takecoins(interaction: discord.Interaction, member: discord.Member, amount: int):
    if not has_role(interaction, CO_OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    data = load_data()
    remove_coins(data, member.id, amount)
    save_data(data)
    embed = discord.Embed(title="🪙 Coins Taken", color=discord.Color.red())
    embed.add_field(name="Member", value=member.mention, inline=False)
    embed.add_field(name="Amount", value=f"{amount} 🪙", inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="clearcoins", description="Clear a member's coins")
async def clearcoins(interaction: discord.Interaction, member: discord.Member):
    if not has_role(interaction, CO_OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    data = load_data()
    user_id = str(member.id)
    if "economy" in data and user_id in data["economy"]:
        data["economy"][user_id]["coins"] = 0
        save_data(data)
    embed = discord.Embed(title="🪙 Coins Cleared", color=discord.Color.red())
    embed.add_field(name="Member", value=member.mention, inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="shop", description="View the shop")
async def shop(interaction: discord.Interaction):
    data = load_data()
    custom_items = data.get("custom_shop_items", [])
    all_items = SHOP_ITEMS + custom_items
    embed = discord.Embed(title="🛒 Launchly Shop", color=discord.Color.blue())
    for item in all_items:
        embed.add_field(name=item["name"], value=f"Price: {item['price']} 🪙 | ID: `{item['id']}`", inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="buy", description="Buy an item from the shop")
@app_commands.choices(item_id=[
    app_commands.Choice(name="100m Brainrot - 700 🪙", value="100m_brainrot"),
    app_commands.Choice(name="125m Brainrot - 1000 🪙", value="125m_brainrot"),
    app_commands.Choice(name="150m Brainrot - 1500 🪙", value="150m_brainrot"),
    app_commands.Choice(name="175m Brainrot - 1750 🪙", value="175m_brainrot"),
    app_commands.Choice(name="200m Brainrot - 2000 🪙", value="200m_brainrot"),
    app_commands.Choice(name="200m+ Brainrot - 2500 🪙", value="200m_plus_brainrot"),
    app_commands.Choice(name="Rare Brainrot - 4000 🪙", value="rare_brainrot"),
])
async def buy(interaction: discord.Interaction, item_id: app_commands.Choice[str]):
    data = load_data()
    custom_items = data.get("custom_shop_items", [])
    all_items = SHOP_ITEMS + custom_items
    item = next((i for i in all_items if i["id"] == item_id.value), None)
    if not item:
        await interaction.response.send_message("❌ Item not found!", ephemeral=True)
        return
    user_id = str(interaction.user.id)
    coins = get_balance(data, interaction.user.id)
    if coins < item["price"]:
        embed = discord.Embed(title="❌ Not Enough Coins", color=discord.Color.red())
        embed.add_field(name="Required", value=f"{item['price']} 🪙", inline=True)
        embed.add_field(name="Your Balance", value=f"{coins} 🪙", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    remove_coins(data, interaction.user.id, item["price"])
    if "economy" not in data:
        data["economy"] = {}
    if user_id not in data["economy"]:
        data["economy"][user_id] = {"coins": 0, "inventory": [], "message_count": 0}
    data["economy"][user_id]["inventory"].append(item)
    save_data(data)
    embed = discord.Embed(title="✅ Item Purchased!", color=discord.Color.green())
    embed.add_field(name="Item", value=item["name"], inline=False)
    embed.add_field(name="Price", value=f"{item['price']} 🪙", inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="inventory", description="View your inventory")
async def inventory(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    data = load_data()
    user_id = str(member.id)
    items = data.get("economy", {}).get(user_id, {}).get("inventory", [])
    embed = discord.Embed(title=f"🎒 {member.display_name}'s Inventory", color=discord.Color.green())
    if not items:
        embed.description = "No items yet!"
    else:
        for i, item in enumerate(items):
            embed.add_field(name=item["name"], value=f"Claim ID: `{i}`", inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="clearinventory", description="Clear a member's inventory")
async def clearinventory(interaction: discord.Interaction, member: discord.Member):
    if not has_role(interaction, CO_OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    data = load_data()
    user_id = str(member.id)
    if "economy" in data and user_id in data["economy"]:
        data["economy"][user_id]["inventory"] = []
        save_data(data)
    embed = discord.Embed(title="🎒 Inventory Cleared", color=discord.Color.red())
    embed.add_field(name="Member", value=member.mention, inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="coinflip", description="Flip a coin and gamble your coins")
@app_commands.choices(choice=[
    app_commands.Choice(name="Heads", value="heads"),
    app_commands.Choice(name="Tails", value="tails"),
])
async def coinflip(interaction: discord.Interaction, amount: int, choice: app_commands.Choice[str]):
    data = load_data()
    coins = get_balance(data, interaction.user.id)
    if coins < amount:
        embed = discord.Embed(title="❌ Not Enough Coins", color=discord.Color.red())
        embed.add_field(name="Your Balance", value=f"{coins} 🪙", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    result = random.choice(["heads", "tails"])
    if choice.value == result:
        add_coins(data, interaction.user.id, amount)
        save_data(data)
        new_balance = get_balance(data, interaction.user.id)
        embed = discord.Embed(title="🪙 You Won!", color=discord.Color.green())
        embed.add_field(name="Result", value=f"**{result.capitalize()}**", inline=True)
        embed.add_field(name="Winnings", value=f"+{amount} 🪙", inline=True)
        embed.add_field(name="New Balance", value=f"{new_balance} 🪙", inline=False)
    else:
        remove_coins(data, interaction.user.id, amount)
        save_data(data)
        new_balance = get_balance(data, interaction.user.id)
        embed = discord.Embed(title="🪙 You Lost!", color=discord.Color.red())
        embed.add_field(name="Result", value=f"**{result.capitalize()}**", inline=True)
        embed.add_field(name="Lost", value=f"-{amount} 🪙", inline=True)
        embed.add_field(name="New Balance", value=f"{new_balance} 🪙", inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="additem", description="Add an item to the shop")
async def additem(interaction: discord.Interaction, item_id: str, item_name: str, price: int):
    if not has_role(interaction, CO_OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    data = load_data()
    if "custom_shop_items" not in data:
        data["custom_shop_items"] = []
    data["custom_shop_items"].append({"id": item_id, "name": item_name, "price": price})
    save_data(data)
    embed = discord.Embed(title="✅ Item Added to Shop", color=discord.Color.green())
    embed.add_field(name="Item", value=item_name, inline=False)
    embed.add_field(name="Price", value=f"{price} 🪙", inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="removeitem", description="Remove an item from the shop")
async def removeitem(interaction: discord.Interaction, item_id: str):
    if not has_role(interaction, CO_OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    data = load_data()
    if "custom_shop_items" not in data:
        await interaction.response.send_message("❌ Item not found!", ephemeral=True)
        return
    data["custom_shop_items"] = [i for i in data["custom_shop_items"] if i["id"] != item_id]
    save_data(data)
    embed = discord.Embed(title="✅ Item Removed from Shop", color=discord.Color.red())
    embed.add_field(name="Item ID", value=item_id, inline=False)
    await interaction.response.send_message(embed=embed)

# ============ CLAIM / TICKETS ============

@tree.command(name="claim", description="Claim an item from your inventory")
async def claim(interaction: discord.Interaction, item_index: int):
    data = load_data()
    user_id = str(interaction.user.id)
    items = data.get("economy", {}).get(user_id, {}).get("inventory", [])
    if item_index < 0 or item_index >= len(items):
        await interaction.response.send_message("❌ Invalid item ID!", ephemeral=True)
        return
    item = items[item_index]
    claims_channel = discord.utils.get(interaction.guild.text_channels, name=CLAIMS_CHANNEL)
    if not claims_channel:
        await interaction.response.send_message("❌ Claims channel not found!", ephemeral=True)
        return
    embed = discord.Embed(title="🎟️ New Claim Request", color=discord.Color.orange())
    embed.add_field(name="User", value=interaction.user.mention, inline=False)
    embed.add_field(name="Item", value=item["name"], inline=False)
    embed.set_footer(text="Click the button below to open a ticket for this claim!")
    view = ClaimButton(claimer=interaction.user, item_name=item["name"])
    await claims_channel.send(embed=embed, view=view)
    await interaction.response.send_message(f"✅ Your claim request has been sent to the staff!", ephemeral=True)

@tree.command(name="close", description="Close a claim ticket")
async def close(interaction: discord.Interaction):
    if not has_role(interaction, CO_OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    await interaction.response.send_message("🔒 Closing ticket in 5 seconds...")
    await asyncio.sleep(5)
    await interaction.channel.delete()

# ============ CODES ============

@tree.command(name="makecode", description="Create a code members can redeem for coins")
async def makecode(interaction: discord.Interaction, code: str, coins: int, minutes: int):
    if not has_role(interaction, CO_OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    data = load_data()
    if "codes" not in data:
        data["codes"] = {}
    import time
    data["codes"][code] = {
        "coins": coins,
        "expires": time.time() + (minutes * 60),
        "used_by": []
    }
    save_data(data)
    embed = discord.Embed(title="🎟️ Code Created", color=discord.Color.green())
    embed.add_field(name="Code", value=f"`{code}`", inline=False)
    embed.add_field(name="Reward", value=f"{coins} 🪙", inline=False)
    embed.add_field(name="Expires In", value=f"{minutes} minutes", inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="usecode", description="Redeem a code for coins")
async def usecode(interaction: discord.Interaction, code: str):
    import time
    data = load_data()
    if "codes" not in data or code not in data["codes"]:
        await interaction.response.send_message("❌ Invalid code!", ephemeral=True)
        return
    code_data = data["codes"][code]
    if time.time() > code_data["expires"]:
        await interaction.response.send_message("❌ This code has expired!", ephemeral=True)
        return
    user_id = str(interaction.user.id)
    if user_id in code_data["used_by"]:
        await interaction.response.send_message("❌ You already used this code!", ephemeral=True)
        return
    code_data["used_by"].append(user_id)
    add_coins(data, interaction.user.id, code_data["coins"])
    save_data(data)
    embed = discord.Embed(title="✅ Code Redeemed!", color=discord.Color.green())
    embed.add_field(name="Code", value=f"`{code}`", inline=False)
    embed.add_field(name="Reward", value=f"{code_data['coins']} 🪙", inline=False)
    await interaction.response.send_message(embed=embed)

# ============ VOUCH ============

@tree.command(name="vouch", description="Vouch for a member")
async def vouch(interaction: discord.Interaction, member: discord.Member):
    if member.id == interaction.user.id:
        await interaction.response.send_message("❌ You can't vouch for yourself!", ephemeral=True)
        return
    data = load_data()
    if "vouches" not in data:
        data["vouches"] = {}
    user_id = str(member.id)
    if user_id not in data["vouches"]:
        data["vouches"][user_id] = {"count": 0, "vouchers": []}
    if isinstance(data["vouches"][user_id], int):
        data["vouches"][user_id] = {"count": data["vouches"][user_id], "vouchers": []}
    data["vouches"][user_id]["count"] += 1
    data["vouches"][user_id]["vouchers"].append(str(interaction.user.id))
    save_data(data)
    total = data["vouches"][user_id]["count"]
    embed = discord.Embed(title="🌟 Vouch", color=discord.Color.gold())
    embed.add_field(name="Vouched By", value=interaction.user.mention, inline=False)
    embed.add_field(name="Vouched For", value=member.mention, inline=False)
    embed.add_field(name="Total Vouches", value=f"{total} 🌟", inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="show-vouches", description="Show your vouches")
async def show_vouches(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    data = load_data()
    user_id = str(member.id)
    vouch_data = data.get("vouches", {}).get(user_id, {"count": 0, "vouchers": []})
    if isinstance(vouch_data, int):
        vouch_data = {"count": vouch_data, "vouchers": []}
    total = vouch_data["count"]
    vouchers = vouch_data["vouchers"]
    embed = discord.Embed(title=f"⭐ {member.display_name}'s Vouches", color=discord.Color.gold())
    embed.add_field(name="Total Vouches", value=f"{total} 🌟", inline=False)
    view = VouchListButton(member=member, vouchers=vouchers)
    await interaction.response.send_message(embed=embed, view=view)

@tree.command(name="remove-vouch", description="Remove a vouch from a member")
async def remove_vouch(interaction: discord.Interaction, member: discord.Member):
    if not has_role(interaction, REMOVE_VOUCH_ROLES):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    data = load_data()
    user_id = str(member.id)
    if "vouches" not in data or user_id not in data["vouches"]:
        await interaction.response.send_message(f"❌ {member.mention} has no vouches!", ephemeral=True)
        return
    if isinstance(data["vouches"][user_id], int):
        data["vouches"][user_id] = {"count": data["vouches"][user_id], "vouchers": []}
    if data["vouches"][user_id]["count"] <= 0:
        await interaction.response.send_message(f"❌ {member.mention} has no vouches!", ephemeral=True)
        return
    data["vouches"][user_id]["count"] -= 1
    if data["vouches"][user_id]["vouchers"]:
        data["vouches"][user_id]["vouchers"].pop()
    save_data(data)
    log_channel = discord.utils.get(interaction.guild.text_channels, name=📂｜𝑹𝒆𝒎𝒐𝒗𝒆 𝑽𝒐𝒖𝒄𝒉𝒆𝒔 𝑳𝒐𝒈𝒔)
    if log_channel:
        log_embed = discord.Embed(title="🗑️ Vouch Removed", color=discord.Color.red())
        log_embed.add_field(name="Member", value=member.mention, inline=False)
        log_embed.add_field(name="Removed By", value=interaction.user.mention, inline=False)
        log_embed.add_field(name="Remaining Vouches", value=str(data["vouches"][user_id]["count"]), inline=False)
        await log_channel.send(embed=log_embed)
    embed = discord.Embed(title="✅ Vouch Removed", color=discord.Color.green())
    embed.add_field(name="Member", value=member.mention, inline=False)
    embed.add_field(name="Remaining Vouches", value=str(data["vouches"][user_id]["count"]), inline=False)
    await interaction.response.send_message(embed=embed)

# ============ EMBED ============

@tree.command(name="embed", description="Send a custom embed message")
async def embed_command(interaction: discord.Interaction, color: str, message: str):
    if not has_role(interaction, EMBED_ROLES):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    try:
        color = color.strip("#")
        color_int = int(color, 16)
        embed = discord.Embed(description=message, color=discord.Color(color_int))
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("✅ Embed sent!", ephemeral=True)
    except:
        await interaction.response.send_message("❌ Invalid hex color! Example: `FF0000` for red", ephemeral=True)

# ============ HELP COINFLIP ============

@tree.command(name="help-coinflip", description="Learn how to use the coinflip command")
async def help_coinflip(interaction: discord.Interaction):
    embed = discord.Embed(title="🪙 Coinflip Guide", color=discord.Color.gold())
    embed.add_field(name="Step 1 — Place your bet", value="Place the amount of coins from your balance in the command. You can choose how many — no minimum and no maximum!", inline=False)
    embed.add_field(name="Step 2 — Choose your side", value="Choose the side you want to bet on. There are only two options: **Heads** or **Tails**.", inline=False)
    embed.add_field(name="Step 3 — See the result", value="After you choose a side press Enter and look at the message the bot sent you.\n\n✅ **You Won!** — The amount you betted will be doubled and added to your balance.\n❌ **You Lost!** — The amount you betted will be removed from your balance.", inline=False)
    embed.add_field(name="❓ Still confused?", value="Make a support ticket and our staff will help you out!", inline=False)
    embed.set_footer(text="Launchly Bot 🚀")
    await interaction.response.send_message(embed=embed)

# ============ HELP ============

@tree.command(name="help", description="Show all available commands")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="📖 Launchly Commands", color=discord.Color.blurple())
    embed.add_field(name="🛡️ Moderation", value="`/kick` `/ban` `/unban` `/mute` `/unmute` `/warn` `/unwarn` `/clearwarns` `/lock` `/unlock` `/lockall` `/unlockall` `/slowmode` `/changenickname`", inline=False)
    embed.add_field(name="🪙 Economy", value="`/balance` `/shop` `/buy` `/inventory` `/coinflip` `/usecode`", inline=False)
    embed.add_field(name="⭐ Social", value="`/vouch` `/show-vouches`", inline=False)
    embed.add_field(name="🎟️ Tickets", value="`/claim` `/close`", inline=False)
    embed.add_field(name="❓ Help", value="`/help-coinflip`", inline=False)
    embed.add_field(name="👑 Staff Only", value="`/givecoin` `/takecoins` `/clearcoins` `/clearinventory` `/makecode` `/additem` `/removeitem` `/promote` `/demote` `/setlogchannel` `/grantaccess` `/revokeaccess` `/embed` `/remove-vouch`", inline=False)
    embed.set_footer(text="Launchly Bot 🚀")
    await interaction.response.send_message(embed=embed)

import os
client.run(os.environ.get("DISCORD_TOKEN"))