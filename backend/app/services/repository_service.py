"""
Repository service for cloning GitHub repos and extracting ZIP uploads.
Handles preprocessing to ignore unnecessary files and directories.
"""

import os
import uuid
import shutil
import zipfile
import tempfile
from pathlib import Path

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger("repository")

IGNORE_DIRS = {
    "node_modules", ".git", "__pycache__", ".next", ".nuxt", "dist", "build",
    "out", ".cache", "venv", ".venv", "env", "coverage", ".nyc_output",
    ".idea", ".vscode", "vendor", "target", "bin", "obj", ".terraform",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "eggs",
}

IGNORE_EXTENSIONS = {
    ".pyc", ".pyo", ".class", ".o", ".so", ".dll", ".exe",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".mp3", ".mp4", ".wav", ".ttf", ".woff", ".woff2", ".eot",
    ".zip", ".tar", ".gz", ".rar", ".pdf", ".doc", ".docx",
    ".lock", ".map", ".DS_Store",
}

IGNORE_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "Pipfile.lock", "poetry.lock", ".DS_Store", "Thumbs.db",
}

ANALYZABLE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cs", ".go",
    ".html", ".css", ".scss", ".json", ".yaml", ".yml", ".toml",
    ".md", ".sql", ".graphql", ".sh", ".dockerfile",
}


class RepoFile:
    """Represents a file discovered in the repository."""
    def __init__(self, path: str, relative_path: str, size: int, extension: str):
        self.path = path
        self.relative_path = relative_path
        self.size = size
        self.extension = extension

    def read_content(self) -> str:
        try:
            with open(self.path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""


class RepositoryService:
    """Service for acquiring and preprocessing source code repositories."""

    def __init__(self):
        self.settings = get_settings()
        self._temp_dirs: dict[str, str] = {}

    async def clone_github_repo(self, github_url: str, branch: str = "main"):
        repo_id = str(uuid.uuid4())[:8]
        repo_name = self._extract_repo_name(github_url)
        temp_dir = tempfile.mkdtemp(prefix=f"reqgen_{repo_id}_")
        self._temp_dirs[repo_id] = temp_dir

        logger.info(f"Cloning {github_url} (branch: {branch})")
        try:
            import git
            clone_url = github_url
            if self.settings.GITHUB_TOKEN and "github.com" in github_url:
                clone_url = github_url.replace(
                    "https://github.com",
                    f"https://{self.settings.GITHUB_TOKEN}@github.com",
                )
            git.Repo.clone_from(clone_url, temp_dir, branch=branch, depth=1)
        except Exception as e:
            raise ValueError(f"Failed to clone repository: {e}")

        files = self._discover_files(temp_dir)
        logger.info(f"Discovered {len(files)} analyzable files in {repo_name}")
        return repo_id, repo_name, files

    async def extract_upload(self, file_content: bytes, filename: str):
        repo_id = str(uuid.uuid4())[:8]
        repo_name = Path(filename).stem
        temp_dir = tempfile.mkdtemp(prefix=f"reqgen_{repo_id}_")
        self._temp_dirs[repo_id] = temp_dir

        zip_path = os.path.join(temp_dir, filename)
        with open(zip_path, "wb") as f:
            f.write(file_content)

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                total_size = sum(i.file_size for i in zf.infolist())
                max_size = self.settings.MAX_REPO_SIZE_MB * 1024 * 1024
                if total_size > max_size:
                    raise ValueError(f"Archive exceeds {self.settings.MAX_REPO_SIZE_MB}MB limit")
                extract_dir = os.path.join(temp_dir, "source")
                zf.extractall(extract_dir)
        except zipfile.BadZipFile:
            raise ValueError("Invalid ZIP file")

        entries = os.listdir(extract_dir)
        if len(entries) == 1 and os.path.isdir(os.path.join(extract_dir, entries[0])):
            extract_dir = os.path.join(extract_dir, entries[0])
            repo_name = entries[0]

        os.remove(zip_path)
        files = self._discover_files(extract_dir)
        return repo_id, repo_name, files

    def _extract_repo_name(self, url: str) -> str:
        url = url.rstrip("/").rstrip(".git")
        parts = url.split("/")
        return f"{parts[-2]}/{parts[-1]}" if len(parts) >= 2 else parts[-1]

    def _discover_files(self, root_dir: str) -> list[RepoFile]:
        files = []
        max_files = self.settings.MAX_FILES_TO_ANALYZE
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]
            for filename in filenames:
                if len(files) >= max_files:
                    return files
                if filename in IGNORE_FILES:
                    continue
                ext = Path(filename).suffix.lower()
                if ext in IGNORE_EXTENSIONS or (ext and ext not in ANALYZABLE_EXTENSIONS):
                    continue
                filepath = os.path.join(dirpath, filename)
                try:
                    size = os.path.getsize(filepath)
                    if size > 500 * 1024:
                        continue
                    files.append(RepoFile(filepath, os.path.relpath(filepath, root_dir), size, ext))
                except OSError:
                    continue
        return files

    def cleanup(self, repo_id: str):
        temp_dir = self._temp_dirs.pop(repo_id, None)
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

    def detect_stack(self, files: list[RepoFile]) -> list[str]:
        frameworks = set()
        for f in files:
            name = os.path.basename(f.relative_path).lower()
            if name == "package.json":
                c = f.read_content()
                for fw, key in [("react", '"react"'), ("nextjs", '"next"'), ("vue", '"vue"'),
                                ("angular", '"@angular/core"'), ("express", '"express"')]:
                    if key in c:
                        frameworks.add(fw)
            elif name in ("requirements.txt", "pyproject.toml"):
                c = f.read_content().lower()
                for fw, key in [("fastapi", "fastapi"), ("flask", "flask"), ("django", "django")]:
                    if key in c:
                        frameworks.add(fw)
        return list(frameworks) or ["unknown"]


def get_repository_service() -> RepositoryService:
    settings = get_settings()
    if settings.MOCK_MODE:
        return MockRepositoryService()
    return RepositoryService()


class MockRepositoryService(RepositoryService):
    """Mock repository service that returns sample project data."""

    async def clone_github_repo(self, github_url: str, branch: str = "main"):
        from app.services._mock_data import get_mock_files
        repo_id = str(uuid.uuid4())[:8]
        repo_name = self._extract_repo_name(github_url)
        temp_dir = tempfile.mkdtemp(prefix=f"reqgen_{repo_id}_")
        self._temp_dirs[repo_id] = temp_dir
        files = []
        for rel_path, content in get_mock_files().items():
            full_path = os.path.join(temp_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)
            files.append(RepoFile(full_path, rel_path, len(content), Path(rel_path).suffix))
        logger.info(f"[MOCK] Created {len(files)} mock files for {repo_name}")
        return repo_id, repo_name, files

    async def extract_upload(self, file_content: bytes, filename: str):
        return await self.clone_github_repo(f"https://github.com/mock/{Path(filename).stem}")
