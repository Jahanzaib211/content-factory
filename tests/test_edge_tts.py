import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Mock edge_tts module
mock_edge_tts = MagicMock()
mock_edge_tts.list_voices = AsyncMock(return_value=[
    {"ShortName": "en-US-GuyNeural", "FriendlyName": "Guy", "Locale": "en-US", "Gender": "Male"},
    {"ShortName": "en-US-JennyNeural", "FriendlyName": "Jenny", "Locale": "en-US", "Gender": "Female"},
    {"ShortName": "es-ES-ElviraNeural", "FriendlyName": "Elvira", "Locale": "es-ES", "Gender": "Female"},
])

class MockCommunicate:
    def __init__(self, text, voice, **kwargs):
        self.text = text
        self.voice = voice
    async def save(self, path):
        with open(path, "wb") as f:
            f.write(b"\xff\xfb\x90\x00" + b"\x00" * 100)

mock_edge_tts.Communicate = MockCommunicate

import sys
sys.modules["edge_tts"] = mock_edge_tts

from engines.edge_tts import EdgeTTSEngine, VOICE_PRESETS
from engines.base import EngineResult


class TestEdgeTTSEngine:
    def test_init(self):
        engine = EdgeTTSEngine()
        assert engine.provider_id == "edge-tts"
        assert engine.requires_key is False

    @pytest.mark.anyio
    async def test_health(self):
        engine = EdgeTTSEngine()
        health = await engine.health()
        assert health.healthy is True
        assert "voices" in health.detail

    @pytest.mark.anyio
    async def test_synthesize(self):
        engine = EdgeTTSEngine()
        result = await engine.synthesize("Hello world", voice="en-US-GuyNeural", output="/tmp/test_edge.mp3")
        assert isinstance(result, EngineResult)
        assert result.success is True
        assert result.data["audio_path"] == "/tmp/test_edge.mp3"
        assert result.data["voice"] == "en-US-GuyNeural"
        assert result.data["duration_ms"] > 0

    @pytest.mark.anyio
    async def test_synthesize_empty_text(self):
        engine = EdgeTTSEngine()
        result = await engine.synthesize("", voice="en-US-GuyNeural")
        assert isinstance(result, EngineResult)
        assert result.success is False
        assert "empty" in result.error.lower() or "text" in result.error.lower()

    @pytest.mark.anyio
    async def test_list_voices(self):
        engine = EdgeTTSEngine()
        result = await engine.list_voices()
        assert isinstance(result, EngineResult)
        assert result.success is True
        assert len(result.data) == 3
        assert result.data[0]["voice_id"] == "en-US-GuyNeural"

    @pytest.mark.anyio
    async def test_list_voices_filter_language(self):
        engine = EdgeTTSEngine()
        result = await engine.list_voices(language="es")
        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0]["language"] == "es-ES"

    @pytest.mark.anyio
    async def test_list_voices_filter_gender(self):
        engine = EdgeTTSEngine()
        result = await engine.list_voices(gender="Female")
        assert result.success is True
        assert len(result.data) == 2

    def test_preset_voices(self):
        engine = EdgeTTSEngine()
        presets = engine.get_preset_voices()
        assert len(presets) > 10
        assert presets[0]["voice_id"] in VOICE_PRESETS

    def test_voice_presets_defined(self):
        assert "en-US-GuyNeural" in VOICE_PRESETS
        assert "en-US-JennyNeural" in VOICE_PRESETS
        assert "zh-CN-XiaoxiaoNeural" in VOICE_PRESETS
