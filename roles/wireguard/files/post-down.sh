#!/bin/bash

INTERFACE="${1}"

iptables -D FORWARD -i "${INTERFACE}" -o "${INTERFACE}" -j ACCEPT
iptables -D FORWARD -i "${INTERFACE}" -o eth0 -j ACCEPT
iptables -D FORWARD -i eth0 -o "${INTERFACE}" -j ACCEPT
iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

iptables -t nat -D PREROUTING -i "${INTERFACE}" -p tcp -d 10.0.0.1 --dport 53 -j DNAT --to-destination 127.0.0.1:53
iptables -t nat -D PREROUTING -i "${INTERFACE}" -p udp -d 10.0.0.1 --dport 53 -j DNAT --to-destination 127.0.0.1:53
iptables -D INPUT -i "${INTERFACE}" -p tcp --dport 53 -j ACCEPT
iptables -D INPUT -i "${INTERFACE}" -p udp --dport 53 -j ACCEPT
