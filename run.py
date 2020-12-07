import asyncio
import datetime
import json
import multiprocessing
import os
import pickle
import sys
import tkinter as tk
import tkinter.ttk as ttk
import webbrowser
from functools import partial
from tkinter import messagebox as tk_msgbox

import requests

from twitch_bot import main as main_bot
import factorio_rcon # To ensure pyinstaller bundles it

VERSION="1.0"

DEFAULT_TWITCH_CHANNEL = "my_channel_name"
DEFAULT_FACTORIO_USERNAME = "my_username"
DEFAULT_BOT_CLIENT_ID = "abcdefghijklmnopqrstuvwxyz0123"
DEFAULT_RCON_IP = "123.456.789.123"
DEFAULT_RCON_PORT = 25575
DEFAULT_RCON_PASSWORD = "my_password"

cur_thread = None

def logprint(logfile, msg):
    with open(logfile, "w") as log:
        log.write(msg)
        print(msg)

class App:
    def __init__(self, master):
        """
        Parameters:
        -----------
            master : Tk object
        """

        self.master = master
        self.col_txt_primary = "#F6F7F8"
        self.col_bg = "#3c3b3d"
        self.col_fg = "#7db1b1"
        self.font_vl = ("Arial", 14, "bold")
        self.font_l = ("Arial", 12, "bold")
        self.font_lu = ("Arial", 12, "bold", "underline")
        self.font_s = ("Arial", 10)
        self.font_su = ("Arial", 10, "underline")
        self.logfile = "statusfile.txt"
        self.config_dir = "configs"

        self.bot_name = None
        self.bot_client_id = DEFAULT_BOT_CLIENT_ID
        self.bot_oauth_token = None
        self.rcon_ip = DEFAULT_RCON_IP
        self.rcon_port = DEFAULT_RCON_PORT
        self.rcon_password = DEFAULT_RCON_PASSWORD

        self.configs = read_json(self.config_dir)

        self.master.title("Factorio Twitch Bot V"+VERSION+" - By UnlucksMcGee")
        self.master.geometry('{}x{}'.format(800, 600))
        self.master.configure(bg=self.col_bg)

        # For enabling/disabling all the objects
        self.objects_enabled = True
        self.tkinter_object_list = []

        logprint(self.logfile, "Status: Off")

        # Settings
        settings_frame = tk.Frame(self.master, borderwidth=3, bg=self.col_fg, relief=tk.SUNKEN)
        settings_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=0, anchor=tk.N, padx=10, pady=(10, 0))

        self.twitch_channel = tk.StringVar()
        self.twitch_channel.set(DEFAULT_TWITCH_CHANNEL)
        twitch_channel_label = tk.Label(settings_frame, text="Twitch Channel", font=self.font_l, bg=self.col_fg)
        twitch_channel_textbox = tk.Entry(settings_frame, width=50, font=self.font_s, textvariable=self.twitch_channel)
        twitch_channel_label.grid(sticky="e", row=0, column=0, padx=5, pady=5)
        twitch_channel_textbox.grid(sticky="w", row=0, column=1, padx=5)
        self.tkinter_object_list.append(twitch_channel_textbox)

        self.factorio_username = tk.StringVar()
        self.factorio_username.set(DEFAULT_FACTORIO_USERNAME)
        factorio_username_label = tk.Label(settings_frame, text="Factorio Username", font=self.font_l, bg=self.col_fg)
        factorio_username_textbox = tk.Entry(settings_frame, width=50, font=self.font_s, textvariable=self.factorio_username)
        factorio_username_label.grid(sticky="e", row=1, column=0, padx=5, pady=5)
        factorio_username_textbox.grid(sticky="w", row=1, column=1, padx=5)
        self.tkinter_object_list.append(factorio_username_textbox)

        # Commands settings
        canvas_parent_frame = tk.Frame(self.master, bg=self.col_bg)
        canvas = tk.Canvas(canvas_parent_frame, borderwidth=3, bg=self.col_fg, relief=tk.SUNKEN)
        commands_frame = tk.Frame(canvas, borderwidth=3, bg=self.col_fg)
        scrollbar = tk.Scrollbar(canvas_parent_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        canvas_window = canvas.create_window((4,4), window=commands_frame, anchor="nw", tags="commands_frame")
        commands_frame.bind("<Configure>", lambda _: canvas.configure(scrollregion=canvas.bbox(canvas_window)))
        canvas_parent_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, anchor=tk.N, padx=10, pady=(10,0))

        # Bind mousewheel to scroll area
        def bind_mousewheel():
            # For Windows
            canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(1 if event.delta < 0 else -1, "units"))
            # For Linux
            canvas.bind_all("<Button-4>", lambda event: canvas.yview_scroll(-1, "units"))
            canvas.bind_all("<Button-5>", lambda event: canvas.yview_scroll(1, "units"))

        def unbind_mousewheel():
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas_parent_frame.bind('<Enter>', lambda _: bind_mousewheel())
        canvas_parent_frame.bind('<Leave>', lambda _: unbind_mousewheel())

        # Heading label
        cur_row_number = 0
        heading_label = tk.Label(commands_frame, text="Command selection", font=self.font_vl, bg=self.col_fg)
        heading_label.grid(sticky="w", row=0, column=0, padx=5, pady=(2,2))
        cur_row_number += 1
        # Create checkboxes
        for dict_idx, json_dict in enumerate(self.configs):
            heading_label = tk.Label(commands_frame, text=json_dict["heading"], font=self.font_lu, bg=self.col_fg)
            heading_label.grid(sticky="w", row=cur_row_number, column=0, padx=5, pady=(10,2))
            cur_row_number +=1

            for command_idx, command in enumerate(json_dict["commands"]):
                # Add a checkbox status key-value pair to the command dictionary
                self.configs[dict_idx]["commands"][command_idx]["checkbox_status"] = tk.IntVar()
                self.configs[dict_idx]["commands"][command_idx]["checkbox_status"].set(self.configs[dict_idx]["commands"][command_idx]["enabled_on_startup"]) # Set default enabled/disabled on startup
                checkbox_text = f"!{command['command_name']}" if command["args_description"] is None else f"!{command['command_name']} {command['args_description']}"
                if command["overwrite"] == False:
                    checkbox_text = "Appended to: " + checkbox_text
                checkbox_text = f"{command['heading']} ({checkbox_text})"
                command_checkbox = tk.Checkbutton(commands_frame, text=checkbox_text, variable=self.configs[dict_idx]["commands"][command_idx]["checkbox_status"], font=self.font_s, bg=self.col_fg, activebackground=self.col_fg, disabledforeground=self.col_bg)
                command_checkbox.grid(sticky="w", row=cur_row_number, column=0, padx=2)
                self.tkinter_object_list.append(command_checkbox)
                cur_row_number +=1

        # Start frame
        start_frame = tk.Frame(self.master, borderwidth=2, bg=self.col_fg, relief=tk.SUNKEN)
        start_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False, anchor=tk.N, padx=10, pady=(10,0))

        start_button = tk.Button(start_frame, text="Start Bot", command=partial(threaded_main, self), font=self.font_l)
        start_button.pack(pady=5)
        self.tkinter_object_list.append(start_button) # Only add start_button to be disabled. Stop button should never be disabled

        stop_button = tk.Button(start_frame, text="Stop Bot", command=partial(stop_thread, self.logfile), font=self.font_l)
        stop_button.pack(pady=5)

        # Output frame
        output_frame = tk.Frame(self.master, borderwidth=2, bg=self.col_fg, relief=tk.SUNKEN)
        output_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False, anchor=tk.N, padx=10, pady=10)

        self.status = tk.StringVar(self.master)
        self.status.set("Status: Off")
        output_label = tk.Label(output_frame, textvariable=self.status, font=self.font_l, bg=self.col_fg)
        output_label.pack(side=tk.LEFT, anchor="w", fill=tk.BOTH, padx=5, pady=(5,30))

    def check_log(self):
        with open(self.logfile, "r") as log:
            text = "".join(log.readlines())

            self.status.set(text)
        self.master.update_idletasks()

        if text[-11:] == "Status: Off" and self.objects_enabled == False:
            # Enable objects
            for obj in self.tkinter_object_list:
                obj["state"] = "normal"
            self.objects_enabled = True
            # print("Enabled tkinter objects")

        self.master.after(200, self.check_log)

    def read_and_save_settings(self):
        settings_fp = "settings.txt"
        # Read settings if it exists, otherwise it writes current (default) values
        if os.path.exists(settings_fp):
            with open("settings.txt", "r") as settings:
                lines = settings.readlines()
                for line in lines:
                    if len(line.split("=", 1)) < 2:
                        print("Couldn't parse settings option.")
                        continue
                    category = line.split("=", 1)[0].strip()
                    data = line.split("=", 1)[1].strip()
                    if len(data) < 2:
                        print("Couldn't parse settings option.")
                        continue
                    if (data[0] == '"' and data[-1] == '"') or (data[0] == "'" and data[-1] == "'"):
                        data = data[1:-1]
                    if category == "TWITCH_CHANNEL":
                        # Don't overwrite it, if it was changed within GUI
                        if self.twitch_channel.get() == DEFAULT_TWITCH_CHANNEL:
                            self.twitch_channel.set(data)
                    elif category == "FACTORIO_USERNAME":
                        # Don't overwrite it, if it was changed within GUI
                        if self.factorio_username.get() == DEFAULT_FACTORIO_USERNAME:
                            self.factorio_username.set(data)
                    elif category == "BOT_CLIENT_ID":
                        self.bot_client_id = data
                    elif category == "RCON_IP":
                        self.rcon_ip = data
                    elif category == "RCON_PORT":
                        try:
                            self.rcon_port = int(data)
                        except ValueError:
                            msg = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error parsing port. Make sure it is an integer."
                            with open("error_log.txt", "a") as f:
                                f.write(msg+"\n")
                                print(msg)
                            tk_msgbox.showwarning(title="Invalid port", message="Error parsing port. Make sure it is an integer.")
                    elif category == "RCON_PASSWORD":
                        self.rcon_password = data
                    else:
                        print("Invalid settings option.")
                    # print(f"read {category}: {data}")

        with open(settings_fp, "w") as f:
            f.write("TWITCH_CHANNEL = "+self.twitch_channel.get().strip()+"\n")
            f.write("FACTORIO_USERNAME = "+self.factorio_username.get().strip()+"\n")
            f.write("BOT_CLIENT_ID = "+ (self.bot_client_id if self.bot_client_id else DEFAULT_BOT_CLIENT_ID)+"\n")
            f.write("RCON_IP = "+self.rcon_ip+"\n")
            f.write("RCON_PORT = "+str(self.rcon_port)+"\n")
            f.write("RCON_PASSWORD = "+self.rcon_password+"\n")
            # print("Saved settings.")

    def save_json_config(self):
        for json_file in self.configs:
            filepath = json_file["filepath"]
            temp_dict = _copy_clean_dict(json_file)

            with open(filepath, "w") as f:
                f.write(json.dumps(temp_dict, indent=4, sort_keys=False))

        print("Saved json config.")


