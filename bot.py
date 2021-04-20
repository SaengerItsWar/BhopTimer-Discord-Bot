import discord
import mysql.connector
import a2s
import asyncio
import math
import json
import random
from steam.steamid import SteamID
from datetime import datetime
from discord.ext import tasks, commands 
 
stylename = []
alias = []
 
def loadStyles(style):
    styles = json.load(style) 
    for i in styles: 
        stylename.append(styles[i]['style'])
        alias.append(styles[i]['alias'])
           
with open("styles.json") as styles:
    loadStyles(styles)
    
with open("config.json") as cfg:
    config = json.load(cfg)  
    
TOKEN            = config["bot_token"]
PREFIX           = config["command_prefix"]
ICON             = config["embed_icon"]
IP               = config["server_ip"]
PORT             = config["server_port"]
DB_IP            = config["db_ip"]
DB_DB            = config["db_database"]
DB_USER          = config["db_user"]
DB_PASS          = config["db_pass"]
TABLE_PREFIX     = config["table_prefix"]
STATS_PAGE       = config["webstats_url"]
SSJ_COOLDOWN     = config["ssj_cooldown"]
RECORDS_COOLDOWN = config["records_cooldown"]
WR_COOLDOWN      = config["wr_cooldown"]

help_command = commands.DefaultHelpCommand(
    no_category = 'Commands'
)
bot = commands.Bot(command_prefix=PREFIX, help_command=help_command)
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
 
@tasks.loop(seconds=120.0)
async def status_task():
    await bot.change_presence(activity=discord.Game(name=a2s.info(SERVER_ADDRESS, timeout=120).map_name))
  
@bot.command(aliases=['record', 'mtop', 'maptop', 'maprecord'], brief="Gets the map record for a given map and style", usage="[map] <style>")
@commands.cooldown(1, WR_COOLDOWN, commands.BucketType.user)
async def wr(ctx, arg, arg2=None):      
    await searchRecord(ctx, arg, 0, arg2)
    
