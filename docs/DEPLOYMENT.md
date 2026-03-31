# Deployment

## Running with Docker

### Quick start (data is lost when the container is removed)

```bash
bash scripts/start.sh
```

### Persistent data (recommended)

The SQLite database lives inside the container at `/data/kanban.db`. If the container is removed (`docker rm`) without a volume, all board data is lost.

Mount a named volume to persist data across container restarts and removals:

```bash
docker build -t kanban-studio .
docker run -d \
  --name kanban \
  -p 8000:8000 \
  --env-file .env \
  -v kanban_data:/data \
  kanban-studio
```

To remove the container while keeping the data:

```bash
docker rm -f kanban          # data volume is preserved
docker volume ls             # kanban_data still listed
```

To wipe everything including data:

```bash
docker rm -f kanban
docker volume rm kanban_data
```

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | API key for OpenRouter AI |

Place these in a `.env` file at the project root. Do not commit this file to source control.

## Stopping the container

```bash
bash scripts/stop.sh
```

## Sessions

Auth tokens are stored in memory and expire after 8 hours. Restarting the container also invalidates all tokens — users will need to log in again.
