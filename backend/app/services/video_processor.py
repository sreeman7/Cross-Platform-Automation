"""Video processing utilities (compression, conversion, metadata)."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Executes local processing steps for downloaded videos."""

    async def process_video(self, input_path: Path, output_dir: Path) -> Path:
        """Process the input video and return processed file path."""

        output_dir.mkdir(parents=True, exist_ok=True)
        processed_path = output_dir / "processed.mp4"
        logger.info("Processing video", extra={"input": str(input_path), "output": str(processed_path)})
        processed_path.write_bytes(input_path.read_bytes())
        return processed_path
