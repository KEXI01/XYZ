import asyncio
import shlex
import os
import hashlib
from typing import Tuple, Optional, Dict, Any
from pathlib import Path
from git import Repo, Remote
from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError
import config
from ..logging import LOGGER
from src.data import REPO_PASS
from cryptography.fernet import Fernet

class GitManager:
    def __init__(self):
        self.repo_link = "https://github.com/KEXI01/XYZ"
        self.repo_path = Path.cwd()
        self.encryption_key = self._generate_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)

    def _generate_encryption_key(self) -> bytes:
        return Fernet.generate_key()

    def _encrypt_data(self, data: str) -> str:
        return self.cipher_suite.encrypt(data.encode()).decode()

    def _decrypt_data(self, encrypted_data: str) -> str:
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()

    def _verify_password(self) -> bool:
        try:
            input_hash = hashlib.sha256(str(config.REPO_PASS).encode()).hexdigest()
            stored_hashes = [hashlib.sha256(str(p).encode()).hexdigest() for p in REPO_PASS]
            return input_hash in stored_hashes
        except Exception as e:
            LOGGER(__name__).error(f"Password verification failed: {str(e)}")
            return False

    async def _run_command(self, cmd: str, cwd: Optional[str] = None) -> Tuple[str, str, int, int]:
        args = shlex.split(cmd)
        process = await asyncio.create_subprocess_exec(
            *args,
            cwd=cwd or str(self.repo_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return (
            stdout.decode("utf-8", "replace").strip(),
            stderr.decode("utf-8", "replace").strip(),
            process.returncode,
            process.pid,
        )

    def _prepare_upstream_url(self) -> str:
        if not config.GIT_TOKEN:
            return self.repo_link

        try:
            repo_path = self.repo_link.split("https://")[1]
            if "@" in repo_path:
                repo_path = repo_path.split("@")[1]
            return f"https://{config.GIT_USERNAME}:{self._encrypt_data(config.GIT_TOKEN)}@{repo_path}"
        except (IndexError, AttributeError) as e:
            LOGGER(__name__).error(f"URL preparation failed: {str(e)}")
            raise ValueError("Invalid repository URL format") from e

    def _setup_remote(self, repo: Repo) -> Remote:
        upstream_url = self._prepare_upstream_url()
        
        try:
            if "origin" in repo.remotes:
                origin = repo.remote("origin")
                if origin.url != upstream_url:
                    origin.set_url(upstream_url)
            else:
                origin = repo.create_remote("origin", upstream_url)
            return origin
        except Exception as e:
            LOGGER(__name__).error(f"Remote setup failed: {str(e)}")
            raise

    def _checkout_branch(self, repo: Repo, origin: Remote) -> None:
        try:
            if config.UPSTREAM_BRANCH not in repo.heads:
                repo.create_head(
                    config.UPSTREAM_BRANCH,
                    origin.refs[config.UPSTREAM_BRANCH],
                )
            
            branch = repo.heads[config.UPSTREAM_BRANCH]
            if not branch.tracking_branch():
                branch.set_tracking_branch(origin.refs[config.UPSTREAM_BRANCH])
            
            branch.checkout(True)
        except Exception as e:
            LOGGER(__name__).error(f"Branch checkout failed: {str(e)}")
            raise

    async def _install_requirements(self) -> bool:
        cmds = [
            "pip3 install --upgrade pip",
            "pip3 install --no-cache-dir -r requirements.txt",
            "pip3 check"
        ]
        
        for cmd in cmds:
            stdout, stderr, returncode, _ = await self._run_command(cmd)
            if returncode != 0:
                LOGGER(__name__).error(
                    f"Command failed: {cmd}\n"
                    f"STDOUT: {stdout}\n"
                    f"STDERR: {stderr}"
                )
                return False
        return True

    async def _cleanup_repository(self, repo: Repo) -> None:
        try:
            repo.git.clean("-fd")
            repo.git.reset("--hard")
            repo.remote().prune()
        except Exception as e:
            LOGGER(__name__).warning(f"Cleanup operations partially failed: {str(e)}")

    async def _validate_repository(self, repo: Repo) -> bool:
        try:
            repo.git.fsck()
            repo.head.commit
            return True
        except Exception as e:
            LOGGER(__name__).error(f"Repository validation failed: {str(e)}")
            return False

    async def initialize_or_update(self) -> Dict[str, Any]:
        if not self._verify_password():
            return {
                "success": False,
                "message": "Invalid repository password",
                "error": "Authentication failed"
            }

        try:
            try:
                repo = Repo(self.repo_path)
                if not await self._validate_repository(repo):
                    raise InvalidGitRepositoryError("Repository validation failed")
                LOGGER(__name__).info("Existing valid git repository found")
            except (InvalidGitRepositoryError, NoSuchPathError):
                LOGGER(__name__).info("Initializing new git repository")
                repo = Repo.init(self.repo_path)
                await self._cleanup_repository(repo)

            origin = self._setup_remote(repo)
            origin.fetch()
            self._checkout_branch(repo, origin)

            try:
                origin.pull(config.UPSTREAM_BRANCH)
            except GitCommandError:
                LOGGER(__name__).warning("Merge conflict detected, performing hard reset")
                repo.git.reset("--hard", "FETCH_HEAD")

            if not await self._install_requirements():
                return {
                    "success": False,
                    "message": "Requirements installation failed",
                    "error": "Package installation error"
                }

            await self._cleanup_repository(repo)

            return {
                "success": True,
                "message": "Repository successfully updated",
                "commit": repo.head.commit.hexsha,
                "branch": str(repo.active_branch)
            }

        except Exception as e:
            LOGGER(__name__).error(f"Repository operation failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": "Repository operation failed",
                "error": str(e)
            }

async def git() -> Dict[str, Any]:
    manager = GitManager()
    return await manager.initialize_or_update()
