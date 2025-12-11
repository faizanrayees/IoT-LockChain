import socket, threading, time, json, argparse, uuid
from common.crypto_utils import *
from common.constants import *

def run_device(i):
    name = f"Device-{uuid.uuid4().hex[:6]}-{i}"  

    try:
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.connect(('127.0.0.1', 8888))  

        s.recv(1024)  # "HI"
        priv, pub = generate_ecdh_pair()
        s.send(serialize_pubkey(pub))
        server_pub = load_pubkey(s.recv(4096))
        f = derive_key(priv, server_pub)

        s.send(f.encrypt(json.dumps({"type": "REG", "name": name}).encode()))
        resp = json.loads(f.decrypt(s.recv(4096)))
        print(f"[+] Registered → {resp['id']} | Key version: {resp['version']} (Device {i})")

        def ping():
            while True:
                try:
                    s.send(f.encrypt(json.dumps({"type": "PING"}).encode()))
                    time.sleep(10)
                except Exception as e:
                    print(f"[-] Ping failed for Device {i}: {str(e)}")
                    break

        threading.Thread(target=ping, daemon=True).start()

        while True:
            try:
                time.sleep(10)
                s.send(f.encrypt(json.dumps({"type": "DATA", "temp": 25}).encode()))
            except Exception as e:
                print(f"[-] Data send failed for Device {i}: {str(e)}")
                break
    except Exception as e:
        print(f"[-] Error for Device {i}: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run multiple IoT devices.")
    parser.add_argument("--num", type=int, default=8, help="Number of devices to connect (default: 8)")
    args = parser.parse_args()

    print(f"Starting {args.num} devices...")
    threads = []
    for i in range(1, args.num + 1):
        t = threading.Thread(target=run_device, args=(i,))
        threads.append(t)
        t.start()
        time.sleep(0.5)  

    for t in threads:
        t.join()  #process stays alive until manual stop