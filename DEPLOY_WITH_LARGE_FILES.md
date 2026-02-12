# RAG API Deployment with Large Files

## Problem: Git repo too large (4K+ files from chroma_db/)

## Solution: Exclude large files from git, upload separately

---

## Option 1: Upload ChromaDB to Render Persistent Disk (Recommended)

### Step 1: Clean git repo
```powershell
cd C:\Users\ACER\RAG-Project

# Remove tracked large files
git rm -r --cached chroma_db Federal_Contracting
git commit -m "Remove large files from git"

# Check repo size (should be small now)
git status
```

### Step 2: Deploy to Render
1. Push lean repo to GitHub:
   ```powershell
   git push origin main
   ```

2. Create Render web service (same as before)
   - Add persistent disk: `/opt/render/project/src/chroma_db`

### Step 3: Upload ChromaDB to Render disk

**Option A: Using rsync (if you have SSH access)**
```powershell
# Zip chroma_db locally
tar -czf chroma_db.tar.gz chroma_db/

# Upload via Render Shell
# In Render dashboard: Shell tab
cd /opt/render/project/src
# Upload file via web interface or wget from cloud storage
tar -xzf chroma_db.tar.gz
```

**Option B: Object storage (S3/Backblaze)**
```powershell
# Upload to S3
aws s3 cp chroma_db/ s3://your-bucket/chroma_db/ --recursive

# On Render, download in startup:
# Add to start command:
aws s3 sync s3://your-bucket/chroma_db/ /opt/render/project/src/chroma_db/
uvicorn rag_api_simple:app --host 0.0.0.0 --port $PORT
```

---

## Option 2: Rebuild ChromaDB on Server

### Step 1: Modify startup command
In Render dashboard, set **Start Command**:
```bash
bash build_chroma_on_deploy.sh && uvicorn rag_api_simple:app --host 0.0.0.0 --port $PORT
```

### Step 2: Upload source documents
- Upload `Federal_Contracting/` folder to Render persistent disk
- Or store in S3 and download during build

### Pros:
- ✅ Git repo stays tiny
- ✅ ChromaDB always fresh from source

### Cons:
- ⚠️ First deployment takes 5-10 minutes
- ⚠️ Need to upload source documents separately

---

## Option 3: Use ngrok (Simplest - No Upload Needed!)

If the hassle of uploading is too much:

```powershell
# Keep everything local - no git needed!
cd C:\Users\ACER\RAG-Project

# Start API (chroma_db already local)
python rag_api_simple.py

# Expose in another terminal
ngrok http 8000

# Use the URL in Lambda
# https://xxxx.ngrok-free.app/query
```

**Setup ngrok static domain (free):**
```powershell
# Sign up at ngrok.com (free)
ngrok config add-authtoken YOUR_TOKEN

# Get static subdomain
ngrok http 8000 --domain=your-company-rag.ngrok-free.app
```

**Keep it running:**
- Windows Task Scheduler to auto-start
- Or run in background with `pythonw`

---

## Recommendation

**For 4K+ files issue:**

1. **Best for reliability**: Render + Upload ChromaDB via web/S3 (Option 1)
2. **Best for simplicity**: ngrok (Option 3) - no upload hassle
3. **Best for automation**: Rebuild on deploy (Option 2) - but slower

**Quick fix NOW:**
```powershell
# Use ngrok - no git upload needed
cd C:\Users\ACER\RAG-Project
python rag_api_simple.py

# In another terminal
ngrok http 8000
```

You get instant API without dealing with 4K+ files in git! 🚀

---

## Current Repo Status

After updating .gitignore:
```powershell
git status
# Shows: Modified files only (.py files, requirements.txt)
# Excludes: chroma_db/ (4K+ files), Federal_Contracting/ (large docs)
```

Clean up tracked files:
```powershell
git rm -r --cached chroma_db Federal_Contracting
git add .gitignore
git commit -m "Exclude large files from git repo"
```

Your repo should now be lean (~50-100 files instead of 4K+).
