#!/usr/bin/env python3

import csv
import json
import logging
import os
import sys

import requests
from letterboxd_stats import web_scraper as ws
from plexapi.exceptions import BadRequest, NotFound
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer
from plexapi.utils import searchType

# Change the current working directory to the location of this script
current_script_path = os.path.abspath(__file__)
current_script_dir = os.path.dirname(current_script_path)
os.chdir(current_script_dir)

DEBUG = os.getenv('DEBUG', 'false') != 'false'

log_level = logging.INFO
if DEBUG:
    log_level = logging.DEBUG


# Configure logging
logging.basicConfig(
    level=log_level,
    format='%(asctime)s.%(msecs)03d %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("sync.log"),  # Log to a file
        logging.StreamHandler()          # Log to the console
    ]
)

letterboxd_to_tmdb_map = {}
plex_guid_lookup_table = {}

# Set DEBUG mode based on the environment variable

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
                    logging.debug(f"Failed to scrape TMDB ID for {lb_title}")
                    continue

                if tmdb_id is None:
                    logging.debug(f"Failed to find valid TMDB Movie ID for {lb_title}")
                    continue

                new_mappings += f"{lb_url},{tmdb_id}\n"
                logging.debug(f"Added mapping for {lb_title}")

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
        logging.debug(f"Failed to find video for {lb_url}. Reason: {e}")
        return None

def get_plex_video_by_tmdb_id(tmdb_id, libtype='movie'):

    plex = PlexServer('https://metadata.provider.plex.tv', token=os.getenv('PLEX_TOKEN'))

    guid = 'tmdb://' + tmdb_id
    logging.debug(f"Querying Plex for GUID {guid}")

    try:
        video = plex.fetchItem(f'/library/metadata/matches?type={searchType(libtype)}&guid={guid}')
    except NotFound as e:
        logging.warning(f"Plex could not find a match for TMDb GUID {guid}: {e}")
        video = None
    except Exception as e:
        logging.error(f"Unexpected error during Plex fetchItem for GUID {guid}: {e}", exc_info=True)
        video = None
    return video

def sync_plex_ratings_from_letterboxd(ratings_csv='./ratings'):
    """Sync user ratings from Letterboxd to Plex."""

    with open(ratings_csv, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)  # Skip the header

        for row in reader:
            lb_title = row[1]
            lb_url = row[3]

            video = get_plex_video_by_letterboxd_url(lb_url)
            if not video:
                logging.debug(f"Rating: Failed to find: {lb_title}")
                continue

            lb_rating = float(row[4]) * 2  # Convert Letterboxd's X/5 to Plex's X/10 rating system

            if video.userRating != lb_rating:
                video.rate(lb_rating)
                logging.debug(f"Rated {video.title} at {lb_rating}/10")
            else:
                logging.debug(f"Skipped rating {video.title}. Already rated at {video.userRating}/10")


def sync_plex_watchlist_from_letterboxd(user, watchlist_csv='./watchlist.csv'):
    """Sync user watchlist from Letterboxd to Plex."""
    current_watchlist = user.watchlist()

    with open(watchlist_csv, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)  # Skip the header

        for row in reader:
            lb_title = row[1]
            lb_url = row[3]

            video = get_plex_video_by_letterboxd_url(lb_url)
            if not video:
                tmdb_id = letterboxd_to_tmdb_map.get(lb_url)
                if not tmdb_id:
                    logging.warning(f"Skipping: No TMDB ID found for {lb_url}")
                    continue  # or return
                video = get_plex_video_by_tmdb_id(tmdb_id)

            if not video:
                logging.debug(f"Watchlist: Failed to find in Plex: {lb_title}")
                continue

            if not any(v.guid == video.guid for v in current_watchlist):
                try:
                    video.addToWatchlist(user)
                    logging.info(f"Added to watchlist: {video.title}")
                except BadRequest:
                    logging.error(f"An error occured when adding \"{video.title}\" to watchlist.")
            else:
                logging.debug(f"Already on watchlist: {video.title}")


