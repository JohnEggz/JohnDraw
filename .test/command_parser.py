import shlex

class Command:
    def __init__(self, name, args, kwargs, flags):
        self.name = name       # The main command (e.g., "canvas")
        self.args = args       # Positional args (e.g., ["move"])
        self.kwargs = kwargs   # Key-value pairs (e.g., {"x": "-50"})
        self.flags = flags     # Boolean flags (e.g., {"animate"})

    def __repr__(self):
        return f"<Cmd: {self.name} args={self.args} kwargs={self.kwargs} flags={self.flags}>"

def parse_command(command_str: str) -> Command:
    """
    Parses a Linux CLI style string:
    'canvas move --x=-50 --y=0 --animate'
    """
    if not command_str:
        return None

    # shlex handles quotes and splitting correctly (e.g., 'val with spaces')
    try:
        tokens = shlex.split(command_str)
    except ValueError as e:
        print(f"Command Parse Error: {e}")
        return None

    if not tokens:
        return None

    cmd_name = tokens[0]
    args = []
    kwargs = {}
    flags = set()

    # Iterate over the rest of the tokens
    for token in tokens[1:]:
        if token.startswith("--"):
            # It is a flag or a key-value pair
            content = token[2:] # Strip '--'
            
            if "=" in content:
                # Handle --key=value
                key, value = content.split("=", 1)
                kwargs[key] = value
            else:
                # Handle --flag
                flags.add(content)
        else:
            # It is a positional argument
            args.append(token)

    return Command(cmd_name, args, kwargs, flags)
