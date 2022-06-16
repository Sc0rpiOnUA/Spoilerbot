import discord
import os
import random
import re
from string import punctuation
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_choice, create_option
from replit import db
from inspirobot import Inspirobot
from keep_alive import keep_alive

prefix = "$"
basic_color = 0x98ff98 # - Mint Green

client = commands.Bot(command_prefix=prefix, help_command=None)
slash = SlashCommand(client, sync_commands=True)
inspiro = Inspirobot(client)

#Commands for help menu
help_description = f"Currently available commands for Spoilerbot\n\n\
**Spoilerbot supports slash commands!**\n\
To access them, use `/` instead of the prefix `{prefix}`\n"

general_commands = f"\
`{prefix}help` - list all the available commands\n\
`{prefix}ping` - get the response from the bot\n\
`{prefix}servertime` - get the time of the server (used for scheduling inspiropics)"

autospoilering_commands = f"\
`{prefix}aslist` - list all autospoiled channels\n\
`{prefix}ason` - turn ON autospoilering in the current channel\n\
`{prefix}asoff` - turn OFF autospoilering in the current channel"

inspire_commands = f"\
`{prefix}inspiroquote` - get an inspirational quote\n\
`{prefix}inspiropic` - get an image from Inspirobot\n\
`{prefix}apicnew [Server time]` - schedule an automatic Inspiropic every day for the specified time\n\
`{prefix}apiclist` - list all scheduled Inspiropics on the server\n\
`{prefix}apicdel [Index]` - delete scheduled Inspiropic time at an index"

encouragement_commands = f"\
`{prefix}elist` - list all the custom encouragements\n\
`{prefix}enew [Encouraging message]` - add a custom encouragement\n\
`{prefix}edelete [Index]` - delete custom encouragement at an index"

help_menu = {
  "General" : general_commands,
  "Autospoilering" : autospoilering_commands,
  "Inspiration" : inspire_commands,
  "Encouragements" : encouragement_commands
}

sad_words = [
  "sad",
  "depressed",
  "unhappy",
  "angry",
  "mad",
  "miserable",
  "destroyed"]

starter_encouragements = [
  "Cheer up!",
  "Hang in there!",
  "You are awesome!"]

split_symbols = punctuation
split_symbols += " "
#-----------------------General functions-----------------------

def list_encouragements():
  if "encouragements" in db.keys():
    encouragements = list(db["encouragements"])
  else:
    encouragements = list()

  encouragements_message = ""
  counter = 1

  if encouragements:
    for encouragement in encouragements:
      encouragements_message += f"{str(counter)}. {encouragement}\n"
      counter += 1
  else:
    encouragements_message = f"No custom encouragements yet. Type ``{prefix}new`` to add some."
  return encouragements_message

def update_encouragements(encouraging_message):
  if "encouragements" in db.keys():
    encouragements = db["encouragements"]
    encouragements.append(encouraging_message)
    db["encouragements"] = encouragements
  else:
    db["encouragements"] = [encouraging_message]

def delete_encouragement(index):
  if "encouragements" in db.keys():    
    encouragements = db["encouragements"]
    if encouragements and index >= 0 and index < len(encouragements) :
      del encouragements[index]
      db["encouragements"] = encouragements
      return "Encouragement deleted successfully!"
    elif not encouragements:
      return f"No custom encouragements yet. Type ``{prefix}new`` to add some."
    else:
      return "Index out of range."
  else:
    return f"No custom encouragements yet. Type ``{prefix}new`` to add some."

def new_spoiler_channels(server_id, channel, all_channels):
  if all_channels == True:
    db[f"{server_id}_autospoilering_all"] = "True"
  else:
    db[f"{server_id}_autospoilering_all"] = "False"
    db[f"{server_id}_{channel}_autospoilering"] = "True"

#!!!!!!!!!!!!!!!!!!!!!! Splitting needs rework !!!!!!!!!!!!!!!!!!!!!!!!!
def list_spoiler_channels(server_id):
  all_autospoiled = False
  channels = []
  server_options = db.prefix(server_id)
  for server_option in server_options:
    sections = server_option.split('_')
    if server_option == f"{server_id}_autospoilering_all" and db[server_option] == "True":
      all_autospoiled = True
    elif sections[2] == "autospoilering" and db[server_option] == "True":
      channels.append(sections[1])
  return channels, all_autospoiled

