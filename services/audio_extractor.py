from pathlib import Path
from typing import Optional

from moviepy.editor import VideoFileClip

from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AudioExtractor:
    """Handles video ingestion and audio extraction"""

    def __init__(self):
        self.temp_dir = settings.get_temp_audio_path()

    def extract_audio(self, video_path: str, video_id: str) -> Optional[str]:
        """
        Extract audio from video file.

        Args:
            video_path: Path to video file
            video_id: Unique video identifier

        Returns:
            Path to extracted audio file (16kHz mono WAV)
        """
        try:
            logger.info(f"Extracting audio for video_id={video_id}")

            video_clip = VideoFileClip(video_path)

            if video_clip.audio is None:
                logger.error(f"No audio track found in video_id={video_id}")
                video_clip.close()
                return None

            audio_path = self.temp_dir / f"{video_id}_audio.wav"

            video_clip.audio.write_audiofile(
                str(audio_path),
                fps=16000,
                nbytes=2,
                codec="pcm_s16le",
                verbose=False,
                logger=None,
            )

            video_clip.close()

            logger.info(f"Audio extracted: video_id={video_id}")
            return str(audio_path)

        except Exception as e:
            logger.error(
                f"Audio extraction failed: video_id={video_id}, error={str(e)}"
            )
            return None

    def cleanup(self, audio_path: str):
        """Delete temporary audio file"""
        try:
            import os

            if os.path.exists(audio_path):
                os.remove(audio_path)
                logger.info(f"Cleaned up audio file: {audio_path}")
        except Exception as e:
            logger.warning(f"Cleanup failed for {audio_path}: {str(e)}")
