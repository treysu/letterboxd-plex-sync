# 🎭 Letterboxd Plex Sync

A tool that syncs [Letterboxd](https://letterboxd.com/) user data (ratings, watch history, and watchlists) to a personal [Plex](https://www.plex.tv/) server. THIS IS A ONE WAY SYNC. This tool aims to enhance your Plex experience by keeping your viewing stats up to date with your Letterboxd profile! 🚀

## ⚠️ Disclaimer

This project is provided “as-is” without any guarantees or warranties of any kind. By using this tool, you accept full responsibility for any risks, including but not limited to data loss, misconfigurations, or disruptions to your Plex or Radarr server.
- Rate Limits: Frequent use of this tool may trigger API rate limits for Plex, TMDB, or Radarr. Ensure you comply with their respective terms of service.
- Letterboxd Scraping: This tool relies on simulating Letterboxd browser actions. Use this tool responsibly and at your own risk, as it is unknown if this could result in account restrictions. 
- Sensitive Data: Handle your .env file carefully, as it contains sensitive credentials (e.g., Plex token, Letterboxd credentials, API keys). Do not share this file or include it in public repositories.
- Testing Recommended: Test this tool on a non-production server or with a limited dataset before deploying it to your main Plex or Radarr setup.
- Use at Your Own Risk: The authors are not responsible for **any** consequences resulting from the use of this tool.


## ⚙️ How It Works

This project simplifies syncing Letterboxd data to Plex by offering a simple Python script, as well as a Docker container wrapping that script with a cron process for easy deployment and automation. 

The script leverages:
- [Plex API wrapper](https://github.com/pkkid/python-plexapi) to interact with your Plex server.
- [letterboxd_stats](https://github.com/mBaratta96/letterboxd_stats) library to download and process Letterboxd user data.

Currently, it focuses on syncing:
- ⭐ User ratings
- 📜 Watch history
- 🗛 Watchlist (now with Radarr support)


### 🎯 The Script
The core functionality is provided by a Python script that:
1. **Fetches Data**: Downloads user data from Letterboxd using the `letterboxd_stats` library.
2. **Processes Metadata**: Maps Letterboxd data to Plex-compatible IDs using TMDB for additional metadata when required.
3. **Syncs Data**: Updates the Plex server by:
   - Adding ratings from Letterboxd.
   - Marking movies as watched/unwatched.
   - Syncing the Letterboxd watchlist, optionally integrating with Radarr.

The script behavior is highly configurable through environment variables, allowing users to tailor the sync to their specific requirements.

### 📚 Library Selection

The script can sync data across all movie-type libraries in your Plex server. However, if you'd like to target a specific library, you can set the `PLEX_LIBRARY_NAME` environment variable. For example:

- If `PLEX_LIBRARY_NAME` is set (e.g., "Movies"), the script will sync data only with that library.
- If `PLEX_LIBRARY_NAME` is not set, the script will automatically iterate through all movie libraries in your Plex server, ensuring comprehensive syncing without additional configuration.

### 🎞️ Radarr Integration

For users who manage their media with Radarr, the script offers an additional integration:

- When the `SYNC_WATCHLIST_TO_RADARR` (default: `false`) environment variable is set to `true`, the script will take movies from your Letterboxd watchlist and add them to Radarr as monitored movies.
- To enable this, you must provide:
  - `RADARR_URL`: The base URL for your Radarr server.
  - `RADARR_TOKEN`: The API key for authenticating with Radarr.
  - Optionally, specify `RADARR_TAGS` to tag these movies (e.g., `letterboxd-plex-sync`), helping you organize and manage additions in Radarr.

### 🧊 Docker Container Integration
The Python script is wrapped within a lightweight Docker container that automates execution via a cron process. The container:
1. **Runs Immediately (Optional)**: With the `RUN_NOW` environment variable, the sync job can execute as soon as the container starts.
2. **Schedules Jobs**: A cron process schedules recurring sync jobs based on the `CRON_SCHEDULE` environment variable.
3. **Logs Activity**: Outputs logs to a combined file for easy monitoring of sync activities and troubleshooting.

### 📂 Configuration and Portability
The container is designed for ease of use:
- Configurations are passed as environment variables in a `.env` file.
- Users can choose between running the script locally or using Docker, depending on their preferences and setup.

This design ensures seamless integration with your existing Plex server and minimal manual intervention once deployed.


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
####  
- **`CRON_SCHEDULE`**: The schedule for the cron job (e.g., `0 4 */1 * *` for every day at 4:00AM). Defaults to `0 4 */1 * *`.
####
- **`SYNC_WATCHLIST`**: Set to `true` to sync the watchlist from Letterboxd to Plex. Defaults to `true`.
- **`SYNC_WATCHED`**: Set to `true` to sync watched status from Letterboxd to Plex. Defaults to `true`.
- **`SYNC_RATINGS`**: Set to `true` to sync user ratings from Letterboxd to Plex. Defaults to `true`.
- **`PLEX_LIBRARY_NAME`**: The Plex Movies library to use. Defaults to syncing all Movie-type libraries.
- **`PLEX_USER`**: The Plex user to use for syncing, if not the default admin.
- **`PLEX_PIN`**: The PIN associated with the Plex user, if required.
####
- **`SYNC_WATCHLIST_TO_RADARR`**: Set to `true` to sync the Letterboxd watchlist to Radarr. Defaults to `false`.
- **`RADARR_URL`**: The base URL of your Radarr server (e.g., `http://your-radarr-server:7878`). Required if syncing watchlist to Radarr.
- **`RADARR_TOKEN`**: The API key for your Radarr server. Required if syncing watchlist to Radarr.
- **`RADARR_TAGS`**: A comma-separated list of tags to assign to movies added to Radarr. Tags must exist in Radarr or will be created automatically if they don’t. Optional.
- **`RADARR_ROOT_FOLDER`**: The root folder path in Radarr where new movies will be added (e.g., `/movies`). Defaults to `/movies` if not provided. Optional.
- **`RADARR_MONITORED`**: Whether to set movies as monitored in Radarr. Defaults to `true`.
- **`RADARR_SEARCH`**: Whether to search for the movie after it is added to Radarr.  Defaults to `true`.
- **`RADARR_QUALITY_PROFILE`**: The name of the quality profile to use in Radarr (e.g., `HD - 1080p`). If not provided or not found, defaults to the profile with ID `1`. Optional.



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

# Radarr configuration
RADARR_URL="http://your-radarr-server:7878"  # required if syncing to Radarr
RADARR_TOKEN="your_radarr_api_key_here"      # required if syncing to Radarr
RADARR_TAGS="letterboxd-plex-sync, auto"     # optional: set whatever tags you like, or comment this out to skip adding tags
#RADARR_ROOT_FOLDER='/movies'                # Radarr desintation folder. default: '/movies'
#RADARR_MONITORED='true'                     # Monitor movie in Radarr. default: 'true'  
#RADARR_SEARCH='true'                        # Search movie after adding. default: 'true' 
#RADARR_QUALITY_PROFILE='HD - 1080p'         # default: Whichever profile has index 1 (usually 'Any')

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
    #platform: linux/x86_64 # typically only needed for Apple Silicon
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