def delete_spoiler_channels(server_id, channel, all_channels):
  if all_channels == True:
    server_options = db.prefix(server_id)
    if f"{server_id}_autospoilering_all" in db.keys():
      db[f"{server_id}_autospoilering_all"] = "False"
    for server_option in server_options:
      sections = server_option.split('_')
      if sections[2] == "autospoilering":
        db[server_option] = "False"
  else:
    if f"{server_id}_autospoilering_all" in db.keys():
      db[f"{server_id}_autospoilering_all"] = "False"
    if f"{server_id}_{channel}_autospoilering" in db.keys():
      db[f"{server_id}_{channel}_autospoilering"] = "False"

def new_autoinspiropic_time(server_id, channel, server_time):
  index = 0
  while f"{server_id}_{channel}_autoinspiropic_{index}" in db.keys():
    index += 1
  db[f"{server_id}_{channel}_autoinspiropic_{index}"] = server_time

def list_autoinspiropic_times(server_id):
  channels = []
  server_options = db.prefix(server_id)
  counter = 1
  for server_option in server_options:
    sections = server_option.split('_')
    if sections[2] == "autoinspiropic":
      channels.append(f"{counter}. {sections[1]} ({sections[3]}) - {db[server_option]}")
      counter += 1
  return channels

def delete_autoinspiropic_time(server_id, index):
  options_list = [option for option in db.prefix(server_id) if option.split('_')[2] == "autoinspiropic"]  

  if index < 0 or index > len(options_list):
    return "Index out of bounds!"
  else:
    index -= 1
    del db[options_list[index]]
    return "Time deleted successfully!"
      

def create_standard_embed(embed_title, embed_description, embed_color):
  new_embed = discord.Embed(title=embed_title, description=embed_description, color=embed_color)
  return new_embed

#---------------------Commands functions---------------------

def create_help_embed():
  help_embed = create_standard_embed("Spoilerbot Help", help_description, basic_color)
  for section_name, section_value in help_menu.items():
    help_embed.add_field(name=section_name, value=section_value, inline=False)
  return help_embed

def create_inspiroquote_embed():
  quote = inspiro.get_inspiroquote()
  inspire_embed = create_standard_embed(quote[0], " -" + quote[1], basic_color)
  return inspire_embed

def create_encouragements_embed():
  encouragements_embed = create_standard_embed("Custom encouragements:", list_encouragements(), basic_color)
  return encouragements_embed

def add_new_encouragement(encouraging_message):
  update_encouragements(encouraging_message)
  new_encouragement_embed = create_standard_embed("Adding encouragement...", "New encouraging message added!", basic_color)
  return new_encouragement_embed

def delete_encouragement_embed(index):
  deletion_embed = create_standard_embed("Deleting encouragement...", delete_encouragement(int(index)-1), basic_color)
  return deletion_embed

def create_spoilered_embed(ctx):
  server_id = ctx.guild.id
  spoiled_channels = list_spoiler_channels(server_id)
  if spoiled_channels[1] == True:
    new_spoiler_embed = create_standard_embed("Autospoilered channels:", "All channels are being autospoilered!", basic_color)
  else:
    new_line = "\n"
    new_spoiler_embed = create_standard_embed("Autospoilered channels:", f"{new_line.join(spoiled_channels[0])}", basic_color)
  return new_spoiler_embed

def spoiler_the_channel(ctx):
  channel = ctx.channel
  server_id = ctx.guild.id
  new_spoiler_channels(server_id, channel, False)
  new_spoiler_embed = create_standard_embed("Enabling autospoilering...", f"Autospoilering for {channel.mention} channel enabled!", basic_color)
  return new_spoiler_embed

def unspoiler_the_channel(ctx):
  channel = ctx.channel
  server_id = ctx.guild.id
  delete_spoiler_channels(server_id, channel, False)
  new_spoiler_embed = create_standard_embed("Disabling autospoilering...", f"Autospoilering for {channel.mention} channel disabled!", basic_color)
  return new_spoiler_embed

def autoinspiropic_the_channel(ctx, server_time):
  channel = ctx.channel
  server_id = ctx.guild.id
  new_autoinspiropic_time(server_id, channel, server_time)
  new_autoinspiropic_embed = create_standard_embed("Scheduling inspiropics for the channel...", f"Inspiropics for {channel.mention} channel at {server_time} scheduled!", basic_color)
  return new_autoinspiropic_embed

