#!/usr/bin/env python
# encoding: utf-8

from flask import Flask, render_template, request
import json
import random
from pymongo import Connection

databaseName = "TOPAZ"
connection = Connection()
db = connection[databaseName]
status_runtime = db['statusruntime']

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/newstatus', methods=['GET', 'POST'])
def newstatus():
    status_list = []
    for e in status_runtime.find().sort("_id"):
        status_list.append(e)
    return json.dumps(status_list)

if __name__ == "__main__":
    app.run(debug=True)

# @app.route('/getstatus')
# def getstatus():
# #     response = {"name": 'DUT1',
# #                 "data": random.sample([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 10)}
#     name = request.args.get("name", "", type=str)
#     response = status_runtime.find_one({'_id': int(name)})
#     if (int(name) == response["_id"]):
#         return json.dumps(response)
#     else:
#         return json.dumps({"name": name,
#                            "CYCLES": [{
#                                        "TIME":[],
#                                        "VCAP":[],
#                                        "TEMP":[]
#                                        }],
#                            })

# @app.route('/getinfo')
# def getinfo():
#     dutnum = request.args.get("dutnum", 0, type=int)
#     if (dutnum != 0):
#         dutinfo = {}
#         dutinfo.update(return_info())
#         return json.dumps({"name": dutnum,
#                            "info": dutinfo})
#     else:
#         return json.dumps({"dutnum": dutnum,
#                            "result": "fail"
#                            })
# 
# def return_info():
#     status = {
#               "SN" : ''.join(random.sample('zyxwvutsrqponmlkjihgfedcba', 8)),
#               "vol" : round(random.uniform(0, 20), 2),
#               "temp" : round(random.uniform(0, 20), 2),
#               }
#     return status
