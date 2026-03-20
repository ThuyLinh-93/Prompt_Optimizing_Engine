import logging
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    config_path: str = "config.yaml"
    log_level: str = "INFO"
    log_file: str | None = None
    langsmith_api_key: str = ""
    openai_api_key: str = ""
    input_dir: str
    output_dir: str
    result_base_path: str | None = None

    # --- 환경변수 오버라이드 (None이면 config.yaml 값 사용) ---
    langsmith_enabled: bool | None = None

    llm_provider: str | None = None
    vllm_base_url: str | None = None
    vllm_model: str | None = None
    openai_model: str | None = None
    llm_temperature: float | None = None
    llm_max_tokens: int | None = None

    server_host: str | None = None
    server_port: int | None = None

    file_script: str | None = None
    file_summary: str | None = None
    file_prompt: str | None = None
    file_rubric: str | None = None

    context_max_input_tokens: int | None = None
    context_strategy: str | None = None
    context_chunk_size: int | None = None


def apply_env_overrides(config: dict) -> dict:
    """settings의 환경변수 값이 설정되어 있으면 config dict를 오버라이드한다."""
    s = settings

    # LangSmith
    if s.langsmith_enabled is not None:
        config.setdefault("langsmith", {})["enabled"] = s.langsmith_enabled

    # LLM
    if s.llm_provider is not None:
        config["llm"]["provider"] = s.llm_provider
    if s.vllm_base_url is not None:
        config["llm"]["vllm"]["base_url"] = s.vllm_base_url
    if s.vllm_model is not None:
        config["llm"]["vllm"]["model"] = s.vllm_model
    if s.openai_model is not None:
        config["llm"]["openai"]["model"] = s.openai_model
    if s.llm_temperature is not None:
        config["llm"]["temperature"] = s.llm_temperature
    if s.llm_max_tokens is not None:
        config["llm"]["max_tokens"] = s.llm_max_tokens

    # Server
    if s.server_host is not None:
        config.setdefault("server", {})["host"] = s.server_host
    if s.server_port is not None:
        config.setdefault("server", {})["port"] = s.server_port

    # Files
    if s.file_script is not None:
        config.setdefault("files", {})["script"] = s.file_script
    if s.file_summary is not None:
        config.setdefault("files", {})["summary"] = s.file_summary
    if s.file_prompt is not None:
        config.setdefault("files", {})["prompt"] = s.file_prompt
    if s.file_rubric is not None:
        config.setdefault("files", {})["rubric"] = s.file_rubric

    # Context
    if s.context_max_input_tokens is not None:
        config.setdefault("context", {})["max_input_tokens"] = s.context_max_input_tokens
    if s.context_strategy is not None:
        config.setdefault("context", {})["strategy"] = s.context_strategy
    if s.context_chunk_size is not None:
        config.setdefault("context", {})["chunk_size"] = s.context_chunk_size

    return config


settings = Settings()


def setup_logging() -> None:
    """settings 기반으로 로깅을 설정한다. LOG_FILE이 지정되면 파일에도 기록."""
    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if settings.log_file:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))

    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=handlers,
    )