@wr.error
async def wr_cooldown(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await cooldownMessage(ctx, error)

@bot.command(aliases=['brecord', 'btop', 'bonustop', 'bonusrecord'], brief="Gets the bonus record for a given map and style", usage="[map] <style>")
@commands.cooldown(1, WR_COOLDOWN, commands.BucketType.user)
async def bwr(ctx, arg, arg2=None):
    await searchRecord(ctx, arg, 1, arg2)
    
@bwr.error
async def bwr_cooldown(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await cooldownMessage(ctx, error)
   
@bot.command(brief="Gets all records for player of given Steam ID", usage="[steamid]")
@commands.cooldown(1, RECORDS_COOLDOWN, commands.BucketType.user)
async def records(ctx, arg, arg2=None):
    steamid3 = formatSteamID3(arg)
    if not arg2:
        style = 0
    else:
        style = getStyleID(arg2)
        if style == -1:
            await ctx.send("Error: Unknown style")
            return
        
    sql = "SELECT time, map FROM(SELECT a.map, a.time, COUNT(b.map) + 1 AS rank FROM playertimes a LEFT JOIN playertimes b ON a.time > b.time AND a.map = b.map AND a.style = b.style AND a.track = b.track WHERE a.auth = %s AND a.style = %s AND a.track = 0 GROUP BY a.map, a.time, a.jumps, a.id, a.points  ORDER BY a.map ASC) AS t WHERE rank = 1 ORDER BY map ASC;"
    conn = mysql.connector.connect(**db)
    cursor = conn.cursor()
    cursor.execute(sql, (steamid3, style))
    results = cursor.fetchall()
    
    sql = "SELECT name FROM users WHERE auth = %s;"
    conn = mysql.connector.connect(**db)
    cursor = conn.cursor()
    cursor.execute(sql, (steamid3,))
    player = cursor.fetchone()
    
    text = []
    text2 = ""
    embed = []
    pages = 0
    for count, row in enumerate(results, 1):
        time = formatSeconds(row[0])   

        text2 += "\n" + row[1] + ": " + str(time) 
      
        if count % 25 == 0:
            pages += 1
            text.append(text2)
            text2 = ""
            
    text.append(text2) #final page of maps if count not multiple of 25
    pages += 1
    
    emojis = ['\u25c0', '\u25b6']
    
    embed=discord.Embed(title="MAP RECORDS - " + getStyleName(style) + "\nPlayer: " + player[0], description=text[0], color=0xda190b)
    msg = await ctx.send(embed=embed) 
    
    def check(reaction, user):
        return user == ctx.message.author and (str(reaction.emoji) in emojis and reaction.message.id == msg.id)
    
    j = 0
    while True:
        await msg.add_reaction('\u25c0')
        await msg.add_reaction('\u25b6')
        
        reaction, user = await bot.wait_for('reaction_add', check=check)
        if str(reaction.emoji) == "\u25c0":  
            if j == 0:
                j = pages - 1
                embed=discord.Embed(title="MAP RECORDS - " + getStyleName(style) + "\nPlayer: " + player[0], description=text[j], color=0xda190b)
                await msg.edit(embed=embed)
            else:
                j -= 1
                embed=discord.Embed(title="MAP RECORDS - " + getStyleName(style) + "\nPlayer: " + player[0], description=text[j], color=0xda190b)
                await msg.edit(embed=embed)
            await msg.clear_reactions()
        if str(reaction.emoji) == "\u25b6":
            if j == pages - 1:
                j = 0
                embed=discord.Embed(title="MAP RECORDS - " + getStyleName(style) + "\nPlayer: " + player[0], description=text[j], color=0xda190b)
                await msg.edit(embed=embed)
            else:
                j += 1
                embed=discord.Embed(title="MAP RECORDS - " + getStyleName(style) + "\nPlayer: " + player[0], description=text[j], color=0xda190b)
                await msg.edit(embed=embed)
            await msg.clear_reactions()
    
    conn.close()
    cursor.close()
  
@records.error
async def records_cooldown(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await cooldownMessage(ctx, error)
        
async def searchRecord(ctx, mapname, track, style):
    conn = mysql.connector.connect(**db)
    cursor = conn.cursor()
    
    if not style:
        styleid = 0
    else:
        styleid = getStyleID(style)
        if styleid == -1:
            await ctx.send("Error: Unknown style")
            return

    sql = "SELECT time, jumps, sync, strafes, date, map, u.name, p.auth FROM " + TABLE_PREFIX + "playertimes p, " + TABLE_PREFIX + "users u WHERE map = %s AND track = %s AND style = %s AND u.auth = p.auth ORDER BY time ASC LIMIT 1"
    cursor.execute(sql, (mapname, track, styleid))
    results = cursor.fetchone()
    if results:
        await printRecord(ctx, results, track, styleid)
    else:
        sql = "SELECT time, jumps, sync, strafes, date, map, u.name, p.auth FROM " + TABLE_PREFIX + "playertimes p, " + TABLE_PREFIX + "users u WHERE map LIKE %s AND track = %s AND style = %s AND u.auth = p.auth ORDER BY time ASC LIMIT 1"  
        cursor.execute(sql, ('%' + mapname + '%', track, styleid))
        results = cursor.fetchone()
        if results:
            await printRecord(ctx, results, track, styleid)
        else:
            await ctx.send("No records found for " + mapname)
    
    conn.close()
    cursor.close()
        
async def printRecord(ctx, results, track, style):      
    time = results[0]
    jumps = str(results[1])
    sync = str(results[2])
    strafes = str(results[3])
    timestamp = results[4]
    mapname = str(results[5])
    user = str(results[6]) 
    auth = results[7]
    
    if track == 0:
        trackName = "Map"
        trackColour = 0x1183f4
    else:
        trackName = "Bonus"
        trackColour = 0xe79f0c
        
    time = formatSeconds(results[0])
    date_time = datetime.fromtimestamp(timestamp)
    d = date_time.strftime("%d/%m/%Y")  
    steamid = SteamID(auth)
    link = "http://www.steamcommunity.com/profiles/" + str(steamid.as_64)
    
    if STATS_PAGE:
        statslink = STATS_PAGE + "/?track=" + str(track) + "&map=" + mapname + "&style=" + str(style)
        embed=discord.Embed(title=trackName + " Record - " + getStyleName(style), description="[" + mapname + "](" + statslink + ")", color=trackColour)
    if not STATS_PAGE:
        embed=discord.Embed(title=trackName + " Record - " + getStyleName(style), description=mapname, color=trackColour)
        
    embed.set_thumbnail(url=ICON)
    embed.set_footer(text="Join: steam://connect/" + IP + ":" + str(PORT))
    embed.add_field(name="Player‎‎", value="[" + user + "](" + link + ")", inline=True)
    embed.add_field(name="Time", value=time, inline=True)
    embed.add_field(name="Jumps", value=jumps, inline=True)
    embed.add_field(name="Sync", value=sync + "%", inline=True)
    embed.add_field(name="Strafes", value=strafes, inline=True)
    embed.add_field(name="Date", value=d, inline=True)
    
    await ctx.send(embed=embed)

@bot.command(brief="Shows the top 10 ranked players")
async def top(ctx):
    conn = mysql.connector.connect(**db)
    cursor = conn.cursor()
    sql = "SELECT name, points from users ORDER BY points DESC LIMIT 10"
    cursor.execute(sql)
    results = cursor.fetchall()
    embed=discord.Embed(title="Top Players", color=0xda190b)
    embed.add_field(name="Rank", value=formatRank(results), inline=True)
    embed.add_field(name="Name", value=formatName(results), inline=True)
    embed.add_field(name="Points", value=formatPoints(results), inline=True)
    
    await ctx.send(embed=embed)

@bot.command(brief="Randomly generates an SSJ")
@commands.cooldown(1, SSJ_COOLDOWN, commands.BucketType.user)
async def ssj(ctx):
    num = random.randint(480,700)       
    
    await ctx.send(ctx.message.author.mention + " has a SSJ of " + str(num))
   
@ssj.error
async def ssj_cooldown(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await cooldownMessage(ctx, error)
        
def formatSeconds(time):
    minutes = time / 60
    i, d = divmod(minutes, 1)
    seconds = d * 60
    minutes = math.trunc(i)
    seconds = round(seconds, 3)
    if time > 59:
        formatted = str(minutes) + ":" + str(seconds) 
    else:
        formatted = str(seconds) 
        
    return formatted
        
def formatSteamID3(arg):
    my_id = SteamID(arg) 
    steamid3 = str(my_id.as_32)
    
    return steamid3
 
def getStyleID(style):
    for i in range(len(alias)):
        if style.lower() in alias[i]:
            return i      
    return -1        

def getStyleName(styleid):
    return stylename[styleid]
    
def formatRank(results):
    rank = ""
    for count, row in enumerate(results, 1):
        rank += "#" + str(count) + "\n"
    return rank
    
def formatName(results):
    name = ""
    for count, row in enumerate(results, 1):
        name += str(row[0]) + "\n"
    return name
    
def formatPoints(results):
    points = ""
    for count, row in enumerate(results, 1):
        points += str(row[1]) + "\n"
    return points

async def cooldownMessage(ctx, error):
    msg = 'This command is on cooldown, please try again in {:.2f}s'.format(error.retry_after)
    await ctx.send(msg)
        
bot.run(TOKEN)
