import argparse
import asyncio
import importlib.util
import os
import re
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

from browser_use import Agent, Browser, ChatBrowserUse, ChatOpenAI
from browser_use.llm.litellm import ChatLiteLLM

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(ENV_FILE)

RESPONSES_CHAT_PATH = Path(__file__).resolve().with_name("openai-responses-chat.py")
RESPONSES_CHAT_SPEC = importlib.util.spec_from_file_location("browser_tools_openai_responses", RESPONSES_CHAT_PATH)
if RESPONSES_CHAT_SPEC is None or RESPONSES_CHAT_SPEC.loader is None:
    raise SystemExit(f"Unable to load Responses API wrapper from {RESPONSES_CHAT_PATH}")
RESPONSES_CHAT_MODULE = importlib.util.module_from_spec(RESPONSES_CHAT_SPEC)
RESPONSES_CHAT_SPEC.loader.exec_module(RESPONSES_CHAT_MODULE)
ChatOpenAIResponses = RESPONSES_CHAT_MODULE.ChatOpenAIResponses

DEFAULT_BROWSER_PATHS = [
    os.getenv("CHROME_PATH"),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)


def resolve_browser_binary() -> str:
    for candidate in DEFAULT_BROWSER_PATHS:
        if candidate and Path(candidate).exists():
            return candidate
    raise SystemExit("No Chrome or Edge executable was found. Set CHROME_PATH in .env.")


