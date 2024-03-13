#!/usr/bin/env python3

import os
import sys
import csv
from plexapi.server import PlexServer
from plexapi.myplex import MyPlexAccount

from letterboxd_stats import web_scraper as ws
from letterboxd_stats import config as lbs_config

import timing

# Set pwd the the directory of this script
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

LB_TO_TMDB_CSV = 'resources/lb_URL_to_tmdb_id.csv'
lb_to_tmdb_dict = {}

guid_lookup_table = {}

# make sure  file exists
f = open(LB_TO_TMDB_CSV, 'a')
f.close()


if os.getenv('DEBUG') is None or os.getenv('DEBUG') == 'False':
    DEBUG = False
else:
    DEBUG = True


def build_lb_tmdb_mapping_file(csv_input):

    build_mapping_dict()

    csvf = open(csv_input, 'r')
    reader = csv.reader(csvf, delimiter=',')
    next(reader)  # skip header

    temp_str = ''

    for row in reader:

        lb_title = row[1]
        lb_link = row[3]

        if not lb_link in lb_to_tmdb_dict:  # check for id in previous mappings list
            try:
                tmdb_id = ws.get_tmdb_id(lb_link, False)  # use web scraper to get ID
            except:
                if DEBUG:
                    print('Failed to scrape TMDB ID for ' + lb_title)
                continue

            try:
                temp_str = (
                    temp_str + lb_link + ',' + str(tmdb_id) + '\n'
                )  # add to list for next time
                if DEBUG:
                    print('Added mapping for ' + lb_title)
            except Exception as e:
                if DEBUG:
                    print('No TMDB ID found for ' + lb_title)
                if DEBUG:
                    print('******' + e.with_traceback)

    f = open(LB_TO_TMDB_CSV, 'a')
    f.write(temp_str)  # add to list for next time
    f.close()


def build_mapping_dict(mapping_csv=LB_TO_TMDB_CSV):

    for row in csv.reader(open(mapping_csv)):
        lb_to_tmdb_dict[row[0]] = row[1]


def get_plex_video_with_lb_url(lb_url):

    try:
        tmdb_id = lb_to_tmdb_dict[lb_url]
        video = guid_lookup_table['tmdb://' + str(tmdb_id)]
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
    except Exception as e:
        if DEBUG:
            print('Failed to find %s. Reason: %s' % (lb_url, e))
        return None

    return video


def update_plex_ratings(ratings_csv='./ratings'):
    print('Syncing Plex user ratings from Letterboxd.')

    csvf = open(ratings_csv, 'r')
    reader = csv.reader(csvf, delimiter=',')
    next(reader)  # skip header

    for row in reader:

        lb_title = row[1]
        lb_link = row[3]

        video = get_plex_video_with_lb_url(lb_link)
        if not video:
            if DEBUG:
                print('Rating: Failed to find: ' + lb_title)
            continue  # skip

        lb_rating = float(row[4]) * 2  # convert from X/5 to X/10 rating system

        if video.userRating != lb_rating:
            video.rate(lb_rating)
            if True:
                print('Rated ' + video.title + ' at ' + str(lb_rating) + '/10')
        else:
            if DEBUG:
                print('Skipped rating ' + video.title + '. Already rated.')


def update_plex_watchlist(user=None, watchlist_csv='./watchlist.csv'):
    print('Syncing Plex user watchlist from Letterboxd.')

    watchlist = user.watchlist()

    csvf = open(watchlist_csv, 'r')
    reader = csv.reader(csvf, delimiter=',')
    next(reader)  # skip header

    for row in reader:

        lb_title = row[1]
        lb_link = row[3]

        video = get_plex_video_with_lb_url(lb_link)
        if not video:
            if DEBUG:
                print('Watchlist: Failed to find in Plex: ' + lb_title)
            continue  # skip

        if not any(v.guid == video.guid for v in watchlist):
            video.addToWatchlist(user)
            if True:
                print('Added ' + video.title + ' to watchlist.')
        else:
            if DEBUG:
                print('Already on watchlist:' + video.title)


