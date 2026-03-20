# LangGraph Studio 연결 가이드

## 개요

review-agent의 LangGraph 그래프를 Studio UI에서 시각화·디버깅할 수 있도록 연결하는 과정을 정리한다.

## 사전 조건

- Python **3.13** (3.14는 `langgraph-api` 의존성인 `jsonschema-rs`의 PyO3가 미지원)
- uv 패키지 매니저
- LangSmith API Key (`.env`에 설정)

## 작업 내역

### 1. Python 버전 고정

`langgraph-cli[inmem]`의 하위 의존성(`jsonschema-rs` → PyO3)이 Python 3.14를 지원하지 않아 3.13으로 고정했다.

```bash
uv python pin 3.13
```

이 명령은 `.python-version` 파일을 생성/수정하여 uv가 항상 3.13을 사용하도록 한다.

`pyproject.toml`의 `requires-python`도 함께 변경:

```toml
requires-python = ">=3.13"
```

### 2. langgraph-cli[inmem] 설치

```bash
uv add "langgraph-cli[inmem]"
```

`[inmem]` extra는 로컬 인메모리 서버를 띄우기 위한 런타임(`langgraph-api`, `langgraph-runtime-inmem`)을 포함한다.

### 3. langgraph.json 생성 (프로젝트 루트)

```json
{
  "graphs": {
    "review": "./graph/review_graph.py:graph"
  },
  "env": ".env",
  "dependencies": ["."]
}
```

| 키 | 설명 |
|---|---|
| `graphs` | Studio에 노출할 그래프. `모듈경로:변수명` 형식 |
| `env` | 환경변수 파일 경로 |
| `dependencies` | pip install 대상. `"."` = 현재 프로젝트(pyproject.toml 기준) |

### 4. 모듈 레벨 graph 변수 추가

`graph/review_graph.py` 맨 아래에 compiled graph를 모듈 레벨 변수로 노출해야 Studio가 인식한다.

```python
# 기존 build_review_graph() 함수는 그대로 유지

# LangGraph Studio용 모듈 레벨 변수
graph = build_review_graph()
```

### 5. .env 설정

```env
LANGSMITH_API_KEY=lsv2_pt_xxxxx
```

LangSmith Personal API Key를 사용한다. Service Key는 workspace 권한 문제로 403이 발생할 수 있다.

## 실행 방법

```bash
uv run langgraph dev
```

정상 기동 시 아래 정보가 출력된다:

| 항목 | URL |
|---|---|
| API | http://127.0.0.1:2024 |
| Studio UI | https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024 |
| API Docs | http://127.0.0.1:2024/docs |

브라우저에서 Studio UI URL을 열면 그래프 노드 흐름 시각화, 입력 테스트, LangSmith 트레이싱을 확인할 수 있다.

## 수정된 파일 목록

| 파일 | 변경 내용 |
|---|---|
| `.python-version` | `3.14` → `3.13` |
| `pyproject.toml` | `requires-python` 변경, `langgraph-cli[inmem]` 의존성 추가 |
| `langgraph.json` | 신규 생성 — Studio 설정 파일 |
| `graph/review_graph.py` | 모듈 레벨 `graph = build_review_graph()` 추가 |

## 트러블슈팅

### Python 3.14 호환성 오류

```
error: Failed to build `jsonschema-rs==0.29.1`
pyo3_build_config: Unsupported Python version: 3.14
```

→ `uv python pin 3.13`으로 해결. uv는 `.python-version` 파일이 있으면 해당 버전으로 venv를 생성한다.

### `No dependencies found in config` 오류

```
Error: No dependencies found in config.
```

→ `langgraph.json`에 `"dependencies": ["."]` 추가로 해결.
