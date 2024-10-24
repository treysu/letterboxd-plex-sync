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

# Use the CRON_SCHEDULE environment variable or default to every 6 hours
CRON_SCHEDULE=${CRON_SCHEDULE:-"0 */6 * * *"}

# Replace the placeholder in the cron template with the actual cron schedule
sed "s|\${CRON_SCHEDULE}|$CRON_SCHEDULE|g" /etc/cron.d/crontab_template > /etc/cron.d/crontab

# Apply permissions and load the new crontab
chmod 0644 /etc/cron.d/crontab
crontab /etc/cron.d/crontab

# Start cron explicitly regardless of RUN_NOW
echo "Starting cron..."
cron

touch /app/combined_log.txt
tail -f /app/combined_log.txt