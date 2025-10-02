#!/usr/bin/env python3
import argparse
import sys
import subprocess


def bd(args): 
    print("bd called", args)

def bj(args): 
    if args.watch:
        subprocess.run(["oc", "get", "-w", "jobs"])
    else:
        subprocess.run(["oc", "get", "jobs"])
def bl(args): 
    print("bl called", args)
def bp(args): 
    print("bp called", args)
def bs(args): 
    print("bs called", args)
def bq(args): 
    print("bq called", args)
def bw(args): 
    print("bw called", args)
def br(args): 
    print("br called", args)
def bwk(args): 
    print("bwk called", args)

def main():
    valid_args = {"bd", "bj", "bl", "bp", "bs", "bq", "bw", "br", "bwk"}

    parser = argparse.ArgumentParser(description="Command-line tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create subparsers for valid command
    for cmd in valid_args:
        sub = subparsers.add_parser(cmd, help=f"Run {cmd}")
        if cmd == "bd":
            sub.add_argument("-h", nargs="*")
        elif cmd == "bj":
            sub.add_argument("-w", "--watch", action="store_true",
                             help="Watch jobs continuously")

    args = parser.parse_args()

    # Lookup the function by name and call it
    func = globals().get(args.command)
    if func:
        sys.exit(func(args))
    else:
        print(f"Unknown command {args.command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
