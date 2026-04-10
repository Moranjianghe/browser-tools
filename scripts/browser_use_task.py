import argparse
import asyncio
import importlib.util
import os
from pathlib import Path

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


def build_llm():
    provider = os.getenv("BROWSER_USE_LLM", "openai").strip().lower()
    model = os.getenv("BROWSER_USE_MODEL", "gpt-5.3-codex").strip()
    reasoning_effort = os.getenv("BROWSER_USE_REASONING_EFFORT", "high").strip().lower()
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
                model=model or "gpt-5.3-codex",
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
            model=model or "gpt-5.3-codex",
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
    args = parser.parse_args()

    if args.provider:
        os.environ["BROWSER_USE_LLM"] = args.provider
    if args.model:
        os.environ["BROWSER_USE_MODEL"] = args.model

    task = " ".join(args.task).strip()
    if not task:
        raise SystemExit("Task cannot be empty.")

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
