"""Start the local kitchen app against the Windows PostgreSQL database."""

from base64 import b64encode
import getpass
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
from threading import Thread
from time import sleep
from urllib.parse import quote
from urllib.request import Request, urlopen
import webbrowser

import uvicorn

BASE = "http://127.0.0.1:8000"


def open_pages_when_ready(owner_password: str) -> None:
    authorization = b64encode(f"owner:{owner_password}".encode()).decode()
    request = Request(f"{BASE}/owner", headers={"Authorization": f"Basic {authorization}"})
    for _ in range(50):
        sleep(0.2)
        try:
            with urlopen(request, timeout=0.5) as response:
                if response.status != 200:
                    continue
                print("Owner login check passed.", flush=True)
                webbrowser.open(f"{BASE}/#/menu")
                webbrowser.open(f"{BASE}/owner", new=2)
                return
        except OSError:
            continue
    print(f"Could not verify the dashboard. Check startup output for {BASE}/owner.", flush=True)


def main() -> None:
    os.chdir(Path(__file__).resolve().parent)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        if sys.platform == "win32":
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            listener.bind(("127.0.0.1", 8000))
        except OSError:
            raise SystemExit("Port 8000 is busy. Stop the old Percy server and reopen this launcher.") from None

        password = getpass.getpass("Password for the percy database account: ")
        os.environ["DATABASE_URL"] = f"postgresql+psycopg://percy:{quote(password, safe='')}@127.0.0.1:5432/percy"
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)

        owner_password = secrets.token_urlsafe(32)
        os.environ["OWNER_PASSWORD"] = owner_password
        os.environ["KITCHEN_PASSWORD"] = secrets.token_urlsafe(32)
        print(f"Kitchen board: {BASE}/kitchen", flush=True)
        print("Kitchen username: kitchen", flush=True)
        print("Kitchen password for this run:", os.environ["KITCHEN_PASSWORD"], flush=True)
        print(f"Owner dashboard: {BASE}/owner", flush=True)
        print("Dashboard username: owner", flush=True)
        print("Dashboard password for this run:", owner_password, flush=True)
        Thread(target=open_pages_when_ready, args=(owner_password,), daemon=True).start()
        server = uvicorn.Server(uvicorn.Config("app.main:app", host="127.0.0.1", port=8000, use_colors=False))
        server.run(sockets=[listener])


if __name__ == "__main__":
    main()
