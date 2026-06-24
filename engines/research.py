"""
Research Engine — trend scanning, keyword research, SEO scoring.

Provides vidIQ-style intelligence for the one-click pipeline:
  - TrendScanner: Google Trends + YouTube trending topics
  - KeywordResearch: search volume, competition, opportunity scoring
  - SEOScorer: 0-100 score for any topic/keyword
  - IdeaGenerator: AI-powered video idea generation from trends

All classes are async and use httpx for HTTP calls.
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

import httpx

log = logging.getLogger(__name__)

# ── Data Models ───────────────────────────────────────────────────────


@dataclass
class TrendTopic:
    title: str
    traffic_level: str  # "rising", "breakout", "stable", "declining"
    search_volume: int  # estimated monthly searches
    related_queries: List[str] = field(default_factory=list)
    source: str = "google_trends"
    score: float = 0.0  # 0-100 SEO score


@dataclass
class KeywordResult:
    keyword: str
    search_volume: int
    competition: float  # 0.0 (easy) to 1.0 (impossible)
    score: float  # 0-100 opportunity score
    cpc: float = 0.0  # cost per click (ads indicator)
    related_keywords: List[str] = field(default_factory=list)
    trend_direction: str = "stable"  # rising, stable, declining


@dataclass
class VideoIdea:
    title: str
    hook: str
    description: str
    tags: List[str]
    estimated_views: str  # "low", "medium", "high", "viral"
    score: float  # 0-100
    source_trend: str = ""
    platform: str = "youtube"


# ── Google Trends (via pytrends or HTTP fallback) ────────────────────


class TrendScanner:
    """Scan Google Trends for rising topics in any niche."""

    def __init__(self):
        self._pytrends = None
        self._try_import_pytrends()

    def _try_import_pytrends(self):
        try:
            from pytrends.request import TrendReq
            self._pytrends = TrendReq(hl="en-US", tz=360)
            log.info("TrendScanner: pytrends loaded")
        except ImportError:
            log.warning("TrendScanner: pytrends not installed, using HTTP fallback")

    async def get_trending_topics(
        self,
        niche: str = "",
        timeframe: str = "today 1-month",
        geo: str = "",
    ) -> List[TrendTopic]:
        """Get trending topics for a niche. Uses pytrends if available, else HTTP."""
        if self._pytrends:
            return await self._get_trends_pytrends(niche, timeframe, geo)
        return await self._get_trends_http(niche)

    async def _get_trends_pytrends(
        self, keyword: str, timeframe: str, geo: str
    ) -> List[TrendTopic]:
        """Use pytrends to get real-time trend data."""
        loop = asyncio.get_running_loop()

        def _fetch():
            try:
                self._pytrends.build_payload(
                    [keyword] if keyword else ["youtube"],
                    cat=0,
                    timeframe=timeframe,
                    geo=geo,
                )
                # Rising queries
                rising = self._pytrends.related_queries()
                topics = []

                if keyword and keyword in rising:
                    rq = rising[keyword]
                    if rq.get("rising") is not None:
                        for _, row in rq["rising"].head(10).iterrows():
                            topics.append(TrendTopic(
                                title=row.get("query", ""),
                                traffic_level=row.get("value", "rising"),
                                search_volume=int(row.get("value", 100)),
                                source="google_trends",
                            ))

                # Interest over time for the keyword itself
                iot = self._pytrends.interest_over_time()
                if not iot.empty and keyword in iot.columns:
                    recent = iot[keyword].iloc[-4:].mean()
                    baseline = iot[keyword].iloc[:-4].mean() if len(iot) > 4 else recent
                    if baseline > 0:
                        growth = ((recent - baseline) / baseline) * 100
                        topics.insert(0, TrendTopic(
                            title=keyword,
                            traffic_level="rising" if growth > 10 else "stable",
                            search_volume=int(recent * 100),
                            source="google_trends",
                            score=min(100, max(0, growth + 50)),
                        ))

                return topics
            except Exception as e:
                log.warning(f"pytrends error: {e}")
                return []

        return await loop.run_in_executor(None, _fetch)

    async def _get_trends_http(self, niche: str) -> List[TrendTopic]:
        """Fallback: scrape Google Trends trending searches page."""
        topics = []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Try trending searches page (daily trends)
                r = await client.get(
                    "https://trends.google.com/trends/trendingsearches/daily",
                    params={"geo": "US"},
                    follow_redirects=True,
                )
                if r.status_code == 200:
                    # Parse title keywords from the HTML
                    import re
                    # Google Trends daily trends page has <div class="mZ3RIc"> for titles
                    titles = re.findall(r'class="mZ3RIc"[^>]*>([^<]+)<', r.text)
                    for title in titles[:10]:
                        topics.append(TrendTopic(
                            title=title.strip(),
                            traffic_level="rising",
                            search_volume=5000,  # estimated from trending status
                            source="google_trends_fallback",
                        ))
                    if not topics:
                        # Try alternative parsing: look for search terms in JSON
                        json_match = re.search(r'window.__INITIAL_STATE__\s*=\s*({.*?});', r.text)
                        if json_match:
                            import json
                            try:
                                state = json.loads(json_match.group(1))
                                for item in state.get("dailyTrends", {}).get("trendCards", [])[:10]:
                                    topics.append(TrendTopic(
                                        title=item.get("title", ""),
                                        traffic_level="rising",
                                        search_volume=item.get("searchVolume", 5000),
                                        source="google_trends_fallback",
                                    ))
                            except (json.JSONDecodeError, KeyError):
                                pass
        except Exception as e:
            log.warning(f"Trend HTTP fallback failed: {e}")
        return topics

    async def get_youtube_trending(self, region_code: str = "US", category_id: str = "0") -> List[TrendTopic]:
        """Get trending videos from YouTube Data API v3."""
        api_key = os.getenv("YOUTUBE_DATA_API_KEY", "")
        if not api_key:
            log.info("TrendScanner: no YOUTUBE_DATA_API_KEY, skipping YouTube trending")
            return []

        topics = []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(
                    "https://www.googleapis.com/youtube/v3/videos",
                    params={
                        "part": "snippet,statistics",
                        "chart": "mostPopular",
                        "regionCode": region_code,
                        "categoryId": category_id,
                        "maxResults": 20,
                        "key": api_key,
                    },
                )
                r.raise_for_status()
                data = r.json()
                for item in data.get("items", []):
                    snippet = item.get("snippet", {})
                    stats = item.get("statistics", {})
                    topics.append(TrendTopic(
                        title=snippet.get("title", ""),
                        traffic_level="rising",
                        search_volume=int(stats.get("viewCount", 0)),
                        related_queries=[snippet.get("channelTitle", "")],
                        source="youtube_trending",
                    ))
        except Exception as e:
            log.warning(f"YouTube trending fetch failed: {e}")
        return topics


# ── Keyword Research ─────────────────────────────────────────────────


class KeywordResearch:
    """Keyword research with search volume, competition, and scoring."""

    def __init__(self):
        self._trends = TrendScanner()

    async def research_keyword(self, keyword: str) -> KeywordResult:
        """Full keyword research: volume, competition, score."""
        # Get Google Trends data
        topics = await self._trends.get_trending_topics(keyword)
        trend_volume = topics[0].search_volume if topics else 0

        # Get related keywords via Google Suggestions (counts as competition signal)
        related = await self._get_google_suggestions(keyword)

        # Estimate competition from keyword length + suggestion count
        competition = self._estimate_competition(keyword, len(related))

        # Estimate volume from trends data + keyword characteristics
        volume = trend_volume if trend_volume > 0 else self._estimate_volume(keyword, len(related))

        # Calculate opportunity score
        score = self._calculate_score(volume, competition)

        return KeywordResult(
            keyword=keyword,
            search_volume=volume,
            competition=competition,
            score=score,
            related_keywords=related,
            trend_direction=topics[0].traffic_level if topics else "stable",
        )

    async def research_bulk(self, keywords: List[str]) -> List[KeywordResult]:
        """Research multiple keywords concurrently."""
        tasks = [self.research_keyword(kw) for kw in keywords]
        return await asyncio.gather(*tasks, return_exceptions=False)

    def _estimate_competition(self, keyword: str, suggestion_count: int = 0) -> float:
        """Estimate competition from keyword characteristics + suggestion count.

        More Google autocomplete suggestions = more competition (people are searching).
        Longer keywords = less competition (long-tail).
        """
        # Base competition from keyword length
        words = keyword.split()
        if len(words) == 1:
            base = 0.85
        elif len(words) == 2:
            base = 0.65
        elif len(words) == 3:
            base = 0.45
        else:
            base = 0.25

        # Adjust based on suggestion count (more suggestions = more competition)
        # 0 suggestions = low comp, 8 suggestions = high comp
        suggestion_boost = min(0.15, suggestion_count * 0.02)

        return min(0.95, base + suggestion_boost)

    def _estimate_volume(self, keyword: str, suggestion_count: int = 0) -> int:
        """Estimate volume from keyword length + suggestion count.

        More suggestions = higher search volume.
        Shorter keywords = higher volume.
        """
        words = keyword.split()
        if len(words) == 1:
            base = 100000
        elif len(words) == 2:
            base = 50000
        elif len(words) == 3:
            base = 15000
        else:
            base = 5000

        # Boost from suggestion count (more suggestions = more searches)
        volume_boost = suggestion_count * 2000
        return base + volume_boost

    def _calculate_score(self, volume: int, competition: float) -> float:
        """Calculate 0-100 opportunity score. High volume + low competition = high score."""
        if competition == 0:
            competition = 0.01
        # Score = volume_normalized / competition
        vol_norm = min(volume / 1000, 100)  # cap at 100
        score = (vol_norm / (competition * 100)) * 100
        return min(100, max(0, score))

    async def _get_google_suggestions(self, keyword: str) -> List[str]:
        """Get Google autocomplete suggestions."""
        suggestions = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    "https://suggestqueries.google.com/complete/search",
                    params={"client": "firefox", "q": keyword},
                )
                if r.status_code == 200:
                    data = r.json()
                    if len(data) > 1:
                        suggestions = data[1][:8]
        except Exception:
            pass
        return suggestions


# ── SEO Scorer ───────────────────────────────────────────────────────


class SEOScorer:
    """Score any topic 0-100 for YouTube SEO potential."""

    def __init__(self):
        self._keyword_research = KeywordResearch()

    async def score_topic(self, topic: str) -> Dict[str, Any]:
        """Score a topic and return breakdown."""
        kr = await self._keyword_research.research_keyword(topic)

        # Factor 1: Search volume (0-30 points)
        vol_score = min(30, (kr.search_volume / 100000) * 30)

        # Factor 2: Competition inverse (0-30 points)
        comp_score = (1 - kr.competition) * 30

        # Factor 3: Trend direction (0-20 points)
        trend_map = {"breakout": 20, "rising": 15, "stable": 10, "declining": 0}
        trend_score = trend_map.get(kr.trend_direction, 10)

        # Factor 4: Keyword length bonus (long-tail = easier to rank) (0-20 points)
        words = topic.split()
        length_score = min(20, len(words) * 5)

        total = vol_score + comp_score + trend_score + length_score

        return {
            "topic": topic,
            "score": round(total, 1),
            "breakdown": {
                "search_volume": {"score": round(vol_score, 1), "value": kr.search_volume},
                "competition": {"score": round(comp_score, 1), "value": kr.competition},
                "trend": {"score": round(trend_score, 1), "direction": kr.trend_direction},
                "long_tail": {"score": round(length_score, 1), "word_count": len(words)},
            },
            "related_keywords": kr.related_keywords,
            "recommendation": self._get_recommendation(total),
        }

    def _get_recommendation(self, score: float) -> str:
        if score >= 80:
            return "Excellent topic — high demand, low competition. Create immediately."
        elif score >= 60:
            return "Good topic — solid opportunity. Worth creating."
        elif score >= 40:
            return "Moderate topic — consider differentiating angle."
        elif score >= 20:
            return "Competitive topic — needs strong hook to stand out."
        else:
            return "Saturated topic — consider a long-tail variation."


# ── Idea Generator ───────────────────────────────────────────────────


class IdeaGenerator:
    """AI-powered video idea generation from trends + channel data."""

    def __init__(self):
        self._trends = TrendScanner()
        self._scorer = SEOScorer()

    async def generate_ideas(
        self,
        niche: str = "",
        channel_description: str = "",
        count: int = 5,
    ) -> List[VideoIdea]:
        """Generate video ideas based on trends + niche."""
        # Get trending topics
        trending = await self._trends.get_trending_topics(niche)

        # Generate ideas from trends using LLM
        ideas = await self._generate_via_llm(niche, channel_description, trending, count)

        # Score each idea
        for idea in ideas:
            scored = await self._scorer.score_topic(idea.title)
            idea.score = scored["score"]

        # Sort by score descending
        ideas.sort(key=lambda x: x.score, reverse=True)
        return ideas[:count]

    async def _generate_via_llm(
        self,
        niche: str,
        channel_desc: str,
        trends: List[TrendTopic],
        count: int,
    ) -> List[VideoIdea]:
        """Use LLM to generate ideas from trend data."""
        try:
            from engines.llm import LiteLLMRouterEngine
            from engines import get_active, EngineCapability

            eng = None
            try:
                eng = get_active(EngineCapability.LLM)
            except RuntimeError:
                eng = LiteLLMRouterEngine()

            trend_text = "\n".join(
                f"- {t.title} ({t.traffic_level}, ~{t.search_volume} searches)"
                for t in trends[:10]
            ) or "No trend data available"

            prompt = f"""Generate {count} YouTube video ideas for this niche: {niche or 'general content'}
