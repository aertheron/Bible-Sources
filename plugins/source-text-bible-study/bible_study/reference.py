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

    def next(self, current):
        p = self.parse(current)
        last = self.last(p.book, p.end_chapter)
        if p.end_verse < last:
            rest = self.label(Passage(p.book, p.end_chapter, p.end_verse + 1, p.end_chapter, last))
        else:
            c = p.end_chapter + 1
            if str(c) not in self.verses[p.book]:
                return None
            rest = f"{self.books[p.book]['name']} {c}"
        return self.portions(rest)[0]
