import socket, threading, json, time, uuid, os
from datetime import datetime
from common.crypto_utils import *
from common.constants import *

devices = {}
current_version = 1
lock = threading.Lock()
db_file = "devices_db.json"

def save():
    with open(db_file, "w") as f:
        json.dump({"devices": devices, "version": current_version}, f, indent=2)

def load():
    global devices, current_version
    if os.path.exists(db_file):
        try:
            with open(db_file) as f:
                data = json.load(f)
                devices.clear()
                devices.update(data.get("devices", {}))
                current_version = data.get("version", 1)
        except:
            pass

def handle(conn, addr):
    try:
        conn.send(b"HI")
        client_pub = load_pubkey(conn.recv(4096))
        priv, pub = generate_ecdh_pair()
        conn.send(serialize_pubkey(pub))
        fernet = derive_key(priv, client_pub)

        msg = json.loads(fernet.decrypt(conn.recv(4096)))
        dev_id = str(uuid.uuid4())[-8:]

        with lock:   # only lock the critical section
            devices[dev_id] = {
                "id": dev_id, "name": msg["name"], "ip": addr[0],
                "status": "Active", "key_version": current_version,
                "last_seen": datetime.now().isoformat()
            }
        save()
        conn.send(fernet.encrypt(json.dumps({"type":"OK","id":dev_id,"version":current_version}).encode()))
        print(f"[+] {msg['name']} → {dev_id}")

        while True:
            try:
                data = conn.recv(4096)
                if not data: break
                msg = json.loads(fernet.decrypt(data))
                if msg["type"] == "PING":
                    with lock:
                        if dev_id in devices:
                            devices[dev_id]["last_seen"] = datetime.now().isoformat()
                    save()
            except:
                break
    except Exception as e:
        pass
    finally:
        conn.close()

# Auto-Rotation Thread
def rotation():
    global current_version
    while True:
        time.sleep(10)
        with lock:
            if any(d["status"]=="Active" for d in devices.values()):
                current_version += 1
                for d in devices.values():
                    if d["status"] == "Active":
                        d["key_version"] = current_version
                save()
                print(f"[AUTO ROTATION] → version {current_version}")

threading.Thread(target=rotation, daemon=True).start()

load()
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 8888))
s.listen()
print("[SERVER] Running on port 8888 – READY")

while True:
    conn, addr = s.accept()
    threading.Thread(target=handle, args=(conn, addr), daemon=True).start()