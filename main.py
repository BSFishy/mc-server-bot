# Import
import discord
from discord.ext import commands
import os
from os import path
import threading
import configparser
import traceback
import psutil
import subprocess
from shlex import quote, split

dir_path = path.dirname(path.realpath(__file__)) # Get the full path of the directory that this file is contained in

config_file = path.join(dir_path, 'config.ini') # Create the path to the config file using dir_path
if not path.exists(config_file) or not path.isfile(config_file): # Check to make sure the config file exists and is an actual file
    print(f'A config.ini file is required in {dir_path}') # If not, write a log message...
    quit() # and quit

config = configparser.ConfigParser() # Create a new config parser
config.read(config_file) # Read the contents of the config file into the parser

if not config['DEFAULT'] or not config['DEFAULT']['server_dir'] or not config['DEFAULT']['token']: # Check to make sure the necessary information is in the config file
    print('The config file does not have the necessary information. Make sure there is a "DEFAULT" section, with "server_dir" and "token" in it.') # If not, write a log message...
    quit() # and quit

server_dir = config['DEFAULT']['server_dir'] # Get the specified server directory. This should be a directory containing subdirectories, which contain servers
if not path.exists(server_dir) or not path.isdir(server_dir): # Check to make sure the server directory exists and is an actual directory
    print(f'The directory specified for server_dir({server_dir}) either doesn\'t exist, or isn\'t a directory.') # If not, write a log message...
    quit() # and quit

token = config['DEFAULT']['token'] # Get the token

print(f'Using {server_dir} as the server directory.') # Print a log message to inform about the current status
server_threads = [] # A list of all of the thread of the running servers

class Help(commands.DefaultHelpCommand): # Define the help command
    """The help command to be used. This overrides the default help command, in order to provide
    a cleaner and more specialized appearance."""

    def __init__(self, **options):
        """Initialize the variables. This is where instance variables for the class are initialized
        to be used later in methods or externally."""
        self.size_offset = options.pop('size_offset', 5) # The offset to be applied after each command in the main help

        super().__init__(**options) # Call the initializer of the parent class

    def get_ending_note(self):
        """This is the note at the bottom of the main help command."""
        return f"Type {self.clean_prefix}{self.invoked_with} command for more info on a command." # Return a simple formatted end note

    def add_indented_commands(self, commands, *, heading, max_size=None):
        """Add a list of commands to the output. This takes a list of commands and should add
        a formatted line for each of them to the output. If there are no commands, however,
        nothing should happen."""
        if not commands: # Check if there are no commands
            return # Do nothing if there are no commands to add

        max_size = max_size or self.get_max_size(commands) # Get the length to pad the commands with

        get_width = discord.utils._string_width # Get an internal utility function from discord
        for command in commands: # Loop through each command in the commands list
            name = command.name # Get the name of the command
            width = max_size - (get_width(name) - len(name)) # Figure out the width to pad the command name with
            entry = '{0}{1}{2:<{width}} {3}'.format(self.indent * ' ', self.clean_prefix, name, command.short_doc, width=width) # Create a formatted string to add to the help command
            self.paginator.add_line(self.shorten_text(entry)) # Add the formatted string to the help command

    def get_max_size(self, commands):
        """Get the length of the commands. This should return the length of the command with the longest
        name, offset by some value."""
        return max(list(len(command.name) for command in commands)) + self.size_offset # This is the shorthand to get the max length of each command name, then add an offset the the result.

