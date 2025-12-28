#!/bin/bash

while true; do
  if ip link show proton0 &>/dev/null; then
    /usr/local/bin/mongodb-routes.sh
  fi
  sleep 10
done

