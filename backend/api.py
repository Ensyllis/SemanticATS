from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from typing import List, Optional
import voyageai
from qdrant_client import QdrantClient
import logging
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Voyage AI client
voyageai.api_key=os.getenv("VOYAGE_API_KEY")
voyage_client = voyageai.Client()

# Initialize Qdrant client
qdrant_client = QdrantClient(
    url=os.getenv('QDRANT_URL'),
    api_key=os.getenv('QDRANT_API_KEY')
)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite's default port
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,  # Changed this since we removed credentials: 'include'
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept"],
)

class SearchQuery(BaseModel):
    query: str
    mode: str

class SearchResult(BaseModel):
    filename: str
    score: float
    story: Optional[str] = None
    personality: Optional[str] = None
    rawText: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[SearchResult]

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# In your FastAPI backend, update the search endpoint:
@app.post("/search")
async def search_resumes(query: SearchQuery) -> SearchResponse:
    logger.info("Search endpoint hit") 
    try:
        logger.info(f"Searching with query: {query.query} in mode: {query.mode}")
        
        # Generate embedding for the search query
        query_embedding = voyage_client.embed(
            texts=[query.query],
            model="voyage-3",
            input_type="query"
        ).embeddings[0]
        
        # Here's where the magic happens - determine collection based on mode
        if query.mode == "resume":
            collection = "Full_Texts"  # Your new collection
        else:
            collection = "storyteller" if query.mode == "story" else "personality"
        
        # Search in Qdrant
        search_results = qdrant_client.search(
            collection_name=collection,
            query_vector=query_embedding,
            limit=10
        )
        
        # Format results with a twist
        results = []
        for hit in search_results:
            result = SearchResult(
                filename=hit.payload["filename"],
                score=hit.score,
                # Now we're getting fancy - conditionally add fields based on mode
                story=hit.payload.get("story") if query.mode in ["story", "resume"] else None,
                personality=hit.payload.get("personality") if query.mode in ["personality", "resume"] else None,
                rawText=hit.payload.get("raw_text") if query.mode == "resume" else None
            )
            results.append(result)
        
        logger.info(f"Found {len(results)} results")
        return SearchResponse(results=results)
    
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)