class ServerThread(threading.Thread):
    """A thread to run a server. This is a simple thread implementation, which will run
    a server start file in another thread, so it doesn't block the current thread."""

    def __init__(self, dir, file):
        """Initialize the variables. The main objective here is to get the file to actually run.
        Another product is to call the super initializer with a name, but to my knowledge, that
        is not too entirely necessary."""
        self.dir = dir # Store the directory to run the file in
        self.file = file # Store the file to run in an instance variable

        super().__init__(name=f'server-{file}') # Call the super initializer with a name

    def run(self):
        """Run the thread. This is the actual logic of the thread. It is as simple as just running the
        file as a command."""
        print(f'Running server {self.file} in {self.dir}') # Write a simple debug message to the console

        try: # Try to run the file
            subprocess.run(f'start "Server" /D "{self.dir}" /HIGH "{self.file}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) # Run the file
        except Exception as ex: # Catch any exceptions that may occur when running the file
            print(f'Error running {self.file}:\n\n') # Print a console message to help identify issues
            traceback.print_exc() # Print the full error

help_command = Help() # Create the help command
help_command.dm_help = False # Never send help as a dm
help_command.indent = 4 # Indentation of commands from heading
help_command.size_offset = 2 # Add a padding offset to the commands

client = commands.Bot(command_prefix = '.', help_command=help_command, description='This is a bot to assist in starting Minecraft servers')

@client.event
async def on_ready():
    """Called when the bot is initialized."""
    print('Autobots, Roll Out!') # Print a message to the console to aknkowledge the status

# When the bot sees specific message (.help)
@client.command(
    name='helpme',
    brief='Shows list of commands and their duties',
    help='Shows list of commands and their duties',
    description='Helps you')
async def help(ctx):
    await ctx.send(f"```"
        "\n================================="
        "\n==========  Commands  ==========="
        "\n================================="
        "\n \n.helpme (shows this block of text)"
        "\n \n.clear (clears the last 5 messages in chat)"
        "\n \n.select (select 1 or more servers to run)"
        "\n \n.start (starts the server/s selected)"
        "\n \n================================="
        "\n \nNote: (You can see the syntax for any command by adding "'help'" to the start of it)"
        "\n \n(Example: === .help clear === should give you syntax info)```")

@commands.has_permissions(manage_messages=True) # Only run if the user has the correct permission
@client.command(
    name='clear',
    brief='Clear a certain amount of messages',
    help='Clear a certain amount of messages. This will clear the amount of messages specified, or '
         'if none are specified, a default 6 will be deleted. Todo: make permissions matter',
    description='Clear a message.')
async def clear(ctx, amount=6):
    """A simple clear command. This command will simply purge a specific number of messages, defaulting
    to 6. The command can only be run, though, by people who have the 'Manage messages' permission."""
    await ctx.channel.purge(limit=amount) # Actually purge the messages

# --------------------------------------------------------------------------------------- #
# -------------------------- User input to Bot output section --------------------------- #
# --------------------------------------------------------------------------------------- #

def get_server_dirs():
    """Utility function to get a list of server directories. The objective of this function is to
    look through the server directory for subdirectories. From there, it will check the contents of
    those subdirectories, looking for a start file. If none is found, the directory is ignored, and
    the next one is checked. If it does have a start file, it is appended to the list of server
    directories, which is returned."""
    dirs = [f for f in os.listdir(server_dir) if path.isdir(path.join(server_dir, f))] # Get a list of subdirectories in server_dir
    server_dirs = [] # A list of server directories. This will be populated when the subdirectories are checked.

    for dir_tmp in dirs: # Iterate through the subdirectories
        dir = path.join(server_dir, dir_tmp) # Construct an absolute path to the subdirectory
        files = [f for f in os.listdir(dir) if path.isfile(path.join(dir, f))] # Get the files in the subdirectory

        start_file = None # The name of the start file. This is initially None to represent that there is no start file.
        if 'start.bat' in files: # Check if start.bat is a file in the subdirectory
            start_file = 'start.bat' # If so, set the start file to it
        if 'run.bat' in files: # Check if run.bat is a file in the subdirectory
            start_file = 'run.bat' # If so, set the start file to it

        if not start_file: # Check if there is still no start file in the subdirectory
            print(f'No start file in {dir}. Ignoring.') # If there is no start file, log a message to the console...
            continue # and continue without adding it as a server directory

        server_dirs.append(dir_tmp) # Append the directory as a server directory

    return server_dirs # Return the populated list of server directories

def get_server_list():
    """Get a list of servers. This is called every time the run command is called, and should
    check to see what servers are available. The output is a list of dictionaries. Each dictionary
    represents a single server. Each server has a name, a version, and a mods key. They are all
    strings, so they can be filled with whatever data may be useful. The only restriction is that
    the name cannot contain any spaces, as that would conflict with selecting a server using the
    run command. To find the pertinent information, first the servers directory should be polled
    for subdirectories. Each of those should then be check to see if it has a batch start file.
    A few names should be checked for compatibility, for example 'start.bat', 'run.bat', etc.
    Just having a batch start file is enough to be recognized as a server. If no other information
    is found, it should be initialized to 'Unknown'. To find metadata, the individual server
    directories should be polled for a metadata file. This file should contain the necessary
    metadata, but doesn't need to specify everything. Right now, a list is hard-coded for testing"""
    dirs = get_server_dirs() # Get a list of server directories
    servers = [] # A list of servers. This will be populated depending on the contents of the server directories

    for dir in dirs: # Iterate through each server directory
        server = {'name': dir, 'version': 'Unknown', 'mods': 'Unknown'} # Initialize the server with some default data. This can be overriden later
        servers.append(server) # Add the server to the list of servers

        server_config_file = path.join(server_dir, dir, 'metadata.ini') # Construct a path to a metadata file
        if path.exists(server_config_file) and path.isfile(server_config_file): # Check if the metadata file exists and is an actual file
            server_config = configparser.ConfigParser() # Create a configuration parser for the metadata file
            server_config.read(server_config_file) # Read and parse the contents of the metadata file

            server_info = server_config['server'] # Get the server section. This could be None if it does not exist. It is optional
            if server_info: # Check if there is a server section
                server_version = server_info['version'] # Get the version value. Again, this is optional
                if server_version: # Check if there is a version value
                    server['version'] = server_version # Set the version of the server info to the version from the metadata

                server_mods = server_info['mods'] # Get the mods value. Again, this is optional
                if server_mods: # Check if there is a mods value
                    server['mods'] = server_mods # Set the mods of the server info to the mods from the metadata

    return servers # Return the populated list of servers

def start_server(name):
    """Actually start a server. This should be called whenever a server is meant to be started.
    First, we need to check to make sure the inputted server name is valid. To do that, we check
    to make sure we have a valid variable for name. If not, throw a TypeError. Next, we need to
    check if the server is found. To do that, we need to search the servers directory and check if
    the specified name is a directory in there. If it's not, throw a ValueError. The server directory
    should be specified in a configuration file in the same directory as the script. Next, we need to
    check if the server is already running. This should be done by querying the OS to see if there
    is a process already started for the server. If the server is already running, throw a RuntimeError.
    Next, we need to actually start the server. This is as simple as just calling the batch file
    if the server's directory. Any reason that the server should not be started should be logged to
    the console."""
    if not name or not isinstance(name, str): # Check to see if the inputted name is valid.
        raise TypeError('Received an invalid argument') # If the name is not valid, throw a type error.

    server_path = path.join(server_dir, name) # Construct an absolute path to the server's directory
    if not path.exists(server_path) or not path.isdir(server_path): # Check if the server path exists and is an actual directory
        print(f'{server_path} was not a valid server directory') # If not, print a message to the console...
        raise ValueError('The server path is invalid') # and raise a value error

    server_files = [f for f in os.listdir(server_path) if path.isfile(path.join(server_path, f))] # Get a list of files in the server's directory
    start_file = None # The name of the start file. This is initially None to represent that there is no start file.
    if 'start.bat' in server_files: # Check if start.bat is a file in the subdirectory
        start_file = 'start.bat' # If so, set the start file to it
    if 'run.bat' in server_files: # Check if run.bat is a file in the subdirectory
        start_file = 'run.bat' # If so, set the start file to it

    if not start_file: # Check if there is still no start file in the subdirectory
        print(f'{server_path} did not contain a valid start file') # If there is no start file, log an error message to the console...
        raise ValueError('A start file could not be found') # And raise a value error

    start_path = path.join(server_path, start_file) # Construct an absolute path to the start file
    for process in psutil.process_iter(): # Iterate through all of the running processes
        try: # Use try in order to catch any permission errors (They may occur if a process is set to not be visible to specific users)
            if start_path in process.cmdline() and process.status() == psutil.STATUS_RUNNING: # Check if the process' command line command contains the start file and is running (our assumption that that's the process that started it)
                print(f'PID {process.pid} is already running for {start_path}') # If so, print a message to the console...
                raise RuntimeError('The server is already running') # and raise a runtime error
        except RuntimeError: # Catch a runtime error in specific, because we want to ignore it
            raise # Re-raise the runtime error, because that denotes that a server is already running
        except: # Catch any exceptions that may have occured
            pass # Discard any exceptions

    print(f'Starting server "{name}"') # Print a log message to the console to inform of the current status

    server_thread = ServerThread(server_path, start_path) # Create a server thread and initialize it with the start path
    server_thread.start() # Start the server thread
    server_threads.append(server_thread) # Add the server thread to the server threads list for future use (i.e. stopping)

    print(f'Started {name}') # Print a log message to the console to inform of the current status

@@commands.check_any(commands.has_role('Minecraft OPS'), commands.has_permissions(administrator=True)) # Only allow people to start server that have the role or are administrators
@client.command(
    name='run',
    brief='Start a server',
    help='Start a server. The syntax is the command then a list of servers, separated by spaces. '
         'You can also just specify one server to run. To get a list of servers, run this command'
         ' without any arguments.',
    description='Start one or more server(s)')
async def run(ctx, *input):
    """Run server command. This is the command that actually allows users to start a server. The first
    thing to do is to get an updated list of servers. This can be done by calling the get_server_list
    function. Next we need to check to see if we have any input. If not, send a list of servers with
    their respective information. If we do have input, loop through it and check to see if each inputted
    server is valid. If one isn't just ignore it. For every server that is valid, pass it to the"""
    servers = get_server_list() # Get an updated list of servers. This will check each time the command is run, so new servers can be added at will.

    if not input: # Check to see if there is any input. If the user ran the command without any arguments, this will evaluate to true.
        max_size = 0 # This contains the length of the longest server name
        for server in servers: # Loop through all of the servers to find the longest name.
            max_size = max(len(server['name']), max_size) # This is a simple statement which will update max_size with the length of the current server's name if it is longer that max_size.

        msg = '```' # Begin the message string. The entire message uses a single string so that there is only one message and so that we can use formatting.
        msg += 'Available servers:'
        for server in servers: # Loop through all of the servers to add info about each of them.
            msg += '\n\t{0:<{width}} Version: {1} Type: {2}'.format(server['name'], server['version'], server['mods'], width=max_size+4) # Append a pretty string with the server info
        msg += '```'

        await ctx.send(msg) # Send the message
        return # Return so that we don't trigger any logic below (logic that assumes we have input)

    # Here we know that we have some input, because if we didn't control would have stopped at the return statement in the if above.
    server_names = list(s['name'] for s in servers) # Build a list of server names. This is a shorthand foreach loop that just makes a list of the name value of each item in servers.
    for server in input: # Loop through all of the inputted "servers"
        if not isinstance(server, str): # Check to make sure the inputted server is a string. I think it always should be a string, but this will guarantee it for us.
            await ctx.send(f'Input "{server}" is not a valid server. Ignoring.') # Send an error message if it isn't a string

            continue # Continue so that we don't actually do anything with this malformed input

        if server not in server_names: # Check to see if the server name is valid.
            await ctx.send(f'Server "{server}" could not be found. Ignoring.') # Send an error message if the inputted server name is not found

            continue # Continue so that we don't start a server that doesn't exist.

        await ctx.send(f'Starting server "{server}"') # Send a log message to inform the user of the current status

        try: # Try to start the server
            start_server(server) # Actually start the server
        except TypeError: # Catch if the inputted name is invalid for whatever reason
            await ctx.send(f'There was an internal error starting server {server}. Please contact a server administrator.') # Send an error message to inform the user of the status
        except ValueError: # Catch if the inputted name was not found
            await ctx.send(f'The server {server} could not seem to be found. Try again later.') # Send an error message to inform the user of the status
        except RuntimeError: # Catch if the server is already running.
            await ctx.send(f'The server {server} is already running.') # Send an error message to inform the user of the status
        except Exception: # Catch a general exception. This is here in case there was any extreneous error in the os functions.
            print(f'Unknown error starting "{server}". Log:\n') # Print a status message to the console
            traceback.print_exc() # Print the full stack trace
            await ctx.send(f'There was an internal error starting server {server}. Please contact a server administrator.') # Send an error message to inform the user of the status
        else: # If the server started without throwing any sort of error
            await ctx.send(f'Server "{server}" started') # Send a log message to inform the user of the current status. TODO: potentially don't send this? (it could be confused with meaning the server is actually started.)

client.run(token)
