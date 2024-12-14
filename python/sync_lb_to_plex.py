#!/usr/bin/env python3

import os
import sys
import csv
import json
import timing
import requests
from plexapi.exceptions import BadRequest
from plexapi.server import PlexServer
from plexapi.myplex import MyPlexAccount
from letterboxd_stats import web_scraper as ws


# Change the current working directory to the location of this script
current_script_path = os.path.abspath(__file__)
current_script_dir = os.path.dirname(current_script_path)
os.chdir(current_script_dir)

letterboxd_to_tmdb_map = {}
plex_guid_lookup_table = {}

# Set DEBUG mode based on the environment variable
DEBUG = os.getenv('DEBUG', 'false') != 'false'

def populate_letterboxd_tmdb_mapping_file(csv_path, letterboxd_to_tmdb_mapping_csv):
    """Build the Letterboxd to TMDB mapping file if necessary."""
    load_existing_mapping(letterboxd_to_tmdb_mapping_csv)

    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)  # Skip the header

        new_mappings = ''
        for row in reader:
            lb_title = row[1]
            lb_url = row[3]

            if lb_url not in letterboxd_to_tmdb_map:
                try:
                    tmdb_id = ws.get_tmdb_id(lb_url, False)
                except Exception:
                    if DEBUG:
                        print(f"Failed to scrape TMDB ID for {lb_title}")
                    continue

                new_mappings += f"{lb_url},{tmdb_id}\n"
                if DEBUG:
                    print(f"Added mapping for {lb_title}")

        with open(letterboxd_to_tmdb_mapping_csv, 'a', encoding='utf-8') as csvfile:
            csvfile.write(new_mappings)


def load_existing_mapping(mapping_csv):
    """Load the existing Letterboxd-to-TMDB mappings from the CSV file."""
    with open(mapping_csv, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            letterboxd_to_tmdb_map[row[0]] = row[1]


def get_plex_video_by_letterboxd_url(lb_url):
    """Fetch the Plex video object corresponding to a Letterboxd URL."""
    try:
        tmdb_id = letterboxd_to_tmdb_map[lb_url]
        return plex_guid_lookup_table[f"tmdb://{tmdb_id}"]
    except KeyError as e:
        if DEBUG:
            print(f"Failed to find video for {lb_url}. Reason: {e}")
        return None


def sync_plex_ratings_from_letterboxd(ratings_csv='./ratings'):
    """Sync user ratings from Letterboxd to Plex."""
    print('Syncing Plex user ratings from Letterboxd.')

    with open(ratings_csv, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)  # Skip the header

        for row in reader:
            lb_title = row[1]
            lb_url = row[3]

            video = get_plex_video_by_letterboxd_url(lb_url)
            if not video:
                if DEBUG:
                    print(f"Rating: Failed to find: {lb_title}")
                continue

            lb_rating = float(row[4]) * 2  # Convert Letterboxd's X/5 to Plex's X/10 rating system

            if video.userRating != lb_rating:
                video.rate(lb_rating)
                print(f"Rated {video.title} at {lb_rating}/10")
            elif DEBUG:
                print(f"Skipped rating {video.title}. Already rated.")


def sync_plex_watchlist_from_letterboxd(user, watchlist_csv='./watchlist.csv'):
    """Sync user watchlist from Letterboxd to Plex."""
    print('Syncing Plex user watchlist from Letterboxd.')

    current_watchlist = user.watchlist()

    with open(watchlist_csv, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)  # Skip the header

        for row in reader:
            lb_title = row[1]
            lb_url = row[3]

            video = get_plex_video_by_letterboxd_url(lb_url)
            if not video:
                if DEBUG:
                    print(f"Watchlist: Failed to find in Plex: {lb_title}")
                continue

            if not any(v.guid == video.guid for v in current_watchlist):
                try:
                    video.addToWatchlist(user)
                    print(f"Added {video.title} to watchlist.")
                except BadRequest:
                    print(f"An error occured when adding {video.title} to watchlist.") 
            elif DEBUG:
                print(f"Already on watchlist: {video.title}")


def sync_plex_watched_status_from_letterboxd(watched_csv='./watched.csv'):
    """Sync user watched status from Letterboxd to Plex."""
    print('Syncing Plex user watched data from Letterboxd.')

    with open(watched_csv, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)  # Skip the header

        for row in reader:
            lb_title = row[1]
            lb_url = row[3]

            video = get_plex_video_by_letterboxd_url(lb_url)
            if not video:
                if DEBUG:
                    print(f"Watched: Failed to find: {lb_title}")
                continue

            if not video.isPlayed:
                video.markPlayed()
                print(f"Marked {video.title} as played.")
            elif DEBUG:
                print(f"Skipped marking {video.title} as played. Already marked.")


def add_to_radarr(tmdb_id, radarr_url, radarr_token):
    """Add a movie to Radarr using its TMDB ID."""
    headers = {
        "X-Api-Key": radarr_token,
        "Content-Type": "application/json"
    }

    # Radarr API endpoint for adding movies
    endpoint = f"{radarr_url.rstrip('/')}/api/v3/movie"

    # Movie data payload
    payload = {
        "tmdbId": tmdb_id,
        "qualityProfileId": 1,  # Adjust based on your Radarr setup
        "rootFolderPath": "/movies",  # Adjust your root folder path
        "monitored": True,
        "addOptions": {
            "searchForMovie": True
        }
    }

    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Successfully added movie with TMDB ID {tmdb_id} to Radarr.")
    except requests.exceptions.HTTPError as e:
        if response.status_code == 400:
            # Decode the response content
            try:
                error_details = json.loads(response.content.decode('utf-8'))
                for error in error_details:
                    error_code = error.get("errorCode")
                    error_message = error.get("errorMessage")

                    # Handle specific error cases
                    if error_code == "MovieExistsValidator":
                        print(f"Movie with TMDB ID {tmdb_id} is already in Radarr.")
                    elif "not found" in error_message:
                        print(f"Invalid TMDB ID {tmdb_id}: {error_message}")
                    elif error_code == "MoviePathValidator":
                        print(f"Path conflict for TMDB ID {tmdb_id}: {error_message}")
                    else:
                        print(f"Unhandled Radarr error for TMDB ID {tmdb_id}: {error_message}")
            except json.JSONDecodeError:
                print(f"Failed to parse error response for TMDB ID {tmdb_id}. Response content: {response.content}")
        else:
            # Log other HTTP errors
            print(f"Failed to add movie with TMDB ID {tmdb_id} to Radarr: {e}")
            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.content}")
            print(f"Payload: {payload}")

