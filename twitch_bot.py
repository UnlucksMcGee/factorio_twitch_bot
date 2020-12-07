import asyncio
import datetime
import socket
import time
import traceback

import factorio_rcon


CONNECTION_DATA = ("irc.chat.twitch.tv", 6667)
ENCODING = "utf-8"
CHAT_MSG = "PRIVMSG"
MESSAGE_LIMIT = 500
IRCLIMIT = 20
IRCRESETTIME = 30
IGNORED_USERS_LIST = ["nightbot", "streamelements", "streamlabs", "moobot", "deepbot", "wizebot", "ankhbot", "phantombot", "xanbot", "streamcaptainbot", "pretzelrocks", "t0kenmachine", "xtermbot", "xeliebot", "perrythebot", "totallynotabots", "inter_bot", "pedrothesmolboy"]

message_count = 0
time_checkpoint = time.time()

def logprint(logfile, msg):
    with open(logfile, "w") as log:
        log.write(msg)
        print(msg)


def _handshake(server, twitch_channel, bot_oauth_token, bot_name):
    print(f"Connecting to #{twitch_channel} as {bot_name}")
    server.sendall(bytes(f"PASS {bot_oauth_token}\r\n", ENCODING))
    server.sendall(bytes(f"NICK {bot_name}\r\n", ENCODING))
    server.sendall(bytes(f"JOIN #{twitch_channel}\r\n", ENCODING))


async def pong(server):
    server.sendall(bytes("PONG\r\n", ENCODING))


async def send_message(server, twitch_channel, msg):
    global message_count, time_checkpoint
    if msg:
        if time_checkpoint + IRCRESETTIME <= time.time():
            time_checkpoint = time.time()
            message_count = 0

        if message_count < IRCLIMIT:
            server.sendall(bytes(f"{CHAT_MSG} #{twitch_channel} :{msg}\n", ENCODING))
            message_count += 1
        else:
            print("Rate limited.")


def _msg_sanitizer(msg):
    first, *rest = msg
    return f"{first[1:]} {' '.join(rest)}".strip()


def _parse_user_and_msg(irc_response):
    # msg = ':unlucksmcgee!unlucksmcgee@unlucksmcgee.tmi.twitch.tv PRIVMSG #unlucksmcgee :hello'
    split_msg = irc_response.split()
    if len(split_msg) >= 4:
        user_info, _, _, *raw_msg = split_msg
        user = user_info.split("!")[0][1:]
        msg = _msg_sanitizer(raw_msg)

        return user, msg
    else:
        raise ValueError(f"Error?: {irc_response}")


def _is_command_msg(msg):
    return msg.startswith("!")


async def process_msg(logfile, rcon_client, server, twitch_channel, irc_response, commands, factorio_username, stats_help):
    user, msg = _parse_user_and_msg(irc_response)
    msg = msg.strip()

    if not _is_command_msg(msg):
        if user.lower() not in IGNORED_USERS_LIST:
            logprint(logfile, f"Latest message - {user}: {msg[:20]}{'...' if msg[:20] != msg else ''}")
    else:
        remaining_msg = msg[1:] # Remove "!" from msg

        # Sort commands by length, so that it'll first respond to "!stats power" rather than "!stats"
        ordered_commands_list = sorted(commands.keys(), key=lambda k: len(k), reverse=True)

        for cmd_name in ordered_commands_list:
            if remaining_msg.startswith(cmd_name):
                logprint(logfile, f"Latest command - {user}: !{cmd_name}")
                break
        else:
            # Executed if no break was run in for loop i.e. no valid command found.
            return
        
        # Remove command name from msg
        cmd_args = remaining_msg[len(cmd_name):].strip()
        lua_list = []
        for lua_string in commands[cmd_name]:
            if cmd_args != "":
                lua_string = lua_string.replace("__ARG_VALUE__", cmd_args)
            lua_string = lua_string.replace("__FACTORIO_USERNAME__", factorio_username)
            lua_string = lua_string.replace("__STATS_HELP__", stats_help)
            lua_list.append(lua_string)

        out = []
        for lua_script in lua_list:
            response = rcon_client.send_command(lua_script)

            if response and "error" not in response.lower():
                out.append(response)
            else:
                msg = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Message '{msg}' gave Error response '{response}' from lua script: {lua_script}"
                with open("error_log.txt", "a") as f:
                    f.write(msg+"\n")
                    print(msg)
        
        output_string = " ".join(out)
        await send_message(server, twitch_channel, f"/me {output_string}"[:MESSAGE_LIMIT])


async def chat_response(server):
    return server.recv(2048).decode(ENCODING)


async def run_bot(server, logfile, connection_args, commands_config, factorio_username):
    twitch_channel, rcon_ip, rcon_port, rcon_password = connection_args
    logprint(logfile, "Processing commands...")
    twitch_channel = twitch_channel.lower()

    processed_commands = {}
    stats_help_dict = {}
    for command in commands_config:
        cmd_name = command["command_name"]
        if cmd_name not in processed_commands or command["overwrite"] == True:
            processed_commands[cmd_name] = []
            stats_help_dict[cmd_name] = []
        processed_commands[cmd_name].append(command["lua"])
        stats_help_dict[cmd_name].append(f"!{cmd_name}" if command["args_description"] is None else f"!{cmd_name} {command['args_description']}")
    stats_help = " | ".join(sorted(set([desc for _,v in stats_help_dict.items() for desc in v])))

    logprint(logfile, "Connecting to factorio server...")
    try:
        rcon_client = factorio_rcon.RCONClient(rcon_ip, rcon_port, rcon_password)
    except factorio_rcon.factorio_rcon.RCONConnectError:
        logprint(logfile, "Connection to factorio server failed.\nPerhaps change settings.txt.")
        return

    logprint(logfile, "Connections successful. Bot started.")

    chat_buffer = ""
    while True:
        raw_irc_response = await chat_response(server)

        chat_buffer = chat_buffer + raw_irc_response
        messages = chat_buffer.split("\r\n")
        chat_buffer = messages.pop()

        for message in messages:
            if message == "PING :tmi.twitch.tv":
                await pong(server)
            elif len(message.split()) < 2:
                continue
            elif CHAT_MSG in message:
                try:
                    await process_msg(logfile, rcon_client, server, twitch_channel, message, processed_commands, factorio_username, stats_help)
                except factorio_rcon.factorio_rcon.RCONClosed:
                    logprint(logfile, "Lost connection to factorio server. Trying to reconnect...")
                    while True:
                        try:
                            rcon_client = factorio_rcon.RCONClient(rcon_ip, rcon_port, rcon_password)
                            logprint(logfile, "Connection to factorio server successful.")
                            break
                        except factorio_rcon.factorio_rcon.RCONConnectError:
                            time.sleep(5)
                except Exception as e:
                    msg = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error: '{e}'"
                    with open("error_log.txt", "a") as f:
                        f.write(msg+"\n")
                        print(msg)
                    traceback.print_exc()


async def main(logfile, connection_args, commands_config, factorio_username):
    twitch_channel, bot_name, bot_oauth_token, rcon_ip, rcon_port, rcon_password = connection_args
    with socket.socket() as server:
        logprint(logfile, "Connecting to twitch...")
        try:
            server.connect(CONNECTION_DATA)
        except:
            logprint(logfile, "Failed to connect to twitch.")
            return
        _handshake(server, twitch_channel, bot_oauth_token, bot_name)

        await asyncio.gather(run_bot(server, logfile, [twitch_channel, rcon_ip, rcon_port, rcon_password], commands_config, factorio_username))
