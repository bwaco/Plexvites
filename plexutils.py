import configparser

import plexapi
import pytz

config = configparser.ConfigParser()
config.read("config.ini")


TIMEZONE = config["timezone"]["TIMEZONE"]
ADMIN_ID = config["discord"]["ADMIN_ID"]

pst = pytz.timezone(TIMEZONE)


def invite(plex_account, plex_server, sections, database_object, plex_id, discord_id):
    try:
        plex_account.inviteFriend(user=plex_id, server=plex_server, sections=sections)
        database_object.add_user(plex_id, discord_id)
        return f"Successfully invited {plex_id} to {plex_server.friendlyName}"
    except Exception as e:
        return f"Failed to invite {plex_id} to {plex_server.friendlyName}, contact <@{ADMIN_ID}> with the traceback for help. Traceback: {e}"


def remove(plex_account, database_object, discord_id, left_discord):
    try:
        plex_id = database_object.get_plex_id(discord_id)
        plex_account.removeFriend(user=plex_id)
        status = "Removed"
    except TypeError as e:
        return f"{discord_id} is not in the database. Traceback: {e}"
    except plexapi.exceptions.NotFound as e:
        try:
            plex_account.cancelInvite(user=plex_id)
            status = "Cancelled"
        except Exception as e:
            status = "Left"
            database_object.remove_user(discord_id=discord_id, status=status)
            return f"{plex_id} not found in Plex. Removed from database. Traceback: {e}"
    if left_discord:
        status = "Left"
        database_object.remove_user(discord_id=discord_id, status=status)
        return f"{discord_id} left the Discord server. Removed from Plex and database"
    else:
        if status == "Removed":
            database_object.remove_user(discord_id=discord_id, status=status)
            return f"{discord_id} has been removed from Plex"
        elif status == "Cancelled":
            database_object.remove_user(discord_id, status=status)
            return f"{plex_id}'s invite has been cancelled from Plex"
