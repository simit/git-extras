#!/usr/bin/env python3
import argparse
import subprocess as sp

def parse_args():
    parser = argparse.ArgumentParser(description="Git View")
    parser.add_argument("revision",
        nargs="?",
        default=None,
        help="Display the changes in a revision (compared with its parent). If missing, it compares the uncommitted changes to HEAD")
    return parser.parse_args()

def main():
    args = parse_args()

    if args.revision is not None:
        run_cmd(["git", "difftool", "-y", "--dir-diff", "{}^..{}".format(args.revision, args.revision)])
    else:
        run_cmd(["git", "difftool", "-y", "--dir-diff", "HEAD"])

def run_cmd(cmd: list):
    print("Running: {}".format(" ".join(cmd)))
    try:
        sp.run(cmd)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

