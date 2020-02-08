# Discord Minecraft Server Bot
A bot for Discord, which allows you to let members of your Discord server start Minecraft servers with a command.

## Usage
Setup on the server-side is a tiny bit complicated so that usage in Discord is simple.
First, we need to make sure we have the necessary things installed.

### Installation
First thing's first, we need to get everything installed.
The first thing you'll need is [Python](https://www.python.org/downloads/).
This project uses Python 3.7.6, so make sure you install that version or higher.

Next thing, we need to install dependencies.
This project uses [Discord.py](https://discordpy.readthedocs.io/en/latest/) and [psutil](https://psutil.readthedocs.io/en/latest/).
The command to install those is as follows:

```text
pip3 install -U discord.py psutil
```

### Bot setup
The next thing is to actually setup the bot on Discord.
You can follow the [tutorial by Discord.py](https://discordpy.readthedocs.io/en/latest/discord.html) to achieve this.

### Getting the code
Now, you need to get the code.
This is as simple as copying the code in `main.py` to a text file on your computer with the same name.
After that, you'll also need to make a `config.ini` file in the same directory as `main.py`.
A template for `config.ini` can be found in this repository as well.
You can fill in the token for your bot, and put in a path to the directory containing your servers.

### Preparing servers
The last step is to setup your servers.
To do this, you need to create a 'servers directory'.
This should be a directory containing only subdirectories.
Each subdirectory should contain a separate server instance.
Each server should have a `run.bat` or `start.bat` in it.
The structure should look like this:

```text
 servers
  |-server1
  |  | run.bat
  |  | config.ini
  |  \ ...
  \-server2
     | start.bat
     \ ...
```

Once you have that, you should be done.
Just start the script, and you should be able to use the bot in your server.

### Server configuration
Servers can have an optional `metadata.ini` file.
This file specifies the server version and type.
A generic template looks like this:

```ini
[server]
version = 1.12.2
mods = Vanilla
```

These strings are abstract, and have no meaning outside of the one that you give them.
They are simply taken from the metadata file and printed when requested.

### Commands
There are a couple commands that you can use:

 1. `.help`
    A simple help command.
    This will just give some simple information about the commands provided by the bot.
 2. `.clear [amount=6]`
    A purge command.
    This will allow you to purge a certain amount of messages.
 3. `.run [server...]`
    This is the main server command.
    Running it without any parameters will list the available servers and their metadata.
    You can then run it with a server name to start the specific server.
    If the server has already been started, it won't be started again, and servers that aren't found will be ignored.
