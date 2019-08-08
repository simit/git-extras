def get_child_heads(repo, commit):
    """
    Returns a list of heads(branches) that will need to be restacked for a given commit.
    Will ignore any heads that are pointing to the commit given.
    Returns empty list of none are found
    """
    found = []
    for head in repo.heads:
            if head.commit != commit and commit in repo.merge_base(commit, head.commit):
                found.append(head)
    return found

def get_heads_at(repo, commit):
    """
    Return all heads that are pointing to a specific commit.
    Returns empty list if none are found
    """
    found = []
    for head in repo.heads:
            if head.commit == commit:
                found.append(head)
    return found

def delete_head(repo, head):
    """
    Deletes a specified head pointer.
    If git's HEAD was pointing to this, move HEAD to the commit
    """
    if repo.head.commit == head.commit:
        repo.head.reference = head.commit
    repo.delete_head(head, force=True)

def safeget_head(repo, name):
    """
    Returns a Head object if found. Returns None otherwise
    """
    try:
        return repo.heads[name]
    except IndexError:
        return None