def update_plex_watched(watched_csv='./watched.csv'):
    print('Syncing Plex user watched data from Letterboxd.')

    csvf = open(watched_csv, 'r')
    reader = csv.reader(csvf, delimiter=',')
    next(reader)  # skip header

    for row in reader:

        lb_title = row[1]
        lb_link = row[3]

        video = get_plex_video_with_lb_url(lb_link)
        if not video:
            if DEBUG:
                print('Watched: Failed to find: ' + lb_title)
            continue  # skip

        if not video.isPlayed:
            video.markPlayed()
            if True:
                print('Marked ' + video.title + ' as played.')
        else:
            if DEBUG:
                print('Skipped marking ' + video.title + ' as played. Already marked.')
            continue


def reset_library(library, reset_rating=True, reset_played=True):
    print('Resetting library...')
    for video in library.all():
        print('Resetting ratign and watched status: ' + video.title)
        if reset_rating:
            video.rate(0)
        if reset_played:
            if video.isPlayed:
                video.markUnplayed()


def reset_watchlist(user):
    for video in user.watchlist():
        try:
            video.removeFromWatchlist(user)
            print(f'Removed {video.title} from watchlist.')
        except:
            pass


def main():
    # lb program functions
    download = True
    map = True

    # plex program functions
    reset = False

    sync_watchlist = True
    sync_watched = True
    sync_ratings = True

    sync_all = True

    # TESTING FLAGS - COMMENT ALL OUT
    #########################################

    # download = False
    # map = False
    # reset = True
    # sync_watchlist=False
    # sync_watched=False
    # sync_ratings=False
    # sync_all = False

    ##################################################

    if sync_all:
        sync_watchlist = True
        sync_watched = True
        sync_ratings = True

    if download:
        map = True  # no reason to not map if I'm downloading

    print('Starting Sync from Letterboxd to Plex ')

    # hijack stuff from lb-stats config
    lb_folder = lbs_config['root_folder'] + '/static'
    baseurl = lbs_config['Plex']['baseurl']
    token = lbs_config['Plex']['token']

    plex = PlexServer(baseurl, token)
    account = MyPlexAccount(token=token)

    # get optional environment variable
    plex_user_name = os.getenv('PLEX_USER')

    if plex_user_name is not None:

        plex_user_pin = os.getenv(
            'PLEX_PIN'
        )  # default None value is OK if no pin is set
        user = account.switchHomeUser(user=plex_user_name, pin=plex_user_pin)
        user_server = plex.switchUser(plex_user_name)
    else:

        user = account  # use admin (default) account
        user_server = plex

    print('Using Plex user and library: ' + str(user.title))

    movies_library = user_server.library.section('Movies')

    print('-Building GUID lookup table...')
    for item in movies_library.all():
        guid_lookup_table[item.guid] = item
        guid_lookup_table.update({guid.id: item for guid in item.guids})

    if download:
        print('Downloading Letterboxd user data...')

        downloader = ws.Downloader()
        downloader.login()
        downloader.download_stats()

        print('---')

    if map:
        print('Mapping Letterboxd links to TMDB ID...')

        build_lb_tmdb_mapping_file(lb_folder + '/ratings.csv')
        build_lb_tmdb_mapping_file(lb_folder + '/watchlist.csv')
        build_lb_tmdb_mapping_file(lb_folder + '/watched.csv')

    if reset:
        reset_watchlist(account)
        reset_library(movies_library)

    build_mapping_dict()

    if sync_watchlist:
        update_plex_watchlist(user, lb_folder + '/watchlist.csv')
    if sync_watched:
        update_plex_watched(lb_folder + '/watched.csv')
    if sync_ratings:
        update_plex_ratings(lb_folder + '/ratings.csv')

    print('Process complete.')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
