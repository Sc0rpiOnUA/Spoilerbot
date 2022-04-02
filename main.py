import discord
import os
import random
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
`{prefix}help` - list all the available commands"

autospoilering_commands = f"\
`{prefix}aslist` - list all autospoiled channels\n\
`{prefix}ason` - turn ON autospoilering in the current channel\n\
`{prefix}asoff` - turn OFF autospoilering in the current channel"

inspire_commands = f"\
`{prefix}inspiroquote` - get an inspirational quote\n\
`{prefix}inspiropic` - get an image from inspirobot"

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
    if sections[1] + "_" + sections[2] == "autospoilering_all" and db[server_option] == "True":
      all_autospoiled = True
    if sections[2] == "autospoilering" and db[server_option] == "True":
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

def create_standard_embed(embed_title, embed_description, embed_color):
  new_embed = discord.Embed(title=embed_title, description=embed_description, color=embed_color)
  return new_embed
#--------------------------------------------------------------

@client.event
async def on_ready():
  print("We have logged in as {0.user}".format(client))
  await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{prefix}help"))
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

  if any(word in msg.lower() for word in sad_words):
    await message.channel.send(random.choice(options))
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
#========================Slash commands========================

#For faster slash commands update, use guild IDs inside slash.slash():
#guild_ids=[525370181074157578, 813813645351059456]
  
#Ping
@slash.slash(
  name="ping",
  description="Ping",
  guild_ids=[525370181074157578, 813813645351059456]
)
async def _ping(ctx:SlashContext):
  await ctx.send("Pong!")

#Help menu
@slash.slash(
  name="help",
  description="Displays help commands",
  guild_ids=[525370181074157578, 813813645351059456]
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
  guild_ids=[525370181074157578, 813813645351059456]
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
  guild_ids=[525370181074157578, 813813645351059456]
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
  guild_ids=[525370181074157578, 813813645351059456]
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
  guild_ids=[525370181074157578, 813813645351059456],
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
  guild_ids=[525370181074157578, 813813645351059456],
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
  guild_ids=[525370181074157578, 813813645351059456]
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
  guild_ids=[525370181074157578, 813813645351059456]
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
  guild_ids=[525370181074157578, 813813645351059456]
)
async def _asoff(ctx:SlashContext):  
  await ctx.send(embed=unspoiler_the_channel(ctx))

@client.command()
async def asoff(ctx):
  await ctx.channel.send(embed=unspoiler_the_channel(ctx))
#==============================================================

keep_alive()
inspiro.run()
client.run(os.environ['TOKEN'])