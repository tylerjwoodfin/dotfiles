#!/bin/bash
set -e

# Clean up old interface if needed
ip netns exec vpnns ip link delete proton 2>/dev/null || true
ip link delete proton 2>/dev/null || true

# Create interface
ip link add proton type wireguard
wg setconf proton /etc/wireguard/proton.wg
ip link set proton netns vpnns

# Set up inside namespace
ip netns exec vpnns ip addr add 10.2.0.2/32 dev proton
ip netns exec vpnns ip link set proton up

# Add default route only if it doesn't exist
ip netns exec vpnns ip route | grep -q '^default' || \
    ip netns exec vpnns ip route add default dev proton


# DNS
echo "nameserver 10.2.0.1" > /etc/netns/vpnns/resolv.conf

