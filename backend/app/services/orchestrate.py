"""watsonx Orchestrate client for the main chat experience."""

import asyncio
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Iterable

import httpx
import yaml

from app.config import Settings, get_settings


SYSTEM_PROMPT_TEMPLATE = """You are an educational assistant helping a beginner learn about {topic_title}.

You have access to a web search tool. Use it to find information relevant to the user's question about {search_scope}.

Rules you must follow without exception:
1. Search before answering. Do not answer from memory alone.
2. Answer ONLY using information found in your search results.
3. Do NOT generate, guess, or invent any URLs or source links.
   Source links will be attached separately by the system.
4. If the search results do not contain enough information to answer the question, say exactly:
   \"I don't have enough information on that right now. Try checking the sources below or rephrasing your question.\"
5. Keep your answer under 150 words.
6. Use simple, beginner-friendly language. Define technical terms before using them.
7. Stay focused on {topic_title}. If the question is unrelated, say:
   \"I'm focused on {topic_title} right now - ask me anything about that!\"

User question: {question}"""

_TOKEN_CACHE = {"token": None, "expiry": 0}
_TOKEN_LOCK = threading.Lock()


async def call_orchestrate(
    topic_title: str,
    search_scope: str,
    question: str,
) -> dict:
    settings = get_settings()

    if (
        not settings.orchestrate_api_key
        or not settings.orchestrate_agent_id
        or not settings.orchestrate_instance_url
    ):
        return _stub_response(topic_title, question)

    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        topic_title=topic_title,
        search_scope=search_scope,
        question=question,
    )

    try:
        return await _run_orchestrate_request(settings, prompt)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 401:
            raise
        _invalidate_token_cache()
        return await _run_orchestrate_request(settings, prompt)


async def _run_orchestrate_request(settings: Settings, prompt: str) -> dict:
    base_url = settings.orchestrate_instance_url.rstrip("/")
    token = _get_orchestrate_token(settings)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=settings.orchestrate_timeout_seconds) as client:
        run_response = await client.post(
            f"{base_url}/v1/orchestrate/runs",
            headers=headers,
            json={
                "agent_id": settings.orchestrate_agent_id,
                "message": {"role": "user", "content": prompt},
            },
        )
        run_response.raise_for_status()
        run_data = run_response.json()

        run_id = run_data.get("run_id")
        thread_id = run_data.get("thread_id")
        if not run_id or not thread_id:
            raise RuntimeError("Orchestrate did not return a run_id and thread_id.")

        await _wait_for_run_completion(client, base_url, headers, run_id)
        messages_response = await client.get(
            f"{base_url}/v1/orchestrate/threads/{thread_id}/messages",
            headers=headers,
        )
        messages_response.raise_for_status()

    answer = _extract_latest_assistant_text(messages_response.json())
    if not answer:
        answer = "I could not extract a response from watsonx Orchestrate."
    return {"answer": answer, "sources": []}


def _invalidate_token_cache() -> None:
    with _TOKEN_LOCK:
        _TOKEN_CACHE["token"] = None
        _TOKEN_CACHE["expiry"] = 0


def _get_orchestrate_token(settings: Settings) -> str:
    now = int(time.time())
    with _TOKEN_LOCK:
        token = _TOKEN_CACHE.get("token")
        expiry = int(_TOKEN_CACHE.get("expiry") or 0)
        if token and expiry - 60 > now:
            return token

        token, expiry = _refresh_orchestrate_token(settings)
        _TOKEN_CACHE["token"] = token
        _TOKEN_CACHE["expiry"] = expiry
        return token


def _refresh_orchestrate_token(settings: Settings) -> tuple[str, int]:
    backend_root = Path(__file__).resolve().parents[2]
    adk_root = Path(settings.orchestrate_adk_home)
    if not adk_root.is_absolute():
        adk_root = (backend_root / adk_root).resolve()
    adk_root.mkdir(parents=True, exist_ok=True)

    cli_path = Path(settings.orchestrate_cli_path) if settings.orchestrate_cli_path else _default_cli_path()
    if not cli_path.is_absolute():
        cli_path = (backend_root / cli_path).resolve()

    cli_cwd = Path(settings.orchestrate_cli_cwd) if settings.orchestrate_cli_cwd else backend_root
    if not cli_cwd.is_absolute():
        cli_cwd = (backend_root / cli_cwd).resolve()

    if cli_path.exists():
        try:
            token, expiry = _refresh_via_temp_home(
                settings=settings,
                cli_path=cli_path,
                cli_cwd=cli_cwd,
                adk_root=adk_root,
            )
            if token:
                return token, expiry
        except Exception:
            pass

        try:
            token, expiry = _refresh_via_existing_home(
                settings=settings,
                cli_path=cli_path,
                cli_cwd=cli_cwd,
                adk_home=adk_root,
            )
            if token:
                return token, expiry
        except Exception:
            pass

    token, expiry = _read_cached_token(adk_root, settings.orchestrate_env_name)
    if token:
        return token, expiry

    raise RuntimeError(
        f"Unable to refresh watsonx Orchestrate token and no cached token is available in {adk_root}."
    )


def _default_cli_path() -> Path:
    command_name = "orchestrate.exe" if os.name == "nt" else "orchestrate"
    discovered = shutil.which(command_name)
    if discovered:
        return Path(discovered)

    sibling = Path(sys.executable).with_name(command_name)
    if sibling.exists():
        return sibling

    alternate = Path(sys.executable).with_name("orchestrate.exe" if command_name == "orchestrate" else "orchestrate")
    return alternate


