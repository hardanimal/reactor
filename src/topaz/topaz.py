#!/usr/bin/env python
# encoding: utf-8

from flask import Flask, render_template, request
import json
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/getstatus')
def getstatus():
    response = {"name": 'DUT1',
                "data": [7.0, 6.9, 9.5, 14.5, 18.2, 21.5, 25.2, 26.5, 23.3, 18.3, 13.9, 9.6]}
    name = request.args.get("name", "", type=str)
    if name == response["name"]:
        response.update({"result": "pass"})
        return json.dumps(response)
    else:
        return json.dumps({"name": name,
                           "result": "fail",
                           "data": []})

if __name__ == "__main__":
    app.run(debug=True)
