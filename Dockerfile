# Use a slim Python base image to reduce size
FROM python:3.10-slim

# Install dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron vim && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY ./python/generate_config.py .  
COPY ./python/sync_lb_to_plex.py .
COPY ./python/timing.py .
COPY ./python/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Add crontab file and set permissions
COPY cron/crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab && crontab /etc/cron.d/crontab

# Configure cron to log to /var/log/cron.log
#RUN touch /var/log/cron.log && \
#    echo "cron.* /var/log/cron.log" >> /etc/rsyslog.d/cron.conf && \
#    service rsyslog start

# Add an entrypoint script to check RUN_NOW and run the job if needed
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh


# Use the entrypoint script to handle RUN_NOW logic
ENTRYPOINT ["/entrypoint.sh"]