#!/bin/bash

ip netns add vpnns 2>/dev/null

ip link add veth0 type veth peer name veth1
ip link set veth1 netns vpnns

ip addr add 10.200.200.1/24 dev veth0
ip link set veth0 up

ip netns exec vpnns ip addr add 10.200.200.2/24 dev veth1
ip netns exec vpnns ip link set veth1 up
ip netns exec vpnns ip link set lo up

# Firewall rules inside namespace
ip netns exec vpnns iptables -F

