#!/bin/bash

INDEX=$(($(date +%-d) % 15))

BW="/usr/local/bin/bw"
${BW} login --apikey
BW_SESSION=$(${BW} unlock --passwordenv BW_PASSWORD --raw)

${BW} export --format json --output "bw_backup_$INDEX.json" --session $BW_SESSION

${BW} lock
${BW} logout
