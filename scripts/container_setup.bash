#!/bin/bash

# Git config stuff
git config --global user.email "marcin.bogdanski@gmail.com"
git config --global user.name "Marcin Bogdanski"
git config --global credential.helper store
git config --global credential.helper cache

# Git completion
curl https://raw.githubusercontent.com/git/git/master/contrib/completion/git-completion.bash > /root/git-completion.bash
echo "source /root/git-completion.bash" >> /root/.bashrc
