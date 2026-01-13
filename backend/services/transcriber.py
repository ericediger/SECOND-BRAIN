"""Audio transcription service using OpenAI Whisper."""

from pathlib import Path
from typing import Union

from openai import OpenAI

from config import OPENAI_API_KEY, WHISPER_MODEL


class TranscriberService:
    """Transcribes audio files to text using Whisper."""

    SUPPORTED_FORMATS = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm"}

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def transcribe(self, audio_file: Union[str, Path, bytes], filename: str = "audio.webm") -> dict:
        """Transcribe audio file to text.

        Args:
            audio_file: File path, Path object, or bytes of audio data
            filename: Original filename (used for format detection when bytes provided)

        Returns:
            dict with 'success', 'text', and optionally 'error'
        """
        try:
            if isinstance(audio_file, bytes):
                response = self.client.audio.transcriptions.create(
                    model=WHISPER_MODEL,
                    file=(filename, audio_file),
                )
            else:
                file_path = Path(audio_file)

                if not file_path.exists():
                    return {"success": False, "error": "File not found"}

                if file_path.suffix.lower() not in self.SUPPORTED_FORMATS:
                    return {
                        "success": False,
                        "error": f"Unsupported format. Supported: {', '.join(self.SUPPORTED_FORMATS)}",
                    }

                with open(file_path, "rb") as f:
                    response = self.client.audio.transcriptions.create(
                        model=WHISPER_MODEL,
                        file=f,
                    )

            return {
                "success": True,
                "text": response.text,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def transcribe_and_classify(self, audio_file: Union[str, Path, bytes], classifier) -> dict:
        """Transcribe audio and then classify the resulting text.

        Args:
            audio_file: Audio file to transcribe
            classifier: ClassifierService instance to use for classification

        Returns:
            dict with transcription and classification results
        """
        transcription = self.transcribe(audio_file)

        if not transcription["success"]:
            return transcription

        text = transcription["text"]
        classification = classifier.process_capture(text)

        return {
            "success": True,
            "transcription": text,
            "classification": classification,
        }
