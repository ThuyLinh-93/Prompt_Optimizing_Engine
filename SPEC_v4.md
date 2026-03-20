# Prompt Optimizer — Review Agent 스펙

## Context

프롬프트 옵티마이저 시스템의 **review-agent**를 구현한다.
summary-agent가 `scripts_.json`(STT 원문) + `prompts_.st`(시스템 프롬프트)을 받아 `summary_.json`(요약 결과)을 생성하는 파이프라인이 이미 존재한다.
review-agent는 이 요약 결과가 얼마나 잘 되었는지 루브릭 기준으로 평가하고, 프롬프트 개선안을 제시한다.

**LLM**: vLLM 서버 (`10.1.100.61:8080`) / `gaunernst/gemma-3-27b-it-int4-awq`
**프레임워크**: LangChain + LangGraph + LangSmith (트레이싱/모니터링)
**API 서버**: FastAPI (n8n 연동용)
**패키지 매니저**: uv
**Python**: 3.13

## 프로젝트 구조

```
prompt-optimizer/
├── config.yaml                  # LLM 엔드포인트, 경로, 서버, 컨텍스트 설정 (기본값)
├── langgraph.json               # LangGraph Studio 설정
├── pyproject.toml               # 프로젝트 의존성 (uv)
├── .python-version              # Python 3.13 고정
├── Dockerfile                   # Docker 이미지 빌드
├── docker-compose.yml           # Docker Compose 배포
├── .dockerignore
├── api_server.py                # FastAPI 서버 (POST /review, POST /optimize)
├── run_review.py                # CLI 진입점 (리뷰)
├── run_optimize.py              # CLI 진입점 (최적화)
├── settings.py                  # 환경변수 설정 + apply_env_overrides() + setup_logging()
├── graph/
│   ├── __init__.py
│   ├── state.py                 # LangGraph 상태 정의 (TypedDict)
│   ├── review_graph.py          # 리뷰 그래프 정의
│   └── optimize_graph.py        # 최적화 그래프 정의
├── agents/
│   └── review/
│       ├── __init__.py
│       ├── nodes.py             # 그래프 노드 함수들
│       ├── context.py           # 컨텍스트 크기 관리 (청킹/트리밍)
│       └── prompts/
│           ├── review_system.md # 리뷰어 시스템 프롬프트
│           └── output_schema.json # LLM 응답 JSON 형식 정의
├── models/
│   ├── __init__.py
│   └── llm_client.py           # LangChain ChatOpenAI 클라이언트 (vLLM/OpenAI)
├── schemas/
│   ├── __init__.py
│   └── review_result.py        # 출력 JSON 스키마 (Pydantic)
├── tests/
│   ├── __init__.py
│   ├── test_settings.py        # 환경변수 오버라이드 + 로깅 설정 테스트
│   └── test_review_api.py      # /review API 엔드포인트 테스트
├── sample/
│   ├── inputs/                  # 테스트용 샘플 파일
│   │   ├── scripts_.json
│   │   ├── summary_.json
│   │   ├── prompts_.st
│   │   └── score_.json
│   └── outputs/                 # CLI 테스트 결과 저장
├── docs/
│   └── SPEC_v4.md               # 본 문서
├── .env                         # 시크릿 + 환경변수 오버라이드
└── .env.example                 # .env 템플릿
```

## 실행 모드

### 1. API 서버 (n8n 연동)

n8n에서 multipart/form-data로 파일 4개 + Form 필드 2개를 전송하면, 리뷰 결과를 디스크에 저장하고 JSON 응답을 반환한다.

```bash
# 로컬 기동
uv run uvicorn api_server:app --host 0.0.0.0 --port 8080

# Docker 기동
docker compose up -d
```

**엔드포인트: `POST /review`**

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `script` | `UploadFile` | O | STT 원문 JSON |
| `summary` | `UploadFile` | O | 요약 결과 JSON |
| `prompt` | `UploadFile` | O | summary-agent 시스템 프롬프트 |
| `rubric` | `UploadFile` | O | 평가 루브릭 JSON |
| `score_version` | `Form(str)` | X | 채점 루브릭 버전 (기본값: `"v1"`) |
| `prompt_version` | `Form(str)` | X | 프롬프트 버전 (기본값: `"v1"`) |

**요청 예시 (curl):**
```bash
curl -X POST http://localhost:8085/review \
    -F "script=@scripts_.json" \
    -F "summary=@summary_.json" \
    -F "prompt=@prompts_.st" \
    -F "rubric=@score_.json" \
    -F "score_version=v1" \
    -F "prompt_version=v1"
```

