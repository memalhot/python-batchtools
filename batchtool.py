#!/usr/bin/env python3
import argparse
import sys
import subprocess


def bd(args): 
    print("bd called", args)

    # CHECK IF ARGS PROVIDES A WORKLOAD TO DELETE

    # save this somewhere
    result = subprocess.run(["oc", "get", "workloads", "-o", "name"], capture_output=True, text=True, check=True)
    workloads = result.stdout.strip().splitlines()

    workloads = [w for w in workloads if w.startswith("job-job") or w.startswith("workloads/job-job")]

    if not workloads:
        print ("No GPU worloads found to delete")
        return  
    for w in workloads:
        print(w)
        name = w if "/" in w else f"workloads/{w}"
        subprocess.run(["oc", "delete", name])


def bj(args): 
    if args:
        subprocess.run(["oc", "get", "-w", "jobs"])
    else:
        subprocess.run(["oc", "get", "jobs"])
def bl(args):
    subprocess.run()

    print("bl called", args)
def bp(args): 
    print("bp called", args)

    if not pods:
        ret = subprocess.run(["oc", "get", "pods"], capture_output=True, text=True, check=True)

        pods = ret.stdout.strip().split
        print(pods)
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
        if cmd == "bj":
            sub.add_argument("-w", "--watch")

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
