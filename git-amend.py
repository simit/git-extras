#!/usr/bin/env python
import argparse
import os
import subprocess as sp
from git import Repo
import time
from shared.utils import get_heads_at, get_child_heads, safeget_head


def parse_args():
    parser = argparse.ArgumentParser(description="Git Amend")
    parser.add_argument("-a", "--add-all", action="store_true", help="Add all unstaged changes to index before attempting an amend.")
    parser.add_argument("-f", "--force", action="store_true", help="Force an amend even if there are no working copy changes. Useful for adjusting the message of the commit")
    return parser.parse_args()

def main():
    args = parse_args()

    repo = Repo(os.getcwd())

    if args.add_all:
        print("Adding all changes to index")
        repo.git.add(["."])

    if len(repo.index.diff("HEAD")) == 0 and not args.force:
        print("No changes are staged. Use option -a to automatically stage changes, or option -f to force an amend and edit the commit message.")
        exit(0)

    src_commit = repo.head.commit
    src_shortsha = repo.git.rev_parse(src_commit.hexsha, short=True)

    # TODO: Improve to check against other remove branches too
    if src_commit in repo.merge_base(src_commit, repo.remotes.origin.refs.master.commit):
        print("Error: You are trying to amend a revision already pushed on origin/master.")
        exit(1)

    amend_branch_name = "amend-{}".format(src_shortsha)
    if safeget_head(repo, amend_branch_name) is not None:
        print("Error: Found an amend in progress for this commit. Please resolve branch {} before continuing.".format(amend_branch_name))
        exit(1)

    src_has_child_heads = len(get_child_heads(repo, src_commit)) > 0

    # If we have any child heads, we will likely create a temp branch in the end, so move to a detached HEAD state
    if src_has_child_heads:
        # Move to a detached HEAD state
        repo.head.reference = src_commit

    # Amend the changes using commit --amend
    try:
        repo.git.commit(amend=True)
    except KeyboardInterrupt:
        print("Aborting!")
        exit(1)

    if repo.head.commit == src_commit:
        print("Error: Amend was cancelled")
        exit(0)

    amend_commit = repo.head.commit

    if src_has_child_heads:
        # Move the HEAD to a new temp branch
        repo.head.reference = repo.create_head(amend_branch_name)
    else:
        # If there were no child branches for the source commit, move any exact heads to the new commit
        # We do not need to create a temp branch for this
        src_heads = get_heads_at(repo, src_commit)
        for head in src_heads:
            print("Updating {}".format(head.name))
            head.reference = amend_commit


if __name__ == "__main__":
    main()