**응답 (200 OK):**
```json
{
    "total_score": 85.0,
    "result_file_path": "/DATA/WEB/airnote-agent/squad/review/outputs/review_result_v1_v1.json",
    "input_files": {
        "script": "scripts_.json",
        "summary": "summary_.json",
        "prompt": "prompts_.st",
        "rubric": "score_.json"
    }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `total_score` | `float` | 리뷰 총점 |
| `result_file_path` | `string` | 결과 파일 경로. `RESULT_BASE_PATH` 설정 시 해당 경로 기준, 미설정 시 `OUTPUT_DIR` 절대경로 |
| `input_files` | `object` | 입력으로 받은 파일들의 원본 파일명 |
| `input_files.script` | `string` | STT 원문 파일명 |
| `input_files.summary` | `string` | 요약 결과 파일명 |
| `input_files.prompt` | `string` | 시스템 프롬프트 파일명 |
| `input_files.rubric` | `string` | 평가 루브릭 파일명 |

**에러 응답 (500):**
```json
{"detail": "에러 메시지"}
```

**API 모드 동작:**
1. 업로드 파일을 UTF-8 문자열로 읽어 `initial_state`에 직접 주입
2. `load_inputs` 노드는 state에 값이 있으면 디스크 로드 스킵
3. `parse_output` 노드가 output_dir에 결과 파일 저장
4. `total_score`(float), 결과 파일 절대경로, 입력 파일명을 JSON body로 반환

### 2. CLI

```bash
uv run python run_review.py --config config.yaml
```

결과 파일: `{OUTPUT_DIR}/review_result_v1_v1.json`

### 3. Docker 배포

```bash
docker compose up -d
```

| 항목 | 값 |
|---|---|
| 포트 매핑 | `8085:8085` |
| 볼륨 | 호스트 디렉토리 → `/app` 하위 경로 |
| 출력 경로 | 환경변수 `OUTPUT_DIR`로 지정 (컨테이너 내부 경로) |
| 응답 경로 | 환경변수 `RESULT_BASE_PATH`로 호스트 경로 지정 |
| 로그 | 환경변수 `LOG_FILE`로 지정 (컨테이너 내부 경로, 볼륨으로 호스트에 노출) |
| 환경변수 | `.env` 파일 마운트 |

## 입력 파일

| 파일 | 설명 |
|---|---|
| `scripts_.json` | STT 원문 (stt 배열: blockid, speakerName, content, index) |
| `summary_.json` | 요약 결과 (mainKeywords, mainTasks, meetingContent, upcomingSchedule) |
| `prompts_.st` | summary-agent 시스템 프롬프트 (평문 텍스트) |
| `score_.json` | 평가 루브릭 (100점 감점 기반, 5개 카테고리 + hard_cap_rules) |

## LangGraph 설계

### 상태 (`graph/state.py`)

```python
class ReviewState(TypedDict):
    script: str              # scripts_.json 원문
    summary: str             # summary_.json 원문
    prompt: str              # prompts_.st 원문
    rubric: str              # score_.json 원문
    context_strategy: str    # "full" | "no_script" | "chunked"
    script_chunks: list[str] # 청킹된 script (chunked 전략 시)
    review_result: dict      # 최종 리뷰 결과 JSON
    error: str | None        # 에러 메시지
```

### 그래프 흐름

```
[load_inputs] → [check_context] → [review] → [parse_output] → END
                       ↓ (chunked)
                 [chunked_review] → [aggregate] → [parse_output] → END
