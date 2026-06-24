import pytest, os


@pytest.fixture
def tmp_gallery(tmp_path):
    from engines.gallery import GalleryStore
    store = GalleryStore(gallery_dir=str(tmp_path / "gallery"), gallery_file=str(tmp_path / "gallery.json"))
    return store


class TestGalleryStore:
    def test_init(self, tmp_gallery):
        assert tmp_gallery is not None
        assert tmp_gallery.get_stats()["total_items"] == 0

    def test_add_item(self, tmp_gallery):
        item = tmp_gallery.add(
            title="Test Video",
            caption="A test video",
            source="clip",
            template_id="clip_generator",
            file_path="/tmp/test.mp4",
            file_type="video",
            file_size=1024,
            tags=["test", "demo"],
        )
        assert item.title == "Test Video"
        assert item.source == "clip"
        assert item.status == "ready"
        assert item.tags == ["test", "demo"]
        assert item.id is not None

    def test_get_item(self, tmp_gallery):
        item = tmp_gallery.add(
            title="Get Test", caption="", source="factory",
            template_id="short_form", file_path="/tmp/test.mp4", file_type="video",
        )
        retrieved = tmp_gallery.get(item.id)
        assert retrieved is not None
        assert retrieved.title == "Get Test"

    def test_get_nonexistent(self, tmp_gallery):
        assert tmp_gallery.get("nonexistent-id") is None

    def test_list_items(self, tmp_gallery):
        tmp_gallery.add(title="V1", caption="", source="clip", template_id="x", file_path="/a.mp4", file_type="video")
        tmp_gallery.add(title="V2", caption="", source="factory", template_id="y", file_path="/b.mp4", file_type="video")
        items = tmp_gallery.list_items()
        assert len(items) == 2

    def test_list_filter_source(self, tmp_gallery):
        tmp_gallery.add(title="Clip", caption="", source="clip", template_id="x", file_path="/a.mp4", file_type="video")
        tmp_gallery.add(title="Factory", caption="", source="factory", template_id="y", file_path="/b.mp4", file_type="video")
        items = tmp_gallery.list_items(source="clip")
        assert len(items) == 1
        assert items[0].source == "clip"

    def test_list_filter_search(self, tmp_gallery):
        tmp_gallery.add(title="Cat Video", caption="Funny cats", source="clip", template_id="x", file_path="/a.mp4", file_type="video")
        tmp_gallery.add(title="Dog Video", caption="Cute dogs", source="clip", template_id="y", file_path="/b.mp4", file_type="video")
        items = tmp_gallery.list_items(search="cat")
        assert len(items) == 1
        assert "Cat" in items[0].title

    def test_update_caption(self, tmp_gallery):
        item = tmp_gallery.add(title="Edit Me", caption="old", source="clip", template_id="x", file_path="/a.mp4", file_type="video")
        updated = tmp_gallery.update(item.id, caption="new caption")
        assert updated is not None
        assert updated.caption == "new caption"

    def test_mark_published(self, tmp_gallery):
        item = tmp_gallery.add(title="Publish", caption="", source="clip", template_id="x", file_path="/a.mp4", file_type="video")
        tmp_gallery.mark_published(item.id, platform="youtube")
        stored = tmp_gallery.get(item.id)
        assert stored.status == "published"
        assert "youtube" in stored.platforms

    def test_delete_item(self, tmp_gallery):
        item = tmp_gallery.add(title="Delete Me", caption="", source="clip", template_id="x", file_path="/a.mp4", file_type="video")
        deleted = tmp_gallery.delete(item.id)
        assert deleted is True
        assert tmp_gallery.get(item.id) is None
        assert tmp_gallery.get_stats()["total_items"] == 0

    def test_delete_nonexistent(self, tmp_gallery):
        assert tmp_gallery.delete("no-such-id") is False

    def test_stats(self, tmp_gallery):
        tmp_gallery.add(title="V1", caption="", source="clip", template_id="x", file_path="/a.mp4", file_type="video")
        tmp_gallery.add(title="I1", caption="", source="factory", template_id="y", file_path="/b.png", file_type="image")
        stats = tmp_gallery.get_stats()
        assert stats["total_items"] == 2
        assert stats["by_source"]["clip"] == 1
        assert stats["by_source"]["factory"] == 1

    def test_persistence(self, tmp_path):
        from engines.gallery import GalleryStore
        gallery_dir = str(tmp_path / "gallery")
        gallery_file = str(tmp_path / "gallery.json")
        s1 = GalleryStore(gallery_dir=gallery_dir, gallery_file=gallery_file)
        item = s1.add(title="Persist", caption="", source="clip", template_id="x", file_path="/a.mp4", file_type="video")
        s2 = GalleryStore(gallery_dir=gallery_dir, gallery_file=gallery_file)
        assert s2.get(item.id) is not None
        assert s2.get(item.id).title == "Persist"
