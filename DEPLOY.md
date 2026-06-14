# Deploy to Railway

## Files added to this repo

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies (Flask) |
| `Procfile` | Start command for Railway |
| `railway.toml` | Railway build/deploy config |

---

## Steps

### 1. Push these files to GitHub

Make sure `requirements.txt`, `Procfile`, and `railway.toml` are committed and pushed.

### 2. Create a Railway project

1. Go to [railway.app](https://railway.app) and sign in with GitHub.
2. Click **New Project → Deploy from GitHub repo**.
3. Select this repository.
4. Railway will detect `requirements.txt` and install Flask automatically.

### 3. Add a Persistent Volume (important!)

The app stores all data in `library.json` on disk. Without a volume, data is lost on every redeploy.

1. In your Railway project, click your service → **Settings → Volumes**.
2. Click **Add Volume**.
3. Set the mount path to the directory where `library.json` lives (the `tools/` directory inside the repo, which maps to `/app/tools` on Railway, or `/app` if the repo root is `tools/`).
   - If your repo root **is** `tools/`: mount path = `/app`
   - If `tools/` is a subfolder: mount path = `/app/tools`
4. Save.

> **Why this matters:** Railway containers are ephemeral. Any file written inside the container (including `library.json`) is wiped on restart unless it's on a mounted volume.

### 4. Set environment variables (optional)

Railway automatically sets `PORT`. No extra env vars needed unless you add API keys later.

### 5. Deploy

Click **Deploy** (or push a new commit). Railway will:
1. Install Flask via pip
2. Run `python server.py`
3. Expose the app on a public URL like `https://your-app.railway.app`

---

## ⚠️ One-time: migrate existing library.json to the volume

After the volume is mounted, your `library.json` from the repo will be at the mount path. The first deploy will copy it there. Subsequent redeploys will leave it untouched (the volume persists independently of the container).

---

## Local development (unchanged)

```bash
pip install flask
python server.py        # if repo root is tools/
# OR
python tools/server.py  # if running from parent directory
```

Open: http://localhost:5090
