Syncs Letterboxd data to Plex. Work in progress.


You need to modify the letterboxd_stats config to add credentials for Plex, because this code hijacks that config file. 

"
# Where you want the .csv file of your Letterboxd activity to be saved.
root_folder = "/tmp/"

# The size of the ASCII art poster printed in your terminal when you check the details of a movie. Set to 0 to disable 
poster_columns = 0

[TMDB]
api_key = "[tmdb_api_key]"

[Letterboxd]
username = "letterboxd_username"
password = "letterboxd_password"


[Plex]
plex_baseurl = 'http://0.0.0.0:32400'
token = '[PLEX_TOKEN]'
"