Channel context: {channel_desc or 'No channel description'}

Current trending topics:
{trend_text}

For each idea, return a JSON array with objects containing:
- "title": compelling YouTube title (max 60 chars)
- "hook": opening hook sentence (max 15 words)
- "description": 2-sentence video description
- "tags": 5 relevant tags
- "estimated_views": "low", "medium", "high", or "viral"
- "source_trend": which trending topic inspired this

Return ONLY the JSON array, no other text."""

            if hasattr(eng, "generate"):
                result = await eng.generate(prompt)
                text = result.get("text", "") if isinstance(result, dict) else str(result)
            elif hasattr(eng, "chat"):
                result = await eng.chat(prompt)
                text = result.get("content", "") if isinstance(result, dict) else str(result)
            else:
                return self._fallback_ideas(niche, count)

            # Parse JSON from response
            import json
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            elif not text.strip().startswith("["):
                # Try to find array in response
                start = text.find("[")
                end = text.rfind("]") + 1
                if start >= 0 and end > start:
                    text = text[start:end]

            ideas_data = json.loads(text)
            return [
                VideoIdea(
                    title=item.get("title", f"{niche} video"),
                    hook=item.get("hook", ""),
                    description=item.get("description", ""),
                    tags=item.get("tags", []),
                    estimated_views=item.get("estimated_views", "medium"),
                    score=0,  # scored later
                    source_trend=item.get("source_trend", ""),
                )
                for item in ideas_data
            ]
        except Exception as e:
            log.warning(f"LLM idea generation failed: {e}")
            return self._fallback_ideas(niche, count)

    def _fallback_ideas(self, niche: str, count: int) -> List[VideoIdea]:
        """Fallback ideas when LLM is unavailable. Uses niche-specific templates."""
        import random
        templates = [
            {"title": f"10 {niche} Tips Nobody Tells You", "hook": f"Here's what most people get wrong about {niche}", "estimated_views": "high", "tags": [niche, "tips", "tutorial", "2026", "guide"]},
            {"title": f"I Tried {niche} for 30 Days — Here's What Happened", "hook": f"I spent 30 days nonstop on {niche}", "estimated_views": "viral", "tags": [niche, "challenge", "30days", "experiment", "results"]},
            {"title": f"The Truth About {niche} Nobody Wants to Hear", "hook": f"Everyone lies about {niche}", "estimated_views": "high", "tags": [niche, "truth", "myths", "debunked", "reality"]},
            {"title": f"{niche} in 2026: What's Changed", "hook": f"{niche} looks completely different now", "estimated_views": "medium", "tags": [niche, "2026", "update", "trends", "changes"]},
            {"title": f"Why {niche} is Dead (And What's Next)", "hook": f"{niche} as we know it is over", "estimated_views": "viral", "tags": [niche, "future", "prediction", "dead", "next"]},
            {"title": f"The {niche} Starter Kit for Complete Beginners", "hook": f"Everything you need to start with {niche}", "estimated_views": "medium", "tags": [niche, "beginner", "starter", "basics", "入门"]},
            {"title": f"How I Made $10K with {niche}", "hook": f"This {niche} strategy changed everything", "estimated_views": "viral", "tags": [niche, "money", "income", "strategy", "success"]},
            {"title": f"{niche} vs. The Competition: Which is Better?", "hook": f"I tested every {niche} option so you don't have to", "estimated_views": "high", "tags": [niche, "comparison", "review", "versus", "best"]},
            {"title": f"The Biggest {niche} Mistakes (And How to Fix Them)", "hook": f"Stop making these {niche} mistakes today", "estimated_views": "high", "tags": [niche, "mistakes", "fix", "improve", "common"]},
            {"title": f"{niche}: The Ultimate Guide for 2026", "hook": f"This is everything I wish I knew about {niche}", "estimated_views": "high", "tags": [niche, "guide", "ultimate", "2026", "comprehensive"]},
        ]
        random.shuffle(templates)
        return [
            VideoIdea(
                title=t["title"],
                hook=t["hook"],
                description=f"A comprehensive video about {t['title'].lower()}. Perfect for {niche} enthusiasts looking to level up.",
                tags=t["tags"],
                estimated_views=t["estimated_views"],
                score=random.randint(40, 65),
            )
            for t in templates[:count]
        ]


__all__ = [
    "TrendScanner",
    "KeywordResearch",
    "SEOScorer",
    "IdeaGenerator",
    "TrendTopic",
    "KeywordResult",
    "VideoIdea",
]
