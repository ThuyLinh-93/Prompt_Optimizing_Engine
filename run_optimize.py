import argparse
import json
import sys
from pathlib import Path

import yaml

from graph.optimize_graph import build_optimize_graph
from models.llm_client import get_llm, setup_langsmith
from settings import apply_env_overrides, settings, setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Prompt Optimizer — Optimize Agent")
    parser.add_argument(
        "--config", default=None, help="config.yaml 경로 (기본: 환경변수 CONFIG_PATH)"
    )
    parser.add_argument("--prompt", required=True, help="원본 프롬프트 파일 경로")
    parser.add_argument("--review-result", required=True, help="리뷰 결과 JSON 파일 경로")
    parser.add_argument("--output-dir", help="출력 디렉토리 (config의 output_dir 대신 사용)")
    args = parser.parse_args()

    config_path = args.config or settings.config_path
    config = load_config(config_path)
    config = apply_env_overrides(config)

    config["paths"] = {
        "input_dir": settings.input_dir,
        "output_dir": args.output_dir or settings.output_dir,
    }

    setup_langsmith(config)
    llm = get_llm(config)

    # 입력 파일 읽기
    prompt_text = Path(args.prompt).read_text(encoding="utf-8")
    review_result = json.loads(Path(args.review_result).read_text(encoding="utf-8"))

    graph_config = {
        "run_name": "optimizer",
        "configurable": {
            "llm": llm,
            "paths": config["paths"],
            "app_config": config,
            "save_to_disk": True,
        },
    }

    graph = build_optimize_graph()

    initial_state = {
        "prompt": prompt_text,
        "review_result": review_result,
        "optimized_prompt": "",
        "error": None,
    }

    logger.info("Optimize agent started")
    result = graph.invoke(initial_state, config=graph_config)

    if result.get("error"):
        logger.error("Optimization failed: %s", result["error"])
        sys.exit(1)

    output_path = Path(config["paths"]["output_dir"]) / "optimized_prompts.st"
    logger.info("Optimization completed: %s", output_path)


if __name__ == "__main__":
    main()
