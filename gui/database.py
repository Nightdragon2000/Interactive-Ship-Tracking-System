import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
import pymysql
import json
import os

CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "credentials.json")

class DatabaseSetupWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Database Setup")
        self.master.geometry("500x580")
        self.master.configure(bg="#e8f0f2")
        self.create_widgets()

    def create_widgets(self):
        btn_back = tk.Button(self.master, text="← Go Back", command=self.go_back,
                             font=("Helvetica", 12), bg="#e8f0f2", fg="#1f3b4d",
                             bd=0, highlightthickness=0, activebackground="#e8f0f2",
                             activeforeground="#1f3b4d", cursor="hand2")
        btn_back.place(x=10, y=10)

        tk.Label(self.master, text="Configure Your Database",
                 font=("Helvetica", 18, "bold"),
                 bg="#e8f0f2", fg="#1f3b4d").pack(pady=(40, 5))

        tk.Label(self.master, text="Please enter the connection details below:",
                 font=("Helvetica", 11), bg="#e8f0f2", fg="#3b3b3b").pack(pady=(0, 20))

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

        tk.Label(form, text="Host:", font=label_font, bg="#e8f0f2").grid(row=2, column=0, sticky="w", pady=(10, 0))
        self.host_entry = tk.Entry(form, width=entry_width)
        self.host_entry.insert(0, "localhost")
        self.host_entry.grid(row=3, column=0, pady=5)

        tk.Label(form, text="Port:", font=label_font, bg="#e8f0f2").grid(row=4, column=0, sticky="w", pady=(10, 0))
        self.port_entry = tk.Entry(form, width=entry_width)
        self.port_entry.insert(0, "5432")
        self.port_entry.grid(row=5, column=0, pady=5)

        tk.Label(form, text="Username:", font=label_font, bg="#e8f0f2").grid(row=6, column=0, sticky="w", pady=(10, 0))
        self.user_entry = tk.Entry(form, width=entry_width)
        self.user_entry.insert(0, "postgres")
        self.user_entry.grid(row=7, column=0, pady=5)

        tk.Label(form, text="Password:", font=label_font, bg="#e8f0f2").grid(row=8, column=0, sticky="w", pady=(10, 0))
        self.pass_entry = tk.Entry(form, show="*", width=entry_width)
        self.pass_entry.grid(row=9, column=0, pady=5)

        tk.Button(self.master, text="Create Database and Table",
                  command=self.connect_and_setup,
                  font=("Helvetica", 11, "bold"),
                  width=30, height=2,
                  bg="#4a90e2", fg="white",
                  activebackground="#357ABD", activeforeground="white",
                  bd=0, cursor="hand2").pack(pady=30)

    def set_default_fields(self, event=None):
        engine = self.engine_var.get()
        if engine == "postgresql":
            self.port_entry.delete(0, tk.END)
            self.port_entry.insert(0, "5432")
            self.user_entry.delete(0, tk.END)
            self.user_entry.insert(0, "postgres")
        elif engine == "mysql":
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
                # Initial connection
                conn = psycopg2.connect(dbname="postgres", user=user, password=password, host=host, port=port)
                conn.autocommit = True
                cur = conn.cursor()
                cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}';")
                exists = cur.fetchone()
                if exists:
                    if not messagebox.askyesno("Overwrite?", "Database already exists. Overwrite and delete existing data?"):
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

            elif engine == "mysql":
                conn = pymysql.connect(host=host, user=user, password=password, port=int(port))
                cur = conn.cursor()
                cur.execute("SHOW DATABASES;")
                databases = [db[0] for db in cur.fetchall()]
                if db_name in databases:
                    if not messagebox.askyesno("Overwrite?", "Database already exists. Overwrite and delete existing data?"):
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
            if "no password supplied" in err:
                messagebox.showerror("Missing Password", "Please enter your database password.")
            elif "authentication failed" in err or "access denied" in err or "password authentication failed" in err:
                messagebox.showerror("Authentication Error", "Incorrect username or password.")
            elif "could not connect" in err or "connection to server" in err:
                messagebox.showerror("Connection Error", "Cannot connect to the database server. Please check the host and port.")
            else:
                messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")

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
