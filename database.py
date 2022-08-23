import configparser
from datetime import datetime

import pymongo
import pytz
from pymongo.server_api import ServerApi

config = configparser.ConfigParser()
config.read("config.ini")

TIMEZONE = config["timezone"]["TIMEZONE"]
DATABASE_URL = config["database"]["DATABASE_URL"]

pst = pytz.timezone(TIMEZONE)

client = pymongo.MongoClient(
    DATABASE_URL,
    server_api=ServerApi("1"),
)
db = client.test

mydb = client["plexvites"]


def get_database():
    return mydb


def get_plex_id(discord_id):
    return mydb.users.find_one({"discord_id": discord_id}, {"_id": 0, "plex_id": 1})[
        "plex_id"
    ]


def add_user(plex_id, discord_id):
    mydb.users.insert_one(
        {
            "plex_id": plex_id,
            "discord_id": discord_id,
            "status": "Invited",
            "date_invited": datetime.now(pst).strftime("%Y-%m-%d %H:%M:%S"),
            "date_removed": None,
        }
    )


# edit the status of an item in the database
def edit_status(discord_id, status):
    mydb.users.update_one({"discord_id": discord_id}, {"$set": {"status": status}})


def remove_time(discord_id, time):
    mydb.users.update_one({"discord_id": discord_id}, {"$set": {"date_removed": time}})


def remove_user(discord_id, status):
    mydb.users.update_one({"discord_id": discord_id}, {"$set": {"status": status}})
    mydb.users.update_one(
        {"discord_id": discord_id},
        {"$set": {"date_removed": datetime.now(pst).strftime("%Y-%m-%d %H:%M:%S")}},
    )


def dbls():
    return mydb.users.find(
        {},
        {
            "_id": 0,
            "plex_id": 1,
            "discord_id": 1,
            "status": 1,
            "date_invited": 1,
            "date_removed": 1,
        },
    )
