# Use a slim Python base image to reduce size
FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron vim && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files 
COPY ./python/sync_lb_to_plex.py .
COPY ./python/timing.py .
COPY ./python/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary files
RUN touch output.txt error.txt

# Add crontab file and set permissions
COPY cron/crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab && crontab /etc/cron.d/crontab

# Set the entrypoint to run cron and keep the container alive
CMD ["cron", "-f"]
