import discord
import os
import random
import requests
import json
import schedule
import time
from discord.ext import commands
from replit import db
from threading import Thread

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

  def updater(self):
      while True:
        UTC_time = time.gmtime(time.time())
        print(f"Current time: {UTC_time.tm_hour}:{UTC_time.tm_min}:{UTC_time.tm_sec}")
        time.sleep(59.9)

  def run(self):
    update_thread = Thread(target=self.updater)
    update_thread.start()
  
