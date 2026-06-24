import os, json, pytest
from engines.analytics import YouTubeAnalytics, TikTokAnalytics, InstagramAnalytics, AnalyticsStore, AnalyticsEngine, VideoMetrics, ChannelMetrics


class TestAnalyticsStore:
    def test_init_default(self):
        store = AnalyticsStore()
        assert store is not None
        assert isinstance(store._data, dict)
        assert isinstance(store._channels, dict)

    def test_store_and_retrieve_video_metrics(self):
        store = AnalyticsStore()
        m = VideoMetrics(platform="youtube", video_id="test_v1", title="Test", views=100, likes=10, score=5.0)
        store.store_video_metrics(m)
        videos = store.get_video_metrics("youtube")
        assert any(v["video_id"] == "test_v1" for v in videos)

    def test_store_and_retrieve_channel_metrics(self):
        store = AnalyticsStore()
        ch = ChannelMetrics(platform="youtube", channel_id="test_ch1", channel_name="Test Channel", subscribers=1000)
        store.store_channel_metrics(ch)
        channels = store.get_channel_metrics("youtube")
        assert any(c["channel_id"] == "test_ch1" for c in channels)

    def test_get_top_videos(self):
        store = AnalyticsStore()
        store.store_video_metrics(VideoMetrics(platform="youtube", video_id="low", score=10))
        store.store_video_metrics(VideoMetrics(platform="youtube", video_id="high", score=90))
        top = store.get_top_videos(5)
        assert top[0]["video_id"] == "high"


class TestYouTubeAnalytics:
    def test_init(self):
        yt = YouTubeAnalytics()
        assert yt is not None

    def test_available_without_key(self):
        os.environ.pop("YOUTUBE_DATA_API_KEY", None)
        yt = YouTubeAnalytics()
        assert not yt.available

    @pytest.mark.anyio
    async def test_get_video_metrics_without_key(self):
        os.environ.pop("YOUTUBE_DATA_API_KEY", None)
        yt = YouTubeAnalytics()
        result = await yt.get_video_metrics("fake_id")
        assert result is None

    @pytest.mark.anyio
    async def test_get_channel_metrics_without_key(self):
        os.environ.pop("YOUTUBE_DATA_API_KEY", None)
        yt = YouTubeAnalytics()
        result = await yt.get_channel_metrics("fake_id")
        assert result is None


class TestTikTokAnalytics:
    def test_init(self):
        tt = TikTokAnalytics()
        assert tt is not None

    def test_available_without_key(self):
        os.environ.pop("TIKTOK_ACCESS_TOKEN", None)
        tt = TikTokAnalytics()
        assert not tt.available

    @pytest.mark.anyio
    async def test_get_video_metrics_without_key(self):
        os.environ.pop("TIKTOK_ACCESS_TOKEN", None)
        tt = TikTokAnalytics()
        result = await tt.get_video_metrics("fake_id")
        assert result is None


class TestInstagramAnalytics:
    def test_init(self):
        ig = InstagramAnalytics()
        assert ig is not None

    def test_available_without_key(self):
        os.environ.pop("INSTAGRAM_ACCESS_TOKEN", None)
        ig = InstagramAnalytics()
        assert not ig.available

    @pytest.mark.anyio
    async def test_get_video_metrics_without_key(self):
        os.environ.pop("INSTAGRAM_ACCESS_TOKEN", None)
        ig = InstagramAnalytics()
        result = await ig.get_video_metrics("fake_id")
        assert result is None


class TestAnalyticsEngine:
    def test_init(self):
        ae = AnalyticsEngine()
        assert ae is not None
        assert ae.youtube is not None
        assert ae.tiktok is not None
        assert ae.instagram is not None
        assert ae.store is not None

    def test_get_dashboard_empty(self):
        ae = AnalyticsEngine()
        dashboard = ae.get_dashboard_data()
        assert isinstance(dashboard, dict)
        assert "summary" in dashboard
        assert "top_videos" in dashboard
        assert "platforms" in dashboard
