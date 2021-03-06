# Welcome

Welcome to git-extras, a collection of tools to help you work with git.

# Pre-requiste

This only works with python2.7 and pip.
brew install python
sudo easy_install pip

# Installation

As you're reading this, you've probably already cloned the repo on your machine.

Add this folder to the PATH environment variable. 
For bash, add to .bashrc (for zsh, add to .zshrc)
```
export PATH=$HOME/<path to this repo on your machine>:$PATH
```

## Install python dependencies
```
pip install -r requirements.txt
```

## Add git alias commands
```
git config --global alias.amend "\!git amend.py"
git config --global alias.restack "\!git restack.py"
git config --global alias.sl "\!git smartlog.py"
git config --global alias.view "\!git view.py"
```

OR

```
git config --global alias.amend "\!python git-amend.py"
git config --global alias.restack "\!python git-restack.py"
git config --global alias.sl "\!python git-smartlog.py"
git config --global alias.view "\!python git-view.py"
```
