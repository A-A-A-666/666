from flask import Flask, jsonify
import os
import time
import subprocess

start_time = time.time()
target_host = "google.com"

app = Flask(__name__)

def get_uptime():
    return round(time.time() - start_time, 2)

def get_ping(host):
    try:
        result = subprocess.run(
            ["ping", "-c", "1", host],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "time=" in line:
                    return line.split("time=")[1].split(" ")[0]
        return "Ping failed"
    except Exception as e:
        return str(e)

@app.route('/')
def status():
    return jsonify({
        "status": "running",
        "uptime_seconds": get_uptime(),
        "ping_ms": get_ping(target_host)
    })

def start():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