def _copy_clean_dict(d):
    # Remove filepath key:value, as well as the multiple checkbox_status key:values (present in each command)
# ["filepath","checkbox_status"]
    out = {x: d[x] for x in d if x not in ["filepath", "commands"]}

    # Manually add commands, but remove "checkbox_status"
    out["commands"] = []

    for command in d["commands"]:
        temp = {x: command[x] for x in command if x != "checkbox_status"}
        out["commands"].append(temp)

    return out


def callback_main(logfile, connection_args, commands_config, factorio_username):
    asyncio.run(main_bot(logfile, connection_args, commands_config, factorio_username))

    with open(logfile, "r") as log:
        text = "".join(log.readlines())
        if text == "Status: Off":
            text = ""
        else:
            text += " "
    logprint(logfile, text + "Status: Off")


def threaded_main(app_instance):
    global cur_thread
    if cur_thread is not None:
        if cur_thread.is_alive():
            logprint(app_instance.logfile, "Bot's already running.")
            return
    app_instance.read_and_save_settings()

    logprint(app_instance.logfile, "Started bot")
    for obj in app_instance.tkinter_object_list:
        obj["state"] = "disabled"
    app_instance.objects_enabled = False
    # print("Disabled tkinter objects")

    commands_config = []
    for idx_config, config in enumerate(app_instance.configs):
        for idx_cmd, command in enumerate(config["commands"]):
            if command["checkbox_status"].get():
                commands_config.append(
                    {
                        "command_name": command["command_name"],
                        "overwrite": command["overwrite"],
                        "args_description": command["args_description"],
                        "lua": command["lua"],
                    }
                )
                app_instance.configs[idx_config]["commands"][idx_cmd]["enabled_on_startup"] = True
            else:
                app_instance.configs[idx_config]["commands"][idx_cmd]["enabled_on_startup"] = False

    app_instance.save_json_config()

    connection_args = [app_instance.twitch_channel.get().strip().lower(), app_instance.bot_name.strip().lower(), app_instance.bot_oauth_token, app_instance.rcon_ip, app_instance.rcon_port, app_instance.rcon_password]

    cur_thread = multiprocessing.Process(target=callback_main, args=(app_instance.logfile, connection_args, commands_config, app_instance.factorio_username.get()), daemon=False)
    cur_thread.start()


