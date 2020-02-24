# BhopTimer-Discord-Bot
Work in progress Discord bot with various commands, based off https://github.com/ryczek02/bhop-discord-bot

Current features: 
- !wr
- !bwr
- !ssj
- Bot status shows server player count

## CONFIG

```python
{
    "bot_token": "", 	#BOT TOKEN
    "command_prefix": "!", 		#BOT COMMAND PREFIX
    "embed_icon": "https://site.com/logo.png", 	#ICON FOR EMBED
    "server_ip": "XXX.XXX.XXX.XXX", 	#BHOP SERVER IP
    "server_port": 27015, 	#SERVER PORT
    "server_name": "", 		#SERVER NAME FOR BOT STATUS
    "db_ip": "XXX.XXX.XXX.XXX", 	#DATABASE IP
    "db_database": "database", 		#DATABASE 
    "db_user": "username", 		#DATABASE USER
    "db_pass": "password", 		#DATABASE PORT
    "table_prefix": "", 	#DATABASE TABLE PREFIX. LEAVE BLANK TO DISABLE
    "webstats_url": "https://mysite.com/stats" 		#BHOP WEBSTATS LINK. LEAVE BLANK TO DISABLE
}

```
