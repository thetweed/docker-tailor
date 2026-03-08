# Docker Setup Guide

This guide explains how to run the Resume Tailor application using Docker.

## Prerequisites

- Docker installed on your system ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (included with Docker Desktop)
- An Anthropic API key ([Get one here](https://console.anthropic.com/settings/keys))

## Quick Start

1. **Clone or download this repository**

2. **Set up your environment variables**

   Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   FLASK_SECRET_KEY=your_secret_key_here
   ```

3. **Start the application**

   ```bash
   docker-compose up -d
   ```

   The `-d` flag runs it in detached mode (background).

4. **Access the application**

   Open your browser and navigate to:
   ```
   http://localhost:8080
   ```

## Docker Commands

### Start the application
```bash
docker-compose up -d
```

### Stop the application
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f resume-tailor
```

### Restart the application
```bash
docker-compose restart
```

### Rebuild the image (after code changes)
```bash
docker-compose up -d --build
```

### Stop and remove containers (data preserved)
```bash
docker-compose down
```
Your data in `data/`, `uploads/`, and `flask_session/` is stored on your host machine as bind mounts and is **not** affected by `docker-compose down`.

### Permanently delete all app data
```bash
docker-compose down
rm -rf data/ uploads/ flask_session/
```
**Warning**: This permanently deletes your database, uploaded files, and sessions. There is no undo.

## Data Persistence

Your data is stored in the following directories on your host machine:

- `./data/` - SQLite database
- `./uploads/` - Uploaded resume files
- `./flask_session/` - Session data

These directories are automatically created when you start the container. Your data persists even if you stop or remove the container.

### Session File Cleanup

The `docker-compose.yml` includes a `session-cleanup` sidecar service that automatically deletes session files not accessed in 7+ days. It runs once every 24 hours using a minimal Alpine Linux image. No configuration is needed — it starts alongside the main application.

If you want to change the retention period, edit the `-atime +7` value in `docker-compose.yml` (the number is days). To disable it entirely, remove or comment out the `session-cleanup` service block.

## Accessing the Container

If you need to access the running container:

```bash
docker exec -it resume-tailor-app bash
```

## Troubleshooting

### Port already in use
If port 8080 is already in use, you can change it in `docker-compose.yml`:
```yaml
ports:
  - "9090:5000"  # Change 9090 to any available port
```

### API key not working
Make sure your `.env` file is in the same directory as `docker-compose.yml` and contains:
```
ANTHROPIC_API_KEY=sk-ant-...
```

### Permission issues
If you encounter permission issues with volumes:
```bash
sudo chown -R $USER:$USER data/ uploads/ flask_session/
```

### Check container health
```bash
docker ps
```
Look for the "STATUS" column - it should show "healthy" after about 40 seconds.

### View detailed logs
```bash
docker-compose logs -f
```

## Building Without Docker Compose

If you prefer to use Docker directly:

```bash
# Build the image
docker build -t resume-tailor .

# Run the container
docker run -d \
  -p 8080:5000 \
  -e ANTHROPIC_API_KEY=your_api_key_here \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/flask_session:/app/flask_session \
  --name resume-tailor-app \
  resume-tailor
```

## Security Notes

- **Never commit your `.env` file** to version control
- `FLASK_SECRET_KEY` must be a unique, random string — it protects sessions and CSRF tokens. Generate one with: `python -c "import secrets; print(secrets.token_hex(32))"`
- If you change `FLASK_SECRET_KEY` or rebuild the container from scratch, existing browser sessions become invalid. Clear cookies for `localhost:8080` if you see a "CSRF session token is missing" error after a rebuild
- All forms are protected against cross-site request forgery (CSRF)
- All your data stays local — only job descriptions are sent to Anthropic's API for analysis
- The application is designed for single-user personal use

## Updating the Application

To update to a newer version:

1. **Back up your data** (recommended before any update):
   ```bash
   tar -czf backup-$(date +%Y%m%d).tar.gz data/ uploads/
   ```

2. Pull the latest code

3. Rebuild and restart:
   ```bash
   docker-compose up -d --build
   ```

Your data in `data/` and `uploads/` is stored as bind mounts and will be preserved. The database schema is updated automatically on startup if needed.

After rebuilding, clear your browser cookies for `localhost:8080` to avoid stale session issues.
