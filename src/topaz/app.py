#!/usr/bin/env python
# encoding: utf-8

from flask import Flask, render_template, request
import json
from pymongo import Connection

databaseName = "topaz_bi"
connection = Connection()
db = connection[databaseName]
status_runtime = db['dut_running']

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/newstatus', methods=['GET', 'POST'])
def newstatus():
    status_list = []
    for e in status_runtime.find():
        last_status = {"ID": e["_id"] + 1, "PWRCYCS": None,
                       "STATUS": e["STATUS"], "CYCLE": None, "FWVER": None,
                       "HWVER": None, "SN": None, "MODEL": None,
                       "VCAP": None, "TEMP": None}
        if "PWRCYCS" in e:
            last_status["PWRCYCS"] = e["PWRCYCS"]
            last_status["CYCLE"] = e["PWRCYCS"] + 1
            last_status["FWVER"] = e["FWVER"]
            last_status["HWVER"] = e["HWVER"]
            last_status["SN"] = e["SN"]
            last_status["MODEL"] = e["MODEL"]
            cycles = "CYCLES" + str(e["PWRCYCS"] + 1)
            if cycles in e:
                cycles_list = e["CYCLES" + str(e["PWRCYCS"] + 1)]
                last_cycle = cycles_list[len(cycles_list) - 1]
                # last_cycle = cycles_list.pop()
                last_status["VCAP"] = last_cycle["VCAP"]
                last_status["TEMP"] = last_cycle["TEMP"]
        status_list.append(last_status)
    return json.dumps(status_list)


@app.route('/chart_data', methods=['GET', 'POST'])
def chart_data():
    result = {"time": [],
              "vcap": [],
              "temp": [],
              "cycle": 0}
    id = request.args.get('id', type=int)
    dut_data = status_runtime.find_one({"_id": id - 1})
    if dut_data is not None:
        if "PWRCYCS" in dut_data:
            result["cycle"] = dut_data["PWRCYCS"] + 1
            cycles = "CYCLES" + str(dut_data["PWRCYCS"] + 1)
            if cycles in dut_data:
                for e in dut_data["CYCLES" + str(dut_data["PWRCYCS"] + 1)]:
                    result["time"].append(round(e["TIME"], 2))
                    result["vcap"].append(round(e["VCAP"], 2))
                    result["temp"].append(round(e["TEMP"], 2))
    return json.dumps(result)


if __name__ == "__main__":
    app.run(debug=True)
