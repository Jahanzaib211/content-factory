import os, json, pytest
from engines.scheduler import TimeOptimizer, RecurringScheduler, PlatformCropper, PostingSlot


class TestTimeOptimizer:
    def test_init(self):
        to = TimeOptimizer()
        assert to is not None

    @pytest.mark.anyio
    async def test_best_times_youtube(self):
        to = TimeOptimizer()
        times = await to.get_best_times("youtube")
        assert isinstance(times, list)
        assert len(times) > 0
        assert isinstance(times[0], PostingSlot)
        assert times[0].platform == "youtube"

    @pytest.mark.anyio
    async def test_best_times_tiktok(self):
        to = TimeOptimizer()
        times = await to.get_best_times("tiktok")
        assert len(times) > 0
        assert times[0].platform == "tiktok"

    @pytest.mark.anyio
    async def test_best_times_instagram(self):
        to = TimeOptimizer()
        times = await to.get_best_times("instagram")
        assert len(times) > 0
        assert times[0].platform == "instagram"

    @pytest.mark.anyio
    async def test_best_times_unknown_platform(self):
        to = TimeOptimizer()
        times = await to.get_best_times("unknown_platform")
        assert len(times) > 0


class TestRecurringScheduler:
    def test_init(self):
        rs = RecurringScheduler()
        assert rs is not None

    def test_create_and_list(self):
        rs = RecurringScheduler()
        sched = rs.create_schedule(
            template_id="talking_head",
            inputs={"topic": "AI news"},
            platforms=["youtube"],
            cron_expression="0 10 * * 1-5",
        )
        assert hasattr(sched, "schedule_id") or "schedule_id" in sched
        items = rs.list_schedules()
        assert len(items) >= 1

    def test_delete(self):
        rs = RecurringScheduler()
        sched = rs.create_schedule(
            template_id="talking_head",
            inputs={},
            platforms=["youtube"],
            cron_expression="0 10 * * *",
        )
        schedule_id = sched.schedule_id if hasattr(sched, "schedule_id") else sched["schedule_id"]
        rs.delete_schedule(schedule_id)
        items = rs.list_schedules()
        assert all(
            (s.schedule_id if hasattr(s, "schedule_id") else s["schedule_id"]) != schedule_id
            for s in items
        )

    def test_toggle(self):
        rs = RecurringScheduler()
        sched = rs.create_schedule(
            template_id="test",
            inputs={},
            platforms=["youtube"],
            cron_expression="0 10 * * *",
        )
        schedule_id = sched.schedule_id if hasattr(sched, "schedule_id") else sched["schedule_id"]
        rs.toggle_schedule(schedule_id, False)
        s = rs.get_schedule(schedule_id)
        assert not s.enabled

    def test_get_due_schedules(self):
        rs = RecurringScheduler()
        due = rs.get_due_schedules()
        assert isinstance(due, list)

    def test_calculate_next_run(self):
        rs = RecurringScheduler()
        # Every day at 10:00
        next_run = rs._calculate_next_run("0 10 * * *")
        assert "T10:00:00" in next_run
        # Mon/Wed/Fri at 9:00
        next_run2 = rs._calculate_next_run("0 9 * * 1,3,5")
        assert "T09:00:00" in next_run2
        # Invalid cron (too few fields) returns a future time
        next_run3 = rs._calculate_next_run("0 10")
        assert next_run3.endswith("Z")


class TestPlatformCropper:
    def test_init(self):
        pc = PlatformCropper()
        assert pc is not None

    def test_crop_for_platform_nonexistent(self):
        pc = PlatformCropper()
        with pytest.raises(RuntimeError):
            pc.crop_for_platform("/nonexistent/video.mp4", "tiktok", "/tmp/out.mp4")

    def test_aspect_ratios_defined(self):
        assert "tiktok" in PlatformCropper.ASPECT_RATIOS
        assert "youtube" in PlatformCropper.ASPECT_RATIOS
        assert "instagram_post" in PlatformCropper.ASPECT_RATIOS

    def test_crop_for_all_platforms_nonexistent(self):
        pc = PlatformCropper()
        results = pc.crop_for_all_platforms("/nonexistent.mp4", "/tmp", ["tiktok"])
        assert "tiktok" in results
        assert "error" in results["tiktok"]