```

**노드 설명:**
1. **load_inputs** — state에 값이 없으면 디스크에서 파일 4개 로드 (API 모드에서는 스킵)
2. **check_context** — 전체 토큰 추정 → 전략 결정 (full / no_script / chunked)
3. **review** — LLM 호출 (full 또는 no_script 전략)
4. **chunked_review** — script를 청크별로 나눠 각각 LLM 호출
5. **aggregate** — 청크별 결과를 집계하여 최종 점수 산출
6. **parse_output** — LLM 응답을 Pydantic 스키마로 파싱 + 항상 디스크에 저장

**조건부 엣지:**
- `check_context` → strategy가 "chunked"이면 `chunked_review`, 아니면 `review`
- error 발생 시 → `parse_output`으로 직행

### 결과 파일 네이밍

`review_result_{score_version}_{prompt_version}.json`

- `score_version`: 채점 루브릭 버전 (API Form 필드 또는 기본값 "v1")
- `prompt_version`: 프롬프트 버전 (API Form 필드 또는 기본값 "v1")

### 결과 JSON metadata

`parse_output` 노드가 결과 JSON에 `metadata` 필드를 자동 추가한다.

```json
{
    "metadata": {
        "model": "vllm",
        "timestamp": "2026-03-10T08:35:07.140863+00:00",
        "context_strategy": "full",
        "score_version": "v1",
        "prompt_version": "v1"
    }
}
```

### `configurable` 구조

그래프 실행 시 `RunnableConfig`에 전달되는 설정:

```python
graph_config = {
    "configurable": {
        "llm": ChatOpenAI,          # LLM 클라이언트 인스턴스
        "paths": {
            "input_dir": "./sample/inputs",
            "output_dir": "./outputs",
        },
        "files": {                   # CLI 모드에서 파일명 매핑
            "script": "scripts_.json",
            "summary": "summary_.json",
            "prompt": "prompts_.st",
            "rubric": "score_.json",
        },
        "app_config": { ... },       # config.yaml 전체
        "score_version": "v1",       # 채점 루브릭 버전
        "prompt_version": "v1",      # 프롬프트 버전
    }
}
```

## 환경변수 설정 (`settings.py`)

pydantic-settings 기반으로 환경변수를 중앙 관리한다. `.env` 파일을 자동 로드하며, OS 환경변수로도 오버라이드 가능.

### 기본 설정

| 환경변수 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `CONFIG_PATH` | `str` | `config.yaml` | config.yaml 경로 |
| `LOG_LEVEL` | `str` | `INFO` | 로그 레벨 (DEBUG/INFO/WARNING/ERROR) |
| `LOG_FILE` | `str` | (없음) | 로그 파일 경로. 미설정 시 콘솔만 |
| `LANGSMITH_API_KEY` | `str` | `""` | LangSmith API Key |
| `OPENAI_API_KEY` | `str` | `""` | OpenAI API Key |
| `INPUT_DIR` | `str` | (필수) | 입력 파일 디렉토리 |
| `OUTPUT_DIR` | `str` | (필수) | 출력 파일 디렉토리 |
| `RESULT_BASE_PATH` | `str` | (없음) | API 응답의 `result_file_path`에 사용할 경로. 미설정 시 `OUTPUT_DIR` 절대경로 사용 |

### config.yaml 오버라이드

`config.yaml`은 기본값으로 유지하되, 환경변수가 설정되면 해당 값을 덮어쓴다.
미설정(None)이면 `config.yaml` 값을 그대로 사용한다.
`apply_env_overrides(config)`가 엔트리포인트 3곳(`run_review.py`, `run_optimize.py`, `api_server.py`)에서 config.yaml 로드 직후 호출된다.

| 환경변수 | config.yaml 경로 | 타입 |
|---------|-----------------|------|
| `LANGSMITH_ENABLED` | `langsmith.enabled` | `bool` |
| `LLM_PROVIDER` | `llm.provider` | `str` |
| `VLLM_BASE_URL` | `llm.vllm.base_url` | `str` |
| `VLLM_MODEL` | `llm.vllm.model` | `str` |
| `OPENAI_MODEL` | `llm.openai.model` | `str` |
| `LLM_TEMPERATURE` | `llm.temperature` | `float` |
| `LLM_MAX_TOKENS` | `llm.max_tokens` | `int` |
| `SERVER_HOST` | `server.host` | `str` |
| `SERVER_PORT` | `server.port` | `int` |
| `FILE_SCRIPT` | `files.script` | `str` |
| `FILE_SUMMARY` | `files.summary` | `str` |
| `FILE_PROMPT` | `files.prompt` | `str` |
| `FILE_RUBRIC` | `files.rubric` | `str` |
| `CONTEXT_MAX_INPUT_TOKENS` | `context.max_input_tokens` | `int` |
| `CONTEXT_STRATEGY` | `context.strategy` | `str` |
| `CONTEXT_CHUNK_SIZE` | `context.chunk_size` | `int` |

### 설정 우선순위

```
OS 환경변수 > .env 파일 > config.yaml (기본값)
```

### `.env.example`

```env
LANGSMITH_API_KEY=
OPENAI_API_KEY=
INPUT_DIR=./squad/sample/inputs
OUTPUT_DIR=./squad/review/outputs
# RESULT_BASE_PATH=/DATA/WEB/airnote-agent/squad/review/outputs
# LOG_LEVEL=INFO
# LOG_FILE=/app/squad/logs/review-agent.log