def sync_watchlist_to_radarr(watchlist_csv, radarr_url, radarr_token):
    """Sync the Letterboxd watchlist to Radarr."""
    print("Syncing Letterboxd watchlist to Radarr.")

    existing_tmdb_ids = get_radarr_movies(radarr_url, radarr_token)

    with open(watchlist_csv, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)  # Skip the header

        for row in reader:
            lb_title = row[1]
            lb_url = row[3]

            # Fetch TMDB ID for the movie
            tmdb_id = letterboxd_to_tmdb_map.get(lb_url)
            if not tmdb_id:
                if DEBUG:
                    print(f"Radarr Sync: Failed to find TMDB ID for {lb_title}")
                continue

            if int(tmdb_id) in existing_tmdb_ids:
                if DEBUG:
                    print(f"Skipping {lb_title}. Already in Radarr.")
                continue

            # Add to Radarr
            add_to_radarr(tmdb_id, radarr_url, radarr_token)


def get_radarr_movies(radarr_url, radarr_token):
    """Fetch the list of movies currently in Radarr."""
    headers = {"X-Api-Key": radarr_token}
    endpoint = f"{radarr_url.rstrip('/')}/api/v3/movie"
    
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        movies = response.json()
        return {movie['tmdbId'] for movie in movies}  # Return a set of TMDB IDs
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch movies from Radarr: {e}")
        return set()  # Return an empty set on failure



