# Factorio Stats Twitch Bot - By UnlucksMcGee

This application is a twitch chat bot that runs locally on your pc, and interfaces with a factorio server to get certain statistics on-demand, based on received commands in twitch chat. These statistics are then output in twitch chat.

![Screenshot](screenshot.png?raw=true)

The chat bot only has one main command `!stats`. Additional parameters can be appended to request other statistics. Therefore it shouldn't conflict with existing chat bots, assuming they don't use a `!stats` command.

The application gives you the option to select which commands to enable.

NOTE: The application runs commands on the server, thus achievements will be disabled for the savegame.

## How to run

Download the latest release [here](https://github.com/UnlucksMcGee/factorio_twitch_bot/releases) for your OS (Windows or Linux) and extract it.

#### 1. Generate client ID

For the bot, you may want to create a separate twitch account (alternatively you can just use your current twitch account).
Note: you will need Two-Factor Authentication (2FA) enabled for this step.

Go to https://dev.twitch.tv/ and login with this twitch account. Then click `Your Console`->`Register Your Application`.
Fill in the fields:

 * name: `FactorioChatBot`
 * OAuth Redirect URLs: `https://twitchapps.com/tokengen/`
 * Category: `Chat Bot`

Complete the reCAPTCHA and click `save` at the bottom.
Copy the Client ID and paste it into `settings.txt`.

#### 2. Update settings.txt

Before starting the application, check the `settings.txt` file to update it's values appropriately. Keep these secret/hidden from stream.

* `TWITCH_CHANNEL` is the twitch channel that the bot should connect to i.e. your channel name.
* `FACTORIO_USERNAME` is your in-game factorio username that is used in some commands e.g. space-exploration mod command to say which planet you're currently viewing.
* `BOT_CLIENT_ID` is the client ID obtained in the previous step.
* `RCON_IP` is the ip of your factorio server.
* `RCON_PORT` is the rcon port of your factorio server (default is 25575).
* `RCON_PASSWORD` is the rcon password of your factorio server.

(If you are running the server yourself, use the following command line arguments: `--rcon-port 25575 --rcon-password my_password`)

#### 2. Prepare factorio server

The application runs commands on the server, thus achievements will be disabled for the savegame.
To enable commands on the server, you need to repeat a command twice.

* Enable commands by typing "`/c`" in chat twice.

#### 3. Start the application

When you launch the application on Windows, the Microsoft SmartScreen may pop up since the exe is by an "unknown publisher". If I want to avoid that I'd have to pay $400+ each year for a digital certificate...

To bypass it, click `More info` -> `Run anyway`

On first launch, it will open your browser and ask you to authorize the `FactorioChatBot` app created earlier. Make sure you're logged in with the same account used earlier (if you are not, copy the url and paste it into an incognito window where you can login to the appropriate account).

Then copy the oauth token and paste it into the textbox of the application.

#### 4. Start the chatbot

After selecting the appropriate commands you want enabled, click `Start Bot`, which will attempt to connect to twitch and the factorio server, and thereafter it will respond to commands received in chat.

## Current commands and Mod integrations

#### Base game

* Total playtime on the save (Appended to `!stats`) e.g. "Total playtime: 2 days, 13 hours."
* Power stats (`!stats power`) e.g. "Nauvis power stats - 2900 accumulator: 0.0W (0.0%) | 2908 solar-panel: 174.5MW (56.8%) | 230 steam-engine: 11.2MW (3.7%) | 384 steam-turbine: 121.4MW (39.5%)."
* Science production (`!stats science`) e.g. "Science production (last hour): R:28.8/m G:28.8/m M:0.0/m B:30.2/m P:28.1/m Y:28.9/m W:33.4/m."
* Kill stats (`!stats kills`) e.g. "Total kills (kill rate for last hour) - Spawners:11k (1.1/min) Biters:36k (5.2/min) Spitters:36k (4.8/min) Worms:10k (1.9/min)."
* Item production stats (`!stats production <internal-item-name>`) e.g. `!stats production electronic-circuit`: "Total Electronic circuit production (rate for last 10min): 5.15M (5.52k/min)."
* Item consumption stats (`!stats consumption <internal-item-name>`) e.g. `!stats consumption electronic-circuit`: "Total Electronic circuit consumption (rate for last 10min): 4.80M (5.38k/min)."

* Ribbon world (race to edge) - West Progress (Appended to `!stats`) e.g. "West progress: 451968 tiles (45.2%)."
* Ribbon world (race to edge) - East Progress (Appended to `!stats`) e.g. "East progress: 354048 tiles (35.4%)."

#### [Bob's Tech Mod](https://mods.factorio.com/mods/Bobingabout/bobtech) by Bobingabout

* Science production using Bob's naming (`!stats science`) e.g. "Bob's Mod Science production (last hour): Y:27.9/m R:28.8/m M:0.0/m B:30.2/m Pink:28.1/m Purple:28.9/m G:28.8/m W:33.4/m."

#### [Krastorio 2](https://mods.factorio.com/mod/Krastorio2) by Krastor

* Science production (`!stats science`) e.g. "Krastorio 2 Science production (last hour): Basic:25.5/m R:28.8/m G:28.8/m M:0.0/m B:30.2/m P:28.1/m Y:28.9/m W:33.4/m Matter:25.5/m Advanced:25.5/m Singularity:25.5/m."

#### [Space Exploration](https://mods.factorio.com/mod/space-exploration) by Earendel

* Get player's current planet (Appended to `!stats`) e.g. "cl0wnt0wn is currently viewing moon: Shellabby."
* Current planets (`!stats planets`) e.g. "Planets (5): Nauvis, Thrasos, Talos, Corus, Shennong."
* Current moons (`!stats moons`) e.g. "Moons (2): Morus, Shellabby."
* Surface stats (`!stats surface <planet/moon name>`) e.g. `!stats surface Termina`: "Termina (moon) stats - Radius: 3350, Day length: 51.14min, Primary resource: se-holmium-ore, Threat: 3%"
* Power stats (`!stats power <planet/moon name>`) e.g. `!stats power Talos`: "Talos power stats - 121 se-space-solar-panel: 45.2MW (71.1%) | 25 se-space-solar-panel-2: 18.4MW (28.9)."
* Science production: only non-zero values are shown due to the large number of science research items (`!stats science`) e.g. "Science production (last hour): R:17.5/m G:22.8/m W:21.4/m AS1:8.8/m AS2:2.1/m ES1:6.2/m ES2:2.1/m DS1:3.9/m."

This science production command also includes support for if you are using space-exploration+krastorio2 in your savegame.

#### [Ribbon Maze Mod](https://mods.factorio.com/mod/RibbonMaze018) by H8UL, kajacx

* Maze stats: width, height and number of dead ends (`!stats maze`) e.g. "RibbonMaze is currently 21 units wide and 47 units tall with 37 dead ends."

#### [Armoured Biters](https://mods.factorio.com/mod/ArmouredBiters) by CybranM

* Kill stats, including new 'Snappers' (`!stats kills`) e.g. "Total kills (kill rate for last hour) - Spawners:11k (1.1/min) Snappers:28k (4.2/min) Biters:36k (5.2/min) Spitters:36k (4.8/min) Worms:10k (1.9/min)."

#### [Angel's Exploration Mod](https://mods.factorio.com/mod/angelsexploration) by Arch666Angel

* Kill stats, including new 'Psykers' and 'Scarabs' (`!stats kills`) e.g. "Total kills (kill rate for last hour) - Spawners:11k (1.1/min) Psykers:28k (4.2/min) Scarabs:26k (4.5/min) Biters:36k (5.2/min) Spitters:36k (4.8/min) Worms:10k (1.9/min)."

#### Stats help

* Show detailed help for stats commands (Appended to `!stats`) e.g. "Also try: !stats | !stats about | !stats consumption \<internal-item-name\> | !stats kills | !stats maze | !stats power | !stats production \<internal-item-name\> | !stats science"
* Suggest to try !stats help (Appended to `!stats`) e.g. "Try '!stats help' for more."
* Show detailed help for stats commands (`!stats help`) e.g. "Try: !stats | !stats about | !stats consumption \<internal-item-name\> | !stats kills | !stats maze | !stats power | !stats production \<internal-item-name\> | !stats science"

## Issues

Errors are written to a `error_log.txt` file.
If you lose internet connection, you may need to stop and start the bot again.

## Adding more commands

This requires some lua and JSON format knowledge.

#### Config file documentation

Description of the json file properties:

* `heading` is the title displayed in the GUI
* `priority` defines the ordering in the application, as well as if a command should be overwritten by another config file's command (lower = less priority). Therefore if `!stats science` is enabled in base game and bob's. Then the bob's science command will overwrite the base game one, as it has a higher priority.
* `overwrite` defines if this command should overwrite a previously loaded implementation. Example: the science command of mods should overwrite the base game's science command. If false, then it appends it's result to the command.
* `args description` is for describing the argument that the command expects. `null` if not arg expected.
* `lua` is the actual code that gets run on the server. Note: prefix it with `/silent-command`, and the resulting output from `rcon.print` is what appears in the twitch chat message.
* `enabled_on_startup` defines whether this command should be already ticked when the application is launched.

Within the lua code, there are 3 special strings that get replaced at runtime.

* `__FACTORIO_USERNAME__` is replaced with the factorio username specified in the settings.
* `__ARG_VALUE__` is replaced by the argument value given in the command message (only if this command accepts arg values i.e. if `args_description` is not null).
* `__STATS_HELP__` is replaced by a concatenated list of all the enabled commands.

## Possible future additions

* Add support for Angel's mod science when using the 'Technology Overhaul' map setting. This setting add's science analyzers, datacores and alien life plant samples to research tech, instead of using science packs.
* Add option to auto-detect mods/settings and enable all compatible commands.
