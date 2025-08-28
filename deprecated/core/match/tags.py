from __future__ import annotations
import re
from typing import Dict, Iterable, Set
from ..utils.text import norm_tag

# Базовые алиасы (минимальный набор под MVP; дополним по ходу)
ALIASES: Dict[str, Set[str]] = {
    "art": {"art", "exhibition", "gallery", "นิทรรศการ", "ศิลปะ"},
    "music": {"music", "live music", "concert", "gig", "ดนตรี"},
    "food": {"food", "street food", "streetfood", "อาหาร"},
    "market": {"market", "markets", "bazaar", "fair", "flea", "ตลาด", "ถนนคนเดิน"},
    "outdoor": {"outdoor", "outdoors", "outside", "กลางแจ้ง"},
    "rooftop": {"rooftop", "rooftop bar", "sky bar", "skybar"},
}

_TOKEN_SPLIT = re.compile(r"[^a-z0-9]+")

def _stem_en(w: str) -> str:
    # очень простой стемминг для мн. числа
    if len(w) > 3 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 2 and w.endswith("es"):
        return w[:-2]
    if len(w) > 1 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w

def _tokens_en(s: str) -> Set[str]:
    # не ломаем тайский: для EN токенизируем, тайский остаётся как фразы
    return {t for t in _TOKEN_SPLIT.split(s.lower()) if t}

class TagIndex:
    __slots__ = ("phrases", "tokens", "stems")
    def __init__(self, phrases: Set[str], tokens: Set[str], stems: Set[str]):
        self.phrases = phrases
        self.tokens = tokens
        self.stems = stems

def build_tag_index(tags: Iterable[str], attrs: dict | None = None) -> TagIndex:
    phrases: Set[str] = set()
    tokens: Set[str] = set()
    stems: Set[str] = set()
    for t in tags or []:
        nt = norm_tag(t)             # нормализованная фраза
        if not nt:
            continue
        phrases.add(nt)
        # токены и стемы — только для латиницы
        for tok in _tokens_en(nt):
            tokens.add(tok)
            stems.add(_stem_en(tok))
    # учёт бинарных атрибутов как «виртуальных тегов»
    a = attrs or {}
    if a.get("outdoor"): phrases.add("outdoor")
    if a.get("rooftop"): phrases.add("rooftop")
    if a.get("market"): phrases.add("market")
    if a.get("streetfood"): phrases.update({"street food", "streetfood"})
    return TagIndex(phrases, tokens, stems)

def _alias_set(q: str) -> Set[str]:
    qn = norm_tag(q)
    base = _stem_en(qn)
    return ALIASES.get(base, {qn, base})

def match_score(query: str, idx: TagIndex) -> int:
    """2 — точная фраза/алиас-фраза; 1 — токен/стем/алиас-токен; 0 — нет совпадения."""
    qn = norm_tag(query)
    if not qn:
        return 0
    # 1) прямые фразы
    if qn in idx.phrases:
        return 2
    # 2) алиас-фразы (в т.ч. тайские)
    aliases = _alias_set(qn)
    if idx.phrases.intersection(aliases):
        return 2
    # 3) токены/стемы без подстрок (чтобы 'art' != 'party')
    qtok = _tokens_en(qn)
    qstems = {_stem_en(t) for t in qtok} or {_stem_en(qn)}
    if idx.tokens.intersection(qtok) or idx.stems.intersection(qstems):
        return 1
    # 4) алиас-токены
    alias_tokens = set().union(*(_tokens_en(a) for a in aliases))
    alias_stems = {_stem_en(t) for t in alias_tokens}
    if idx.tokens.intersection(alias_tokens) or idx.stems.intersection(alias_stems):
        return 1
    return 0
