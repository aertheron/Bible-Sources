"""Canonical request labels with explicitly separate native source references."""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from .store import StudyError, config


def lookup_key(value):
    return re.sub(r"[\s_.-]+", "", "".join(c for c in unicodedata.normalize("NFD", value.lower()) if not unicodedata.combining(c)))


@dataclass(frozen=True)
class Passage:
    book: str
    start_chapter: int
    start_verse: int
    end_chapter: int
    end_verse: int

    def contains(self, chapter, verse):
        return (self.start_chapter, self.start_verse) <= (int(chapter), int(verse)) <= (self.end_chapter, self.end_verse)

    def as_dict(self):
        return dict(book=self.book, start_chapter=self.start_chapter, start_verse=self.start_verse, end_chapter=self.end_chapter, end_verse=self.end_verse)


class References:
    def __init__(self):
        self.books = config("books")["books"]
        self.aliases = {lookup_key(alias): book for book, row in self.books.items() for alias in [book, row["name"], *row["aliases"]]}
        self.verses = config("base-references")["verses"]

    def book(self, label):
        found = self.aliases.get(lookup_key(label))
        if not found:
            raise StudyError("unknown_book", f"Unrecognized book: {label}")
        return found

    def last(self, book, chapter):
        values = self.verses[book].get(str(chapter))
        if not values:
            raise StudyError("invalid_chapter", f"{self.books[book]['name']} has no chapter {chapter} in the selected base.")
        return max(values)

    def parse(self, reference, allow_book=False):
        if not isinstance(reference, str) or len(reference) > 240:
            raise StudyError("reference", "Supply a short Bible reference.")
        text = re.sub(r"[–—]", "-", reference.strip())
        if allow_book:
            stripped = re.sub(r"^(?:the\s+)?(?:whole(?:\s+of)?|all(?:\s+of)?|hele|heel)\s+", "", text, flags=re.I)
            if lookup_key(stripped) in self.aliases:
                book = self.book(stripped)
                end = max(map(int, self.verses[book]))
                return Passage(book, 1, 1, end, self.last(book, end))
        m = re.fullmatch(r"(.+?)\s+(\d+)(?::(\d+))?(?:\s*-\s*(\d+)(?::(\d+))?)?", text)
        if not m:
            raise StudyError("reference", "Use a reference such as Genesis 1:1-2:3 or Romans 12:1-2.")
        book = self.book(m[1]); sc = int(m[2]); sv = int(m[3] or 1)
        if m[4] is None:
            ec = sc; ev = int(m[3]) if m[3] else self.last(book, sc)
        elif m[5] is not None:
            ec = int(m[4]); ev = int(m[5])
        elif m[3] is not None:
            ec = sc; ev = int(m[4])
        else:
            ec = int(m[4]); ev = self.last(book, ec)
        if sc < 1 or ec < 1 or sv < 1 or ev < 1 or sv > self.last(book, sc) or ev > self.last(book, ec) or (sc, sv) > (ec, ev):
            raise StudyError("invalid_reference", "The requested chapter/verse range is invalid for the named base text.")
        return Passage(book, sc, sv, ec, ev)

    def label(self, p):
        name = self.books[p.book]["name"]
        if p.start_chapter == p.end_chapter:
            if p.start_verse == 1 and p.end_verse == self.last(p.book, p.start_chapter):
                return f"{name} {p.start_chapter}"
            end = "" if p.start_verse == p.end_verse else f"-{p.end_verse}"
            return f"{name} {p.start_chapter}:{p.start_verse}{end}"
        return f"{name} {p.start_chapter}:{p.start_verse}-{p.end_chapter}:{p.end_verse}"

    def scope(self, p):
        if p.end_chapter == p.start_chapter:
            return p
        if p.end_chapter == p.start_chapter + 1:
            tail = self.last(p.book, p.start_chapter) - p.start_verse + 1
            head = p.end_verse
            both_full = p.start_verse == 1 and head == self.last(p.book, p.end_chapter)
            if min(tail, head) <= 5 and not both_full:
                return p
        raise StudyError("portion_scope", "This stage accepts one chapter plus a few adjacent verses. Plan the request into sequential portions first.")

    def count(self, p):
        return sum(len([v for v in self.verses[p.book][str(c)] if p.contains(c, v)]) for c in range(p.start_chapter, p.end_chapter + 1))

    def portions(self, reference):
        p = self.parse(reference, allow_book=True)
        policy = config("chunking")
        try:
            self.scope(p)
            if self.count(p) <= policy["soft_max_verses"]:
                return [{"reference": self.label(p), "boundary_status": "requested_bounded_portion"}]
        except StudyError:
            pass
        out = []
        for c in range(p.start_chapter, p.end_chapter + 1):
            start = p.start_verse if c == p.start_chapter else 1
            end = p.end_verse if c == p.end_chapter else self.last(p.book, c)
            if end - start + 1 <= policy["soft_max_verses"]:
                out.append({"reference": self.label(Passage(p.book, c, start, c, end)), "boundary_status": "chapter_or_requested_boundary"})
                continue
            units = policy["chapter_units"].get(f"{p.book}:{c}")
            if units:
                bounds = [(max(start, a), min(end, b)) for a, b in units if b >= start and a <= end]
                status = "curated_literary_boundary"
            else:
                bounds = [(a, min(a + policy["fallback_verses"] - 1, end)) for a in range(start, end + 1, policy["fallback_verses"])]
                status = "provisional_size_boundary_review_discourse"
            out.extend({"reference": self.label(Passage(p.book, c, a, c, b)), "boundary_status": status} for a, b in bounds)
        return out

    def study_scope(self, reference, exact=False):
        requested = self.parse(reference, allow_book=True)
        candidates = []
        for unit in config("literary-units")["units"]:
            u = self.parse(unit["reference"])
            if unit.get("auto_expand") and u.book == requested.book and (u.start_chapter, u.start_verse) <= (requested.start_chapter, requested.start_verse) and (requested.end_chapter, requested.end_verse) <= (u.end_chapter, u.end_verse):
                candidates.append((self.count(u), unit, u))
        selected = min(candidates, key=lambda item: item[0]) if candidates else None
        target = requested if exact or selected is None else selected[2]
        return {"requested_reference": self.label(requested), "study_reference": self.label(target), "expanded": target != requested, "selection": "exact_requested_scope" if exact else "curated_literary_unit" if selected else "host_literary_review_required", "literary_unit_reference": selected[1]["reference"] if selected else None, "literary_unit_title": selected[1]["title"] if selected else None, "instruction": "Explain the chosen literary boundary before studying it, including added verses and why they complete the argument or scene. For example: You asked for Genesis 1; I will study Genesis 1:1–2:3 because the seventh day completes this creation account. Complete the selected unit using bounded sequential retrieval. The unit index is not exhaustive: review unindexed boundaries from source discourse, then replan a defensible adjusted range with the exact option. Honour an explicit request to study only the named verses; still explain the surrounding unit."}

    def next(self, current):
        p = self.parse(current)
        last = self.last(p.book, p.end_chapter)
        after = (p.end_chapter, p.end_verse + 1) if p.end_verse < last else (p.end_chapter + 1, 1)
        if str(after[0]) not in self.verses[p.book]:
            return None

        # Complete a curated literary unit before defaulting to a chapter break.
        # Never expand the current study or exceed the bounded source limits.
        relevant = []
        for unit in config("literary-units")["units"]:
            u = self.parse(unit["reference"])
            if u.book == p.book and (u.start_chapter, u.start_verse) <= (p.start_chapter, p.start_verse) and (p.end_chapter, p.end_verse) <= (u.end_chapter, u.end_verse) and after <= (u.end_chapter, u.end_verse):
                relevant.append((self.count(u), unit, u))
        for _, unit, u in sorted(relevant, key=lambda item: item[0]):
            remainder = Passage(p.book, after[0], after[1], u.end_chapter, u.end_verse)
            try:
                self.scope(remainder)
            except StudyError as error:
                if error.code != "portion_scope":
                    raise
                continue
            if self.count(remainder) <= config("chunking")["soft_max_verses"]:
                return {"reference": self.label(remainder), "boundary_status": "curated_literary_continuation", "literary_unit_reference": unit["reference"], "literary_unit_title": unit["title"]}

        # Fallback to the original bounded chapter/curated-chunk logic.
        if p.end_verse < last:
            rest = self.label(Passage(p.book, p.end_chapter, p.end_verse + 1, p.end_chapter, last))
        else:
            rest = f"{self.books[p.book]['name']} {after[0]}"
        return self.portions(rest)[0]
