import sys, types, pytest

# Stub pytrends so tests run without it installed
pytrends_mod = types.ModuleType("pytrends")
pytrends_req = types.ModuleType("pytrends.request")
pytrends_req.TrendReq = type("TrendReq", (), {"__init__": lambda *a, **kw: None})
pytrends_mod.request = pytrends_req
sys.modules["pytrends"] = pytrends_mod
sys.modules["pytrends.request"] = pytrends_req

from engines.research import TrendScanner, KeywordResearch, SEOScorer, IdeaGenerator, TrendTopic, KeywordResult, VideoIdea


class TestTrendScanner:
    def test_init(self):
        ts = TrendScanner()
        assert ts is not None

    @pytest.mark.anyio
    async def test_get_trending_topics(self):
        ts = TrendScanner()
        result = await ts.get_trending_topics("AI")
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], TrendTopic)

    @pytest.mark.anyio
    async def test_youtube_trending_no_key(self):
        ts = TrendScanner()
        result = await ts.get_youtube_trending()
        assert isinstance(result, list)


class TestKeywordResearch:
    def test_init(self):
        kr = KeywordResearch()
        assert kr is not None

    def test_estimate_competition(self):
        kr = KeywordResearch()
        assert kr._estimate_competition("python") == 0.9
        assert kr._estimate_competition("python programming") == 0.7
        assert kr._estimate_competition("python web tutorial") == 0.5
        assert kr._estimate_competition("best python web framework 2026") == 0.3

    def test_calculate_score(self):
        kr = KeywordResearch()
        score = kr._calculate_score(50000, 0.5)
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100

    def test_estimate_volume(self):
        kr = KeywordResearch()
        assert kr._estimate_volume("python") == 100000
        assert kr._estimate_volume("python programming") == 50000


class TestSEOScorer:
    def test_init(self):
        ss = SEOScorer()
        assert ss is not None

    def test_get_recommendation(self):
        ss = SEOScorer()
        assert "Excellent" in ss._get_recommendation(90)
        assert "Good" in ss._get_recommendation(70)
        assert "Moderate" in ss._get_recommendation(50)
        assert "Competitive" in ss._get_recommendation(30)
        assert "Saturated" in ss._get_recommendation(10)


class TestIdeaGenerator:
    def test_init(self):
        ig = IdeaGenerator()
        assert ig is not None

    def test_fallback_ideas(self):
        ig = IdeaGenerator()
        ideas = ig._fallback_ideas("AI", 3)
        assert isinstance(ideas, list)
        assert len(ideas) == 3
        assert all(isinstance(i, VideoIdea) for i in ideas)
        assert all(i.score == 50 for i in ideas)

    def test_fallback_ideas_different_niches(self):
        ig = IdeaGenerator()
        ideas1 = ig._fallback_ideas("cooking", 2)
        ideas2 = ig._fallback_ideas("fitness", 2)
        assert ideas1[0].title != ideas2[0].title


class TestDataModels:
    def test_trend_topic(self):
        t = TrendTopic(title="AI", traffic_level="rising", search_volume=5000)
        assert t.title == "AI"
        assert t.source == "google_trends"

    def test_keyword_result(self):
        k = KeywordResult(keyword="test", search_volume=1000, competition=0.5, score=75)
        assert k.keyword == "test"

    def test_video_idea(self):
        v = VideoIdea(title="Test", hook="Hook", description="Desc", tags=["a"], estimated_views="high", score=80)
        assert v.title == "Test"