def main():
    """Main function to sync Letterboxd data with Plex."""
    
    letterboxd_to_tmdb_csv = os.getenv('LB_TMDB_MAP_CSV_PATH_OVERRIDE', '/app/data/lb_URL_to_tmdb_id.csv')
    download_letterboxd_data = os.getenv('DOWNLOAD_LETTERBOXD_DATA', 'true') == 'true'
    map_letterboxd_to_tmdb = os.getenv('MAP_LETTERBOXD_TO_TMDB', 'true') == 'true'
    sync_watchlist_enabled = os.getenv('SYNC_WATCHLIST', 'true') == 'true'
    sync_watched_enabled = os.getenv('SYNC_WATCHED', 'true') == 'true'
    sync_ratings_enabled = os.getenv('SYNC_RATINGS', 'true') == 'true'
    sync_watchlist_to_radarr_enabled = os.getenv('SYNC_WATCHLIST_TO_RADARR', 'false') == 'true'

    print('Starting Sync from Letterboxd to Plex')

    # Ensure the Letterboxd-to-TMDB CSV file exists
    open(letterboxd_to_tmdb_csv, 'a', encoding='utf-8').close()

    # Load Plex and MyPlex account details from environment variables
    plex_base_url = os.getenv('PLEX_BASEURL')
    plex_token = os.getenv('PLEX_TOKEN')

    if not plex_base_url or not plex_token:
        print("Plex base URL and token are required. Please set them in environment variables.")
        return

    plex = PlexServer(plex_base_url, plex_token)
    account = MyPlexAccount(token=plex_token)

    plex_user_name = os.getenv('PLEX_USER')
    if plex_user_name:
        plex_user_pin = os.getenv('PLEX_PIN')
        user = account.switchHomeUser(user=plex_user_name, pin=plex_user_pin)
        plex = plex.switchUser(plex_user_name)
    else:
        user = account  # Use admin account by default

    print(f'Using Plex user and library: {user.title}')

    movies_library = plex.library.section('Movies')

    # Build Plex GUID lookup table for fast access
    print('-Building GUID lookup table...')
    for item in movies_library.all():
        plex_guid_lookup_table[item.guid] = item
        plex_guid_lookup_table.update({guid.id: item for guid in item.guids})

    if download_letterboxd_data:
        print('Downloading Letterboxd user data...')
        downloader = ws.Downloader()
        downloader.login()
        downloader.download_stats()

    if map_letterboxd_to_tmdb:
        print('Mapping Letterboxd links to TMDB ID...')
        populate_letterboxd_tmdb_mapping_file(os.getenv('LETTERBOXD_RATINGS_CSV', '/tmp/static/ratings.csv'), letterboxd_to_tmdb_csv)
        populate_letterboxd_tmdb_mapping_file(os.getenv('LETTERBOXD_WATCHLIST_CSV', '/tmp/static/watchlist.csv'), letterboxd_to_tmdb_csv)
        populate_letterboxd_tmdb_mapping_file(os.getenv('LETTERBOXD_WATCHED_CSV', '/tmp/static/watched.csv'), letterboxd_to_tmdb_csv)

    #if reset_plex_data:
    #    reset_plex_watchlist(account)
    #    reset_plex_library(movies_library)

    load_existing_mapping(letterboxd_to_tmdb_csv)

    if sync_watchlist_enabled:
        sync_plex_watchlist_from_letterboxd(user, os.getenv('LETTERBOXD_WATCHLIST_CSV', '/tmp/static/watchlist.csv'))
    if sync_watched_enabled:
        sync_plex_watched_status_from_letterboxd(os.getenv('LETTERBOXD_WATCHED_CSV', '/tmp/static/watched.csv'))
    if sync_ratings_enabled:
        sync_plex_ratings_from_letterboxd(os.getenv('LETTERBOXD_RATINGS_CSV', '/tmp/static/ratings.csv'))
        
    if sync_watchlist_to_radarr_enabled:
        radarr_url = os.getenv('RADARR_URL')
        radarr_token = os.getenv('RADARR_TOKEN')

        if not radarr_url or not radarr_token:
            print("Radarr URL and Token are required for syncing watchlist to Radarr.")
            return

        sync_watchlist_to_radarr(os.getenv('LETTERBOXD_WATCHLIST_CSV', '/tmp/static/watchlist.csv'), radarr_url, radarr_token)


    print('Sync process complete.')



if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Process interrupted.')
        sys.exit(0)