def sync_plex_watched_status_from_letterboxd(watched_csv='./watched.csv'):
    """Sync user watched status from Letterboxd to Plex."""
    with open(watched_csv, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)  # Skip the header

        for row in reader:
            lb_title = row[1]
            lb_url = row[3]

            video = get_plex_video_by_letterboxd_url(lb_url)
            if not video:
                logging.debug(f"Watched: Failed to find: {lb_title}")
                continue

            if not video.isPlayed:
                video.markPlayed()
                logging.info(f"Marked {video.title} as played.")
            else:
                logging.debug(f"Skipped marking {video.title} as played. Already marked.")


def get_or_create_tag(radarr_url, radarr_token, tag_name):
    """Fetch the ID of an existing tag or create a new one."""
    headers = {
        "X-Api-Key": radarr_token,
        "Content-Type": "application/json"
    }
    tags_endpoint = f"{radarr_url.rstrip('/')}/api/v3/tag"

    # Get existing tags
    response = requests.get(tags_endpoint, headers=headers)
    response.raise_for_status()
    existing_tags = response.json()

    # Check if the tag already exists
    for tag in existing_tags:
        if tag["label"].lower() == tag_name.lower():
            return tag["id"]

    # If tag doesn't exist, create it
    new_tag_payload = {"label": tag_name}
    create_response = requests.post(tags_endpoint, json=new_tag_payload, headers=headers)
    create_response.raise_for_status()
    new_tag = create_response.json()
    return new_tag["id"]

def add_to_radarr(tmdb_id, radarr_url, radarr_token, tag_names=None):
    """Add a movie to Radarr using its TMDB ID and optionally assign tags by name."""
    headers = {
        "X-Api-Key": radarr_token,
        "Content-Type": "application/json"
    }

    # Fetch the root folder path from the environment variable, default to "/movies"

    quality_profile_name = os.getenv('RADARR_QUALITY_PROFILE')
    quality_profile = get_quality_profile_id(radarr_url, radarr_token, quality_profile_name) if quality_profile_name else None
    quality_profile = quality_profile or 1

    # Fetch the root folder path from the environment variable, default to "/movies"
    root_folder_path = os.getenv('RADARR_ROOT_FOLDER', '/movies')

    radarr_monitored = os.getenv('RADARR_MONITORED', 'true') == 'true'
    radarr_search = os.getenv('RADARR_SEARCH', 'true') == 'true'

    # Radarr API endpoint for adding movies
    endpoint = f"{radarr_url.rstrip('/')}/api/v3/movie"

    # Movie data payload
    payload = {
        "tmdbId": tmdb_id,
        "qualityProfileId": int(quality_profile),  # Adjust based on your Radarr setup
        "rootFolderPath": root_folder_path,  # Adjust your root folder path
        "monitored": radarr_monitored,
        "addOptions": {
            "searchForMovie": radarr_search
        },
    }

    # Convert tag names to tag IDs
    tag_ids = []
    if tag_names:
        for tag_name in tag_names:
            tag_id = get_or_create_tag(radarr_url, radarr_token, tag_name)
            tag_ids.append(tag_id)
        payload["tags"] = tag_ids

    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        logging.info(f"Successfully added movie with TMDB ID {tmdb_id} to Radarr.")
    except requests.exceptions.HTTPError as e:
        if response.status_code == 400:
            try:
                error_details = json.loads(response.content.decode('utf-8'))
                for error in error_details:
                    error_code = error.get("errorCode")
                    error_message = error.get("errorMessage")

                    if error_code == "MovieExistsValidator":
                        logging.warning(f"Movie with TMDB ID {tmdb_id} is already in Radarr.")
                    elif "A movie with this ID was not found" in error_message:
                        logging.warning(f"A movie with TMDB ID {tmdb_id} was not found in Radarr search.")
                    elif error_code == "MoviePathValidator":
                        logging.warning(f"Path conflict for TMDB ID {tmdb_id}: {error_message}")
                    else:
                        logging.error(f"Unhandled Radarr error for TMDB ID {tmdb_id}: {error_message}")
            except json.JSONDecodeError:
                logging.error(f"Failed to parse error response for TMDB ID {tmdb_id}. Response content: {response.content}")
        else:
            logging.warning(f"Failed to add movie with TMDB ID {tmdb_id} to Radarr: {e}")
            logging.warning(f"Response status code: {response.status_code}")
            logging.warning(f"Response content: {response.content}")
            logging.warning(f"Payload: {payload}")

