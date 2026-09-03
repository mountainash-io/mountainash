from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path


def write_text_if_changed(path: Path, content: str) -> bool:
    """Atomically replace *path* when its UTF-8 contents differ.

    Returns ``True`` when the destination is replaced and ``False`` when its
    existing bytes already match. The temporary file is created beside the
    destination so replacement remains atomic on the same filesystem.
    """
    content_bytes = content.encode("utf-8")
    try:
        if path.read_bytes() == content_bytes:
            return False
        mode = stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        mode = 0o644

    temp_path: Path | None = None
    try:
        file_descriptor, temp_name = tempfile.mkstemp(dir=path.parent)
        temp_path = Path(temp_name)
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
        os.chmod(temp_path, mode)
        os.replace(temp_path, path)
        return True
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