# --- config.yaml 오버라이드 (설정 시 config.yaml 값 대신 사용) ---
# LANGSMITH_ENABLED=true
# LLM_PROVIDER=vllm
# VLLM_BASE_URL=http://10.1.100.61:8080/v1
# VLLM_MODEL=gaunernst/gemma-3-27b-it-int4-awq
# OPENAI_MODEL=gpt-4o
# LLM_TEMPERATURE=0.3
# LLM_MAX_TOKENS=4096
# SERVER_HOST=0.0.0.0
# SERVER_PORT=8000
# FILE_SCRIPT=script.json
# FILE_SUMMARY=summary.json
# FILE_PROMPT=prompt.txt
# FILE_RUBRIC=rubric.md
# CONTEXT_MAX_INPUT_TOKENS=32000
# CONTEXT_STRATEGY=auto
# CONTEXT_CHUNK_SIZE=2000
```

## config.yaml

```yaml
llm:
  provider: "vllm"
  vllm:
    base_url: "http://10.1.100.61:8080/v1"
    model: "gaunernst/gemma-3-27b-it-int4-awq"
  openai:
    model: "gpt-4o"
  temperature: 0.3
  max_tokens: 4096

langsmith:
  enabled: true
  project: "prompt-optimizer"

server:
  host: "0.0.0.0"
  port: 8080

files:
  script: "scripts_.json"
  summary: "summary_.json"
  prompt: "prompts_.st"
  rubric: "score_.json"

context:
  max_input_tokens: 32000
  strategy: "auto"               # auto | full | no_script | chunked
  chunk_size: 2000
```

## 로깅

### 설정

`setup_logging()`이 모든 엔트리포인트에서 모듈 로드 시 호출된다.

- **콘솔**: 항상 출력
- **파일**: `LOG_FILE` 환경변수 설정 시 추가. 디렉토리 자동 생성
- **포맷**: `2026-03-10 14:30:00,123 [INFO] agents.review.nodes - LLM call started (strategy: full)`
- **레벨**: `LOG_LEVEL` 환경변수로 제어 (기본: `INFO`)

### 리뷰 에이전트 로그 포인트

| 노드 | 레벨 | 로그 메시지 |
|------|------|------------|
| `load_inputs` | INFO | `Loading input files from {path}` |
| `load_inputs` | INFO | `Input files loaded (script={n} chars, summary={n} chars)` |
| `load_inputs` | INFO | `Inputs already present in state, skipping disk load` |
| `load_inputs` | ERROR | `Input file not found: {error}` |
| `check_context` | INFO | `Context strategy resolved: {strategy}` |
| `check_context` | INFO | `Script split into {n} chunks` |
| `review` | INFO | `LLM call started (strategy: {strategy})` |
| `review` | INFO | `LLM response received ({n} chars)` |
| `chunked_review` | INFO | `Chunked review started ({n} chunks)` |
| `chunked_review` | INFO | `Chunk {i}/{n} LLM call` / `response received ({n} chars)` |
| `chunked_review` | INFO | `Chunked review completed` |
| `aggregate` | INFO | `Aggregation LLM call ({n} chunks)` |
| `aggregate` | INFO | `Aggregation response received ({n} chars)` |
| `parse_output` | INFO | `Parsing LLM response ({n} chars)` |
| `parse_output` | ERROR | `JSON parse failed: {error}` |
| `parse_output` | ERROR | `Schema validation failed: {error}` |
| `parse_output` | DEBUG | `Review result:\n{json}` |
| `parse_output` | INFO | `Review result saved: {path} (total_score: {score})` |

## 핵심 모듈

### `api_server.py`
- FastAPI 앱. `POST /review`, `POST /optimize` 엔드포인트
- `/review`: multipart/form-data 파일 4개 + Form 필드 2개 수신 → 그래프 실행 → JSON 응답 (total_score, result_file_path, input_files)
- `/optimize`: 프롬프트 + 리뷰결과 2개 파일 수신 → 최적화 → FileResponse

### `models/llm_client.py`
- `config.yaml`의 `llm.provider` 값에 따라 클라이언트 생성:
  - `"vllm"` → `ChatOpenAI(base_url=vllm.base_url, model=vllm.model)`
  - `"openai"` → `ChatOpenAI(model=openai.model)` (OPENAI_API_KEY는 .env)
- `get_llm(config)` 팩토리 함수로 provider 스위칭
- `setup_langsmith(config)` — `langsmith.enabled`가 true이면 트레이싱 활성화

### `agents/review/context.py`
**3단계 fallback:**
1. **full** — 모든 입력이 컨텍스트 한도 내 → 그대로 전달
2. **no_script** — summary + prompt + rubric만 전달
3. **chunked** — script를 분할 → 각 청크별 부분 평가 → 집계

토큰 추정: 글자 수 기반 (한글 1자 ≈ 2토큰, 영문 1단어 ≈ 1.3토큰)

### `agents/review/prompts/`
- **`review_system.md`** — 리뷰 시스템 프롬프트 템플릿. Python `.format()`으로 변수 주입 (`{rubric}`, `{prompt}`, `{summary}`, `{script}`, `{output_schema}`)
- **`output_schema.json`** — LLM 응답 JSON 형식 정의. `.format()`과 분리되어 이스케이프 없이 관리

### `schemas/review_result.py`

```python
class CriterionResult(BaseModel):
    name: str               # 루브릭 항목명
    score: float            # 획득 점수
    max_score: float        # 만점
    reason: str             # 점수 근거
    improvements: list[str] # 개선 제안

