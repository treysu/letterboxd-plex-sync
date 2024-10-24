#!/bin/bash

# Source environment variables
source /etc/environment

echo "$(date) Starting sync job" >> /app/combined_log.txt
cd /app && /usr/local/bin/python /app/sync_lb_to_plex.py &>> /app/combined_log.txt
