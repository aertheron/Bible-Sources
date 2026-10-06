"""Pinned, hash-verified local or remote source access. No source mutations."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class StudyError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)

    def as_dict(self):
        return {"error": {"code": self.code, "message": str(self)}}


def config(name):
    return json.loads((Path(__file__).parent / "config" / f"{name}.json").read_text(encoding="utf-8"))


def bounded(value, limit=60000):
    size = len(json.dumps(value, ensure_ascii=False, separators=(",", ":")))
    if size > limit:
        raise StudyError("packet_budget", f"Packet has {size} characters; limit {limit}. Retrieve fewer verses, witnesses or records and merge concise findings at the next stage.")
    return value


class SourceStore:
    def __init__(self, data_root=None, cache_root=None, offline=None):
        self.profile = config("source-profile")
        candidate = data_root or os.environ.get("BIBLE_STUDY_DATA")
        if candidate:
            self.root = Path(candidate).expanduser().resolve()
            if not (self.root / "indexes/book-catalog.json").is_file():
                raise StudyError("data_root", "The data root must contain indexes/book-catalog.json.")
        else:
            checkout = Path(__file__).resolve().parents[3]
            self.root = checkout if (checkout / "indexes/book-catalog.json").is_file() else None
        self.cache = Path(cache_root or os.environ.get("BIBLE_STUDY_CACHE", "~/.cache/source-text-bible-study")).expanduser() / self.profile["commit"]
        self.offline = os.environ.get("BIBLE_STUDY_OFFLINE") == "1" if offline is None else offline
        self._metadata = {}

    @staticmethod
    def safe_path(path):
        if not isinstance(path, str) or not path or "\\" in path:
            raise StudyError("source_path", "Invalid source path.")
        p = PurePosixPath(path)
        if p.is_absolute() or ".." in p.parts:
            raise StudyError("source_path", "Source paths must stay within the pinned repository.")
        return path

    @staticmethod
    def verify(data, expected):
        if not isinstance(expected, str) or len(expected) != 64 or hashlib.sha256(data).hexdigest() != expected:
            raise StudyError("source_hash", "Source bytes do not match the pinned SHA-256; do not interpret this packet.")
        return data

    def _bytes(self, path, expected, offset=None, length=None):
        path = self.safe_path(path)
        if offset is not None and (type(offset) is not int or type(length) is not int or offset < 0 or not 0 < length <= 4 * 1024 * 1024):
            raise StudyError("source_span", "Invalid or oversized byte span.")
        if self.root:
            local = (self.root / path).resolve()
            if not local.is_relative_to(self.root):
                raise StudyError("source_path", "Source symlink escapes the repository.")
            try:
                with local.open("rb") as f:
                    if offset is not None:
                        f.seek(offset)
                    data = f.read(length if length is not None else 8 * 1024 * 1024 + 1)
            except OSError as e:
                raise StudyError("source_missing", f"Source file unavailable: {path}") from e
            return self.verify(data, expected)
        key = hashlib.sha256(f"{path}:{offset}:{length}".encode()).hexdigest()
        cached = self.cache / key
        if cached.is_file():
            return self.verify(cached.read_bytes(), expected)
        if self.offline:
            raise StudyError("offline_cache_miss", f"Pinned source is not cached: {path}")
        headers = {"User-Agent": "source-text-bible-study/0.1.0"}
        if offset is not None:
            headers["Range"] = f"bytes={offset}-{offset + length - 1}"
        url = f"https://raw.githubusercontent.com/{self.profile['repository']}/{self.profile['commit']}/{path}"
        try:
            with urlopen(Request(url, headers=headers), timeout=25) as response:
                if response.status == 206:
                    if offset is None or not response.headers.get("Content-Range", "").startswith(f"bytes {offset}-"):
                        raise StudyError("source_range", "Remote source returned an unexpected byte range.")
                elif offset is not None:
                    remaining = offset
                    while remaining:
                        discarded = response.read(min(65536, remaining))
                        if not discarded:
                            raise StudyError("source_range", "Remote source ended before the requested span.")
                        remaining -= len(discarded)
                data = response.read(length if length is not None else 8 * 1024 * 1024 + 1)
        except (HTTPError, URLError, TimeoutError, OSError) as e:
            raise StudyError("source_network", f"Could not fetch the pinned source {path}: {type(e).__name__}") from e
        self.verify(data, expected)
        self.cache.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=self.cache, delete=False) as f:
            f.write(data)
            temporary = f.name
        os.replace(temporary, cached)
        return data

    def read(self, path):
        expected = self.profile["metadata_hashes"].get(path)
        if not expected:
            raise StudyError("unregistered_source", "Whole-file reads are limited to registered metadata and apparatus.")
        if path not in self._metadata:
            self._metadata[path] = self._bytes(path, expected)
        return self._metadata[path]

    def json(self, path):
        return json.loads(self.read(path))

    def span(self, record):
        return self._bytes(record.get("file", record.get("path")), record["sha256"], int(record["byte_offset"]), int(record["byte_length"]))

    def evidence(self, record):
        return {"repository": self.profile["repository"], "source_commit": self.profile["commit"], "file": record.get("file", record.get("path")), "byte_offset": int(record["byte_offset"]), "byte_length": int(record["byte_length"]), "sha256": record["sha256"]}
