"""Start the local kitchen app against the Windows PostgreSQL database."""

import getpass
import os
from pathlib import Path
import secrets
import subprocess
import sys
from threading import Thread
from time import sleep
from urllib.parse import quote
from urllib.request import urlopen
import webbrowser

import uvicorn


def open_menu_when_ready() -> None:
    for _ in range(50):
        sleep(0.2)
        try:
            with urlopen("http://127.0.0.1:8000/api/health", timeout=0.5):
                webbrowser.open("http://127.0.0.1:8000/#/menu")
                return
        except OSError:
            continue
    print("If startup succeeded, open http://127.0.0.1:8000/#/menu.")


def main() -> None:
    os.chdir(Path(__file__).resolve().parent)
    password = getpass.getpass("Password for the percy database account: ")
    os.environ["DATABASE_URL"] = f"postgresql+psycopg://percy:{quote(password, safe='')}@127.0.0.1:5432/percy"
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)

    os.environ["OWNER_PASSWORD"] = secrets.token_urlsafe(32)
    os.environ["KITCHEN_PASSWORD"] = secrets.token_urlsafe(32)
    print("Kitchen board: http://127.0.0.1:8000/kitchen", flush=True)
    print("Kitchen username: kitchen", flush=True)
    print("Kitchen password for this run:", os.environ["KITCHEN_PASSWORD"], flush=True)
    print("Owner dashboard: http://127.0.0.1:8000/owner", flush=True)
    print("Dashboard username: owner", flush=True)
    print("Dashboard password for this run:", os.environ["OWNER_PASSWORD"], flush=True)
    worker = Thread(target=open_menu_when_ready, daemon=True)
    worker.start()
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
