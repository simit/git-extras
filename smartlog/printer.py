#!/usr/bin/env python3
from git import Repo
from smartlog import Node
from collections import defaultdict
from colorama import Fore, Style
from datetime import datetime

class TreePrinter:
    def __init__(self, repo, root_node, main_ref, node_printer):
        if repo is None:
            raise ValueError("Repo must not be None")
        if root_node is None:
            raise ValueError("Root node must not be None")
        if node_printer is None:
            raise ValueError("Node printer must not be None")

        self.repo = repo
        self.root_node = root_node
        self.node_printer = node_printer

    def print_tree(self):
        self.print_node(self.root_node, prefix="")

    def print_node(self, node, prefix):
        main_graph_connector = ""
        for i, child in enumerate(self.sorted_children(node)):
            self.print_node(child, prefix + main_graph_connector + (" " if i > 0 else ""))

            child_is_head = (self.repo.head.commit == child.commit) if child.commit is not None else False

            # Print the child node
            summary = self.node_printer.node_summary(child)

            # Add padding lines to reach at least the minimum desired number of line
            min_summary_len = 2
            if len(summary) < min_summary_len:
                summary += [""] * (min_summary_len - len(summary))

            # 1st line
            bullet = "*" if child_is_head else "o"
            if i == 0:
                graph = main_graph_connector + bullet
            else:
                graph = main_graph_connector + " " + bullet
            print(prefix + graph + "  " + summary[0])

            # Update the connector character
            graph_connector = "|" if child.is_direct_child() else ":"
            if i == 0:
                main_graph_connector = graph_connector

            # 2nd line
            if i == 0:
                graph = main_graph_connector
            else:
                graph = main_graph_connector + "/ "
            print(prefix + graph + "  " + summary[1])

            if i > 0:
                main_graph_connector = graph_connector

            # Remaining lines
            if i == 0:
                graph = main_graph_connector
            else:
                graph = graph_connector + "  "
            for line in summary[2:]:
                print(prefix + graph + "  " + line)


            # Spacing to parent node
            if i < len(node.children) - 1:
                graph = main_graph_connector
            else:
                graph = graph_connector
            print(prefix + graph)


    def sorted_children(self, node):
        """
        This method will sort a node's children in an order suited for display.
        Any child that is marked as main will be placed first so that it gets displayed first
        """
        def compare(x):
            if x.is_main:
                return 0
            return x.commit.committed_date
        return sorted(node.children, key=compare)




class RefList:
    """
    This class can quickly map from a commit sha to a list of branch names (heads).
    By default, it will compute the map for
    - HEAD
    - all local branches
    """
    def __init__(self, repo, extra_refs=[]):
        self.repo = repo
        self.heads = defaultdict(list)

        if self.repo.head.is_detached:
            self.heads[self.repo.head.commit.hexsha].append("HEAD")
        for ref in self.repo.heads:
            self.add(ref)

        for ref in extra_refs:
            self.add(ref)

    def add(self, ref):
        if not ref:
            return

        if not self.repo.head.is_detached and self.repo.head.ref == ref:
            name = "HEAD -> " + ref.name
        else:
            name = ref.name
        self.heads[ref.commit.hexsha].append(name)

    def get(self, commit):
        return self.heads[commit.hexsha]


class NodePrinter:
    def __init__(self, repo, reflist):
        self.repo = repo
        self.reflist = reflist


    def node_summary(self, node):
        """
        This method returns a summary description for a given node
        The structure for this is:
        - line 1: sha author [branches] relative_time
        - line 2: commit summary (first line of message)
        """
        if node.commit is None:
            return []

        lines = []

        # Format the first line and start with the short sha
        line = ""
        sha = node.repo.git.rev_parse(node.commit.hexsha, short=True)
        is_head = (self.repo.head.commit == node.commit) if node.commit is not None else False
        line += (Fore.MAGENTA if is_head else Fore.YELLOW) + sha + "  " + Fore.RESET

        # Add the author
        author = node.commit.author.email.rsplit("@")[0]
        line += author + "  "

        # Add any diffs
        diff = self.differential_revision(node.commit)
        if diff is not None:
            line += Fore.BLUE + diff + "  " + Fore.RESET

        # Add the local branches
        if self.reflist is not None:
            refs = self.reflist.get(node.commit)
            if len(refs) > 0:
                line += Fore.GREEN + "(" + ", ".join(refs) + ")  " + Fore.RESET

        # Add the commit date as a relative string
        line += self.format_commit_date(node.commit.committed_date) + "  "

        lines.append(line)

        # Format the second line
        lines.append(node.commit.summary)

        return lines


    def differential_revision(self, commit):
        if commit is None:
            return None

        diff_line_prefix = "Differential Revision:"
        lines = commit.message.splitlines()
        for l in lines:
            if l.startswith(diff_line_prefix):
                l = l[len(diff_line_prefix):]
                return l.strip().rsplit('/', 1)[-1]
        return None


    def format_commit_date(self, timestamp):
        if timestamp is None:
            return "Now"

        then = datetime.utcfromtimestamp(timestamp)
        diff = datetime.utcnow() - then

        second_diff = diff.seconds
        day_diff = diff.days

        if day_diff < 0:
            return "<Invalid time>"

        if day_diff == 0:
            if second_diff < 10:
                return "just now"
            if second_diff < 60:
                return str(second_diff) + " seconds ago"
            if second_diff < 120:
                return "a minute ago"
            if second_diff < 3600:
                return str(second_diff / 60) + " minutes ago"
            if second_diff < 7200:
                return "an hour ago"
            if second_diff < 86400:
                return str(second_diff / 3600) + " hours ago"
        if day_diff == 1:
            return "Yesterday"
        if day_diff < 7:
            return str(day_diff) + " days ago"
        if day_diff < 31:
            return str(day_diff / 7) + " weeks ago"

        return then.strftime("%Y-%m-%d")