def _refresh_via_temp_home(
    *,
    settings: Settings,
    cli_path: Path,
    cli_cwd: Path,
    adk_root: Path,
) -> tuple[str, int]:
    with tempfile.TemporaryDirectory(dir=adk_root, prefix="refresh-") as temp_home_str:
        temp_home = Path(temp_home_str)
        env_name = f"{settings.orchestrate_env_name}-{int(time.time())}"
        env = _build_cli_env(temp_home)

        _run_cli(
            [
                str(cli_path),
                "env",
                "add",
                "-n",
                env_name,
                "-u",
                settings.orchestrate_instance_url,
                "--type",
                "mcsp",
            ],
            cli_cwd,
            env,
        )

        _run_cli(
            [
                str(cli_path),
                "env",
                "activate",
                env_name,
                "--api-key",
                settings.orchestrate_api_key,
            ],
            cli_cwd,
            env,
        )

        return _read_cached_token(temp_home, env_name)


def _refresh_via_existing_home(
    *,
    settings: Settings,
    cli_path: Path,
    cli_cwd: Path,
    adk_home: Path,
) -> tuple[str, int]:
    adk_home.mkdir(parents=True, exist_ok=True)
    env = _build_cli_env(adk_home)

    _run_cli(
        [
            str(cli_path),
            "env",
            "activate",
            settings.orchestrate_env_name,
            "--api-key",
            settings.orchestrate_api_key,
        ],
        cli_cwd,
        env,
        allow_failure=True,
    )

    token, expiry = _read_cached_token(adk_home, settings.orchestrate_env_name)
    if token:
        return token, expiry

    _run_cli(
        [
            str(cli_path),
            "env",
            "add",
            "-n",
            settings.orchestrate_env_name,
            "-u",
            settings.orchestrate_instance_url,
            "--type",
            "mcsp",
        ],
        cli_cwd,
        env,
        allow_failure=True,
    )

    _run_cli(
        [
            str(cli_path),
            "env",
            "activate",
            settings.orchestrate_env_name,
            "--api-key",
            settings.orchestrate_api_key,
        ],
        cli_cwd,
        env,
    )
    return _read_cached_token(adk_home, settings.orchestrate_env_name)


def _build_cli_env(adk_home: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(adk_home)
    env["USERPROFILE"] = str(adk_home)
    return env


def _read_cached_token(adk_home: Path, env_name: str) -> tuple[str, int]:
    credentials_path = adk_home / ".cache" / "orchestrate" / "credentials.yaml"
    if not credentials_path.exists():
        return "", 0
    payload = yaml.safe_load(credentials_path.read_text(encoding="utf-8")) or {}
    auth_entries = payload.get("auth") or {}
    auth_payload = auth_entries.get(env_name) or next(iter(auth_entries.values()), {})
    return auth_payload.get("wxo_mcsp_token", ""), int(auth_payload.get("wxo_mcsp_token_expiry") or 0)


def _run_cli(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str],
    *,
    allow_failure: bool = False,
) -> None:
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
    )
    if result.returncode == 0 or allow_failure:
        return

    output = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
    raise RuntimeError(f"Command failed: {cmd}\n{output}")


async def _wait_for_run_completion(
    client: httpx.AsyncClient,
    base_url: str,
    headers: dict[str, str],
    run_id: str,
    *,
    max_attempts: int = 30,
    delay_seconds: float = 2.0,
) -> None:
    terminal_states = {"completed", "failed", "cancelled"}

    for _ in range(max_attempts):
        response = await client.get(f"{base_url}/v1/orchestrate/runs/{run_id}", headers=headers)
        response.raise_for_status()
        payload = response.json()
        status = str(payload.get("status", "")).lower()
        if status in terminal_states:
            if status != "completed":
                raise RuntimeError(f"Orchestrate run ended with status '{status}'.")
            return
        await asyncio.sleep(delay_seconds)

    raise TimeoutError("Timed out waiting for watsonx Orchestrate to finish the run.")


def _extract_latest_assistant_text(payload: Any) -> str:
    messages = payload if isinstance(payload, list) else payload.get("data", [])
    if not isinstance(messages, list):
        return ""

    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "assistant":
            return _content_to_text(message.get("content"))
    return ""


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, dict):
        return _content_to_text(content.get("text") or content.get("content") or "")
    if isinstance(content, Iterable) and not isinstance(content, (str, bytes)):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("response_type") == "text":
                    parts.append(str(item.get("text", "")).strip())
                elif "text" in item:
                    parts.append(str(item.get("text", "")).strip())
                elif "content" in item:
                    parts.append(_content_to_text(item.get("content")))
            elif isinstance(item, str):
                parts.append(item.strip())
        return "\n".join(part for part in parts if part)
    return ""


def _stub_response(topic_title: str, question: str) -> dict:
    return {
        "answer": (
            f"[Demo mode - Orchestrate not connected] This is where the live research answer about '{question}' would appear. "
            f"Once you add your watsonx Orchestrate credentials to .env.local, this chatbot will search the web and synthesize a real answer about {topic_title}."
        ),
        "sources": [
            {
                "title": "watsonx Orchestrate - IBM",
                "url": "https://www.ibm.com/products/watsonx-orchestrate",
                "excerpt": "Add ORCHESTRATE_INSTANCE_URL, ORCHESTRATE_API_KEY, and ORCHESTRATE_AGENT_ID to .env.local.",
            }
        ],
    }




