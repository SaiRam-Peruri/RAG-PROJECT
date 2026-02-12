# Free ChromaDB API Deployment Options

## 🏆 OPTION 1: Render.com (BEST - Easiest + Persistent Storage)

### Why Render?
- ✅ **Free tier**: 750 hours/month (always-on for one service)
- ✅ **Persistent disk**: ChromaDB data stays between restarts
- ✅ **HTTPS**: Free SSL certificate
- ✅ **Auto-deploy**: Push to GitHub → auto redeploy
- ✅ **No credit card**: Required but no charges

### Setup (15 minutes):

#### 1. Prepare Repository
```powershell
cd C:\Users\ACER\RAG-Project

# Make sure you have git initialized
git init
git add rag_api_simple.py requirements.txt chroma_db/
git commit -m "Add RAG API for deployment"

# Push to GitHub (create repository first at github.com)
git remote add origin https://github.com/YOUR_USERNAME/rag-api.git
git push -u origin main
```

#### 2. Deploy on Render
1. Go to https://render.com and sign up (free)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `rag-api`
   - **Region**: Oregon (US West)
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn rag_api_simple:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free
5. Click **"Advanced"** → Add Disk:
   - **Name**: `chromadb`
   - **Mount Path**: `/opt/render/project/src/chroma_db`
   - **Size**: 1 GB (free)
6. Click **"Create Web Service"**

#### 3. Wait for deployment (~5 minutes)
You'll get a URL like: `https://rag-api-xxxx.onrender.com`

#### 4. Test
```powershell
# Health check
curl https://rag-api-xxxx.onrender.com/health

# Query
curl -X POST https://rag-api-xxxx.onrender.com/query `
  -H "Content-Type: application/json" `
  -d '{"query": "past performance", "n_results": 3}'
```

#### 5. Update Lambda
```powershell
aws lambda update-function-configuration `
  --function-name automation_proposal `
  --environment "Variables={
    KIMI_API_KEY=sk-xxx,
    RAG_API_URL=https://rag-api-xxxx.onrender.com/query,
    TAVILY_API_KEY=tvly-xxx,
    BRAVE_API_KEY=BSA-xxx,
    BUCKET_NAME=itadvisors
  }" `
  --region us-east-1
```

**⚠️ Free tier limitations:**
- Spins down after 15 min of inactivity (50-second cold start)
- 750 hours/month (31 days = 744 hours, so always-on works!)

---

## 🐳 OPTION 2: Fly.io (Good for Containers)

### Why Fly.io?
- ✅ **Free tier**: 3 shared-cpu VMs, 3GB persistent volumes
- ✅ **Global**: Deploy near your users
- ✅ **Fast**: Good performance
- ⚠️ **Requires credit card** (but no charges on free tier)

### Setup (20 minutes):

#### 1. Create Dockerfile
```dockerfile
# Save as: Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY rag_api_simple.py .
COPY chroma_db ./chroma_db

ENV CHROMA_PATH=/app/chroma_db

EXPOSE 8000

