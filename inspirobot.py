import discord
import requests
import json
import time
import asyncio
from replit import db

class Inspirobot:

  def __init__(self, client):
    self.client = client

  def get_inspiroquote(self):
    response = requests.get\
    ("https://zenquotes.io/api/random")
    json_data = json.loads(response.text)
    quote = json_data[0]['q']
    author = json_data[0]['a']
    return quote, author
  
  def get_inspiropic(self):
    response = requests.get\
    ("https://inspirobot.me/api?generate=true")  
    return response.text

  def seconds_till_next_minute(self):
    current_seconds = int(time.strftime("%S", time.localtime()))
    seconds_left = 60 - current_seconds
    return seconds_left

  def get_local_time(self):
    return time.strftime("%H:%M:%S", time.localtime())

  def get_UTC_time(self):
    return time.strftime("%H:%M:%S", time.gmtime())

  async def updater(self):
    while True:
      local_time = time.strftime("%H:%M", time.localtime())
      print(f"Current time: {local_time}")

      servers = [k for k, v in db.items() if v == local_time]
      if servers:
        for server in servers:
          sections = server.split('_')
          guild = self.client.get_guild(int(sections[0]))
          channel = discord.utils.get(guild.channels, name=sections[1])
          channel_id = channel.id 
          print(guild)
          print(channel)
          print(channel_id)
          if sections[2] == "autoinspiropic":
            await channel.send(self.get_inspiropic())
          elif sections[2] == "autoinspiroquote":
            await channel.send(self.get_inspiroquote())
                
      
      await asyncio.sleep(self.seconds_till_next_minute())

  async def run(self):        
    try:
      print("Starting loop")
      asyncio.get_event_loop().create_task(self.updater())
    except KeyboardInterrupt:
      pass
    finally:
      print("Do nothing")
      pass
