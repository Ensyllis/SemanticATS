# SemanticATS: AI-Powered Resume Screening System

SemanticATS is an intelligent resume screening system that uses modern AI to understand the actual context and impact of candidates' experience, rather than just counting keywords. It transforms traditional keyword-based ATS systems by focusing on the semantic meaning of resumes and job requirements.

## Table of Contents

1. [Overview](#overview)
2. [Backend Setup](#backend-setup)
   - [Setting Up semantic_ats.py](#setting-up-semantic_atspy)
   - [Environment Configuration](#environment-configuration)
   - [Running the Backend](#running-the-backend)
3. [API Integration](#api-integration)
4. [Frontend Setup](#frontend-setup)
5. [Docker Deployment](#docker-deployment)
6. [Troubleshooting](#troubleshooting)
7. [Support](#support)

## Overview

SemanticATS leverages cutting-edge AI technologies to provide a more intelligent approach to resume screening:

- **Natural language search** for candidate requirements
- **Context-aware resume understanding** that captures accomplishments and impact
- **Semantic similarity matching** instead of basic keyword counting
- **Real-time search results** with high relevance
- **Dark mode UI** for better user experience

### Technology Stack

- **Frontend**: TypeScript, React, Tailwind CSS
- **Backend**: Python, FastAPI
- **AI**: 
  - Claude 3.5 Sonnet for story extraction and personality analysis
  - VoyageAI for advanced semantic embeddings
- **Storage**: Qdrant Vector Database
- **Deployment**: Docker, Docker Compose

## Backend Setup

### Setting Up semantic_ats.py

The `semantic_ats.py` script is the core processor that handles:
1. Processing resume files
2. Generating narrative stories about each candidate
3. Extracting personality insights
4. Creating semantic embeddings
5. Storing data in the vector database

#### Directory Structure Setup

First, create the following directory structure in your backend folder:

```
backend/
Γö£ΓöÇΓöÇ semantic_ats.py
Γö£ΓöÇΓöÇ api.py
Γö£ΓöÇΓöÇ .env
ΓööΓöÇΓöÇ data/
    Γö£ΓöÇΓöÇ resumes/            # Place your raw resume files here
    Γö£ΓöÇΓöÇ processed_resumes/  # Successfully processed resumes are moved here
    Γö£ΓöÇΓöÇ errors/             # Problematic files are moved here
    ΓööΓöÇΓöÇ results/
        Γö£ΓöÇΓöÇ storyteller/    # JSON results for storyteller analysis
        ΓööΓöÇΓöÇ personality/    # JSON results for personality analysis
```

You don't need to manually create these folders; the script will automatically create them when run.

#### Resume File Preparation

1. Prepare your resume files in plain text format (`.txt`)
2. Place them in the `data/resumes/` folder
3. File naming will be preserved in the system, so consider using a consistent naming convention

**Example:**
```
data/resumes/
  candidate1_developer.txt
  candidate2_designer.txt
  candidate3_manager.txt
```

### Environment Configuration

The backend requires several API keys to function. Create a `.env` file in the backend directory with the following variables:

```env
# AI API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key
VOYAGE_API_KEY=your_voyage_api_key

# Qdrant Vector DB Configuration
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key

# Logging Configuration
DEBUG=True
LOG_LEVEL=INFO
```

#### How to Get the Required API Keys

1. **Anthropic API Key (for Claude 3.5)**
   - Visit: https://www.anthropic.com/
   - Register or sign in to your account
   - Navigate to the API section to create a new API key
   - Copy the key to your `.env` file

2. **VoyageAI API Key (for embeddings)**
   - Visit: https://voyageai.com/
   - Create an account
   - Go to the API section in your dashboard
   - Generate a new API key and copy it to your `.env` file

3. **Qdrant Vector Database**
   - Option 1: Use Qdrant Cloud
     - Visit: https://qdrant.tech/
     - Create an account
     - Create a new cluster
     - Copy the cluster URL and API key to your `.env` file
   - Option 2: Self-host Qdrant
     - Follow the instructions at: https://qdrant.tech/documentation/guides/installation/
     - Use `http://localhost:6333` as your QDRANT_URL
     - No API key required for local installations

### Running the Backend

#### Installing Dependencies

Install the required Python packages:

```bash
cd backend
pip install -r requirements.txt
```

The requirements include:
- anthropic (for Claude AI)
- voyageai (for embeddings)
- qdrant-client (for vector database)
- python-dotenv (for environment management)
- fastapi & uvicorn (for API server)
- PDF and DOCX handlers (for document processing)

#### Processing Resumes

To process your resume files, run:

```bash
python semantic_ats.py
```

This will:
1. Read all text files from the `data/resumes/` directory
2. Generate a narrative story for each resume using Claude 3.5
3. Extract personality insights for each resume
4. Save JSON results to the respective results directories
5. Move processed files to `data/processed_resumes/`
6. Generate embeddings for all processed data
7. Upload the data and embeddings to Qdrant vector database

**Expected Output:**
- Console logs showing progress
- Detailed logs in the `logs/` directory
- JSON files in `data/results/storyteller/` and `data/results/personality/`

**Note on Processing Time and Cost:**
- Processing takes approximately 5-7 seconds per resume
- Cost is approximately $7 for 400 resumes (based on current Claude 3.5 Sonnet pricing)

#### How to Verify Processing is Complete

The processing is complete when:

1. The script finishes executing and returns to a command prompt
2. All original resume files have been moved from `data/resumes/` to `data/processed_resumes/`
3. JSON files have been created in both results directories
4. The console or log files show "Processing complete" messages
5. No errors are reported in the logs

You can verify the data was successfully uploaded to Qdrant by checking the log files for "Uploaded batch" messages.

## API Integration

After processing resumes, you need to start the API server to make the data accessible:

```bash
cd backend
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

The API provides the following endpoints:

- `GET /health` - Check if the API is running
- `POST /search` - Search for resumes based on query and mode

You can test the API is working using curl:

```bash
curl -X GET http://localhost:8000/health
# Should return: {"status": "healthy"}

curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"experienced software developer with python", "mode":"story"}'
```

## Frontend Setup

The frontend connects to the backend API and provides a user-friendly interface for searching resumes.

### Environment Configuration

Create a `.env.local` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
```

For production, change this to your server's IP or domain:

```env
VITE_API_URL=http://your-server-ip:8000
```

### Running the Frontend Locally

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:3000

## Docker Deployment

SemanticATS can be easily deployed using Docker and Docker Compose.

### Backend Docker Deployment

The backend container handles the API server. The resume processing is typically done as a one-time setup step before deployment.

1. Build and tag the backend image:

```bash
cd backend
docker build -t semanticats-backend:latest .
docker tag semanticats-backend:latest yourusername/semanticats-backend:latest
docker push yourusername/semanticats-backend:latest
```

2. Create a `docker-compose.yml` file for the backend:

```yaml
services:
  semantic_ats:
    build: .
    container_name: semantic_ats
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
    networks:
      - semantic_ats_network

networks:
  semantic_ats_network:
    driver: bridge
```

### Full Deployment with Frontend and Backend

For a complete deployment with both frontend and backend:

1. Create a `docker-compose.yml` in your project root:

```yaml
services:
  frontend:
    image: yourusername/semanticats-frontend:latest
    container_name: semantic_ats_frontend
    ports:
      - "3000:80"
    environment:
      - VITE_API_URL=http://your-server-ip:8000
    depends_on:
      - backend
    networks:
      - semantic_ats_network

  backend:
    image: yourusername/semanticats-backend:latest
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
    networks:
      - semantic_ats_network

networks:
  semantic_ats_network:
    driver: bridge
```

2. Deploy with Docker Compose:

```bash
docker-compose pull
docker-compose up -d
```

3. Verify the containers are running:

```bash
docker-compose ps
```

Your SemanticATS system should now be accessible at:
- Frontend: http://your-server-ip:3000
- API: http://your-server-ip:8000

## Troubleshooting

### Common Issues and Solutions

1. **API Key Authentication Errors**
   - Verify your API keys are correctly set in the `.env` file
   - Check for any whitespace around the key values
   - Ensure the APIs are active and have sufficient credits

2. **Resume Processing Errors**
   - Check the `data/errors/` directory for problematic files
   - Verify the text files are in UTF-8 encoding
   - Make sure the resume files are in plain text format
   - Look at the log files in the `logs/` directory for specific error messages

3. **Docker Deployment Issues**
   - Ensure Docker and Docker Compose are installed correctly
   - Verify network connectivity between containers
   - Check container logs with `docker-compose logs`
   - Make sure all required environment variables are set

4. **Frontend Connection Problems**
   - Verify the API URL is correctly set in the frontend's .env.local file
   - Check that the backend is running and accessible
   - Look for CORS errors in the browser's developer console

### Logs and Debugging

The system creates detailed logs in the `logs/` directory. These logs include:
- Processing status for each resume
- API request/response details
- Error messages and stack traces

To enable more verbose logging, set `DEBUG=True` and `LOG_LEVEL=DEBUG` in your `.env` file.

## Support

If you encounter any issues with setup or deployment, there are several ways to get help:

1. Check the logs in the `logs/` directory for detailed error messages
2. Review the troubleshooting section in this README
3. Contact the developer directly at josephliu1127@gmail.com

If you're in the Chicago area, the developer has offered to help with setup and debugging in person over coffee or drinks.

---

Built with Γ¥ñ∩╕Å by Joseph Liu
