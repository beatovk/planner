from core.match.tags import build_tag_index, match_score
from core.utils.text import norm_tag


class Place:
    def __init__(self, tags, attrs=None):
        self.tags = tags
        self.attrs = attrs or {}


def test_music_matches_live_music_but_art_not_party():
    idx = build_tag_index(["live music"], {})
    assert match_score("music", idx) >= 1
    assert match_score("live music", idx) >= 2
    idx2 = build_tag_index(["party"], {})
    assert match_score("art", idx2) == 0  # нет ложного совпадения


def test_markets_matches_market_and_thai_alias():
    idx = build_tag_index(["market"], {})
    assert match_score("markets", idx) >= 1
    idx_th = build_tag_index(["ตลาด"], {})
    assert match_score("markets", idx_th) >= 1  # алиас тайский


def test_food_matches_street_food_phrase_and_tokens():
    idx = build_tag_index(["street food"], {})
    assert match_score("food", idx) >= 1
    assert match_score("street food", idx) >= 2


def test_attrs_cover_outdoor_and_rooftop():
    idx = build_tag_index([], {"outdoor": True, "rooftop": True})
    assert match_score("outdoor", idx) >= 1
    assert match_score("rooftop", idx) >= 1


def test_stemming_works_for_plural_forms():
    idx = build_tag_index(["outdoors", "markets"], {})
    assert match_score("outdoor", idx) >= 1
    assert match_score("market", idx) >= 1


def test_exact_phrase_matching():
    idx = build_tag_index(["live music", "thai food"], {})
    assert match_score("live music", idx) == 2
    assert match_score("thai food", idx) == 2
    assert match_score("music", idx) >= 1
    assert match_score("food", idx) >= 1


def test_no_false_positives():
    idx = build_tag_index(["party", "nightclub"], {})
    assert match_score("art", idx) == 0
    assert match_score("market", idx) == 0
    assert match_score("outdoor", idx) == 0
