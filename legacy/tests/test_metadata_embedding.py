"""Test script to verify metadata embedding in audio files."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from services.downloader import download_audio


@pytest.mark.asyncio
async def test_metadata_postprocessor_configured():
    """Verify that FFmpegMetadata postprocessor is configured."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        mock_info = {
            "title": "Test Song",
            "uploader": "Test Artist",
            "duration": 180,
            "ext": "m4a",
        }

        with patch("services.downloader.yt_dlp.YoutubeDL") as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.return_value = mock_info
            mock_ydl.prepare_filename.return_value = str(Path(tmp_dir) / "Test Song.mp3")
            mock_ydl.__enter__.return_value = mock_ydl
            mock_ydl.__exit__.return_value = None
            mock_ydl_class.return_value = mock_ydl

            await download_audio(
                url="https://www.youtube.com/watch?v=test",
                audio_format="mp3",
                quality="0",
                output_dir=tmp_dir,
            )

            # Verify YoutubeDL was called
            assert mock_ydl_class.called

            # Get the ydl_opts passed to YoutubeDL
            call_args = mock_ydl_class.call_args[0][0]

            # Verify postprocessors are configured
            assert "postprocessors" in call_args
            postprocessors = call_args["postprocessors"]

            # Check that FFmpegMetadata is in the postprocessors list
            metadata_pp = [pp for pp in postprocessors if pp.get("key") == "FFmpegMetadata"]
            assert len(metadata_pp) == 1, "FFmpegMetadata postprocessor should be configured"
            assert metadata_pp[0].get("add_metadata") is True

            # Check that EmbedThumbnail is also configured
            thumbnail_pp = [pp for pp in postprocessors if pp.get("key") == "EmbedThumbnail"]
            assert len(thumbnail_pp) == 1, "EmbedThumbnail postprocessor should be configured"

            # Check that FFmpegThumbnailsConvertor is configured
            convertor_pp = [
                pp for pp in postprocessors if pp.get("key") == "FFmpegThumbnailsConvertor"
            ]
            assert len(convertor_pp) == 1, "FFmpegThumbnailsConvertor should be configured"


@pytest.mark.asyncio
async def test_metadata_order():
    """Verify postprocessors are in correct order."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        mock_info = {
            "title": "Test Song",
            "uploader": "Test Artist",
            "duration": 180,
            "ext": "mp3",
        }

        with patch("services.downloader.yt_dlp.YoutubeDL") as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.return_value = mock_info
            mock_ydl.prepare_filename.return_value = str(Path(tmp_dir) / "Test Song.mp3")
            mock_ydl.__enter__.return_value = mock_ydl
            mock_ydl.__exit__.return_value = None
            mock_ydl_class.return_value = mock_ydl

            await download_audio(
                url="https://www.youtube.com/watch?v=test",
                audio_format="mp3",
                quality="0",
                output_dir=tmp_dir,
            )

            call_args = mock_ydl_class.call_args[0][0]
            postprocessors = call_args["postprocessors"]

            # Extract keys in order
            pp_keys = [pp.get("key") for pp in postprocessors]

            # Verify order: ExtractAudio -> ThumbnailsConvertor -> EmbedThumbnail -> Metadata
            # This ensures metadata is added after thumbnail is embedded
            assert "FFmpegExtractAudio" in pp_keys
            assert "FFmpegThumbnailsConvertor" in pp_keys
            assert "EmbedThumbnail" in pp_keys
            assert "FFmpegMetadata" in pp_keys

            # Metadata should come after thumbnail embedding
            metadata_idx = pp_keys.index("FFmpegMetadata")
            thumbnail_idx = pp_keys.index("EmbedThumbnail")
            assert metadata_idx > thumbnail_idx, (
                "Metadata should be added after thumbnail embedding"
            )
