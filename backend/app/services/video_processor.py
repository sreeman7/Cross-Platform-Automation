"""Video processing utilities (compression, conversion, metadata)."""

import asyncio
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Executes local processing steps for downloaded videos."""

    async def process_video(self, input_path: Path, output_dir: Path) -> Path:
        """Convert to H.264/AAC MP4 suitable for upload."""

        if not input_path.is_file() or input_path.stat().st_size == 0:
            raise ValueError("Input video is missing or empty")
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise RuntimeError("FFmpeg executable is required for video processing")
        output_dir.mkdir(parents=True, exist_ok=True)
        processed_path = output_dir / "processed.mp4"
        logger.info("Processing video", extra={"input": str(input_path), "output": str(processed_path)})
        process = await asyncio.create_subprocess_exec(
            ffmpeg, "-y", "-i", str(input_path), "-c:v", "libx264", "-preset", "medium",
            "-crf", "25", "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart",
            str(processed_path), stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()
        if process.returncode != 0 or not processed_path.is_file():
            logger.error("FFmpeg failed: %s", stderr.decode(errors="replace")[-1000:])
            raise RuntimeError("Video conversion failed; check source video format")
        return processed_path
