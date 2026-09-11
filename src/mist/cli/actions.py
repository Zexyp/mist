import argparse

class CommandHelpAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # we want to indicate that desired parser didn't run
        match option_string:
            case "-h":
                parser.print_usage()
            case "--help":
                parser.print_help()
            case _:
                assert False

        parser.exit(1)


class RootHelpAction(argparse.Action):
    def __init__(self, option_strings, dest, commands=None, **kwargs):
        super().__init__(option_strings, dest, **kwargs)
        self.commands = commands

    def __call__(self, parser, namespace, values, option_string=None):
        # help is a valid action so just exit normally
        match option_string:
            case "-h":
                parser.print_usage()
            case "--help":
                parser.print_help()
                print("commands:")
                for name, subparser in self.commands.items():
                    print(f"  {name:16}", end="")
                    if subparser.description:
                        print(f" {subparser.description}", end="")
                    print()
            case _:
                assert False

        parser.exit()
