import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
import pymysql

from gui.gui_components import (
    create_back_button,
    create_header,
    create_main_button,
    create_instructions
)

CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "..", "core", "database", "credentials.json")

class DatabaseSetupWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Database Setup")
        self.master.geometry("500x600")
        self.master.configure(bg="#e8f0f2")
        self.create_widgets()

    def create_widgets(self):
        create_back_button(self.master, self.go_back).place(x=10, y=10)
        create_header(self.master, "Configure Your Database")
        create_instructions(self.master, "Please enter the connection details below:")

        form = tk.Frame(self.master, bg="#e8f0f2")
        form.pack()

        label_font = ("Helvetica", 10)
        entry_width = 26

        tk.Label(form, text="Database Engine:", font=label_font, bg="#e8f0f2").grid(row=0, column=0, sticky="w", pady=(5, 0))
        self.engine_var = tk.StringVar(value="postgresql")
        engine_dropdown = ttk.Combobox(form, textvariable=self.engine_var,
                                       values=["postgresql", "mysql"], width=entry_width - 2, state="readonly")
        engine_dropdown.grid(row=1, column=0, pady=5)
        engine_dropdown.bind("<<ComboboxSelected>>", self.set_default_fields)

        self.host_entry = self._create_field(form, "Host:", 2, "localhost")
        self.port_entry = self._create_field(form, "Port:", 4, "5432")
        self.user_entry = self._create_field(form, "Username:", 6, "postgres")
        self.pass_entry = self._create_field(form, "Password:", 8, "", show="*")

        create_main_button(self.master, "Create Database and Table", self.connect_and_setup).pack(pady=30)

    def _create_field(self, parent, label, row, default="", show=None):
        tk.Label(parent, text=label, font=("Helvetica", 10), bg="#e8f0f2").grid(row=row, column=0, sticky="w", pady=(10, 0))
        entry = tk.Entry(parent, width=26, show=show)
        entry.insert(0, default)
        entry.grid(row=row + 1, column=0, pady=5)
        return entry

    def set_default_fields(self, event=None):
        if self.engine_var.get() == "postgresql":
            self.port_entry.delete(0, tk.END)
            self.port_entry.insert(0, "5432")
            self.user_entry.delete(0, tk.END)
            self.user_entry.insert(0, "postgres")
        elif self.engine_var.get() == "mysql":
            self.port_entry.delete(0, tk.END)
            self.port_entry.insert(0, "3306")
            self.user_entry.delete(0, tk.END)
            self.user_entry.insert(0, "root")

    def connect_and_setup(self):
        engine = self.engine_var.get()
        host = self.host_entry.get()
        port = self.port_entry.get()
        user = self.user_entry.get()
        password = self.pass_entry.get()
        db_name = "maritime_tracker"

        try:
            if engine == "postgresql":
                self.setup_postgres(host, port, user, password, db_name)
            elif engine == "mysql":
                self.setup_mysql(host, port, user, password, db_name)

            self.save_credentials({
                "engine": engine,
                "host": host,
                "port": port,
                "user": user,
                "password": password,
                "database": db_name
            })
            messagebox.showinfo("Success", "Database and table created successfully!")

        except Exception as e:
            err = str(e).lower()
            if "no password" in err:
                messagebox.showerror("Missing Password", "Please enter your database password.")
            elif "authentication" in err or "access denied" in err:
                messagebox.showerror("Authentication Error", "Incorrect username or password.")
            elif "could not connect" in err:
                messagebox.showerror("Connection Error", "Cannot connect to the server.")
            else:
                messagebox.showerror("Error", f"Unexpected error:\n{e}")

    def setup_postgres(self, host, port, user, password, db_name):
        conn = psycopg2.connect(dbname="postgres", user=user, password=password, host=host, port=port)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}';")
        if cur.fetchone():
            if not messagebox.askyesno("Overwrite?", "Database exists. Overwrite?"):
                conn.close()
                return
            cur.execute(f"DROP DATABASE {db_name};")
        cur.execute(f"CREATE DATABASE {db_name};")
        conn.close()

        conn = psycopg2.connect(dbname=db_name, user=user, password=password, host=host, port=port)
        cur = conn.cursor()
        cur.execute("""
            DROP TABLE IF EXISTS ships;
            CREATE TABLE ships (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP,
                mmsi BIGINT,
                latitude NUMERIC(9,6),
                longitude NUMERIC(9,6),
                speed NUMERIC(5,2),
                image_path TEXT,
                name TEXT,
                destination TEXT,
                eta TEXT,
                navigation_status TEXT
            );
        """)
        conn.commit()
        conn.close()

    def setup_mysql(self, host, port, user, password, db_name):
        conn = pymysql.connect(host=host, user=user, password=password, port=int(port))
        cur = conn.cursor()
        cur.execute("SHOW DATABASES;")
        if db_name in [db[0] for db in cur.fetchall()]:
            if not messagebox.askyesno("Overwrite?", "Database exists. Overwrite?"):
                conn.close()
                return
            cur.execute(f"DROP DATABASE {db_name};")
        cur.execute(f"CREATE DATABASE {db_name};")
        conn.select_db(db_name)
        cur.execute("DROP TABLE IF EXISTS ships;")
        cur.execute("""
            CREATE TABLE ships (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME,
                mmsi BIGINT,
                latitude DECIMAL(9,6),
                longitude DECIMAL(9,6),
                speed DECIMAL(5,2),
                image_path TEXT,
                name TEXT,
                destination TEXT,
                eta TEXT,
                navigation_status TEXT
            );
        """)
        conn.commit()
        conn.close()

    def save_credentials(self, config):
        os.makedirs(os.path.dirname(CREDENTIALS_PATH), exist_ok=True)
        with open(CREDENTIALS_PATH, "w") as f:
            json.dump(config, f, indent=4)

    def go_back(self):
        self.master.destroy()
        from gui.calibration import launch_calibration_window
        launch_calibration_window()

def launch_database_window():
    root = tk.Tk()
    app = DatabaseSetupWindow(root)
    root.mainloop()