def stop_thread(logfile):
    global cur_thread
    if cur_thread is not None:
        cur_thread.terminate()
        logprint(logfile, "Status: Off")


def read_json(directory):
    json_files = [os.path.join(directory, json_fp) for json_fp in os.listdir(directory) if json_fp.endswith(".json")]
    # print(f"reading json: {json_files}")

    list_json_dicts = []
    for json_file in json_files:
        with open(json_file) as f:
            json_dict = json.load(f)
            if "priority" not in json_dict:
                msg = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Unable to read json file: {json_file}"
                with open("error_log.txt", "a") as f:
                    f.write(msg+"\n")
                    print(msg)
            else:
                # Add original filepath for saving checkbox enabled status
                json_dict["filepath"] = json_file
                list_json_dicts.append(json_dict)

    list_json_dicts = sorted(list_json_dicts, key=lambda k: k["priority"])

    if len(list_json_dicts) == 0:
        msg = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Could not find a valid json file in {directory} directory."
        with open("error_log.txt", "a") as f:
            f.write(msg+"\n")
            print(msg)
        sys.exit(1)

    return list_json_dicts


def generate_oauth(client_id):
    scopes = "chat:read+chat:edit" # Read chat messages and send chat messages
    # scopes = "chat:read+chat:edit+whispers:read+whispers:edit"
    redirect = "https://twitchapps.com/tokengen/"
    url = f"https://id.twitch.tv/oauth2/authorize?response_type=token&client_id={client_id}&redirect_uri={redirect}&scope={scopes}"
    webbrowser.open(url)