def create_autoinspiropic_embed(ctx):
  server_id = ctx.guild.id
  autopic_channels = list_autoinspiropic_times(server_id)
  new_line = "\n"
  new_autoinspiropic_embed = create_standard_embed("Scheduled inspiropics for the server (UTC time):", f"{new_line.join(autopic_channels)}", basic_color)
  return new_autoinspiropic_embed

def delete_autoinspiropic_embed(ctx, index):
  server_id = ctx.guild.id
  result = delete_autoinspiropic_time(server_id, index)
  new_autoinspiropic_embed = create_standard_embed("Deleting inspiropics for the channel...", result, basic_color)
  return new_autoinspiropic_embed
#--------------------------------------------------------------

@client.event
async def on_ready():
  print("We have logged in as {0.user}".format(client))
  await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{prefix}help"))
  keep_alive()
  await inspiro.run()
  #await send_Hello()
#--------------------------------------------------------------

@client.listen("on_message")
async def autospoilering(message):
  msg = message.content
  attachments = message.attachments
  author = message.author

  if author == client.user:
    return  

  if attachments:
    server_id = message.guild.id
    channel = message.channel
    if (f"{server_id}_{channel}_autospoilering" in db.keys() and db[f"{server_id}_{channel}_autospoilering"] == "True") or\
    (f"{server_id}_autospoilering_all" in db.keys() and db[f"{server_id}_autospoilering_all"] == "True"):
      await message.delete()
      for attachment in attachments:
        message_text = "**From** " + author.mention + "\n\n" + msg
        file = attachment
        file.filename = f"SPOILER_{file.filename}"
        spoiler = await file.to_file()      
        await message.channel.send(content=message_text, file=spoiler)

@client.listen("on_message")
async def encouraging(message):
  msg = message.content 
  options = starter_encouragements

  if message.author == client.user:
    return 

  if "encouragements" in db.keys():
    options = options + list(db["encouragements"])

  if any(word in re.split(f'[{split_symbols}]', msg.lower()) for word in sad_words):
    await message.channel.send(random.choice(options))
  #========================Slash commands========================

#For faster slash commands update, use guild IDs inside slash.slash():
#guild_ids=[int(os.environ['ID_Test']), int(os.environ['ID_SPeach'])]
  
#Ping
@slash.slash(
  name="ping",
  description="Ping",
  guild_ids=[int(os.environ['ID_Test']), int(os.environ['ID_SPeach'])]
)
async def _ping(ctx:SlashContext):
  await ctx.send("Pong!")

#Help menu
@slash.slash(
  name="help",
  description="Displays help commands",
  guild_ids=[int(os.environ['ID_Test']), int(os.environ['ID_SPeach'])]
)
async def _help(ctx:SlashContext):  
  await ctx.send(embed=create_help_embed())

@client.command()
async def help(ctx): 
  await ctx.channel.send(embed=create_help_embed())

#Get quote from Inspirobot
@slash.slash(
  name="inspiroquote",
  description="Get quote from Inspirobot",
  guild_ids=[int(os.environ['ID_Test']), int(os.environ['ID_SPeach'])]
)
async def _inspiroquote(ctx:SlashContext):  
  await ctx.send(embed=create_inspiroquote_embed())

@client.command()
async def inspiroquote(ctx):
  await ctx.channel.send(embed=create_inspiroquote_embed())

#Get a picture from Inspirobot
@slash.slash(
  name="inspiropic",
  description="Get a picture from Inspirobot",
  guild_ids=[int(os.environ['ID_Test']), int(os.environ['ID_SPeach'])]
)
async def _inspiropic(ctx:SlashContext):  
  await ctx.send(inspiro.get_inspiropic())

@client.command()
async def inspiropic(ctx):
  await ctx.channel.send(inspiro.get_inspiropic())

#List custom encouragements
@slash.slash(
  name="elist",
  description="List custom encouragements",
  guild_ids=[int(os.environ['ID_Test']), int(os.environ['ID_SPeach'])]
)
async def _elist(ctx:SlashContext):  
  await ctx.send(embed=create_encouragements_embed())

@client.command()
async def elist(ctx):
  await ctx.channel.send(embed=create_encouragements_embed())

#Add new encouragement
@slash.slash(
  name="enew",
  description="Add new encouragement",
  guild_ids=[int(os.environ['ID_Test']), int(os.environ['ID_SPeach'])],
  options=[
    create_option(
      name="encouragement",
      description="New encouragement!",
      required=True,
      option_type=3
    )
  ]
)
async def _enew(ctx:SlashContext, *, encouragement:str):  
  await ctx.send(embed=add_new_encouragement(encouragement))

