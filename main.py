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
GUILD_ID = config["discord"]["GUILD_ID"]
ADMIN_ID = config["discord"]["ADMIN_ID"]
PLEXUSER_ID = config["discord"]["PLEXUSER_ID"]

PLEX_USERNAME = config["plex"]["PLEX_USERNAME"]
PLEX_PASSWORD = config["plex"]["PLEX_PASSWORD"]
PLEX_SERVERNAME = config["plex"]["PLEX_SERVERNAME"]

try:
    print("Logging into Plex")
    account = MyPlexAccount("PLEX_USERNAME", "PLEX_PASSWORD")
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
    pass


@bot.slash_command(guild_ids=[GUILD_ID])
async def dbls(ctx):
    if ctx.author.id == ADMIN_ID:
        index = 0
        for x in database.dbls():
            await ctx.respond(
                f'Index: {index} | Plex ID: {x["plex_id"]} | Discord ID: {x["discord_id"]} | Status: {x["status"]} | Date Added: {x["date_invited"]} | Date Removed: {x["date_removed"]}'
            )
            index += 1
    else:
        await ctx.respond("You do not have permission to use this command")


@bot.slash_command(guild_ids=[GUILD_ID])
async def join(ctx, plex_id: discord.Option(str, "Your Plex username or email.")):

    invite = plexutils.invite(
        plex_account=account,
        plex_server=plex,
        sections=sections,
        database_object=database,
        plex_id=plex_id,
        discord_id=ctx.author.id,
    )
    if invite.startswith("Successfully"):
        await ctx.author.add_roles(discord.utils.get(ctx.guild.roles, id=PLEXUSER_ID))
    await ctx.author.send(invite)
    await ctx.respond(invite, ephemeral=True)


@bot.slash_command(guild_ids=[GUILD_ID])
async def remove(
    ctx,
    discord_id: discord.Option(str, "Discord ID"),
    left_discord: discord.Option(bool, "Add left status in database"),
):
    if ctx.author.id == ADMIN_ID:
        await ctx.author.remove_roles(
            discord.utils.get(ctx.guild.roles, id=PLEXUSER_ID)
        )
        await ctx.respond(
            plexutils.remove(
                plex_account=account,
                database_object=database,
                discord_id=int(discord_id),
                left_discord=left_discord,
            )
        )
    else:
        await ctx.respond("Not Authorized")


bot.run(TOKEN)
