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
COPY ./python/requirements.txt .
COPY ./scripts/sync_job_wrapper.sh .

RUN chmod +x sync_job_wrapper.sh

# Replace letterboxd_stats==0.2.14 with GitHub fork in requirements.txt
RUN sed -i 's|letterboxd_stats==0.2.14|git+https://github.com/treysu/letterboxd_stats.git@main#egg=letterboxd_stats|' requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy cron placeholder
COPY cron/crontab_template /etc/cron.d/crontab_template
RUN chmod 0644 /etc/cron.d/crontab_template

# Add an entrypoint script to check RUN_NOW and run the job if needed
COPY ./scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh



# Use the entrypoint script to handle RUN_NOW logic
ENTRYPOINT ["/entrypoint.sh"]