# Semantic ATS

## P.S. Need Help?
If something's not working, reach out. I built this in 4 days but happy to help you set it up on your servers. If you're in Chicago, buy me a good coffee/drink and we can debug together. josephliu1127@gmail.com

## Introduction
Semantic ATS is a resume screening system that uses modern AI to understand the actual context and impact of candidates' experience, rather than just counting keywords. Built with Claude 3.5 for story extraction, VoyageAI for semantic embeddings, and Qdrant for vector search.

Key Features:
- Natural language search for candidate requirements
- Context-aware resume understanding
- Semantic similarity matching instead of keyword counting
- Real-time search results
- Dark mode UI (because we're not savages)

Built on:
- Frontend: TypeScript/React/Tailwind
- Backend: Python/FastAPI
- AI: Claude 3.5 + VoyageAI Embeddings
- Storage: Qdrant Vector DB
- Deployment: Docker + DigitalOcean
  
## Setup

### 1. Get API Keys
- Qdrant: Get URL and API key for your cluster
- Anthropic: Get API key 
- VoyageAI: Get API key

Backend `.env`:
```env
ANTHROPIC_API_KEY=
QDRANT_API_KEY= 
QDRANT_URL=
VOYAGE_API_KEY=

DEBUG=True
LOG_LEVEL=INFO
```

Frontend `nginx.conf`:
```nginx
server {
    listen 80;
    server_name http://YOUR_IP_OR_DOMAIN;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Also set up `.env.local` in frontend folder (change to localhost for development)

### 2. Upload New Data

1. Place .txt resumes in folder structure:
```
data/
  resumes/
    resume1.txt
    resume2.txt
    ...
```

2. Install requirements:
```bash
pip install -r requirements.txt
```

3. Run processor:
```bash
python semantic_ats.py
```
Note: Cost ~$7 for 400 entries

### 3. Local Development

Frontend:
```bash
npm install
npm run dev
```

Backend:
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

Note: Check ipynb files and run Jupyter notebooks for new collection setup

### 4. Docker Deployment

Build & Push:
```bash
docker login
docker build
docker tag username/image
docker push username/image
```

On Production:
```bash
docker-compose pull
docker-compose up -d
```

## P.S. Need Help?
If something's not working, reach out. I built this in 4 days but happy to help you set it up on your servers. If you're in Chicago, buy me a good coffee/drink and we can debug together.

