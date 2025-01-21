#!/bin/bash

INTERFACE="${1}"

iptables -A FORWARD -i "${INTERFACE}" -o "${INTERFACE}" -j ACCEPT
iptables -A FORWARD -i "${INTERFACE}" -o eth0 -j ACCEPT
iptables -A FORWARD -i eth0 -o "${INTERFACE}" -j ACCEPT
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

iptables -t nat -A PREROUTING -i "${INTERFACE}" -p tcp -d 10.0.0.1 --dport 53 -j DNAT --to-destination 127.0.0.1:53
iptables -t nat -A PREROUTING -i "${INTERFACE}" -p udp -d 10.0.0.1 --dport 53 -j DNAT --to-destination 127.0.0.1:53
iptables -A INPUT -i "${INTERFACE}" -p tcp --dport 53 -j ACCEPT
iptables -A INPUT -i "${INTERFACE}" -p udp --dport 53 -j ACCEPT
