# Universal Downloader Bot

A no-command Telegram bot: paste a supported link, it detects the platform,
downloads the best available quality, and uploads it back with a clean caption.

## Setup

```bash
cp .env.example .env   # fill in API_ID, API_HASH, BOT_TOKEN, OWNER_ID
pip install -r requirements.txt
python3 main.py
```

Or with Docker:

```bash
docker build -t downloader-bot .
docker run --env-file .env downloader-bot
```

`ffmpeg` must be installed on the host (the Dockerfile installs it automatically).

## Deploying to Heroku

Two supported paths — pick one, both are already included:

**A) Container stack (recommended, uses the Dockerfile / ffmpeg is bundled)**
```bash
heroku create your-app-name --stack container
git push heroku main
heroku config:set API_ID=... API_HASH=... BOT_TOKEN=... OWNER_ID=... -a your-app-name
```
Uses `heroku.yml` + `Dockerfile`. `app.json` also has `"stack": "container"` set,
so the Heroku "Deploy" button uses this path too.

**B) Classic buildpack (no Docker, needs the `ffmpeg` buildpack added separately)**
```bash
heroku create your-app-name
heroku buildpacks:add --index 1 https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest
heroku buildpacks:add heroku/python
git push heroku main
```
Uses `Procfile` (`worker: python3 main.py`) + `runtime.txt` (pins Python 3.12).

Either way, **scale the worker dyno on** after deploying — Heroku doesn't
start `worker` processes by default:
```bash
heroku ps:scale worker=1 -a your-app-name
```

## Architecture

```
main.py                  entry point, creates the Pyrogram Client
config.py                all settings, read from environment / .env
core/
  detector.py             URL extraction + platform detection (regex)
  downloader.py           async yt-dlp wrapper (runs in a thread executor)
  uploader.py             picks video/audio/photo/document, reports progress
plugins/
  start.py                /start command
  auto_download.py        the main handler — no commands, just link detection
utils/
  progress.py             progress bar text + edit-rate throttling
  caption.py              builds the per-download caption, hides empty fields
  cleanup.py              deletes local files after upload
  logger.py                file + console logging
  auto_updater.py          checks PyPI for new yt-dlp, upgrades, restarts process
```

## yt-dlp auto-update

Enabled by default (`AUTO_UPDATE_YTDLP=true`). Every `YTDLP_CHECK_INTERVAL`
seconds (default 24h), the bot checks PyPI for a newer `yt-dlp` release. If
one exists, it runs `pip install --upgrade yt-dlp` and then restarts its own
process (`os.execv`) so the new version is actually loaded — Python keeps
the old module cached in memory otherwise. The owner (`OWNER_ID`) gets a
DM when this happens.

Two things this can't do:
- **On Heroku, an upgrade only lasts until the next dyno restart/deploy** —
  the filesystem resets then, and it reinstalls from `requirements.txt`
  (which is already unpinned to `yt-dlp>=...`, so a fresh deploy also picks
  up the latest release on its own).
- If YouTube/Instagram/etc. break an extractor **before** a yt-dlp release
  ships a fix, no update — auto or manual — can help until upstream
  publishes one (usually within a day or two).

To disable: set `AUTO_UPDATE_YTDLP=false` and update manually with
`pip install -U yt-dlp` when a platform's downloads start failing.

## How extraction works

Every supported platform in this project is fetched through **yt-dlp**,
which already implements dedicated extractors per site (not a single
generic scraper) — this is genuinely the best available extraction method
for nearly all of the requested platforms, including YouTube, Instagram,
Facebook, X/Twitter, Reddit, Pinterest, Vimeo, Dailymotion, Twitch clips,
Streamable, SoundCloud, and TikTok. `core/detector.py` only decides the
**UI label** and whether an unrecognized link is ignored (groups) or
shown as an error (private chats) — it doesn't gate which links yt-dlp
is capable of handling.

## Honest limitations (read before deploying)

- **Private/friends-only content** (private Instagram accounts, friends-only
  Snapchat, login-gated posts) needs a valid `COOKIES_FILE` for an account
  that actually has access. No downloader can bypass access controls —
  and this bot doesn't try to.
- **4K/1440p** availability depends entirely on what the source platform
  publishes for that specific video — the bot always requests the
  highest stream available, it can't invent resolutions the source
  doesn't have.
- **Large files (2–4GB+)**: your bot account needs Telegram Premium (or
  the deployment needs local-server mode) for uploads above 2GB — this is
  a Telegram platform limit, not something client code can lift.
- **TikTok/Instagram** occasionally rate-limit or block datacenter IPs;
  `PROXY_URL` and `COOKIES_FILE` in `.env` are there to work around that
  when it happens.
- Respect each platform's Terms of Service and copyright law in your
  jurisdiction — only download content you have the right to save.

## Extending

- Redis-backed dedup/caching, multi-worker queues, and rate-limit-aware
  retry/backoff are natural next additions once this base is running in
  production — the current in-memory `_active_urls` set and semaphore
  are single-process and reset on restart.
