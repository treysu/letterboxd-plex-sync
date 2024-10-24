#!/usr/bin/env python3

import os
import sys
import csv
import timing
from plexapi.server import PlexServer
from plexapi.myplex import MyPlexAccount
from letterboxd_stats import web_scraper as ws


# Change the current working directory to the location of this script
current_script_path = os.path.abspath(__file__)
current_script_dir = os.path.dirname(current_script_path)
os.chdir(current_script_dir)

# Path to the CSV that maps Letterboxd URLs to TMDB IDs
LETTERBOXD_TO_TMDB_CSV = '/app/data/lb_URL_to_tmdb_id.csv'
letterboxd_to_tmdb_map = {}
plex_guid_lookup_table = {}

# Ensure the Letterboxd-to-TMDB CSV file exists
open(LETTERBOXD_TO_TMDB_CSV, 'a').close()

# Set DEBUG mode based on the environment variable
DEBUG = os.getenv('DEBUG', 'false') != 'false'

def populate_letterboxd_tmdb_mapping_file(csv_path):
    """Build the Letterboxd to TMDB mapping file if necessary."""
    load_existing_mapping()

    with open(csv_path, 'r') as csvfile:
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

        with open(LETTERBOXD_TO_TMDB_CSV, 'a') as csvfile:
            csvfile.write(new_mappings)


def load_existing_mapping(mapping_csv=LETTERBOXD_TO_TMDB_CSV):
    """Load the existing Letterboxd-to-TMDB mappings from the CSV file."""
    with open(mapping_csv, 'r') as csvfile:
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

    with open(ratings_csv, 'r') as csvfile:
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

    with open(watchlist_csv, 'r') as csvfile:
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
                video.addToWatchlist(user)
                print(f"Added {video.title} to watchlist.")
            elif DEBUG:
                print(f"Already on watchlist: {video.title}")


def sync_plex_watched_status_from_letterboxd(watched_csv='./watched.csv'):
    """Sync user watched status from Letterboxd to Plex."""
    print('Syncing Plex user watched data from Letterboxd.')

    with open(watched_csv, 'r') as csvfile:
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


def reset_plex_library(library, reset_rating=True, reset_played=True):
    """Reset ratings and watched status for the entire Plex library."""
    print('Resetting library...')
    for video in library.all():
        print(f'Resetting rating and watched status: {video.title}')
        if reset_rating:
            video.rate(0)
        if reset_played and video.isPlayed:
            video.markUnplayed()


def reset_plex_watchlist(user):
    """Clear the Plex watchlist."""
    for video in user.watchlist():
        video.removeFromWatchlist(user)
        print(f'Removed {video.title} from watchlist.')




def main():
    """Main function to sync Letterboxd data with Plex."""
    
    download_letterboxd_data = os.getenv('DOWNLOAD_LETTERBOXD_DATA', 'true') == 'true'
    map_letterboxd_to_tmdb = os.getenv('MAP_LETTERBOXD_TO_TMDB', 'true') == 'true'
    #reset_plex_data = os.getenv('RESET_PLEX_DATA', 'false') == 'true'

    sync_watchlist = os.getenv('SYNC_WATCHLIST', 'true') == 'true'
    sync_watched = os.getenv('SYNC_WATCHED', 'true') == 'true'
    sync_ratings = os.getenv('SYNC_RATINGS', 'true') == 'true'

    print('Starting Sync from Letterboxd to Plex')

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
        populate_letterboxd_tmdb_mapping_file(os.getenv('LETTERBOXD_RATINGS_CSV', '/tmp/static/ratings.csv'))
        populate_letterboxd_tmdb_mapping_file(os.getenv('LETTERBOXD_WATCHLIST_CSV', '/tmp/static/watchlist.csv'))
        populate_letterboxd_tmdb_mapping_file(os.getenv('LETTERBOXD_WATCHED_CSV', '/tmp/static/watched.csv'))

    #if reset_plex_data:
    #    reset_plex_watchlist(account)
    #    reset_plex_library(movies_library)

    load_existing_mapping()

    if sync_watchlist:
        sync_plex_watchlist_from_letterboxd(user, os.getenv('LETTERBOXD_WATCHLIST_CSV', '/tmp/static/watchlist.csv'))
    if sync_watched:
        sync_plex_watched_status_from_letterboxd(os.getenv('LETTERBOXD_WATCHED_CSV', '/tmp/static/watched.csv'))
    if sync_ratings:
        sync_plex_ratings_from_letterboxd(os.getenv('LETTERBOXD_RATINGS_CSV', '/tmp/static/ratings.csv'))

    print('Sync process complete.')



if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Process interrupted.')
        sys.exit(0)
