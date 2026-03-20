# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# 의존성 설치
uv sync

# 리뷰 에이전트 실행
uv run python run_review.py --config config.yaml

# LangGraph Studio (그래프 시각화/디버깅)
uv run langgraph dev

# vLLM 서버 연결 확인
curl http://10.1.100.61:8080/v1/models
```

## Architecture

LangGraph 기반 review-agent. 회의록 요약 결과를 루브릭 기준으로 채점하고 프롬프트 개선안을 제시한다.

### Graph Flow

```
load_inputs → check_context → review → parse_output → END
                    ↓ (chunked)
              chunked_review → aggregate → parse_output → END
```

- **load_inputs**: `config.yaml`의 paths/files 설정으로 입력 파일 4개 로드 (script, summary, prompt, rubric)
- **check_context**: 토큰 추정 → 컨텍스트 전략 결정 (full / no_script / chunked)
- **review**: 단일 LLM 호출 (full 또는 no_script)
- **chunked_review**: script를 청크별로 나눠 각각 LLM 호출
- **aggregate**: 청크 결과 집계
- **parse_output**: Pydantic 검증 + `outputs/review_result_{score_version}_{prompt_version}.json` 저장

### Key Patterns

- **Config 전달**: `RunnableConfig`의 `config["configurable"]`로 전달. 하위 키: `llm`, `paths`, `files`, `app_config`
- **LLM 스위칭**: `config.yaml`의 `llm.provider`로 vLLM/OpenAI 전환. `models/llm_client.py`의 `get_llm()` 팩토리
- **프롬프트 조립**: `review_system.md` 템플릿에 Python `.format()`으로 변수 주입. 응답 형식은 `output_schema.json`으로 분리
- **에러 처리**: `state["error"]`에 저장, 모든 노드에서 에러 체크 후 스킵

## Tech Stack

- Python 3.13 (3.14 미지원 — langgraph-api 의존성 제약)
- uv 패키지 매니저
- LangChain + LangGraph + LangSmith
- LLM: vLLM 서버 (`10.1.100.61:8080`, Gemma 3 27B) 또는 OpenAI GPT-4o
- 한국어 프로젝트 (주석, 문서, 프롬프트 모두 한국어)

## Configuration

- `config.yaml`: LLM 엔드포인트, 파일 경로, 컨텍스트 설정
- `.env`: `LANGSMITH_API_KEY` (트레이싱용), `OPENAI_API_KEY` (OpenAI 사용 시)
- `langgraph.json`: LangGraph Studio 설정
- 입력 파일은 `inputs/` 디렉토리에 scp로 주입
