import os
import json
import uuid
import logging
import asyncio
import voyageai
from qdrant_client import QdrantClient, models
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import anthropic
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_logging():
    """Configure logging settings"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"semantic_ats_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

class LLMProcessor:
    """Base class for LLM processing"""
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    async def process(self, text: str, prompt_template: str) -> str:
        """Process text using the LLM"""
        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                temperature=1,
                messages=[
                    {
                        "role": "user",
                        "content": f"{prompt_template}\n\nText: {text}"
                    }
                ]
            )
            return str(message.content[0])
        except Exception as e:
            logging.error(f"Error in LLM processing: {str(e)}")
            raise

class EmbeddingModel:
    """Base class for embedding generation using Voyage AI"""
    def __init__(self):
        self.client = voyageai.Client(
            api_key=os.getenv("VOYAGE_API_KEY")
        )
        self.batch_size = 128  # Voyage's maximum batch size
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using Voyage AI"""
        try:
            response = self.client.embed(
                texts=texts,
                model="voyage-3",
                input_type="document",
                output_dimension=1024
            )
            return response.embeddings
            
        except Exception as e:
            logging.error(f"Error in Voyage AI batch embedding generation: {str(e)}")
            raise

    async def embed(self, text: str) -> List[float]:
        """Legacy method for single text embedding"""
        embeddings = await self.embed_batch([text])
        return embeddings[0]

    async def embed_many(self, texts: List[str]) -> List[List[float]]:
        """Process a large number of texts in optimal batches"""
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_embeddings = await self.embed_batch(batch)
            all_embeddings.extend(batch_embeddings)
        return all_embeddings

