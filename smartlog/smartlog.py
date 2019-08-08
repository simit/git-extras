#!/usr/bin/env python3
from time import time
from git import Repo

class Smartlog:
    """
    Main compute class that can construct a sparse dependency tree and print it.
    Nodes in the tree are either explicit or implicit commits.
    Explicit commits are commits currently pointed to by a reference or local commits not on origin/master yet
    Implicit commits are common ancestors between the local branches and origin/master
    """
    def __init__(self, repo, main_ref, max_age=None):
        if repo is None:
            raise ValueError("Repo must not be None")
        if main_ref is None:
            raise ValueError("Main ref name must not be None")

        self.repo = repo
        self.commit_date_limit = time() - max_age if max_age else None

        self.nodestore = NodeStore(repo)

        # Create a dummy node to store our tree
        self.root_node = Node(repo, None)

        # Create a node for the main ref that we start with. Connect it to the dummy node
        self.main_ref = main_ref
        self.main_node = self.nodestore.add(main_ref.commit)
        self.main_node.parent = self.root_node
        self.main_node.is_main = True
        self.root_node.children.append(self.main_node)

    def add_commit(self, commit):
        if commit is None:
            return

        # Do not add top level commits that are older than our max age
        if self.commit_date_limit is not None and commit.committed_date < self.commit_date_limit:
            return

        # Generate a node object to represent our commit
        commit_node = self.nodestore.get(commit)

        # Find the Lowest Common Ancestor (LCA) between our commit and the main branch
        # and add to our node tree
        lca_node = self.get_merge_base(commit_node, self.main_node)
        if lca_node is None:
            print("Unsupported: All commits must have a merge-base with '{}'".format(self.main_ref.name))
            return
        lca_node.is_main = True
        if not lca_node.is_connected():
            self.add_lca(lca_node, self.main_node)

        # Interate the local commits and add to the tree until we find a node that is already added
        node = commit_node
        while node != lca_node and not node.is_connected():
            next_node = self.nodestore.get(node.commit.parents[0])
            node.parent = next_node
            next_node.children.append(node)
            node = next_node


    def add_lca(self, lca_node, main_node):
        """
        This method will add a LCA node to the tree. It has extra logic that it
        searches for the right place for insertion based on commit orders.
        In the end, the tree structure will have the same sparse ordering as commits
        """
        def insert(node, child, parent):
            """
            Inserts a node between an already existing parent and child nodes
            """
            node.parent = parent
            node.children.append(child)
            parent.children.remove(child)
            parent.children.append(node)
            child.parent = node

        if lca_node == main_node:
            return

        node = main_node
        while node is not None:
            if node.parent == self.root_node:
                insert(lca_node, node, self.root_node)
                break
            else:
                base = self.get_merge_base(lca_node, node.parent)
                if base == node.parent:
                    insert(lca_node, node, node.parent)
                    break
                node = node.parent


    def get_merge_base(self, node1, node2):
        b = self.repo.merge_base(node1.commit, node2.commit)
        return self.nodestore.get(b[0]) if len(b) == 1 else None


class Node:
    """
    This class is a container for a repo commit.
    It is used to hold the dependency tree between sparse commits.
    If a node is a parent of another node, it does not mean that the parent node commit is a parent of the child node commit.
    There could be any number of commits between then, and the algorithm can choose not to expand these into individual commit nodes
    """
    def __init__(self, repo, commit):
        if repo is None:
            raise ValueError("Repo must not be None")
        if commit and len(commit.parents) > 1:
            raise RuntimeError("Commits with mode than one parent are not supported")
        self.repo = repo
        self.commit = commit
        self.parent = None
        self.children = []
        self.is_main = False

    def __str__(self):
        return "Node({}), children:{}".format(self.commit.summary, ", ".join([c.commit.summary for c in self.children]))

    def is_connected(self):
        return self.parent is not None

    def is_direct_child(self):
        """
        This method returns true if the parent of this node's commit matches the node's parent. Basically checks if there are
        commits between this node and its parent that have not been added to our tree.
        """
        if (self.commit is None or
            self.parent is None or
            self.parent.commit is None):
            return False
        return self.commit.parents[0] == self.parent.commit


class NodeStore:
    """
    This class acts like a store for Node objects.
    It can return an already generated Node for a commit, or create a new one if needed.
    """
    def __init__(self, repo):
        if repo is None:
            raise ValueError("Repo must not be None")
        self.repo = repo
        self.map = {}

    def add(self, commit):
        if commit is None:
            return
        node = Node(self.repo, commit)
        self.map[commit.hexsha] = node
        return node

    def get(self, commit):
        if commit is None:
            return None
        try:
            return self.map[commit.hexsha]
        except KeyError:
            return self.add(commit)



