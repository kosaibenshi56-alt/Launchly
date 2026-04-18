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
        data["economy"][user_id] = {"coins": 0, "inventory": []}
    return data["economy"][user_id]["coins"]

def add_coins(data, user_id, amount):
    user_id = str(user_id)
    if "economy" not in data:
        data["economy"] = {}
    if user_id not in data["economy"]:
        data["economy"][user_id] = {"coins": 0, "inventory": []}
    data["economy"][user_id]["coins"] += amount

def remove_coins(data, user_id, amount):
    user_id = str(user_id)
    if "economy" not in data:
        data["economy"] = {}
    if user_id not in data["economy"]:
        data["economy"][user_id] = {"coins": 0, "inventory": []}
    data["economy"][user_id]["coins"] = max(0, data["economy"][user_id]["coins"] - amount)

OWNER = ["Owner"]
CO_OWNER = ["Owner", "Co Owner"]
MANAGER = ["Owner", "Co Owner", "Head Manager", "Manager"]
ADMIN = ["Owner", "Co Owner", "Head Manager", "Manager", "Head Admin", "Admin"]

ROLE_HIERARCHY = [
    "Community Member", "Staff Team", "Trial Moderator", "Support Team",
    "Head Of Support", "Middle Man", "Moderator", "Head Moderator",
    "Admin", "Head Admin", "Manager", "Head Manager", "Co Owner", "Owner"
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

# ============ EVENTS ============

@client.event
async def on_ready():
    guild = discord.Object(id=1494815171334635692)
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
    add_coins(data, message.author.id, 1)
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
    await member.kick(reason=reason)
    await interaction.response.send_message(f"✅ {member.mention} has been kicked. Reason: {reason}")

@tree.command(name="ban", description="Ban a member")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not has_role(interaction, CO_OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ You can't ban someone with a higher or equal role!", ephemeral=True)
        return
    await member.ban(reason=reason)
    await interaction.response.send_message(f"✅ {member.mention} has been banned. Reason: {reason}")

@tree.command(name="unban", description="Unban a user by ID")
async def unban(interaction: discord.Interaction, user_id: str):
    if not has_role(interaction, CO_OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    user = await client.fetch_user(int(user_id))
    await interaction.guild.unban(user)
    await interaction.response.send_message(f"✅ {user} has been unbanned!")

@tree.command(name="mute", description="Mute a member")
async def mute(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not has_role(interaction, ADMIN):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    role = discord.utils.get(interaction.guild.roles, name="Muted")
    await member.add_roles(role)
    await interaction.response.send_message(f"✅ {member.mention} has been muted. Reason: {reason}")

@tree.command(name="unmute", description="Unmute a member")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    if not has_role(interaction, ADMIN):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    role = discord.utils.get(interaction.guild.roles, name="Muted")
    await member.remove_roles(role)
    await interaction.response.send_message(f"✅ {member.mention} has been unmuted!")

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
    await interaction.response.send_message(f"⚠️ {member.mention} has been warned. Reason: {reason}")

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
    await interaction.response.send_message(f"✅ Removed last warning from {member.mention}!")

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
    await interaction.response.send_message(f"✅ Cleared all warnings from {member.mention}!")

@tree.command(name="lock", description="Lock a channel")
async def lock(interaction: discord.Interaction, channel: discord.TextChannel = None):
    if not has_role(interaction, MANAGER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    channel = channel or interaction.channel
    await channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message(f"🔒 {channel.mention} has been locked!")

@tree.command(name="unlock", description="Unlock a channel")
async def unlock(interaction: discord.Interaction, channel: discord.TextChannel = None):
    if not has_role(interaction, MANAGER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    channel = channel or interaction.channel
    await channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message(f"🔓 {channel.mention} has been unlocked!")

@tree.command(name="lockall", description="Lock all channels")
async def lockall(interaction: discord.Interaction):
    if not has_role(interaction, MANAGER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    for channel in interaction.guild.text_channels:
        await channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 All channels have been locked!")

@tree.command(name="unlockall", description="Unlock all channels")
async def unlockall(interaction: discord.Interaction):
    if not has_role(interaction, MANAGER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    for channel in interaction.guild.text_channels:
        await channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 All channels have been unlocked!")

@tree.command(name="slowmode", description="Set slowmode for a channel")
async def slowmode(interaction: discord.Interaction, seconds: int, channel: discord.TextChannel = None):
    if not has_role(interaction, ADMIN):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    channel = channel or interaction.channel
    await channel.edit(slowmode_delay=seconds)
    await interaction.response.send_message(f"✅ Slowmode set to {seconds} seconds in {channel.mention}!")

@tree.command(name="changenickname", description="Change a member's nickname")
async def changenickname(interaction: discord.Interaction, member: discord.Member, nickname: str):
    if not has_role(interaction, ADMIN):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    await member.edit(nick=nickname)
    await interaction.response.send_message(f"✅ Changed {member.mention}'s nickname to {nickname}!")

@tree.command(name="setlogchannel", description="Set the log channel")
async def setlogchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not has_role(interaction, CO_OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    data = load_data()
    data["log_channel"] = channel.id
    save_data(data)
    await interaction.response.send_message(f"✅ Log channel set to {channel.mention}!")

@tree.command(name="grantaccess", description="Grant tester access to a user")
async def grantaccess(interaction: discord.Interaction, member: discord.Member):
    if not has_role(interaction, OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    role = discord.utils.get(interaction.guild.roles, name="Tester")
    await member.add_roles(role)
    await interaction.response.send_message(f"✅ Granted tester access to {member.mention}!")

@tree.command(name="revokeaccess", description="Revoke tester access from a user")
async def revokeaccess(interaction: discord.Interaction, member: discord.Member):
    if not has_role(interaction, OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    role = discord.utils.get(interaction.guild.roles, name="Tester")
    await member.remove_roles(role)
    await interaction.response.send_message(f"✅ Revoked tester access from {member.mention}!")

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
        await interaction.response.send_message(f"✅ {member.mention} has been promoted to **{next_role_name}**!")
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
        await interaction.response.send_message(f"✅ {member.mention} has been demoted to **{prev_role_name}**!")
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
    await interaction.response.send_message(f"✅ Gave {amount} 🪙 to {member.mention}!")

@tree.command(name="takecoins", description="Take coins from a member")
async def takecoins(interaction: discord.Interaction, member: discord.Member, amount: int):
    if not has_role(interaction, CO_OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    data = load_data()
    remove_coins(data, member.id, amount)
    save_data(data)
    await interaction.response.send_message(f"✅ Took {amount} 🪙 from {member.mention}!")

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
    await interaction.response.send_message(f"✅ Cleared coins for {member.mention}!")

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
async def buy(interaction: discord.Interaction, item_id: str):
    data = load_data()
    custom_items = data.get("custom_shop_items", [])
    all_items = SHOP_ITEMS + custom_items
    item = next((i for i in all_items if i["id"] == item_id), None)
    if not item:
        await interaction.response.send_message("❌ Item not found!", ephemeral=True)
        return
    user_id = str(interaction.user.id)
    coins = get_balance(data, interaction.user.id)
    if coins < item["price"]:
        await interaction.response.send_message(f"❌ You don't have enough coins! You need {item['price']} 🪙 but have {coins} 🪙", ephemeral=True)
        return
    remove_coins(data, interaction.user.id, item["price"])
    if "economy" not in data:
        data["economy"] = {}
    if user_id not in data["economy"]:
        data["economy"][user_id] = {"coins": 0, "inventory": []}
    data["economy"][user_id]["inventory"].append(item)
    save_data(data)
    await interaction.response.send_message(f"✅ You bought **{item['name']}** for {item['price']} 🪙!")

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
    await interaction.response.send_message(f"✅ Cleared inventory for {member.mention}!")

@tree.command(name="coinflip", description="Flip a coin and gamble your coins")
@app_commands.choices(choice=[
    app_commands.Choice(name="Heads", value="heads"),
    app_commands.Choice(name="Tails", value="tails"),
])
async def coinflip(interaction: discord.Interaction, amount: int, choice: app_commands.Choice[str]):
    data = load_data()
    coins = get_balance(data, interaction.user.id)
    if coins < amount:
        await interaction.response.send_message(f"❌ You don't have enough coins! You have {coins} 🪙", ephemeral=True)
        return
    result = random.choice(["heads", "tails"])
    if choice.value == result:
        add_coins(data, interaction.user.id, amount)
        save_data(data)
        await interaction.response.send_message(f"🪙 The coin landed on **{result}**! You won {amount} 🪙!")
    else:
        remove_coins(data, interaction.user.id, amount)
        save_data(data)
        await interaction.response.send_message(f"🪙 The coin landed on **{result}**! You lost {amount} 🪙!")

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
    await interaction.response.send_message(f"✅ Added **{item_name}** to the shop for {price} 🪙!")

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
    await interaction.response.send_message(f"✅ Removed item `{item_id}` from the shop!")

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
    guild = interaction.guild
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    for role in guild.roles:
        if role.name in CO_OWNER:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    ticket_channel = await guild.create_text_channel(
        f"claim-{interaction.user.name}",
        overwrites=overwrites
    )
    embed = discord.Embed(title="🎟️ Claim Request", color=discord.Color.orange())
    embed.add_field(name="User", value=interaction.user.mention)
    embed.add_field(name="Item", value=item["name"])
    embed.set_footer(text="An admin will be with you shortly!")
    await ticket_channel.send(embed=embed)
    await interaction.response.send_message(f"✅ Ticket created! Go to {ticket_channel.mention}", ephemeral=True)

@tree.command(name="close", description="Close a claim ticket")
async def close(interaction: discord.Interaction):
    if not has_role(interaction, CO_OWNER):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    if not interaction.channel.name.startswith("claim-"):
        await interaction.response.send_message("❌ This is not a ticket channel!", ephemeral=True)
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
    await interaction.response.send_message(f"✅ Code `{code}` created! Worth {coins} 🪙, expires in {minutes} minutes!")

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
    await interaction.response.send_message(f"✅ You redeemed code `{code}` for {code_data['coins']} 🪙!")

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
        data["vouches"][user_id] = 0
    data["vouches"][user_id] += 1
    save_data(data)
    total = data["vouches"][user_id]
    await interaction.response.send_message(f"✅ {interaction.user.mention} vouched for {member.mention}! They now have **{total}** vouches! ⭐")

# ============ HELP ============

@tree.command(name="help", description="Show all available commands")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="📖 Launchly Commands", color=discord.Color.blurple())
    embed.add_field(name="🛡️ Moderation", value="`/kick` `/ban` `/unban` `/mute` `/unmute` `/warn` `/unwarn` `/clearwarns` `/lock` `/unlock` `/lockall` `/unlockall` `/slowmode` `/changenickname`", inline=False)
    embed.add_field(name="🪙 Economy", value="`/balance` `/shop` `/buy` `/inventory` `/coinflip` `/usecode`", inline=False)
    embed.add_field(name="⭐ Social", value="`/vouch`", inline=False)
    embed.add_field(name="🎟️ Tickets", value="`/claim` `/close`", inline=False)
    embed.add_field(name="👑 Staff Only", value="`/givecoin` `/takecoins` `/clearcoins` `/clearinventory` `/makecode` `/additem` `/removeitem` `/promote` `/demote` `/setlogchannel` `/grantaccess` `/revokeaccess`", inline=False)
    embed.set_footer(text="Launchly Bot 🚀")
    await interaction.response.send_message(embed=embed)

client.run("MTQ5NDgxMDYwMTk0MjE1OTQ1MQ.GIjX0h.d0TOJvqVqW-5gkEmYkA-RNZsIQjBy0pbFYBeVQ")