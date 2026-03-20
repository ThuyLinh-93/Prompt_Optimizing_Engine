import argparse
import logging
import sys
from pathlib import Path

import yaml

from graph.review_graph import build_review_graph
from models.llm_client import get_llm, setup_langsmith
from settings import apply_env_overrides, settings, setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Prompt Optimizer — Review Agent")
    parser.add_argument(
        "--config", default=None, help="config.yaml 경로 (기본: 환경변수 CONFIG_PATH)"
    )
    parser.add_argument("--script", help="script.json 경로 (config의 input_dir 대신 사용)")
    parser.add_argument("--summary", help="summary.json 경로 (config의 input_dir 대신 사용)")
    parser.add_argument("--prompt", help="prompt.txt 경로 (config의 input_dir 대신 사용)")
    parser.add_argument("--rubric", help="rubric.md 경로 (config의 paths.rubric 대신 사용)")
    parser.add_argument("--output-dir", help="출력 디렉토리 (config의 output_dir 대신 사용)")
    args = parser.parse_args()

    config_path = args.config or settings.config_path
    config = load_config(config_path)
    config = apply_env_overrides(config)

    # .env에서 경로 주입
    config["paths"] = {
        "input_dir": settings.input_dir,
        "output_dir": args.output_dir or settings.output_dir,
    }
    if args.rubric:
        config["paths"]["rubric"] = args.rubric

    setup_langsmith(config)
    llm = get_llm(config)

    # LangGraph configurable에 필요한 값 주입
    graph_config = {
        "run_name": "review",
        "configurable": {
            "llm": llm,
            "paths": config["paths"],
            "files": config["files"],
            "app_config": config,
        },
    }

    graph = build_review_graph()

    # 초기 상태
    initial_state = {
        "script": "",
        "summary": "",
        "prompt": "",
        "rubric": "",
        "context_strategy": "",
        "script_chunks": [],
        "review_result": {},
        "error": None,
    }

    logger.info("Review agent started")
    result = graph.invoke(initial_state, config=graph_config)

    if result.get("error"):
        logger.error("Review failed: %s", result["error"])
        sys.exit(1)

    output_path = Path(config["paths"]["output_dir"]) / "review_result_v1_v1.json"
    logger.info("Review completed: %s", output_path)


if __name__ == "__main__":
    main()