def parse_bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def parse_csv_env(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def is_blocked_domain(hostname: str, blocked_domains: list[str]) -> bool:
    normalized_host = hostname.strip().lower().strip(".")
    for blocked in blocked_domains:
        normalized_blocked = blocked.strip().lower().strip(".")
        if not normalized_blocked:
            continue
        if normalized_host == normalized_blocked or normalized_host.endswith(f".{normalized_blocked}"):
            return True
    return False


def strip_blocked_urls(task: str, blocked_domains: list[str]) -> tuple[str, list[str]]:
    removed_urls: list[str] = []

    def replace(match: re.Match[str]) -> str:
        url = match.group(0)
        hostname = (urlparse(url).hostname or "").strip().lower()
        if hostname and is_blocked_domain(hostname, blocked_domains):
            removed_urls.append(url)
            return ""
        return url

    sanitized_task = URL_PATTERN.sub(replace, task)
    sanitized_task = " ".join(sanitized_task.split())
    sanitized_task = re.sub(r"(?i)\bopen\s+and\s+search\s+for\b", "Search for", sanitized_task)
    sanitized_task = re.sub(r"(?i)\bopen\s+and\s+find\b", "Find", sanitized_task)
    sanitized_task = re.sub(r"(?i)\bopen\s+and\s+", "", sanitized_task)
    sanitized_task = sanitized_task.lstrip(" ;,.")
    return sanitized_task, removed_urls


def build_agent_task(task: str, extra_blocked_domains: list[str] | None = None) -> str:
    blocked_domains = parse_csv_env("BROWSER_USE_BLOCKED_DOMAINS", "")
    if extra_blocked_domains:
        blocked_domains.extend(extra_blocked_domains)
    blocked_domains = sorted({domain.strip().lower() for domain in blocked_domains if domain.strip()})

    preferred_search_engines = parse_csv_env(
        "BROWSER_USE_PREFERRED_SEARCH_ENGINES",
        "google.com,duckduckgo.com",
    )
    preferred_sources = parse_csv_env(
        "BROWSER_USE_PREFERRED_SOURCES",
        "official websites,company help centers,government pages,academic papers,reputable English-language sources",
    )

    sanitized_task, removed_urls = strip_blocked_urls(task, blocked_domains)
    if not sanitized_task:
        sanitized_task = task

    rules = [
        "Execution rules:",
        "- Work efficiently. Minimize unnecessary searches, page reloads, and repeated navigation.",
        "- Prefer direct navigation to the target organization's official site or other authoritative sources before using a general search engine.",
    ]

    if blocked_domains:
        rules.append(f"- Do not use these blocked domains: {', '.join(blocked_domains)}.")
    if preferred_search_engines:
        rules.append(
            f"- If a general search engine is necessary, prefer these in order: {', '.join(preferred_search_engines)}."
        )
    if preferred_sources:
        rules.append(f"- Prefer these source types: {', '.join(preferred_sources)}.")
    if removed_urls:
        rules.append(f"- Ignore blocked URLs from the original prompt: {', '.join(removed_urls)}.")

    return "\n".join(rules) + "\n\nUser task:\n" + sanitized_task


def build_llm():
    provider = os.getenv("BROWSER_USE_LLM", "openai").strip().lower()
    model = os.getenv("BROWSER_USE_MODEL", "gpt-5.4-mini").strip()
    reasoning_effort = os.getenv("BROWSER_USE_REASONING_EFFORT", "medium").strip().lower()
    wire_api = os.getenv("OPENAI_WIRE_API", "responses").strip().lower()
    disable_response_storage = parse_bool_env("OPENAI_DISABLE_RESPONSE_STORAGE", True)
    codex_compat_mode = parse_bool_env("OPENAI_CODEX_COMPAT", True)
    codex_originator = (os.getenv("OPENAI_CODEX_ORIGINATOR") or "codex_cli_rs").strip() or "codex_cli_rs"
    codex_user_agent = (os.getenv("OPENAI_CODEX_USER_AGENT") or "").strip() or None
    response_verbosity = (os.getenv("OPENAI_RESPONSE_VERBOSITY") or "").strip().lower() or None
    if reasoning_effort not in {"none", "minimal", "low", "medium", "high", "xhigh"}:
        reasoning_effort = "high"
    if response_verbosity not in {"low", "medium", "high"}:
        response_verbosity = None

    if provider in {"browser-use", "browseruse", "cloud"}:
        return ChatBrowserUse(
            model=model or "bu-latest",
            api_key=os.getenv("BROWSER_USE_API_KEY") or None,
            base_url=os.getenv("BROWSER_USE_API_BASE") or None,
        )

    if provider in {"openai", "compatible", "codex", "codex-compatible"}:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("BROWSER_USE_API_KEY")
        if not api_key:
            raise SystemExit(
                "Missing API key. Set OPENAI_API_KEY or BROWSER_USE_API_KEY in .env before running browser-use."
            )

        if wire_api == "responses":
            return ChatOpenAIResponses(
                model=model or "gpt-5.4-mini",
                api_key=api_key,
                base_url=os.getenv("OPENAI_BASE_URL") or os.getenv("BROWSER_USE_API_BASE") or None,
                reasoning_effort=reasoning_effort,
                store=not disable_response_storage,
                verbosity=response_verbosity,
                codex_compat_mode=codex_compat_mode,
                codex_originator=codex_originator,
                codex_user_agent=codex_user_agent,
                codex_installation_id=(os.getenv("OPENAI_CODEX_INSTALLATION_ID") or "").strip() or None,
                codex_window_id=(os.getenv("OPENAI_CODEX_WINDOW_ID") or "").strip() or None,
                codex_conversation_id=(os.getenv("OPENAI_CODEX_CONVERSATION_ID") or "").strip() or None,
            )

        return ChatOpenAI(
            model=model or "gpt-5.4-mini",
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL") or os.getenv("BROWSER_USE_API_BASE") or None,
            reasoning_effort=reasoning_effort,
        )

    if provider in {"litellm"}:
        api_key = os.getenv("BROWSER_USE_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise SystemExit(
                "Missing API key. Set OPENAI_API_KEY or BROWSER_USE_API_KEY in .env before running browser-use."
            )

        return ChatLiteLLM(
            model=model or "openai/gpt-4.1-mini",
            api_key=api_key,
            api_base=os.getenv("BROWSER_USE_API_BASE") or os.getenv("OPENAI_BASE_URL") or None,
        )

    raise SystemExit(f"Unsupported BROWSER_USE_LLM value: {provider}")


def build_browser(args) -> Browser:
    cdp_url = args.cdp_url or os.getenv("BROWSER_CDP_URL")
    if cdp_url:
        return Browser(cdp_url=cdp_url, is_local=True)

    profile_dir = Path(os.getenv("BROWSER_PROFILE_DIR", PROJECT_ROOT / "profiles" / "shared"))
    profile_dir.mkdir(parents=True, exist_ok=True)

    downloads_dir = PROJECT_ROOT / "downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)

    headless = parse_bool_env("BROWSER_HEADLESS", False)
    if args.headed:
        headless = False
    if args.headless:
        headless = True

    return Browser(
        use_cloud=False,
        executable_path=resolve_browser_binary(),
        headless=headless,
        user_data_dir=str(profile_dir),
        downloads_path=str(downloads_dir),
        accept_downloads=True,
        auto_download_pdfs=True,
    )


async def main():
    parser = argparse.ArgumentParser(description="Run a local browser-use task.")
    parser.add_argument("task", nargs="+", help="Natural-language browser task.")
    parser.add_argument("--cdp-url", help="Attach to an existing debug browser via CDP.")
    parser.add_argument("--headless", action="store_true", help="Force headless mode when launching a new browser.")
    parser.add_argument("--headed", action="store_true", help="Force headed mode when launching a new browser.")
    parser.add_argument("--provider", help="Override BROWSER_USE_LLM for this run.")
    parser.add_argument("--model", help="Override BROWSER_USE_MODEL for this run.")
    parser.add_argument(
        "--block-domain",
        action="append",
        default=[],
        help="Block a domain for this run. Can be passed multiple times.",
    )
    args = parser.parse_args()

    if args.provider:
        os.environ["BROWSER_USE_LLM"] = args.provider
    if args.model:
        os.environ["BROWSER_USE_MODEL"] = args.model

    task = " ".join(args.task).strip()
    if not task:
        raise SystemExit("Task cannot be empty.")
    task = build_agent_task(task, extra_blocked_domains=args.block_domain)

    browser = build_browser(args)
    llm = build_llm()

    try:
        agent = Agent(
            browser=browser,
            task=task,
            llm=llm,
        )
        result = await agent.run()
        print("\n=== RESULT ===")
        print(result)
    finally:
        close_method = getattr(browser, "close", None)
        if callable(close_method):
            await close_method()


if __name__ == "__main__":
    asyncio.run(main())