class ReviewResult(BaseModel):
    total_score: float
    max_total_score: float
    criteria: list[CriterionResult]
    overall_feedback: str
    top_improvements: list[str]  # 우선순위 높은 개선안 3-5개
    metadata: dict               # model, timestamp, context_strategy 등
```

## 리뷰 프롬프트 (`review_system.md`)

```
너는 AI 회의록 요약 프롬프트 품질 평가자다.
아래 평가 루브릭에 따라, 주어진 프롬프트가 STT 원문을 요약한 결과를 평가하라.

평가 시 다음을 확인하라:
1. 요약 결과가 STT 원문의 핵심 내용을 정확히 반영하는가
2. 루브릭의 각 카테고리별 감점 기준에 해당하는 문제가 있는가
3. hard_cap_rules에 해당하는 심각한 문제(환각, 결정사항 왜곡)가 있는가

## 평가 루브릭
{rubric}

## 평가 대상 프롬프트
{prompt}

## 프롬프트가 생성한 요약 결과
{summary}

## 원본 STT 데이터
{script}

## 응답 형식
{output_schema}
```

## 테스트

```bash
uv run pytest tests/ -v
```

| 테스트 파일 | 항목 수 | 검증 내용 |
|---|---|---|
| `test_settings.py` | 9 | 환경변수 오버라이드 (LLM, LangSmith, Server, Files, Context), 콘솔/파일 로깅 |
| `test_review_api.py` | 5 | JSON 응답 구조 (total_score float, input_files), 기본/커스텀 버전, 절대경로, 에러 500 |

## 검증 방법

### CLI
```bash
uv run python run_review.py --config config.yaml
# → {OUTPUT_DIR}/review_result_v1_v1.json 생성 확인
# → 콘솔 로그에 각 노드 진행 상황 출력 확인
```

### API
```bash
uv run uvicorn api_server:app --host 0.0.0.0 --port 8080

curl -X POST http://localhost:8080/review \
    -F "script=@sample/inputs/scripts_.json" \
    -F "summary=@sample/inputs/summary_.json" \
    -F "prompt=@sample/inputs/prompts_.st" \
    -F "rubric=@sample/inputs/score_.json" \
    -F "score_version=v1" \
    -F "prompt_version=v1"
# → {"total_score": 85.0, "result_file_path": "/abs/path/review_result_v1_v1.json", "input_files": {"script": "scripts_.json", "summary": "summary_.json", "prompt": "prompts_.st", "rubric": "score_.json"}}
```

### Docker
```bash
docker compose up -d

curl -X POST http://localhost:8085/review \
    -F "script=@scripts_.json" \
    -F "summary=@summary_.json" \
    -F "prompt=@prompts_.st" \
    -F "rubric=@score_.json" \
    -F "score_version=v1" \
    -F "prompt_version=v1"
# → JSON 응답 + OUTPUT_DIR에 파일 저장 확인
# → LOG_FILE 경로에 로그 기록 확인
```

### LangGraph Studio
```bash
uv run langgraph dev
# → Studio UI에서 그래프 흐름 시각화/디버깅
```
