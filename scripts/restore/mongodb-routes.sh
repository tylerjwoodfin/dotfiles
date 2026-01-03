#!/bin/bash

# Split-tunnel routes to MongoDB Atlas outside ProtonVPN
ip route add 89.192.9.46 via 192.168.1.1 dev enp1s0 || true
ip route add 89.192.9.70 via 192.168.1.1 dev enp1s0 || true
ip route add 89.192.9.80 via 192.168.1.1 dev enp1s0 || true

