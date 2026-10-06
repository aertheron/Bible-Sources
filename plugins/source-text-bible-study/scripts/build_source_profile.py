"""Rebuild pinned metadata and native reference routes from an identified checkout.

Maintenance only; review the resulting diff and run all checks before publication.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", type=Path)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    root = args.repository.resolve()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if head != args.commit:
        parser.error("The checkout HEAD must match the requested source commit.")
    dest = Path(__file__).resolve().parents[1] / "bible_study/config"
    dest.mkdir(parents=True, exist_ok=True)
    def save(name, data):
        (dest / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths = list((root / "indexes").rglob("*")) + list((root / "sources/sblgnt/apparatus").glob("*.txt")) + [root / "resources/research-links.json"]
    hashes = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths) if p.is_file()}
    profile = {"schema_version": "0.1.0", "profile": "shared-public", "repository": "aertheron/Bible-Sources", "commit": args.commit, "metadata_hashes": hashes, "dss_linguistic_headers": {}}
    for path in sorted((root / "sources/dss/2.0.1/enriched/linguistics/books").glob("*.txt")):
        with path.open("rb") as f:
            start = f.read(8192)
        marker = start.index(b"COLUMNS\n") + len(b"COLUMNS\n")
        end = start.index(b"\n", marker) + 1
        profile["dss_linguistic_headers"][path.relative_to(root).as_posix()] = {"file": path.relative_to(root).as_posix(), "byte_offset": marker, "byte_length": end - marker, "sha256": hashlib.sha256(start[marker:end]).hexdigest()}
    catalog = json.loads((root / "indexes/book-catalog.json").read_text())["books"]
    tahot = [x for x in catalog if x["dataset_id"] == "TAHOT"]
    by_tahot_name = {Path(x["file"]).stem.replace("_", " ").lower(): x["book_id"] for x in tahot}
    # Hebrew-native WLC labels and TAHOT/Greek conventions differ. These are
    # book routes only, not reviewed verse-equivalence maps.
    fallback = {"Song": "Sng", "Ps": "Psa", "Prov": "Pro", "Eccl": "Ecc", "Esth": "Est", "Ezek": "Ezk", "Nah": "Nam", "Josh": "Jos", "Judg": "Jdg", "Exod": "Exo", "Deut": "Deu", "Amos": "Amo", "Joel": "Jol", "Obad": "Oba", "Jonah": "Jon", "Zeph": "Zep", "Ruth": "Rut", "1Sam": "1Sa", "2Sam": "2Sa", "1Kgs": "1Ki", "2Kgs": "2Ki", "1Chr": "1Ch", "2Chr": "2Ch"}
    dutch = "Genesis Exodus Leviticus Numeri Deuteronomium Jozua Rechters Ruth 1-Samuel 2-Samuel 1-Koningen 2-Koningen 1-Kronieken 2-Kronieken Ezra Nehemia Ester Job Psalmen Spreuken Prediker Hooglied Jesaja Jeremia Klaagliederen Ezechiël Daniël Hosea Joël Amos Obadja Jona Micha Nahum Habakuk Sefanja Haggai Zacharia Maleachi".split()
    ot_ids = "Gen Exod Lev Num Deut Josh Judg Ruth 1Sam 2Sam 1Kgs 2Kgs 1Chr 2Chr Ezra Neh Esth Job Ps Prov Eccl Song Isa Jer Lam Ezek Dan Hos Joel Amos Obad Jonah Mic Nah Hab Zeph Hag Zech Mal".split()
    nl = dict(zip(ot_ids, [v.replace("-", " ") for v in dutch]))
    nt_names = {"Matt": "Matthew", "Mark": "Mark", "Luke": "Luke", "John": "John", "Acts": "Acts", "Rom": "Romans", "1Cor": "1 Corinthians", "2Cor": "2 Corinthians", "Gal": "Galatians", "Eph": "Ephesians", "Phil": "Philippians", "Col": "Colossians", "1Thess": "1 Thessalonians", "2Thess": "2 Thessalonians", "1Tim": "1 Timothy", "2Tim": "2 Timothy", "Titus": "Titus", "Phlm": "Philemon", "Heb": "Hebrews", "Jas": "James", "1Pet": "1 Peter", "2Pet": "2 Peter", "1John": "1 John", "2John": "2 John", "3John": "3 John", "Jude": "Jude", "Rev": "Revelation"}
    nt_nl = "Matteüs Marcus Lucas Johannes Handelingen Romeinen 1-Korintiërs 2-Korintiërs Galaten Efeziërs Filippenzen Kolossenzen 1-Tessalonicenzen 2-Tessalonicenzen 1-Timoteüs 2-Timoteüs Titus Filemon Hebreeën Jakobus 1-Petrus 2-Petrus 1-Johannes 2-Johannes 3-Johannes Judas Openbaring".split()
    nl.update(zip(nt_names, [v.replace("-", " ") for v in nt_nl]))
    books = {}; verses = {}
    for book in ot_ids:
        rows = [json.loads(line) for line in (root / f"sources/leningrad/verses/wlc-4.20-oshb/{book}.jsonl").read_text().splitlines()]
        name = rows[0]["book_name"]
        t = by_tahot_name.get(name.lower(), fallback.get(book, book))
        greek = {"Est": "ESG", "Dan": "DAG"}.get(t, t.upper())
        greek_ids = {x["book_id"] for x in catalog if x["dataset_id"] == "LXX-GRCBRENT-20260408"}
        routes = {"WLC": ["wlc-4.20-oshb", book], "UXLC": ["uxlc-2.4", book], "TAHOT": ["TAHOT", t]}
        if greek in greek_ids:
            routes["LXX"] = ["LXX-GRCBRENT-20260408", greek]
        books[book] = {"name": name, "testament": "OT", "aliases": list(dict.fromkeys([nl[book], t, "Psalm" if book == "Ps" else name])), "routes": routes, "dss_book": {"Exod": "Ex", "Isa": "Is", "Esth": "Est"}.get(book, book)}
        verses[book] = {}
        for row in rows:
            verses[book].setdefault(str(row["chapter"]), []).append(row["verse"])
    for book, name in nt_names.items():
        rows = re.findall(r"(?m)^\S+ (\d+):(\d+)\t", (root / f"sources/sblgnt/text/{book}.txt").read_text())
        books[book] = {"name": name, "testament": "NT", "aliases": [nl[book]], "routes": {"SBLGNT": ["SBLGNT", book]}}
        verses[book] = {}
        for chapter, verse in rows:
            verses[book].setdefault(chapter, []).append(int(verse))
    save("source-profile", profile)
    save("books", {"schema_version": "0.1.0", "route_status": "book_identity_only_native_verse_equivalence_not_verified", "books": books})
    save("base-references", {"schema_version": "0.1.0", "source_commit": args.commit, "verses": verses})
    print(json.dumps({"metadata_files": len(hashes), "books": len(books), "chapters": sum(map(len, verses.values()))}))


if __name__ == "__main__":
    main()
