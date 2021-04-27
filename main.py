import discord
import os
import requests
import json
import random
from discord.ext import commands
from replit import db
from keep_alive import keep_alive

prefix = "$"
basic_color = 0x98ff98 # - Mint Green

client = commands.Bot(command_prefix=prefix, help_command=None)

#Commands for help menu
help_description = "Currently available commands for Spoilerbot"

general_commands = f"\
`{prefix}help` - list all the available commands"

inspire_commands = f"\
`{prefix}inspiroquote` - get an inspirational quote\n\
`{prefix}inspiropic` - get an image from inspirobot"

encouragement_commands = f"\
`{prefix}elist` - list all the custom encouragements\n\
`{prefix}enew [Encouraging message]` - add a custom encouragement\n\
`{prefix}edelete [Index]` - delete custom encouragement at an index"

help_menu = {
  "General" : general_commands,
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
#--------------------------------------------------------------

def get_inspiroquote():
  response = requests.get\
  ("https://zenquotes.io/api/random")
  json_data = json.loads(response.text)
  quote = json_data[0]['q']
  author = json_data[0]['a']
  return quote, author

def get_inspiropic():
  response = requests.get\
  ("https://inspirobot.me/api?generate=true")  
  return response.text

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
#--------------------------------------------------------------

@client.command()
async def help(ctx):
  help_embed = create_standard_embed("Spoilerbot Help", help_description, basic_color)
  for section_name, section_value in help_menu.items():
    help_embed.add_field(name=section_name, value=section_value, inline=False)
  await ctx.channel.send(embed=help_embed)

@client.command()
async def inspiroquote(ctx):
  quote = get_inspiroquote()
  inspire_embed = create_standard_embed(quote[0], " -" + quote[1], basic_color)
  await ctx.channel.send(embed=inspire_embed)

@client.command()
async def inspiropic(ctx):
  await ctx.channel.send(get_inspiropic())

@client.command()
async def elist(ctx):
  encouragements_embed = create_standard_embed("Custom encouragements:", list_encouragements(), basic_color)      
  await ctx.channel.send(embed=encouragements_embed)

@client.command()
async def enew(ctx, encouraging_message):
  update_encouragements(encouraging_message)
  new_encouragement_embed = create_standard_embed("Adding encouragement...", "New encouraging message added!", basic_color)
  await ctx.channel.send(embed=new_encouragement_embed)

@client.command()
async def edelete(ctx, index):
  deletion_embed = create_standard_embed("Deleting encouragement...", delete_encouragement(index), basic_color)  
  await ctx.channel.send(embed=deletion_embed)

@client.command()
async def spoilcc(ctx):
  channel = ctx.channel
  server_id = ctx.guild.id
  new_spoiler_channels(server_id, channel, False)
  new_spoiler_embed = create_standard_embed("Spoilering channel...", f"Autospoilering for {channel.mention} channel enabled!", basic_color)
  await ctx.channel.send(embed=new_spoiler_embed)
#===========================================================

keep_alive()
client.run(os.environ['TOKEN'])
