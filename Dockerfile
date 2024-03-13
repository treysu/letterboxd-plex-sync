FROM python:3.10
RUN apt-get update && apt-get -y install cron vim pip

WORKDIR /app
 

COPY ./python/sync_lb_to_plex.py .
COPY ./python/timing.py .
COPY ./python/requirements.txt .

RUN pip install -r requirements.txt

RUN touch output.txt
RUN touch error.txt

COPY cron/crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab

RUN /usr/bin/crontab /etc/cron.d/crontab

CMD cron && tail -f /app/output.txt /app/error.txt
