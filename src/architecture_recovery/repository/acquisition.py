from __future__ import annotations

import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse


class RepositoryAcquisitionError(RuntimeError):
    """Raised when a remote repository cannot be cloned."""


def is_repository_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "ssh", "git"} and bool(parsed.netloc)


@contextmanager
def cloned_repository(repository_url: str, ref: str | None = None):
    parsed = urlparse(repository_url)
    if parsed.scheme not in {"http", "https", "ssh", "git"} or not parsed.netloc:
        raise RepositoryAcquisitionError(f"Unsupported repository URL: {repository_url}")
    with tempfile.TemporaryDirectory(prefix="architecture-recovery-") as temporary_directory:
        target = Path(temporary_directory) / "repository"
        command = ["git", "clone", "--depth", "1"]
        if ref:
            command.extend(["--branch", ref])
        command.extend(["--", repository_url, str(target)])
        try:
            result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=300)
        except FileNotFoundError as exc:
            raise RepositoryAcquisitionError("git executable was not found") from exc
        except subprocess.TimeoutExpired as exc:
            raise RepositoryAcquisitionError("Timed out while cloning repository") from exc
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "clone failed").strip()
            raise RepositoryAcquisitionError(f"Could not clone repository: {detail}")
        yield target
