import discord
import mysql.connector
import valve.source.a2s
import asyncio
import math
import json
import random
from steam import SteamID
from datetime import datetime
from discord.ext import commands

with open("config.json") as cfg:
    config = json.load(cfg)
    
TOKEN        = config["bot_token"]
PREFIX       = config["command_prefix"]
ICON         = config["embed_icon"]
IP           = config["server_ip"]
PORT         = config["server_port"]
SERVER       = config["server_name"]
DB_IP        = config["db_ip"]
DB_DB        = config["db_database"]
DB_USER      = config["db_user"]
DB_PASS      = config["db_pass"]
TABLE_PREFIX = config["table_prefix"]
STATS_PAGE   = config["webstats_url"]

bot = commands.Bot(command_prefix=PREFIX)
SERVER_ADDRESS = (IP, PORT)

db = {
  'user': DB_USER,
  'password': DB_PASS,
  'host': DB_IP,
  'database': DB_DB
}
    
@bot.event
async def on_ready():
    status_task.start()
 
@tasks.loop(seconds=60.0)
async def status_task():
    with valve.source.a2s.ServerQuerier(SERVER_ADDRESS) as server:
        info = server.info()
        await bot.change_presence(activity=discord.Game(name="on " + SERVER + " with {player_count}".format(**info) + " players"))
    
@bot.command(aliases=['record', 'mtop', 'maptop', 'maprecord'])
async def wr(ctx, arg):
    sql = "SELECT time, jumps, sync, strafes, date, map, u.name, p.auth FROM " + TABLE_PREFIX + "playertimes p, " + TABLE_PREFIX + "users u WHERE map LIKE '%" + arg + "%' AND track = 0 AND style = 0 AND u.auth = p.auth ORDER BY time ASC LIMIT 1"
    conn = mysql.connector.connect(**db)
    cursor = conn.cursor()
    cursor.execute(sql)
    results = cursor.fetchone()
    time = results[0]
    jumps = str(results[1])
    sync = str(results[2])
    strafes = str(results[3])
    timestamp = results[4]
    mapname = str(results[5])
    user = str(results[6]) 
    auth = results[7]
    
    minutes = time / 60
    i, d = divmod(minutes, 1)
    seconds = d * 60
    minutes = math.trunc(i)
    seconds = round(seconds, 3)
    formatted = str(minutes) + ":" + str(seconds) 
    date_time = datetime.fromtimestamp(timestamp)
    d = date_time.strftime("%d/%m/%Y")  
    link = "http://www.steamcommunity.com/profiles/" + str(SteamID(auth))
    
    if STATS_PAGE:
        statslink = STATS_PAGE + "/?map=" + mapname
        embed=discord.Embed(title="Map Record", description="[" + mapname + "](" + statslink + ")", color=0x1183f4)
    if not STATS_PAGE:
        embed=discord.Embed(title="Map Record", description=mapname, color=0x1183f4)
    embed.set_thumbnail(url=ICON)
    embed.set_footer(text="Join: steam://connect/" + IP + ":" + str(PORT))
    embed.add_field(name="Player‎‎", value="[" + user + "](" + link + ")", inline=True)
    embed.add_field(name="Time", value=formatted, inline=True)
    embed.add_field(name="Jumps", value=jumps, inline=True)
    embed.add_field(name="Sync", value=sync + "%", inline=True)
    embed.add_field(name="Strafes", value=strafes, inline=True)
    embed.add_field(name="Date", value=d, inline=True)
    await ctx.send(embed=embed)
    
    conn.close()
    cursor.close()
    
@bot.command(aliases=['brecord', 'btop', 'bonustop', 'bonusrecord'])
async def bwr(ctx, arg):
    sql = "SELECT time, jumps, sync, strafes, date, map, u.name, p.auth FROM " + TABLE_PREFIX + "playertimes p, " + TABLE_PREFIX + "users u WHERE map LIKE '%" + arg + "%' AND track = 1 AND style = 0 AND u.auth = p.auth ORDER BY time ASC LIMIT 1"
    conn = mysql.connector.connect(**db)
    cursor = conn.cursor()
    cursor.execute(sql)
    results = cursor.fetchone()
    time = results[0]
    jumps = str(results[1])
    sync = str(results[2])
    strafes = str(results[3])
    timestamp = results[4]
    mapname = str(results[5])
    user = str(results[6]) 
    auth = results[7]
    
    minutes = time / 60
    i, d = divmod(minutes, 1)
    seconds = d * 60
    minutes = math.trunc(i)
    seconds = round(seconds, 3)
    formatted = str(minutes) + ":" + str(seconds) 
    date_time = datetime.fromtimestamp(timestamp)
    d = date_time.strftime("%d/%m/%Y")  
    link = "http://www.steamcommunity.com/profiles/" + str(SteamID(auth))
    
    if STATS_PAGE:
        statslink = STATS_PAGE + "/?track=1&map=" + mapname
        embed=discord.Embed(title="Bonus Record", description="[" + mapname + "](" + statslink + ")", color=0xe79f0c)
    if not STATS_PAGE:
        embed=discord.Embed(title="Bonus Record", description=mapname, color=0xe79f0c)
    embed.set_thumbnail(url=ICON)
    embed.set_footer(text="Join: steam://connect/" + IP + ":" + str(PORT))
    embed.add_field(name="Player‎‎", value="[" + user + "](" + link + ")", inline=True)
    embed.add_field(name="Time", value=formatted, inline=True)
    embed.add_field(name="Jumps", value=jumps, inline=True)
    embed.add_field(name="Sync", value=sync + "%", inline=True)
    embed.add_field(name="Strafes", value=strafes, inline=True)
    embed.add_field(name="Date", value=d, inline=True)
    await ctx.send(embed=embed)
    
    conn.close()
    cursor.close()
    
@bot.command()
@commands.cooldown(1, 15, commands.BucketType.user)
async def ssj(ctx):
    num = random.randint(480,700)
    await ctx.send(ctx.message.author.mention + " has a SSJ of " + str(num))
    
bot.run(TOKEN)