CMD ["uvicorn", "rag_api_simple:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Install Fly CLI
```powershell
# Windows
iwr https://fly.io/install.ps1 -useb | iex

# Restart terminal, then login
fly auth login
```

#### 3. Deploy
```powershell
cd C:\Users\ACER\RAG-Project

# Initialize
fly launch --no-deploy
# Name: rag-api
# Region: Choose closest
# Postgres: No
# Redis: No

# Edit fly.toml, add:
# [mounts]
#   source = "chromadb_data"
#   destination = "/app/chroma_db"

# Create volume
fly volumes create chromadb_data --size 1 --region iad

# Deploy
fly deploy
```

#### 4. Get URL
```powershell
fly status
# URL: https://rag-api.fly.dev
```

---

## 🌐 OPTION 3: ngrok (Simplest - Run Locally)

### Why ngrok?
- ✅ **100% free**: No credit card, no limits
- ✅ **Instant**: Ready in 2 minutes
- ✅ **Local**: Runs on your PC
- ⚠️ **Must keep PC running**
- ⚠️ **URL changes** on each restart (can fix with account)

### Setup (2 minutes):

#### 1. Install ngrok
```powershell
# Download from https://ngrok.com/download
# Or use Chocolatey
choco install ngrok
```

#### 2. Run API Locally
```powershell
cd C:\Users\ACER\RAG-Project

# Install dependencies
pip install -r requirements.txt

# Start API
python rag_api_simple.py
# Running on http://localhost:8000
```

#### 3. Expose with ngrok (in another terminal)
```powershell
ngrok http 8000
# Forwarding: https://xxxx-xx-xx-xx-xx.ngrok-free.app -> http://localhost:8000
```

#### 4. Use the URL
```powershell
# Copy the https://xxxx.ngrok-free.app URL
# Update Lambda environment:
aws lambda update-function-configuration `
  --function-name automation_proposal `
  --environment "Variables={RAG_API_URL=https://xxxx.ngrok-free.app/query,...}"
```

**Tips:**
- Sign up for free ngrok account → get static subdomain
- Keep terminal running
- Set up as Windows service for auto-start

---

## 🎯 RECOMMENDATION

**Best choice for you: Render.com**

**Why:**
1. ✅ **Truly free** (no hidden costs)
2. ✅ **Persistent storage** (ChromaDB preserved)
3. ✅ **Auto-deploys** from GitHub
4. ✅ **Always-on** within free tier hours
5. ✅ **HTTPS** included
6. ✅ **Easy setup** (just connect GitHub)

**When to use alternatives:**
- **Fly.io**: If you need global distribution or <15min inactivity is critical
- **ngrok**: If you want instant setup and don't mind keeping PC running

---

## Quick Comparison

| Feature | Render.com | Fly.io | ngrok |
|---------|------------|--------|-------|
| **Cost** | Free | Free | Free |
| **Credit Card** | No charges | No charges | Not needed |
| **Persistent Storage** | ✅ 1GB disk | ✅ 3GB volume | ✅ Local |
| **Always-On** | ⚠️ Sleeps 15min | ✅ Yes | ⚠️ PC must run |
| **Setup Time** | 15 min | 20 min | 2 min |
| **Cold Start** | 50 sec | None | None |
| **HTTPS** | ✅ Included | ✅ Included | ✅ Included |
| **Custom Domain** | ✅ Free | ✅ Free | ⚠️ Paid |
| **Best For** | General use | Low latency | Quick testing |

---

## Testing Your Deployed API

```powershell
# Replace YOUR_URL with actual URL from Render/Fly/ngrok

# Health check
curl https://YOUR_URL/health

# Get stats
curl https://YOUR_URL/stats

# Query company data
curl -X POST https://YOUR_URL/query `
  -H "Content-Type: application/json" `
  -d '{
    "query": "past performance emergency network projects",
    "n_results": 5
  }'

# Search certifications
curl -X POST https://YOUR_URL/query `
  -H "Content-Type: application/json" `
  -d '{
    "query": "company certifications 8a woman owned",
    "n_results": 3
  }'
```

---

## Troubleshooting

### ChromaDB not loading?
```powershell
# Check logs on Render/Fly
render logs --tail
# or
fly logs

# Common issue: chroma_db folder not uploaded
# Solution: Make sure it's in git and not in .gitignore
```

### API responding slow?
- **Render**: First request after sleep takes 50 sec (free tier limitation)
- **Solution**: Use Fly.io (no sleep) or upgrade Render to paid ($7/mo)

### URL changes on every ngrok restart?
```powershell
# Sign up for free ngrok account
ngrok config add-authtoken YOUR_TOKEN

# Get static domain (free tier)
ngrok http 8000 --domain=your-static-name.ngrok-free.app
```

---

## Next Steps

1. **Choose platform** (Render recommended)
2. **Deploy API** (follow steps above)
3. **Test endpoint** (curl commands)
4. **Update Lambda** (set RAG_API_URL)
5. **Deploy enhanced Lambda** (automation_enhanced.py)
6. **Test full flow** (upload RFI to S3)

Need help with any specific step? Let me know!