@client.command()
async def enew(ctx, *, encouragement):
  await ctx.channel.send(embed=add_new_encouragement(encouragement))

#Delete encouragement
@slash.slash(
  name="edelete",
  description="Delete encouragement from index",
  guild_ids=[int(os.environ['ID_Test']), int(os.environ['ID_SPeach'])],
  options=[
    create_option(
      name="index",
      description="Encouragement index",
      required=True,
      option_type=4
    )
  ]
)
async def _edelete(ctx:SlashContext, index:int):  
  await ctx.send(embed=delete_encouragement_embed(index))

@client.command()
async def edelete(ctx, index):
  await ctx.channel.send(embed=delete_encouragement_embed(index))

#List spoilered channels
@slash.slash(
  name="aslist",
  description="List channels with automatic spoilering",
  guild_ids=[int(os.environ['ID_Test']), int(os.environ['ID_SPeach'])]
)
async def _aslist(ctx:SlashContext):  
  await ctx.send(embed=create_spoilered_embed(ctx))

@client.command()
async def aslist(ctx):
  await ctx.channel.send(embed=create_spoilered_embed(ctx))

#Enable autospoilering
@slash.slash(
  name="ason",
  description="Enable autospoilering on this channel",
  guild_ids=[int(os.environ['ID_Test']), int(os.environ['ID_SPeach'])]
)
async def _ason(ctx:SlashContext):  
  await ctx.send(embed=spoiler_the_channel(ctx))

@client.command()
async def ason(ctx):
  await ctx.channel.send(embed=spoiler_the_channel(ctx))

#Disable autospoilering
@slash.slash(
  name="asoff",
  description="Disable autospoilering on this channel",
  guild_ids=[int(os.environ['ID_Test']), int(os.environ['ID_SPeach'])]
)
async def _asoff(ctx:SlashContext):  
  await ctx.send(embed=unspoiler_the_channel(ctx))

@client.command()
async def asoff(ctx):
  await ctx.channel.send(embed=unspoiler_the_channel(ctx))

#Schedule automatic inspiropics for the channel
@slash.slash(
  name="apicnew",
  description="Schedule inspiropics for the channel",
  guild_ids=[int(os.environ['ID_Test']), int(os.environ['ID_SPeach'])],
  options=[
    create_option(
      name="server_time",
      description="Time (on server) when you want daily inspiropics",
      required=True,
      option_type=3
    )
  ]
)
async def _apicnew(ctx:SlashContext, server_time:str):  
  await ctx.send(embed=autoinspiropic_the_channel(ctx, server_time))

@client.command()
async def apicnew(ctx, server_time:str):
  await ctx.channel.send(embed=autoinspiropic_the_channel(ctx, server_time))

#List channels with automatic inspiropics
@slash.slash(
  name="apiclist",
  description="List channels with automatic inspiropics",
  guild_ids=[int(os.environ['ID_Test']), int(os.environ['ID_SPeach'])]
)
async def _apiclist(ctx:SlashContext):  
  await ctx.send(embed=create_autoinspiropic_embed(ctx))

@client.command()
async def apiclist(ctx):
  await ctx.channel.send(embed=create_autoinspiropic_embed(ctx))

#Delete automatic inspiropics by index
@slash.slash(
  name="apicdel",
  description="Delete autoinspiropics time at a given index",
  guild_ids=[int(os.environ['ID_Test']), int(os.environ['ID_SPeach'])],
  options=[
    create_option(
      name="index",
      description="Index of inspiropic time you wish to remove",
      required=True,
      option_type=4
    )
  ]
)
async def _apicdel(ctx:SlashContext, index:str):  
  await ctx.send(embed=delete_autoinspiropic_embed(ctx, index))

@client.command()
async def apicdel(ctx, index:str):
  await ctx.channel.send(embed=delete_autoinspiropic_embed(ctx, index))

#Get server time
@slash.slash(
  name="servertime",
  description="Display server time",
  guild_ids=[int(os.environ['ID_Test']), int(os.environ['ID_SPeach'])]
)
async def _servertime(ctx:SlashContext):  
  await ctx.send(embed=create_standard_embed("🕑 Server time:", inspiro.get_local_time(), basic_color))

@client.command()
async def servertime(ctx):
  await ctx.channel.send(embed=create_standard_embed("🕑 Server time:", inspiro.get_local_time(), basic_color))
#==============================================================


client.run(os.environ['TOKEN'])
