#!/usr/bin/env python3

import os
import toml

# Define the path for the config.toml file
config_path = os.path.expanduser('~/.config/letterboxd_stats/config.toml')

# Environment variables for Plex and Letterboxd configurations
lb_username = os.getenv('LB_USERNAME', '')
lb_password = os.getenv('LB_PASSWORD', '')
tmdb_api_key = os.getenv('TMDB_API_KEY', '')

# Create the config dictionary
config = {
    'root_folder': '/tmp/',
    'poster_columns': 0,
    'TMDB': {
        'api_key': tmdb_api_key
    },
    'Letterboxd': {
        'username': lb_username,
        'password': lb_password
    }
}

# Write the config to the config.toml file
os.makedirs(os.path.dirname(config_path), exist_ok=True)  # Create directory if it doesn't exist
with open(config_path, 'w') as config_file:
    toml.dump(config, config_file)

print(f"Config file generated at: {config_path}")
