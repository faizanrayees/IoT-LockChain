from flask import Flask, render_template_string
import json, os, threading

app = Flask(__name__)
DB_FILE = "devices_db.json"
devices = {}
current_version = 1
lock = threading.Lock()

def load():
    global devices, current_version
    if os.path.exists(DB_FILE):
     with open(DB_FILE) as f:
         data = json.load(f)
         devices = data.get("devices", {})
         current_version = data.get("version", 1)

def save():
 with open(DB_FILE, "w") as f:
     json.dump({"devices": devices, "version": current_version}, f, indent=2)

load()

HTML = """<!DOCTYPE html>
<html><head><title>IoT LockChain</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<meta http-equiv="refresh" content="4">
<style>
 body{background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);color:#fff;min-height:100vh;font-family:Segoe UI}
 .card{border-radius:20px;box-shadow:0 15px 35px rgba(0,0,0,0.7)}
 .heartbeat{color:lime;font-size:32px;animation:pulse 1.5s infinite}
 @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.2}}
 .revoked{opacity:0.5;background:#300}
 footer{margin-top:120px;padding:30px;background:rgba(0,0,0,0.6);border-radius:20px}
</style></head><body><div class="container py-5">
<h1 class="text-center mb-2 text-warning display-2 fw-bold">IoT LockChain</h1>
<p class="text-center text-info mb-5 fs-3">Dynamic Key Management System</p>
<div class="row mb-5 g-5">
 <div class="col-lg-6"><div class="card bg-primary text-white h-100">
  <div class="card-body text-center p-5"><h2 class="display-5 fw-bold">Global Key Version</h2>
   <h1 class="display-1 fw-bold">{{ version }}</h1>
   <button class="btn btn-warning btn-lg px-5 fs-3 shadow" onclick="fetch('/rotate').then(()=>location.reload())">Force Rotation</button>
  </div></div></div>
 <div class="col-lg-6"><div class="card bg-info text-white h-100">
  <div class="card-body p-5"><h2 class="display-5 fw-bold">System Status</h2>
   <h1 class="display-3">{{ active }}</h1><p class="fs-3">Active Devices</p><p class="fs-3">Total: {{ total }}</p>
  </div></div></div></div>
<h2 class="mb-4 text-center fw-bold">Registered Devices</h2>
<div class="table-responsive rounded shadow"><table class="table table-dark table-striped table-hover fs-4">
 <thead class="table-danger"><tr><th>Device ID</th><th>Status</th><th>Heartbeat</th><th>Key Version</th><th>Action</th></tr></thead>
 <tbody>{% for dev in devices.values() %}
  <tr class="{{ 'revoked' if dev.status=='Revoked' else '' }}">
   <td><code class="text-warning fw-bold">{{ dev.id }}</code></td>
   <td><span class="badge bg-{{ 'danger' if dev.status=='Revoked' else 'success' }} fs-4">{{ dev.status }}</span></td>
   <td>{% if dev.status == 'Active' %}<span class="heartbeat">●</span>{% else %}—{% endif %}</td>
   <td class="text-center fw-bold">{{ dev.key_version }}</td>
   <td>{% if dev.status == 'Active' %}
    <button class="btn btn-danger btn-lg" onclick="fetch('/revoke/{{dev.id}}').then(()=>location.reload())">Revoke</button>
   {% else %}
    <button class="btn btn-success btn-lg" onclick="fetch('/activate/{{dev.id}}').then(()=>location.reload())">Activate</button>
   {% endif %}</td>
  </tr>{% endfor %}</tbody></table></div>
<footer class="text-center"><p class="fs-3 mb-0">Mohammed Asjad & Mohammed Rayees Ahmed • Computer Networks Project</p></footer>
</div></body></html>"""

@app.route("/")
def home():
    load()
    active = sum(1 for d in devices.values() if d["status"] == "Active")
    return render_template_string(HTML, version=current_version, devices=devices, active=active, total=len(devices))

@app.route("/rotate")
def rotate():
    global current_version
    with lock:
        current_version += 1
        for d in devices.values():
            if d["status"] == "Active":
                d["key_version"] = current_version
        save()
    return "OK"

@app.route("/revoke/<devid>")
def revoke(devid):
    with lock:
        if devid in devices:
            devices[devid]["status"] = "Revoked"
            save()
    return "OK"

@app.route("/activate/<devid>")
def activate(devid):
    with lock:
        if devid in devices:
            devices[devid]["status"] = "Active"
            devices[devid]["key_version"] = current_version
            save()
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)