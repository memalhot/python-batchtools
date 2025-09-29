import sys
import subprocess


def run(command):
    return subprocess.run(command, check=False, text=True, capture_output=True)

# Define your functions
def bd():
    """delete workloads, if none passed, delete every job"""
    workloads=sys.argv[2:]

    if not workloads:
        res = run(["oc", "get", "workloads", "-o", "name"])
        if res.returncode != 0:
            sys.stderr.write("Failed to list workloads via oc.\n")
            sys.exit(res.returncode)
        workloads = [line.strip() for line in res.stdout.splitlines() if line.strip()]
    
    for w in workloads:
        name = w if "/" in w else f"workloads/{w}"
        res = run(["oc", "delete", name])
        if res.stdout:
            sys.stdout.write(res.stdout)
        if res.stderr:
            sys.stderr.write(res.stderr)
        if res.returncode != 0:
            exit_code = res.returncode

    sys.exit(exit_code)

def bj():
    print("bj called")

def bl():
    print("bl called")

def bp():
    print("bp called")

def bs():
    print("bs called")

def bq():
    print("bq called")

def bw():
    print("bw called")


def main():
    valid_args = {"bd", "bj", "bl", "bp", "bs", "bq", "bw"}

    # Skip the first arg (program name)
    args = sys.argv[1]

    if not args:
        # CHANGE ME
        print("Usage: python script.py <bd|bj|bl|bp|bs|bq|bw>")
        sys.exit(1)

    for arg in args:
        if arg in valid_args:
                globals()[arg]() 
        else:
            print(f"Unknown argument: {arg}")
            sys.exit(1)


if __name__ == "__main__":
    main()