def validate_oauth(oauth_token):
    if oauth_token.startswith("oauth:"):
        oauth_token = oauth_token[6:]
    response = requests.get("https://id.twitch.tv/oauth2/validate", headers={"Authorization": f"OAuth {oauth_token}"}).json()

    if "login" in response:
        username = response["login"]
        return True, username
    else:
        return False, None


if __name__ == "__main__":
    if os.path.exists("error_log.txt"):
        os.remove("error_log.txt")

    multiprocessing.freeze_support()
    root = tk.Tk()

    # Hide window for now
    root.withdraw()
    app = App(root)

    # Read settings
    app.bot_client_id = None
    app.bot_oauth_token = None
    if not os.path.exists("settings.txt"):
        tk_msgbox.showwarning(title="Missing settings.txt file", message="Can't find settings file. Writing default settings file. Please edit it.")
        app.read_and_save_settings()
        sys.exit(1)
    else:
        app.read_and_save_settings()
    # Add on_closing event, to stop bot before closing.
    def on_closing():
        stop_thread(app.logfile)
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Validate oauth token if it exists:
    if os.path.exists("token.pkl"):
        try:
            with open('token.pkl', 'rb') as f:
                oauth_token = pickle.load(f)

            success, username = validate_oauth(oauth_token)
            if success:
                app.bot_oauth_token = oauth_token
                app.bot_name = username
        except requests.exceptions.ConnectionError:
            tk_msgbox.showerror(title="Connection failed", message="Could not connect to twitch to validate oauth token.")
            sys.exit(1)
        except:
            os.remove("token.pkl")

    if app.bot_oauth_token == None:
        if app.bot_client_id and app.bot_client_id != DEFAULT_BOT_CLIENT_ID:
            generate_oauth(app.bot_client_id)
            oauth_token = None

            # Start small gui to paste command into.
            oauth_window = tk.Tk()
            oauth_window.title("Factorio Twitch Bot V"+VERSION+" - By UnlucksMcGee")
            oauth_window.geometry('{}x{}'.format(500, 150))
            oauth_window.configure(bg=app.col_bg)
            settings_frame = tk.Frame(oauth_window, borderwidth=3, bg=app.col_fg, relief=tk.SUNKEN)
            settings_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, anchor=tk.N, padx=10, pady=10)
            tk.Label(settings_frame, font=app.font_s, bg=app.col_fg, text="Please enter the oauth token copied from your browser.\ne.g. abcdefghijklmnopqrstuvwxyz0123").pack(side=tk.TOP, anchor=tk.N, pady=5)
            e1 = tk.Entry(settings_frame, width=50)
            e1.pack(side=tk.TOP, anchor=tk.N, pady=5)
            e1.focus_set()

            def button_cmd():
                oauth_token = e1.get()
                if oauth_token == "":
                    return
                elif not oauth_token.startswith("oauth:"):
                    oauth_token = "oauth:" + oauth_token
                success, username = validate_oauth(oauth_token)
                if success:
                    app.bot_oauth_token = oauth_token
                    app.bot_name = username
                    with open('token.pkl', 'wb') as f:
                        pickle.dump(oauth_token, f)
                    oauth_window.destroy()
                    tk_msgbox.showinfo(title="Success", message="The token was validated.")
                else:
                    tk_msgbox.showwarning(title="Invalid token", message="The token provided could not be validated.")
                    oauth_window.destroy()
                    sys.exit(1)
            tk.Button(settings_frame, text='OK', command=button_cmd).pack(side=tk.TOP, anchor=tk.N, pady=5)
            oauth_window.wait_window()

        else:
            msg = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Invalid/Missing client_id from settings.txt file. Include: BOT_CLIENT_ID=<ID>"
            with open("error_log.txt", "a") as f:
                f.write(msg+"\n")
                print(msg)
            tk_msgbox.showwarning(title="Invalid client ID", message="Invalid/Missing client_id from settings.txt file. Include: BOT_CLIENT_ID=<ID>")
            sys.exit(1)

    # If oauth token is still not set, then close.
    if app.bot_oauth_token == None:
        msg = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - OAuth token is missing."
        with open("error_log.txt", "a") as f:
            f.write(msg+"\n")
            print(msg)
        sys.exit(0)

    # Show window again
    root.update()
    root.deiconify()

    root.after(200, app.check_log)
    root.mainloop()
