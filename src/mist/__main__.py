import sys

from mist import cli

def main():
    args = sys.argv[1:] # discard program name
    return cli.run(args)
    
if __name__ == "__main__":
    main()
