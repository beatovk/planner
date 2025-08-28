from core.normalize.attrs import infer_attrs, enrich_tags, _lower_strip_all


def test_lower_strip_all():
    """Test _lower_strip_all function"""
    result = _lower_strip_all(["  Test  ", "  ", "Another", None, ""])
    assert result == ["test", "another"]


def test_enrich_tags_basic():
    """Test basic tag enrichment"""
    tags = ["Music", "Jazz", "Live"]
    result = enrich_tags(tags)
    assert result == ["music", "jazz", "live"]


def test_enrich_tags_preserve_order():
    """Test that tag order is preserved"""
    tags = ["Zebra", "Apple", "Banana"]
    result = enrich_tags(tags)
    assert result == ["zebra", "apple", "banana"]


def test_enrich_tags_duplicates():
    """Test duplicate removal while preserving order"""
    tags = ["Music", "Jazz", "Music", "Live", "Jazz"]
    result = enrich_tags(tags)
    assert result == ["music", "jazz", "live"]


def test_enrich_tags_editor_labels():
    """Test editor labels are added at the end"""
    tags = ["Music", "Jazz"]
    editor_labels = ["Editor's Pick", "Featured"]
    result = enrich_tags(tags, editor_labels)
    assert result == ["music", "jazz", "editors_pick", "featured"]


def test_enrich_tags_editor_labels_no_duplicates():
    """Test editor labels don't duplicate existing tags"""
    tags = ["Music", "editors_pick"]
    editor_labels = ["Editor's Pick", "Featured"]
    result = enrich_tags(tags, editor_labels)
    assert result == ["music", "editors_pick", "featured"]


def test_infer_attrs_streetfood():
    """Test streetfood attribute inference"""
    attrs = infer_attrs("Amazing Street Food Market")
    assert attrs["streetfood"] is True
    assert attrs["market"] is True


def test_infer_attrs_rooftop():
    """Test rooftop attribute inference"""
    attrs = infer_attrs("Rooftop Sky Bar with Amazing Views")
    assert attrs["rooftop"] is True
    assert attrs["outdoor"] is False  # Not explicitly outdoor


def test_infer_attrs_outdoor():
    """Test outdoor attribute inference"""
    attrs = infer_attrs("Outdoor Garden Party in the Park")
    assert attrs["outdoor"] is True
    assert attrs["indoor"] is False


def test_infer_attrs_live_music():
    """Test live music attribute inference"""
    attrs = infer_attrs("Live Jazz Concert with Amazing Band")
    assert attrs["live_music"] is True


def test_infer_attrs_art():
    """Test art attribute inference"""
    attrs = infer_attrs("Art Exhibition at Modern Gallery")
    assert attrs["art"] is True
    assert attrs["indoor"] is True


def test_infer_attrs_culture():
    """Test culture attribute inference"""
    attrs = infer_attrs("Traditional Thai Culture Festival")
    assert attrs["culture"] is True


def test_infer_attrs_multiple():
    """Test multiple attributes inference"""
    attrs = infer_attrs("Outdoor Street Food Market with Live Music")
    assert attrs["streetfood"] is True
    assert attrs["market"] is True
    assert attrs["outdoor"] is True
    assert attrs["live_music"] is True


def test_infer_attrs_none():
    """Test no attributes inference"""
    attrs = infer_attrs("Generic Event Title")
    assert all(attrs.values()) is False


def test_infer_attrs_with_description():
    """Test attributes inference with description"""
    attrs = infer_attrs("Event Title", "Amazing rooftop bar with street food")
    assert attrs["rooftop"] is True
    assert attrs["streetfood"] is True


def test_enrich_tags_empty():
    """Test enrichment with empty inputs"""
    result = enrich_tags([])
    assert result == []

    result = enrich_tags(None)
    assert result == []

    result = enrich_tags([], [])
    assert result == []
