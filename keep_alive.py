from flask import Flask
from threading import Thread
from replit import db

app = Flask('')

@app.route('/')
def home():
  table = "<b>Database:</b><br/><br/>"
  table += '<table border="1">\
  <tr>\
  <th>Key</th>\
  <th>Value</th>\
  </tr>'
  for key in db.keys():
    table += f"<tr><td>{key}</td><td>{db[key]}</td></tr>"
  table += "</table>"
  return table

def run():
  app.run(host='0.0.0.0',port=8080)  

def keep_alive():
    t = Thread(target=run)
    t.start()