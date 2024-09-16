# 🎬 Letterboxd Plex Sync

A work-in-progress script that syncs [Letterboxd](https://letterboxd.com/) user data (like ratings, watch history, and watchlists) to a personal [Plex](https://www.plex.tv/) server. This tool aims to enhance your Plex experience by keeping your viewing stats up to date with your Letterboxd profile! 🚀

## 🔧 How It Works

The script leverages:
- [Plex API wrapper](https://github.com/pkkid/python-plexapi) to interact with your Plex server.
- [letterboxd_stats](https://github.com/mBaratta96/letterboxd_stats) library to download and process Letterboxd user data.

Currently, it focuses on syncing:
- ⭐ User ratings
- 📚 Watch history
- 📝 Watchlist

## 🐋 Sample Docker Compose Setup

Here's a sample Docker Compose setup to run the `letterboxd_plex_sync` script as a cron job:

```yaml
name: letterboxd_plex_sync
services:
  letterboxd_sync:
    container_name: letterboxd_sync
    restart: unless-stopped
    depends_on:
      - plex
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=US/Mountain
    stdin_open: true
    tty: true    
    env_file:
      - path: ./lb_sync/debug.env
        required: false  
    volumes:
      # Directory containing config.toml for letterboxd_stats
      - "~/.config/letterboxd_stats:/root/.config/letterboxd_stats"
      # Optional: Add resources folder for a pre-generated Letterboxd to TMDb mapping CSV file.
      - "~/lb_sync/resources:/app/resources"
    build: https://github.com/treysullivent/letterboxd_plex_sync.git
    image: letterboxd_plex_sync:dev 
```

## 📝 Configuring `letterboxd_stats/config.toml`

The `letterboxd_plex_sync` script extends the `config.toml` file used by the `letterboxd_stats` Python library. This file is typically located at `~/.config/letterboxd_stats/config.toml` on your system, or you can create it from scratch.

### Adding Plex Configuration

To enable Plex syncing, add the following settings to your `config.toml` file:

```sh
echo -e "\n\
[Plex]\n\
baseurl = 'http://%YOUR_PLEX_BASEIP%:%YOUR_PLEX_PORT%'\n\
token = '%YOUR_PLEX_TOKEN%'\n\
\n\
# Optional: Use a different user than the default (admin)\n\
user = '%YOUR_LOCAL_PLEX_USER_NAME%'\n\
\n\
# Optional: If that user has a PIN\n\
pin = '%YOUR_LOCAL_USER_PIN%'\n" \
| sudo tee -a ~/.config/letterboxd_stats/config.toml
```

### Example `config.toml`

Here’s what your `config.toml` file might look like after adding the required Plex configuration:

```toml
# Where you want the .csv file of your Letterboxd activity to be saved.
root_folder = "/tmp/"

# The size of the ASCII art poster printed in your terminal when you check the details of a movie. Set to 0 to disable.
poster_columns = 0

[TMDB]
api_key = "[%YOUR_TMDB_API_KEY%]"

[Letterboxd]
username = "%YOUR_LB_USERNAME%"
password = "%YOUR_LB_PASSWORD%"

# # # # #     NEW SECTION TO FACILITATE PLEX SYNC     # # # # #
[Plex]
baseurl = 'http://%YOUR_PLEX_BASEIP%:%YOUR_PLEX_PORT%'
token = '%YOUR_PLEX_TOKEN%'

# Optional: Use a different user than the default (admin)
user = '%YOUR_LOCAL_PLEX_USER_NAME%'

# Optional: If that user has a PIN
pin = '%YOUR_LOCAL_USER_PIN%'
```

## 🚀 Usage

1. **Clone the Repository**:  
   ```sh
   git clone https://github.com/treysullivent/letterboxd-plex-sync.git
   cd letterboxd-plex-sync
   ```

2. **Build and Run the Docker Container**:  
   Use the provided Docker Compose setup to build and run the container:
   ```sh
   docker compose up -d
   ```

3. **Configure Your Environment**:  
   Make sure your `config.toml` file is properly set up with your Plex and Letterboxd credentials as shown above.

## 🛠 Future Improvements

- 📊 Better handling of multiple Plex users.
- 🔄 Sync additional types of data (e.g., tags, custom lists).
- 🎨 Improved logging and error handling.

## 📣 Contributing

Feel free to open issues or make pull requests. This project is still a work in progress, and contributions are welcome!
