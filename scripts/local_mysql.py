"""Optional Windows MySQL ZIP runner, isolated to this project's .runtime."""

import argparse
import os
import re
import socket
import subprocess
import time
from pathlib import Path

import MySQLdb
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / ".runtime"
DATA = RUNTIME / "mysql-data"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["init", "start", "stop"])
    parser.add_argument("--basedir", type=Path, default=RUNTIME / "mysql-8.4.13-winx64")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env", override=False)
    database = os.environ["MYSQL_DATABASE"]
    user = os.environ["MYSQL_USER"]
    password = os.environ["MYSQL_PASSWORD"]
    root_password = os.environ["MYSQL_ROOT_PASSWORD"]
    port = int(os.environ.get("MYSQL_PORT", "3308"))
    if not all(re.fullmatch(r"[A-Za-z0-9_]+", value) for value in [database, user]):
        raise SystemExit(
            "For this local helper, database/user must contain only letters, numbers and underscore."
        )
    if os.environ.get("MYSQL_HOST", "127.0.0.1") != "127.0.0.1":
        raise SystemExit("This helper only supports MYSQL_HOST=127.0.0.1.")
    if not 1 <= port <= 65535 or not password or not root_password:
        raise SystemExit("Invalid local database configuration.")

    def connect(admin=False):
        return MySQLdb.connect(
            host="127.0.0.1",
            port=port,
            user="root" if admin else user,
            passwd=root_password if admin else password,
            connect_timeout=2,
            charset="utf8mb4",
        )

    def assert_own_instance(connection):
        with connection.cursor() as cursor:
            cursor.execute("SELECT @@datadir")
            actual = Path(cursor.fetchone()[0]).resolve()
        if actual != DATA.resolve():
            raise SystemExit(
                "This port belongs to another MySQL instance. It was not changed."
            )

    try:
        connection = connect()
    except MySQLdb.OperationalError as error:
        if error.args[0] not in [2002, 2003]:
            raise SystemExit(
                "MySQL is reachable but authentication failed; check .env before continuing."
            ) from None
        connection = None
    if connection:
        assert_own_instance(connection)
        connection.close()
        if args.action == "stop":
            connection = connect(admin=True)
            with connection.cursor() as cursor:
                cursor.execute("SHUTDOWN")
            connection.close()
            for _ in range(60):
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                        pass
                except OSError:
                    print("Local project MySQL stopped; data preserved.")
                    return
                time.sleep(0.5)
            raise SystemExit(
                "Shutdown requested but the port is still open; inspect .runtime/mysql.log."
            )
        else:
            print("Local project MySQL is already running.")
        return
    if args.action == "stop":
        print("Local MySQL is not running.")
        return

    binary = args.basedir.resolve() / "bin" / "mysqld.exe"
    if not binary.is_file():
        raise SystemExit(
            "MySQL ZIP is not extracted. See docs/08-local-environment.md."
        )
    RUNTIME.mkdir(exist_ok=True)
    initial = args.action == "init"
    if initial and DATA.exists() and any(DATA.iterdir()):
        raise SystemExit(
            "Existing data directory preserved. Use start, or inspect the previous initialization log."
        )
    if not initial and not (DATA / "mysql.ibd").exists():
        raise SystemExit("Initialize first: python scripts/local_mysql.py init")
    base = [
        str(binary),
        "--no-defaults",
        f"--basedir={args.basedir.resolve()}",
        f"--datadir={DATA}",
    ]
    init_file = RUNTIME / "mysql-init.sql"
    if initial:
        with (RUNTIME / "mysql-initialize.log").open("w", encoding="utf-8") as log:
            subprocess.run(
                base + ["--initialize-insecure", "--console"],
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
            )
        quote = lambda value: (
            "'" + MySQLdb._mysql.escape_string(value.encode()).decode() + "'"
        )
        statements = [
            f"ALTER USER 'root'@'localhost' IDENTIFIED BY {quote(root_password)};",
            f"CREATE DATABASE `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
        ]
        for host in ["localhost", "127.0.0.1"]:
            statements += [
                f"CREATE USER '{user}'@'{host}' IDENTIFIED BY {quote(password)};",
                f"GRANT ALL PRIVILEGES ON `{database}`.* TO '{user}'@'{host}';",
            ]
        init_file.write_text("\n".join(statements) + "\n", encoding="utf-8")
    command = base + [
        f"--port={port}",
        "--bind-address=127.0.0.1",
        "--mysqlx=OFF",
        "--character-set-server=utf8mb4",
        "--collation-server=utf8mb4_unicode_ci",
        "--console",
    ]
    if initial:
        command.append(f"--init-file={init_file}")
    with (RUNTIME / "mysql.log").open("a", encoding="utf-8") as log:
        process = subprocess.Popen(
            command,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    (RUNTIME / "mysql.pid").write_text(str(process.pid), encoding="ascii")
    for _ in range(60):
        if process.poll() is not None:
            raise SystemExit("MySQL exited; inspect .runtime/mysql.log.")
        try:
            connection = connect()
            assert_own_instance(connection)
            connection.close()
            if initial:
                init_file.unlink()
            print(f"Project MySQL ready on 127.0.0.1:{port}; data: {DATA}")
            return
        except MySQLdb.OperationalError:
            time.sleep(0.5)
    raise SystemExit("MySQL did not become ready; inspect .runtime/mysql.log.")


if __name__ == "__main__":
    main()