def sync_watchlist_to_radarr(watchlist_csv, radarr_url, radarr_token):
    """Sync the Letterboxd watchlist to Radarr."""

    # Fetch and parse tags from the environment variable
    radarr_tags_env = os.getenv('RADARR_TAGS', '')
    radarr_tags = [tag.strip() for tag in radarr_tags_env.split(',')] if radarr_tags_env else []

    logging.info(f"tags: {radarr_tags}")
    existing_tmdb_ids = get_radarr_movies(radarr_url, radarr_token)

    with open(watchlist_csv, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)  # Skip the header

        for row in reader:
            lb_title = row[1]
            lb_url = row[3]

            # Fetch TMDB ID for the movie
            tmdb_id = letterboxd_to_tmdb_map.get(lb_url)
            if tmdb_id is None:
                logging.debug(f"Radarr Sync: Failed to find TMDB ID for {lb_title}")
                continue

            if int(tmdb_id) in existing_tmdb_ids:
                logging.debug(f"Skipping {lb_title}. Already in Radarr.")
                continue

            # Add to Radarr with tags
            add_to_radarr(tmdb_id, radarr_url, radarr_token, tag_names=radarr_tags)

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
        logging.error(f"Failed to fetch movies from Radarr: {e}")
        return set()  # Return an empty set on failure

def get_quality_profile_id(radarr_url, radarr_token, profile_name):
    """
    Retrieve the ID of a quality profile in Radarr by its name.

    Args:
        radarr_url (str): The base URL for the Radarr instance.
        radarr_token (str): The API key for the Radarr instance.
        profile_name (str): The name of the quality profile to search for.

    Returns:
        int or None: The ID of the quality profile, or None if not found.
    """
    headers = {"X-Api-Key": radarr_token}
    endpoint = f"{radarr_url.rstrip('/')}/api/v3/qualityprofile"

    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        quality_profiles = response.json()

        for profile in quality_profiles:
            if profile['name'].lower() == profile_name.lower():
                return profile['id']

        # Return None if no match is found
        return None

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch quality profiles from Radarr: {e}")
        return None


