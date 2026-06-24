import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def mock_mcp_video():
    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.output_path = "/tmp/out.mp4"
    mock_result.duration = 10.0
    mock_result.width = 1920
    mock_result.height = 1080
    mock_result.codec = "h264"
    mock_result.audio_codec = "aac"
    mock_result.bitrate = 5000000
    mock_result.size_bytes = 1024000
    mock_result.size_mb = 1.0
    mock_result.fps = 30.0
    mock_result.aspect_ratio = "16:9"
    mock_result.score = 85
    mock_result.issues = []
    mock_result.scenes = []
    mock_result.scene_count = 0
    mock_result.scene_count = 0
    mock_result.timestamp = 5.0

    for method in ['trim', 'merge', 'add_text', 'add_audio', 'resize', 'crop',
                    'rotate', 'speed', 'fade', 'filter', 'chroma_key', 'overlay_video',
                    'subtitles', 'watermark', 'normalize_audio', 'extract_audio',
                    'thumbnail', 'detect_scenes', 'convert', 'quality_check', 'pipeline',
                    'stabilize', 'info', 'effect_vignette', 'effect_chromatic_aberration',
                    'effect_glow', 'transition_glitch', 'transition_morph']:
        getattr(mock_client, method).return_value = mock_result

    with patch('engines.video_editor.get_editor', return_value=mock_client):
        yield mock_client


from engines.video_editor import (
    trim, merge, add_text, resize, crop, filter, normalize_audio,
    thumbnail, detect_scenes, convert, quality_check, pipeline, info,
)


class TestVideoEditorFunctions:
    def test_trim(self):
        result = trim("/tmp/test.mp4", start="0", duration="10")
        assert result["success"] is True
        assert "output_path" in result

    def test_merge(self):
        result = merge(["/tmp/a.mp4", "/tmp/b.mp4"])
        assert result["success"] is True
        assert "output_path" in result

    def test_add_text(self):
        result = add_text("/tmp/test.mp4", text="Hello World")
        assert result["success"] is True
        assert "output_path" in result

    def test_resize(self):
        result = resize("/tmp/test.mp4", width=720, height=1280)
        assert result["success"] is True
        assert "output_path" in result

    def test_crop(self):
        result = crop("/tmp/test.mp4", width=540, height=960)
        assert result["success"] is True
        assert "output_path" in result

    def test_normalize_audio(self):
        result = normalize_audio("/tmp/test.mp4")
        assert result["success"] is True
        assert "output_path" in result

    def test_thumbnail(self):
        result = thumbnail("/tmp/test.mp4", timestamp=5.0)
        assert result["success"] is True
        assert "output_path" in result

    def test_detect_scenes(self):
        result = detect_scenes("/tmp/test.mp4")
        assert "scenes" in result

    def test_convert(self):
        result = convert("/tmp/test.mp4", format="webm")
        assert result["success"] is True
        assert "output_path" in result

    def test_quality_check(self):
        result = quality_check("/tmp/test.mp4")
        assert result is not None

    def test_info(self):
        result = info("/tmp/test.mp4")
        assert result["width"] == 1920
        assert result["height"] == 1080

    def test_pipeline(self):
        result = pipeline(steps=[
            {"tool": "trim", "params": {"start": "0", "duration": "5"}},
            {"tool": "resize", "params": {"width": 720, "height": 1280}},
        ])
        assert result["success"] is True
        assert "output_path" in result
