#!/usr/bin/env python
import os
import subprocess as sp
from git import Repo
from shared.utils import get_heads_at, get_child_heads, delete_head
import time
import logging
logging.basicConfig(level=logging.ERROR)

AMEND_BRANCH_PREFIX = "amend-"

def main():
    repo = Repo(os.getcwd())

    # Get current commit
    amended_commit = repo.head.commit

    # TODO: Fail if there is any rebase in progress

    # Get the short sha hash for the current commit
    amended_shortsha = repo.git.rev_parse(amended_commit.hexsha, short=True)

    # Find if this commit has an amended branch name on it
    amend_head = None
    for head in repo.heads:
        if head.commit == amended_commit and head.name.startswith(AMEND_BRANCH_PREFIX):
            amend_head = head
            break

    if amend_head is None:
        print("No amend in progress for HEAD commit {}".format(amended_shortsha))
        exit(0)

    src_shortsha = amend_head.name[len(AMEND_BRANCH_PREFIX):]
    if src_shortsha is None:
        print("No amend in progress for HEAD commit {}".format(amended_shortsha))
        exit(0)

    src_commit = repo.commit(src_shortsha)
    if src_commit is None:
        print("Error: Could not locate source commit with hash {}".format(src_shortsha))
        exit(1)

    print("Restacking children of {}".format(src_commit.hexsha))

    can_cleanup = True

    # Move any branches that were exactly on the source commit to the new commit
    src_heads = get_heads_at(repo, src_commit)
    for head in src_heads:
        print("Updating {}".format(head.name))
        head.reference = amended_commit

    # Move any branches that have child commits to the source commit
    heads_to_restack = get_child_heads(repo, src_commit)
    if len(heads_to_restack) > 1:
        can_cleanup = False
        print("Error: Too many child branches found ({}). Restack only supports a single child branch.".format(len(heads_to_restack)))
    elif len(heads_to_restack) == 1:
        head = heads_to_restack[0]
        print("Rebasing {} to amended commit {}".format(head.name, amended_shortsha))
        repo.git.rebase(src_commit, head.name, onto=amended_commit)
        # Verify if the moved branch is now on top of the amended commit
        if amended_commit not in repo.merge_base(amended_commit, head.commit):
            can_cleanup = False
            print("Error: Rebasing {} failed. Please attempt another restack after rebasing has been solved.".format(head.name))

    if can_cleanup:
        # Delete the temporary branch name
        delete_head(repo, amend_head)
    else:
        print("Restack did not finish successfully. Please run restack again after fixing the errors.")
        exit(1)


def safeget_heads(repo, name):
    try:
        return repo.heads[name]
    except IndexError:
        return None


if __name__ == "__main__":
    main()