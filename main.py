import configparser
from optparse import Option

import discord
from discord.ext import commands
from plexapi.myplex import MyPlexAccount

import database
import plexutils

config = configparser.ConfigParser()
config.read("config.ini")

TOKEN = config["discord"]["TOKEN"]
GUILD_ID = int(config["discord"]["GUILD_ID"])
ADMIN_ID = int(config["discord"]["ADMIN_ID"])
PLEXUSER_ID = int(config["discord"]["PLEXUSER_ID"])

PLEX_USERNAME = config["plex"]["PLEX_USERNAME"]
PLEX_PASSWORD = config["plex"]["PLEX_PASSWORD"]
PLEX_SERVERNAME = config["plex"]["PLEX_SERVERNAME"]

try:
    print("Logging into Plex")
    account = MyPlexAccount(PLEX_USERNAME, PLEX_PASSWORD)
    plex = account.resource("The Lair").connect()
    sections = plex.library.sections()

except Exception as e:
    print(f"Failed to login to Plex, Traceback: {e}")

else:
    print("Successfully logged into Plex")

intents = discord.Intents.all()
bot = commands.Bot(intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.event
async def on_member_remove(member):
    left_discord = True
    discord_id = member.id

    remove_user = plexutils.remove(
        plex_account=account,
        database_object=database,
        discord_id=int(discord_id),
        left_discord=left_discord,
    )
    print(f"{member.id} has left the server, ran removal: {remove_user}")


@bot.slash_command(guild_ids=[GUILD_ID])
async def dbls(ctx):
    if ctx.author.id == ADMIN_ID:
        index = 0
        for x in database.dbls():
            await ctx.respond(
                f'Index: {index} | Plex ID: {x["plex_id"]} | Discord ID: {x["discord_id"]} | Status: {x["status"]} | Date Added: {x["date_invited"]} | Date Removed: {x["date_removed"]}'
            )
            index += 1
        print(f"{ctx.author.id} ran DBLS, {index} entries sent")
    else:
        await ctx.respond("You do not have permission to use this command")
        print(f"{ctx.author.id} tried to run DBLS, but did not have permission")


@bot.slash_command(guild_ids=[GUILD_ID])
async def join(ctx, plex_id: discord.Option(str, "Your Plex username or email.")):

    if discord.utils.get(ctx.guild.roles, id=PLEXUSER_ID) not in ctx.author.roles:

        invite_user = plexutils.invite(
            plex_account=account,
            plex_server=plex,
            sections=sections,
            database_object=database,
            plex_id=plex_id,
            discord_id=ctx.author.id,
        )
        if invite_user.startswith("Successfully"):
            await ctx.author.add_roles(
                discord.utils.get(ctx.guild.roles, id=PLEXUSER_ID)
            )
        print(f"{ctx.author.id} | {plex_id} ran join: {invite_user}")
        await ctx.author.send(invite_user)
        await ctx.respond(invite_user, ephemeral=True)
    else:
        await ctx.respond(
            f"You have already been successfully added to Plex, contact @<{ADMIN_ID}> for assistance"
        )
        print(f"{ctx.author.id} tried to run join, but already has Plex role")


@bot.slash_command(guild_ids=[GUILD_ID])
async def remove(
    ctx,
    discord_id: discord.Option(str, "Discord ID"),
    left_discord: discord.Option(bool, "Add left status in database"),
):
    member = discord.Guild.get_member(ctx.guild, int(discord_id))
    if ctx.author.id == ADMIN_ID:
        if left_discord == False:
            await member.remove_roles(
                discord.utils.get(ctx.guild.roles, id=PLEXUSER_ID)
            )
        remove_user = plexutils.remove(
            plex_account=account,
            database_object=database,
            discord_id=int(discord_id),
            left_discord=left_discord,
        )
        print(f"{ctx.author.id} ran remove on {discord_id}: {remove_user}")
        await ctx.respond(remove_user, ephemeral=True)
    else:
        await ctx.respond("Not Authorized", ephemeral=True)
        print(f"{ctx.author.id} tried to run remove, but did not have permission")


bot.run(TOKEN)
