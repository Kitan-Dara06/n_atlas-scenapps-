from typing import Optional, Tuple

import librosa
import torch
from huggingface_hub import login
from transformers import WhisperForConditionalGeneration, WhisperProcessor

from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TranscriptResult:
    """Transcript result metadata"""

    def __init__(
        self,
        video_id: str,
        status: str,
        duration_seconds: float,
        language_detected: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        self.video_id = video_id
        self.status = status
        self.duration_seconds = duration_seconds
        self.language_detected = language_detected
        self.error_message = error_message


class NAtlasTranscriber:
    """N-ATLAS ASR transcription service"""

    def __init__(self):
        logger.info("Initializing N-ATLAS transcriber")

        # Authenticate with Hugging Face
        try:
            login(token=settings.hf_token)
            logger.info("Hugging Face authentication successful")
        except Exception as e:
            logger.error(f"Hugging Face authentication failed: {e}")
            raise

        # Load model
        try:
            self.processor = WhisperProcessor.from_pretrained(settings.n_atlas_model)
            self.model = WhisperForConditionalGeneration.from_pretrained(
                settings.n_atlas_model
            )
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            logger.info(f"N-ATLAS model loaded on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load N-ATLAS model: {e}")
            raise

    def transcribe(
        self, audio_path: str, video_id: str
    ) -> Tuple[Optional[str], TranscriptResult]:
        """
        Transcribe audio to text.

        Args:
            audio_path: Path to audio file
            video_id: Video identifier

        Returns:
            tuple: (transcript_text, TranscriptResult metadata)
        """
        try:
            logger.info(f"Starting transcription: video_id={video_id}")

            # Load audio
            audio, sr = librosa.load(audio_path, sr=16000, mono=True)
            duration = len(audio) / sr

            if sr != 16000:
                error_msg = f"Sample rate mismatch: expected 16000Hz, got {sr}Hz"
                logger.error(f"{error_msg}: video_id={video_id}")
                return None, TranscriptResult(
                    video_id=video_id,
                    status="error",
                    duration_seconds=0.0,
                    error_message=error_msg,
                )

            # Process in chunks (30 second windows)
            chunk_duration = 30.0
            chunk_size = int(chunk_duration * sr)
            total_samples = len(audio)
            transcript_parts = []

            for start in range(0, total_samples, chunk_size):
                end = min(start + chunk_size, total_samples)
                chunk = audio[start:end]

                if len(chunk) < sr:
                    continue

                inputs = self.processor(chunk, sampling_rate=sr, return_tensors="pt")
                input_features = inputs["input_features"].to(self.device)

                with torch.no_grad():
                    generated_ids = self.model.generate(input_features)

                text = self.processor.batch_decode(
                    generated_ids, skip_special_tokens=True
                )[0]

                if text.strip():
                    transcript_parts.append(text.strip())

            full_transcript = " ".join(transcript_parts)

            logger.info(
                f"Transcription complete: video_id={video_id}, duration={duration:.2f}s"
            )

            return full_transcript, TranscriptResult(
                video_id=video_id,
                status="success",
                duration_seconds=duration,
                language_detected="en-NG",
            )

        except Exception as e:
            logger.error(f"Transcription failed: video_id={video_id}, error={str(e)}")
            return None, TranscriptResult(
                video_id=video_id,
                status="error",
                duration_seconds=0.0,
                error_message=str(e),
            )