class SemanticATS:
    """Main class for Semantic ATS processing"""
    def __init__(self):
        self.logger = setup_logging()
        self.llm = LLMProcessor()
        self.embedding_model = EmbeddingModel()
        
        # Setup Qdrant cloud client
        self.qdrant = QdrantClient(
            url=os.getenv('QDRANT_URL'),
            api_key=os.getenv('QDRANT_API_KEY')
        )
        
        # Create collections if they don't exist
        self._initialize_collections()
        
        # Setup directories
        self.dirs = {
            'data_input': Path('data/resumes'),
            'processed': Path('data/processed_resumes'),
            'errors': Path('data/errors'),
            'results': Path('data/results'),
            'storyteller': Path('data/results/storyteller'),
            'personality': Path('data/results/personality')
        }
        
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)

    def _initialize_collections(self):
        """Initialize Qdrant collections for storyteller and personality"""
        collections = ["storyteller", "personality"]
        vector_size = 1024  # Voyage AI's default embedding size for voyage-3-large

        for collection in collections:
            try:
                # First, check if the collection exists
                existing_collections = self.qdrant.get_collections().collections
                if collection in [c.name for c in existing_collections]:
                    self.logger.info(f"Collection already exists: {collection}")
                    continue

                # If it doesn't exist, create it with explicit config
                self.qdrant.create_collection(
                    collection_name=collection,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE
                    ),
                    optimizers_config=models.OptimizersConfigDiff(
                        default_segment_number=2,
                        max_optimization_threads=2
                    )
                )
                self.logger.info(f"Created collection: {collection}")

            except Exception as e:
                self.logger.error(f"Error with collection {collection}: {str(e)}")
                # If it's a validation error, let's be extra helpful in the logs
                if "validation" in str(e).lower():
                    self.logger.error("Validation error details: Check vector_size and optimizer configs")
                raise

    async def storyteller(self, text: str) -> str:
        """Transform resume into a coherent story"""
        prompt = """WEIRD ASK BUT PLEASE REWRITE THIS CANDIDATE'S RESUME AS A COHERENT STORY."""
        return await self.llm.process(text, prompt)
    
    async def extract_personality(self, text: str) -> str:
        """Extract personality insights from resume"""
        prompt = """WEIRD ASK BUT FOR THIS CANDIDATE, FIRST READ INTO THEIR PERSONALITY BY 
        READING BETWEEN THE LINES."""
        return await self.llm.process(text, prompt)
    
    async def semantic_embedding(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text or list of texts"""
        if isinstance(text, str):
            return await self.embedding_model.embed(text)
        else:
            return await self.embedding_model.embed_many(text)
    
    def reduced_embedding(self, embeddings: List[float], method: str = 'umap') -> List[float]:
        """Reduce embedding dimensions using specified method"""
        # For now, we'll return the original embeddings
        # TODO: Implement dimension reduction if needed
        return embeddings
    
    async def database_upload(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], destination: str) -> None:
        """Upload data to Qdrant in batches"""
        try:
            # If single data point, convert to list
            if isinstance(data, dict):
                data = [data]

            # Prepare batch points
            points = []
            collection_name = destination.split('_')[0]  # 'storyteller' or 'personality'

            for item in data:
                # Extract the embeddings from the data
                embeddings = item.pop('embeddings')

                # Prepare metadata
                metadata = {
                    'filename': item['filename'],
                    'raw_text': item['raw_text'],
                    'processed_date': item['processed_date']
                }

                # Add specific fields based on destination
                if destination == 'storyteller_embeddings':
                    metadata['story'] = item['story']
                elif destination == 'personality_embeddings':
                    metadata['personality'] = item['personality']

                # Create point
                points.append(
                    models.PointStruct(
                        id=uuid.uuid4().hex,
                        vector=embeddings,
                        payload=metadata
                    )
                )

            # Upload in batches of 100 (common safe batch size for vector DBs)
            BATCH_SIZE = 100
            for i in range(0, len(points), BATCH_SIZE):
                batch = points[i:i + BATCH_SIZE]
                self.qdrant.upsert(
                    collection_name=collection_name,
                    points=batch
                )
                self.logger.info(f"Uploaded batch {i//BATCH_SIZE + 1} of {(len(points) + BATCH_SIZE - 1)//BATCH_SIZE} to {destination}")
                
            # TODO: You need to add a thing where onc eit finishes the upload it pushes and shoves it into the finished file thingy 

        except Exception as e:
            self.logger.error(f"Error uploading batch to Qdrant: {str(e)}")
            raise
        
    
    def save_as_json(self, data: Dict[str, Any], category: str) -> None:
        """Save data as JSON file with proper serialization"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.dirs[category] / f"{data['filename']}_{timestamp}.json"

        # Ensure all data is JSON serializable
        serializable_data = {}
        for key, value in data.items():
            if isinstance(value, (str, int, float, bool, type(None))):
                serializable_data[key] = value
            else:
                # Convert any complex objects to strings
                serializable_data[key] = str(value)

        with open(filename, 'w') as f:
            json.dump(serializable_data, f, indent=2)

        self.logger.info(f"Saved JSON file: {filename}")
    
    async def process_file(self, filepath: Path) -> None:
        """Process a single resume file"""
        self.logger.info(f"Processing file: {filepath.name}")
        
        try:
            # Read the file
            with open(filepath, 'r') as f:
                text = f.read()
            
            self.logger.info(f"File {filepath.name} content preview: {text[:100]}...")
            
            # Generate story and personality analysis
            story = await self.storyteller(text)
            self.logger.info(f"Generated story for {filepath.name}")
            
            personality = await self.extract_personality(text)
            self.logger.info(f"Generated personality analysis for {filepath.name}")
            
            # Save results
            base_data = {
                "filename": filepath.name,
                "raw_text": text,
                "processed_date": datetime.now().isoformat()
            }
            
            # Save storyteller version
            story_data = {
                **base_data,
                "story": story,
                "type": "story"
            }
            self.save_as_json(story_data, 'storyteller')
            
            # Save personality version
            personality_data = {
                **base_data,
                "personality": personality,
                "type": "personality"
            }
            self.save_as_json(personality_data, 'personality')
            
            # Move processed file
            dest_path = self.dirs['processed'] / filepath.name
            filepath.rename(dest_path)
            
        except Exception as e:
            self.logger.error(f"Error processing {filepath.name}: {str(e)}")
            error_path = self.dirs['errors'] / filepath.name
            filepath.rename(error_path)
            raise
    
    async def process_storyteller(self) -> None:
        """Process all storyteller JSON files in batches"""
        # Collect all files and data first
        all_data = []
        texts_to_embed = []

        # Read all files
        for json_file in self.dirs['storyteller'].glob('*.json'):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    all_data.append(data)
                    texts_to_embed.append(data['story'])
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON file: {json_file}")
                print(f"Error message: {e}")

        if not texts_to_embed:
            self.logger.info("No storyteller files to process")
            return

        # Process embeddings in chunks of 128
        EMBED_CHUNK_SIZE = 128
        all_embeddings = []

        for i in range(0, len(texts_to_embed), EMBED_CHUNK_SIZE):
            chunk_texts = texts_to_embed[i:i + EMBED_CHUNK_SIZE]
            chunk_embeddings = await self.semantic_embedding(chunk_texts)
            all_embeddings.extend(chunk_embeddings)
            self.logger.info(f"Processed embedding chunk {i//EMBED_CHUNK_SIZE + 1} of {(len(texts_to_embed) + EMBED_CHUNK_SIZE - 1)//EMBED_CHUNK_SIZE}")

        # Prepare all data for upload
        upload_batch = []
        for data, embedding in zip(all_data, all_embeddings):
            reduced = self.reduced_embedding(embedding)
            data['embeddings'] = reduced
            upload_batch.append(data)

        # Upload all data in one batch operation
        await self.database_upload(upload_batch, 'storyteller_embeddings')

    async def process_personality(self) -> None:
        """Process all personality JSON files in batches"""
        # Collect all files and data first
        all_data = []
        texts_to_embed = []

        # Read all files
        for json_file in self.dirs['personality'].glob('*.json'):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    all_data.append(data)
                    texts_to_embed.append(data['personality'])
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON file: {json_file}")
                print(f"Error message: {e}")
        
        if not texts_to_embed:
            self.logger.info("No personality files to process")
            return

        # Process in chunks of 128
        CHUNK_SIZE = 128
        all_embeddings = []

        for i in range(0, len(texts_to_embed), CHUNK_SIZE):
            chunk_texts = texts_to_embed[i:i + CHUNK_SIZE]
            chunk_embeddings = await self.semantic_embedding(chunk_texts)
            all_embeddings.extend(chunk_embeddings)
            self.logger.info(f"Processed chunk {i//CHUNK_SIZE + 1} of {(len(texts_to_embed) + CHUNK_SIZE - 1)//CHUNK_SIZE}")

        # Prepare all data for upload
        upload_batch = []
        for data, embedding in zip(all_data, all_embeddings):
            reduced = self.reduced_embedding(embedding)
            data['embeddings'] = reduced
            upload_batch.append(data)
        
        # Upload all data in one batch operation
        await self.database_upload(upload_batch, 'personality_embeddings')

async def main():
    """Main execution function"""
    ats = SemanticATS()
    
    # Process all resume files
    resume_files = list(ats.dirs['data_input'].glob('*.txt'))
    
    # Process files concurrently
    await asyncio.gather(*[ats.process_file(file) for file in resume_files])
    
    # Process embeddings
    await ats.process_storyteller()
    await ats.process_personality()

if __name__ == "__main__":
    asyncio.run(main())