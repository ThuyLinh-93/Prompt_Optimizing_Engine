import json
import logging
import tempfile
from pathlib import Path

import yaml
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from graph.optimize_graph import build_optimize_graph
from graph.review_graph import build_review_graph
from models.llm_client import get_llm, setup_langsmith
from settings import apply_env_overrides, settings, setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Prompt Optimizer — Review Agent API")


def _load_config() -> dict:
    with open(settings.config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    config = apply_env_overrides(config)
    config["paths"] = {
        "input_dir": settings.input_dir,
        "output_dir": settings.output_dir,
    }
    return config


@app.post("/review")
async def review(
    script: UploadFile = File(...),
    summary: UploadFile = File(...),
    prompt: UploadFile = File(...),
    rubric: UploadFile = File(...),
    score_version: str = Form("v1"),
    prompt_version: str = Form("v1"),
):
    """multipart 파일 4개 + Form 필드 2개를 받아 리뷰 결과를 JSON으로 반환한다."""
    config = _load_config()
    setup_langsmith(config)
    llm = get_llm(config)

    # 업로드 파일 내용 읽기
    script_content = (await script.read()).decode("utf-8")
    summary_content = (await summary.read()).decode("utf-8")
    prompt_content = (await prompt.read()).decode("utf-8")
    rubric_content = (await rubric.read()).decode("utf-8")

    graph_config = {
        "run_name": "review",
        "configurable": {
            "llm": llm,
            "paths": config["paths"],
            "files": config.get("files", {}),
            "app_config": config,
            "score_version": score_version,
            "prompt_version": prompt_version,
        },
    }

    initial_state = {
        "script": script_content,
        "summary": summary_content,
        "prompt": prompt_content,
        "rubric": rubric_content,
        "context_strategy": "",
        "script_chunks": [],
        "review_result": {},
        "error": None,
    }

    graph = build_review_graph()
    result = graph.invoke(initial_state, config=graph_config)

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    output_dir = config["paths"]["output_dir"]
    filename = f"review_result_{score_version}_{prompt_version}.json"

    response_dir = settings.result_base_path or str(Path(output_dir).resolve())
    result_file_path = f"{response_dir}/{filename}"

    total_score = result.get("review_result", {}).get("total_score", 0)

    return {
        "total_score": float(total_score),
        "result_file_path": result_file_path,
        "input_files": {
            "script": script.filename,
            "summary": summary.filename,
            "prompt": prompt.filename,
            "rubric": rubric.filename,
        },
    }


@app.post("/optimize")
async def optimize(
    prompt: UploadFile = File(...),
    review_result: UploadFile = File(...),
):
    """프롬프트 + 리뷰결과 2개 파일을 받아 개선된 프롬프트를 FileResponse로 반환한다."""
    config = _load_config()
    setup_langsmith(config)
    llm = get_llm(config)

    prompt_content = (await prompt.read()).decode("utf-8")
    review_result_content = (await review_result.read()).decode("utf-8")

    try:
        review_result_dict = json.loads(review_result_content)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"review_result JSON 파싱 실패: {e}")

    graph_config = {
        "run_name": "optimizer",
        "configurable": {
            "llm": llm,
            "paths": config["paths"],
            "app_config": config,
            "save_to_disk": False,
        },
    }

    initial_state = {
        "prompt": prompt_content,
        "review_result": review_result_dict,
        "optimized_prompt": "",
        "error": None,
    }

    graph = build_optimize_graph()
    result = graph.invoke(initial_state, config=graph_config)

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".st", delete=False, encoding="utf-8"
    )
    tmp.write(result["optimized_prompt"])
    tmp.close()

    return FileResponse(
        path=tmp.name,
        media_type="text/plain",
        filename="optimized_prompts.st",
    )