def main():
    """Main function to sync Letterboxd data with Plex."""

    disclaimer = """
    ****************************************************
    WARNING: This program comes with NO WARRANTY.
    Use it at your own risk. The authors are not responsible
    for any damage or data loss that may occur as a result
    of using this software.
    ****************************************************
    """
    logging.warning(disclaimer)

    logging.info("========================================")
    logging.info("Starting Letterboxd-Plex Sync Program")
    logging.info("========================================")

    letterboxd_to_tmdb_csv = os.getenv('LB_TMDB_MAP_CSV_PATH_OVERRIDE', '/app/data/lb_URL_to_tmdb_id.csv')
    map_letterboxd_to_tmdb = os.getenv('MAP_LETTERBOXD_TO_TMDB', 'true') == 'true'
    sync_watchlist_to_plex_enabled = os.getenv('SYNC_WATCHLIST', 'true') == 'true'
    sync_watched_enabled = os.getenv('SYNC_WATCHED', 'true') == 'true'
    sync_ratings_enabled = os.getenv('SYNC_RATINGS', 'true') == 'true'
    sync_watchlist_to_radarr_enabled = os.getenv('SYNC_WATCHLIST_TO_RADARR', 'false') == 'true'
    plex_library_name = os.getenv('PLEX_LIBRARY_NAME')

    # Ensure the Letterboxd-to-TMDB CSV file exists
    open(letterboxd_to_tmdb_csv, 'a', encoding='utf-8').close()

    # Load Plex and MyPlex account details from environment variables
    plex_base_url = os.getenv('PLEX_BASEURL')
    plex_token = os.getenv('PLEX_TOKEN')

    if not plex_base_url or not plex_token:
        logging.error("PLEX_BASEURL and PLEX_TOKEN are required. Please set them in environment variables.")
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

    logging.info('Downloading Letterboxd user data...')
    downloader = ws.Connector()
    downloader.login()
    downloader.download_stats()


    if plex_library_name:
        movie_libraries = [plex.library.section(plex_library_name)]
        if not movie_libraries:
            raise Exception(f"No Movie library named ""{plex_library_name}"" found on the Plex server!")

    else:
        all_libraries = plex.library.sections()
        movie_libraries = [lib for lib in all_libraries if lib.type == 'movie']

        # Ensure at least one movie library is found
        if not movie_libraries:
            raise Exception("No Movie libraries found on the Plex server!")


    # Optionally, use the first Movie library found (or handle multiple as needed)
    for movies_library in movie_libraries:
        # Build Plex GUID lookup table for fast access
        logging.info(f'Adding all movies from \"{movies_library.title}\" to GUID lookup table...')
        for item in movies_library.all():
            plex_guid_lookup_table[item.guid] = item
            plex_guid_lookup_table.update({guid.id: item for guid in item.guids})


    logging.info('Mapping Letterboxd links to TMDB ID... (this could take a while)')
    populate_letterboxd_tmdb_mapping_file(os.getenv('LETTERBOXD_RATINGS_CSV', '/tmp/static/ratings.csv'), letterboxd_to_tmdb_csv)
    populate_letterboxd_tmdb_mapping_file(os.getenv('LETTERBOXD_WATCHLIST_CSV', '/tmp/static/watchlist.csv'), letterboxd_to_tmdb_csv)
    populate_letterboxd_tmdb_mapping_file(os.getenv('LETTERBOXD_WATCHED_CSV', '/tmp/static/watched.csv'), letterboxd_to_tmdb_csv)
    load_existing_mapping(letterboxd_to_tmdb_csv)


    if sync_watchlist_to_plex_enabled or sync_watched_enabled or sync_ratings_enabled:
        logging.info(f'Using Plex user \"{user.title}\"')

    if sync_watched_enabled:
        logging.info("Syncing Letterboxd watched status to Plex...")
        sync_plex_watched_status_from_letterboxd(os.getenv('LETTERBOXD_WATCHED_CSV', '/tmp/static/watched.csv'))
    if sync_ratings_enabled:
        logging.info("Syncing Letterboxd ratings to Plex...")
        sync_plex_ratings_from_letterboxd(os.getenv('LETTERBOXD_RATINGS_CSV', '/tmp/static/ratings.csv'))

    if sync_watchlist_to_plex_enabled:
        logging.info("Syncing Letterboxd watchlist to Plex...")
        sync_plex_watchlist_from_letterboxd(user, os.getenv('LETTERBOXD_WATCHLIST_CSV', '/tmp/static/watchlist.csv'))

    if sync_watchlist_to_radarr_enabled:
        radarr_url = os.getenv('RADARR_URL')
        radarr_token = os.getenv('RADARR_TOKEN')

        if not radarr_url or not radarr_token:
            logging.error("Radarr URL and Token are required for syncing watchlist to Radarr.")
            return

        logging.info("Syncing Letterboxd watchlist to Radarr.")
        sync_watchlist_to_radarr(os.getenv('LETTERBOXD_WATCHLIST_CSV', '/tmp/static/watchlist.csv'), radarr_url, radarr_token)

    logging.info('Sync process complete.')



if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.error('Process interrupted.')
        sys.exit(0)
