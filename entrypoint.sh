#!/bin/bash

# Generate the config.toml file
python /app/generate_config.py

# Check if the RUN_NOW environment variable is set
if [ "$RUN_NOW" == "true" ]; then
  echo "RUN_NOW is set to true. Running job immediately..."
  # Run your Python script manually (the cron job) before starting cron
  python /app/sync_lb_to_plex.py
else
  echo "RUN_NOW is not set. Proceeding with regular cron schedule."
fi

# Start cron explicitly regardless of RUN_NOW
echo "Starting cron..."
cron

# Keep the container running by tailing the logs
tail -f /var/log/syslog
