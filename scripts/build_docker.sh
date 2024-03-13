#!/bin/bash

docker build . \
    -t 'letterboxd_plex_sync:dev' "$@"
