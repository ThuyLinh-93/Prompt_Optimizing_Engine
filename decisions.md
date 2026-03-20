# 의사결정 기록 (2026-02-26)

## 1. 프롬프트 옵티마이저 — 프로젝트 설계

### 입력 파일 구성
- **요청**: review-agent의 입력 파일 정의
- **결정**:
  | 파일 | 형식 | 설명 |
  |------|------|------|
  | `script.json` | JSON | STT 스크립트 (summary 생성의 원본) |
  | `summary.json` | JSON | summary-agent가 생성한 요약 결과물 |
  | `prompt.txt` | 평문 텍스트 | 평가 대상 AI 에이전트 프롬프트 |
  | `rubric.md` | Markdown | 평가 루브릭 (항목별 수치 점수) |
- **주의**: 초기 논의에서 prompt를 `.json`으로 했다가 → **평문 `.txt`**로 수정

### 구현 방식
- **요청**: 독립 실행형 스크립트 vs Claude Code 커스텀 에이전트
- **결정**: **독립 실행형 Python 스크립트**
- **근거**: 로컬 LLM과 직접 연동, CLI로 자동화 가능

### LLM 선정
- **요청**: 로컬 LLM 사용
- **결정**: vLLM 서버 (`10.1.100.61:8080`) / `gaunernst/gemma-3-27b-it-int4-awq`
- **추가 결정**: OpenAI(ChatGPT)도 config로 스위칭 가능해야 함
  - `config.yaml`의 `llm.provider` 값으로 `"vllm"` | `"openai"` 전환

### 프레임워크 선정
- **요청**: LangChain 사용
- **결정**: **LangChain + LangGraph + LangSmith**
- **LangGraph 도입 시점**: 1주차부터 바로 도입
  - 현재: `load → check_context → review → parse` 단순 흐름
  - 추후: optimizer-agent 추가 시 `review → optimize → re-review` 루프로 확장
- **LangSmith**: 트레이싱/모니터링용. `.env`에 API 키 관리

### 컨텍스트 크기 관리
- **문제**: script.json / summary.json이 LLM 컨텍스트 한도 초과 가능
- **결정**: 3단계 fallback 전략
  1. **full** — 전체 입력이 한도 내 → 그대로 전달
  2. **no_script** — summary + prompt + rubric만 전달
  3. **chunked** — script를 분할 → 청크별 평가 → 집계
- **토큰 추정**: 한글 1자 ≈ 2토큰, 영문 1단어 ≈ 1.3토큰

### 입력 경로 관리
- **요청**: 샘플 파일은 다른 서버에서 scp로 특정 폴더에 넣을 것
- **결정**: `config.yaml`의 `paths.input_dir` 프로퍼티로 관리
  - CLI에서 `--config config.yaml`만 주면 input_dir에서 자동 탐색
  - 개별 파일 경로는 `--script`, `--summary` 등으로 override 가능

### 출력 형식
- **결정**: JSON 파일 (`outputs/review_result.json`)
- **스키마**: Pydantic 모델로 강제
  - 항목별: name, score, max_score, reason, improvements
  - 전체: total_score, overall_feedback, top_improvements, metadata

---

## 2. 구현 결과

### 생성된 파일
```
prompt-optimizer/
├── config.yaml
├── requirements.txt
├── .env.example
├── .gitignore
├── run_review.py                # CLI 진입점
├── docs/SPEC.md                 # 프로젝트 스펙
├── graph/
│   ├── state.py                 # ReviewState (TypedDict)
│   └── review_graph.py          # LangGraph 그래프 정의
├── agents/review/
│   ├── nodes.py                 # 6개 노드 함수 + 라우팅
│   ├── context.py               # 토큰 추정 + fallback 전략
│   └── prompts/review_system.md # 리뷰어 시스템 프롬프트
├── models/
│   └── llm_client.py            # get_llm() 팩토리 + LangSmith 설정
└── schemas/
    └── review_result.py         # Pydantic 출력 스키마
```

### 실행 방법
```bash
pip install -r requirements.txt
# .env 파일에 LANGSMITH_API_KEY, OPENAI_API_KEY 설정
# config.yaml의 paths.input_dir을 scp 대상 폴더로 변경
python run_review.py --config config.yaml
```
