#!/usr/bin/env python
import argparse
import os
import sys
import time
import git
from collections import defaultdict
from colorama import Fore, Style
from smartlog.smartlog import Smartlog
from smartlog.printer import TreePrinter, NodePrinter, RefList

def parse_args():
    parser = argparse.ArgumentParser(description="Git Smartlog")
    parser.add_argument("-a", "--all", action="store_true", help="Display all commits, regardless of age")
    return parser.parse_args()

def main():
    start_time = time.time()

    args = parse_args()

    try:
        repo = git.Repo(os.getcwd())
    except git.exc.InvalidGitRepositoryError:
        print("Invalid git repository at {}".format(os.getcwd()))
        exit(1)

    # Compute minimum age of displayed commits. By default, display last 2 weeks
    if args.all:
        max_age = None
    else:
        max_age = 14 * 24 * 3600  #14 days

    try:
        main_ref = repo.refs["origin/master"]
    except IndexError:
        print("Error: Unable to find origin/master branch")
        exit(-1)

    smartlog = Smartlog(repo, main_ref, max_age=max_age)

    # Add all local branches
    for ref in repo.heads:
        smartlog.add_commit(ref.commit)

    # Add current head commit
    smartlog.add_commit(repo.head.commit)

    reflist = RefList(repo, extra_refs=[main_ref])
    node_printer = NodePrinter(repo, reflist)
    printer = TreePrinter(repo, smartlog.root_node, main_ref, node_printer)
    printer.print_tree()

    print("Finished in {0:.3f}s".format(time.time() - start_time))

if __name__ == "__main__":
    main()