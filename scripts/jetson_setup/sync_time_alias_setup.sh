#!/usr/bin/env bash

ALIAS_LINE='alias sync-time='\''sudo date -s "$(wget --method=HEAD -qSO- --max-redirect=0 google.com 2>&1 | sed -n "s/^ *Date: *//p")" && sudo hwclock -w'\'''

if ! grep -qxF "$ALIAS_LINE" ~/.bashrc; then
  echo "$ALIAS_LINE" >> ~/.bashrc
fi
