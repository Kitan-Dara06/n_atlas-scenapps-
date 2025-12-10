from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models.schemas import (
    HealthResponse,
    ProcessVideoRequest,
    ProcessVideoResponse,
    SearchRequest,
    SearchResponse,
)
from services.audio_extractor import AudioExtractor
from services.mention_detector import MentionDetector
from services.search import TranscriptSearch
from services.transcriber import NAtlasTranscriber
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Global service instances
audio_extractor = None
transcriber = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global audio_extractor, transcriber

    # Startup
    logger.info("Starting N-Atlas service...")
    try:
        audio_extractor = AudioExtractor()
        transcriber = NAtlasTranscriber()
        logger.info("Service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down N-Atlas service...")


# Initialize FastAPI app
app = FastAPI(
    title="N-Atlas Verbal Detection API",
    description="Video transcription, mention detection, and search service",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", model_loaded=transcriber is not None)


@app.post("/process-video", response_model=ProcessVideoResponse)
async def process_video(request: ProcessVideoRequest):
    """
    Process video: transcribe + detect mentions

    Returns both transcript (for search) and mentioned user IDs (for tagging)
    """
    try:
        logger.info(f"Processing video: video_id={request.video_id}")

        # Step 1: Extract audio
        audio_path = audio_extractor.extract_audio(request.video_path, request.video_id)
        if not audio_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio extraction failed",
            )

        try:
            # Step 2: Transcribe
            transcript_text, transcript_result = transcriber.transcribe(
                audio_path, request.video_id
            )

            if transcript_result.status != "success" or not transcript_text:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=transcript_result.error_message or "Transcription failed",
                )

            # Step 3: Detect mentions
            mention_detector = MentionDetector(request.users)
            mentioned_user_ids, mentioned_users = mention_detector.detect_mentions(
                transcript_text, request.video_id
            )

            # Step 4: Return result
            return ProcessVideoResponse(
                video_id=request.video_id,
                mentioned_user_ids=list(mentioned_user_ids),
                mentioned_users=mentioned_users,
                mention_count=len(mentioned_user_ids),
                transcript=transcript_text,  # Backend saves this
                duration_seconds=transcript_result.duration_seconds,
                processed_at=datetime.utcnow().isoformat(),
                status="success",
            )

        finally:
            # Cleanup
            audio_extractor.cleanup(audio_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Video processing failed: video_id={request.video_id}, error={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@app.post("/search", response_model=SearchResponse)
async def search_transcripts(request: SearchRequest):
    """
    Search through transcripts

    Backend sends all transcripts, this returns matching videos
    """
    try:
        logger.info(f"Searching transcripts: query='{request.query}'")

        results = TranscriptSearch.search_transcripts(
            request.query, request.transcripts
        )

        return SearchResponse(
            query=request.query, results=results, total_results=len(results)
        )

    except Exception as e:
        logger.error(f"Search failed: query='{request.query}', error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host=settings.host, port=settings.port, reload=settings.debug
    )
