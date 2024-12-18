# 🎭 Letterboxd Plex Sync

A tool that syncs [Letterboxd](https://letterboxd.com/) user data (ratings, watch history, and watchlists) to a personal [Plex](https://www.plex.tv/) server. THIS IS A ONE WAY SYNC. This tool aims to enhance your Plex experience by keeping your viewing stats up to date with your Letterboxd profile! 🚀

## 🔧 How It Works

The script leverages:
- [Plex API wrapper](https://github.com/pkkid/python-plexapi) to interact with your Plex server.
- [letterboxd_stats](https://github.com/mBaratta96/letterboxd_stats) library to download and process Letterboxd user data.

Currently, it focuses on syncing:
- ⭐ User ratings
- 📜 Watch history
- 🗛 Watchlist (now with Radarr support)

## 🛠️ Environment Variables

The script relies on several environment variables for configuration. Here is a list of all the environment variables you need to set:

### Required Environment Variables
- **`PLEX_BASEURL`**: The base URL of your Plex server (e.g., `http://your-plex-server:32400`).
- **`PLEX_TOKEN`**: Authentication token for accessing your Plex server.
- **`LB_USERNAME`**: Your Letterboxd username.
- **`LB_PASSWORD`**: Your Letterboxd password.
- **`TMDB_API_KEY`**: Your TMDB API key, required for fetching additional metadata.

### Optional Environment Variables
- **`DEBUG`**: Set to `true` to enable debug logging. Defaults to `false`.
- **`RUN_NOW`**: Set to `true` to run the sync job immediately when the container starts. Defaults to `false`.
  
- **`PLEX_LIBRARY_NAME`**: The Plex Movies library to use. Defaults to syncing all Movie-type libraries.
- **`PLEX_USER`**: The Plex user to use for syncing, if not the default admin.
- **`PLEX_PIN`**: The PIN associated with the Plex user, if required.
- **`CRON_SCHEDULE`**: The schedule for the cron job (e.g., `0 4 */1 * *` for every day at 4:00AM). Defaults to `0 4 */1 * *`.

- **`RADARR_URL`**: The base URL of your Radarr server (e.g., `http://your-radarr-server:7878`). Required if syncing watchlist to Radarr.
- **`RADARR_TOKEN`**: The API key for your Radarr server. Required if syncing watchlist to Radarr.

- **`DOWNLOAD_LETTERBOXD_DATA`**: Set to `true` to download Letterboxd data. Defaults to `true`.
- **`MAP_LETTERBOXD_TO_TMDB`**: Set to `true` to map Letterboxd URLs to TMDB IDs. Defaults to `true`.
- **`SYNC_WATCHLIST`**: Set to `true` to sync the watchlist from Letterboxd to Plex. Defaults to `true`.
- **`SYNC_WATCHED`**: Set to `true` to sync watched status from Letterboxd to Plex. Defaults to `true`.
- **`SYNC_RATINGS`**: Set to `true` to sync user ratings from Letterboxd to Plex. Defaults to `true`.
- **`SYNC_WATCHLIST_TO_RADARR`**: Set to `true` to sync the Letterboxd watchlist to Radarr. Defaults to `false`.


### Example `letterboxd.env`
```env
# Schedule for the cron job (default: every day at 4:00AM)
#CRON_SCHEDULE="0 4 */1 * *"

# Immediately run the sync job on container startup (default: false)
#RUN_NOW="false"

# Debug mode (default: false)
#DEBUG="false"

# Plex server configuration (required)
PLEX_BASEURL="http://your-plex-server:32400"
PLEX_TOKEN="your_plex_token_here"

# Plex details (optional depending on setup)
#PLEX_LIBRARY_NAME='Movies'        # Optional: to sync only one library
#PLEX_USER="your_plex_username"    # Optional: switch to a specific Plex user
#PLEX_PIN="your_plex_pin_here"     # Optional: required if switching Plex user

# Letterboxd credentials (required for downloading data)
LB_USERNAME="your_letterboxd_username"
LB_PASSWORD="your_letterboxd_password"

# TMDB API key (required for TMDB lookups)
TMDB_API_KEY="your_tmdb_api_key_here"

# Radarr configuration (required if syncing to Radarr)
RADARR_URL="http://your-radarr-server:7878"  # required if syncing to Radarr
RADARR_TOKEN="your_radarr_api_key_here"      # required if syncing to Radarr
RADARR_TAGS="letterboxd-plex-sync, auto"     # optional: set whatever tags you like, or comment this out to skip adding tags

# Flags to control script behavior
#DOWNLOAD_LETTERBOXD_DATA="true"   # Set to "true" to download Letterboxd data (default: true)
#MAP_LETTERBOXD_TO_TMDB="true"     # Set to "true" to map Letterboxd URLs to TMDB IDs (default: true)

# Sync options (set to "true" or "false" to enable/disable)
#SYNC_WATCHLIST="true"               # default: true
#SYNC_WATCHED="true"                 # default: true
#SYNC_RATINGS="true"                 # default: true
SYNC_WATCHLIST_TO_RADARR="true"      # default: false


```

## 🛠️ Running the Script

There are multiple ways to run the `letterboxd_plex_sync` script:

### 1. Docker Compose

Here's a sample Docker Compose setup to run the `letterboxd_plex_sync` script on a schedule:

```yaml
---
name: letterboxd-plex-sync
services:
  letterboxd-plex-sync:
    container_name: letterboxd-plex-sync
    image: treysu/letterboxd-plex-sync:latest
    restart: unless-stopped
    env_file:
      - path: letterboxd.env
        required: true
    volumes:
      - /etc/localtime:/etc/localtime:ro # optional: for accurate log times
      - path/to/resources:/app/data:rw # technically optional: add folder to avoid regenerating lb to tmdb mapping CSV file
```

To use Docker Compose:

```sh
docker compose up -d
```

### 2. Docker Run

Alternatively, you can run the container directly with Docker:

```sh
docker run -d \
  --env-file letterboxd.env \
  -v path/to/resources:/app/resources:rw \
  treysu/letterboxd-plex-sync:latest
```

### 3. Running Locally

If you prefer to run the script locally without Docker:

1. **Clone the Repository**:  
   ```sh
   git clone https://github.com/treysu/letterboxd-plex-sync.git
   cd letterboxd-plex-sync/python
   ```

2. **Install Dependencies**:  
   Ensure you have Python installed, then install the required packages:
   ```sh
   pip install -r requirements.txt
   ```

3. **Run the Script**:  
   Make sure your `letterboxd.env` file is properly set up with your Plex and Letterboxd credentials, then run the script:
   ```sh
   source letterboxd.env
   python generate_config.py
   python sync_lb_to_plex.py
   ```

## 🛠️ Future Improvements

- 📊 Better handling of multiple Plex users.
- 🔄 Sync additional types of data (e.g., tags, custom lists).
- 🎭 Improved logging and error handling.

## 📣 Contributing

Feel free to open issues or make pull requests. This project is still a work in progress, and contributions are welcome!

