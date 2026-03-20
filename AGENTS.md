# AGENTS

## Project Goal

- Build an AI agent that improves a prompt using an evaluation rubric.

## Product Requirements (Current)

### Phase 1: Prompt Optimization (Completed)
- Input: two files (`rubric`, `prompt`).
- API style: REST endpoint with `multipart/form-data`.
- Output: JSON response containing improved prompt.
- Persistence: store optimization artifacts locally.
- LLM strategy: provider abstraction (`moonshot`, `openai`, `local`).
- Initial mode: single-pass optimization.

### Phase 2: Meeting Summary Generation (In Progress)
- Input: two files (`script`, `improvedPrompt`).
  - `script`: STT 변환된 회의 음성 파일 (텍스트)
  - `improvedPrompt`: 개선된 프롬프트 파일 (Phase 1의 결과)
- API style: REST endpoint with `multipart/form-data`.
- Output: JSON response containing summary metadata + `summary.json` file.
- Output format: `src/main/resources/template_schema.json` 스키마 준수
- Persistence: store summary artifacts locally (Docker/Local 환경 호환).
- LLM strategy: provider abstraction (기존 LlmClient 재사용).

## Current Status

- Phase 1-5 완료: MVP 구현 완료
- 기술 스택: Kotlin + Spring Boot 3.4.3 + Spring WebFlux (Reactor 기반)
- 테스트: `./gradlew test` 및 `./gradlew build` 성공

## Architecture Overview

### Phase 1: Prompt Optimization

```
┌─────────────────────────────────────────────────────────────┐
│                        Web Layer                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │    OptimizePromptController (POST /api/v1/optimize) │   │
│  │    - multipart/form-data 파일 수신                   │   │
│  │    - 파일 유효성 검사 (size, empty)                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                     Use Case Layer                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │      OptimizePromptUseCase                          │   │
│  │      - 프롬프트 조합 (rubric + prompt)              │   │
│  │      - LLM 클라이언트 호출                          │   │
│  │      - 결과 저장소 연동                             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                     Infrastructure Layer                    │
│  ┌─────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │   LlmClient │  │ OptimizationResult│  │ Error Handler │ │
│  │  Interface  │  │     Storage       │  │               │ │
│  └──────┬──────┘  └──────────────────┘  └────────────────┘ │
│         │                                                   │
│  ┌──────┴──────┐                                            │
│  │ Delegating  │──┬─ MoonshotLlmClient                      │
│  │LlmClient    │  ├─ OpenAiLlmClient                        │
│  │            │  └─ LocalOpenAiCompatibleLlmClient         │
│  └─────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

### Phase 2: Meeting Summary Generation

```
┌─────────────────────────────────────────────────────────────┐
│                        Web Layer                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │   SummarizeMeetingController (POST /api/v1/summarize)│  │
│  │    - multipart/form-data 파일 수신                   │   │
│  │    - script + improvedPrompt 파일 처리               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                     Use Case Layer                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │      SummarizeMeetingUseCase                        │   │
│  │      - script + improved prompt 조합                │   │
│  │      - LLM 클라이언트 호출 (JSON 출력 요청)         │   │
│  │      - summary.json 저장소 연동                     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                     Infrastructure Layer                    │
│  ┌─────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │   LlmClient │  │  MeetingSummary  │  │ Error Handler │ │
│  │  Interface  │  │     Storage      │  │               │ │
│  └──────┬──────┘  └──────────────────┘  └────────────────┘ │
│         │                                                   │
│  ┌──────┴──────┐  ┌──────────────────────────────────────┐ │
│  │ Delegating  │──┼─ MoonshotLlmClient (JSON mode)       │ │
│  │LlmClient    │  ├─ OpenAiLlmClient                     │ │
│  │            │  └─ LocalOpenAiCompatibleLlmClient       │ │
│  └─────────────┘     (with response_format=json_schema)   │ │
└─────────────────────────────────────────────────────────────┘
```

## API Specification

### POST /api/v1/optimize

프롬프트 최적화 요청을 처리하는 REST 엔드포인트.

**Request**
- Content-Type: `multipart/form-data`
- Parameters:
  - `rubric` (required): 평가 기준이 담긴 텍스트 파일
  - `prompt` (required): 개선할 프롬프트 텍스트 파일

**Response** (200 OK)
- Content-Type: `text/plain`
- Content-Disposition: `attachment; filename="improved_prompt_v1.txt"`
- Body: 개선된 프롬프트 파일 (다운로드)

**Error Responses**
- `400 Bad Request`: 파일 누락, 빈 파일, 파일 크기 초과
- `500 Internal Server Error`: LLM 호출 실패, 저장소 오류

### POST /api/v1/summarize

회의 음성 script와 개선된 프롬프트를 받아 요약을 생성하는 REST 엔드포인트.

**Request**
- Content-Type: `multipart/form-data`
- Parameters:
  - `script` (required): STT 변환된 회의 음성 텍스트 파일
  - `improvedPrompt` (required): Phase 1에서 생성된 개선된 프롬프트 파일

**Response** (200 OK)
- Content-Type: `application/json`
- Content-Disposition: `attachment; filename="summary_xxx.json"`
- Body: 회의 요약 JSON 파일 (다운로드)

**Error Responses**
- `400 Bad Request`: 파일 누락, 빈 파일, 파일 크기 초과, JSON 파싱 오류
- `500 Internal Server Error`: LLM 호출 실패, 저장소 오류, 스키마 검증 실패

## Configuration

### application.properties

```properties
app.llm.provider=moonshot
app.llm.model=kimi-k2
app.llm.timeout-seconds=60
app.llm.api-key=${LLM_API_KEY:}

app.llm.moonshot.base-url=https://api.moonshot.ai/v1
app.llm.moonshot.api-key=${MOONSHOT_API_KEY:}
app.llm.openai.base-url=https://api.openai.com/v1
app.llm.openai.model=gpt-4o-mini
app.llm.openai.api-key=${OPENAI_API_KEY:}
app.llm.local.base-url=http://localhost:11434/v1
app.llm.local.model=local-model
app.llm.local.api-key=${LOCAL_LLM_API_KEY:}

app.storage.output-dir=outputs
```

## Key Components

| Component | Path | Responsibility |
|-----------|------|----------------|
| Controller | `web/OptimizePromptController.kt` | HTTP 요청/응답 처리, 파일 검증 |
| UseCase | `optimize/OptimizePromptUseCase.kt` | 비즈니스 로직, orchestration |
| PromptComposer | `optimize/PromptComposer.kt` | LLM 입력용 프롬프트 조합 |
| LlmClient Interface | `llm/LlmClient.kt` | Provider-agnostic LLM 인터페이스 |
| Moonshot Adapter | `llm/MoonshotLlmClient.kt` | Moonshot API 구현체 |
| OpenAI Adapter | `llm/OpenAiLlmClient.kt` | OpenAI API 구현체 |
| Local Adapter | `llm/LocalOpenAiCompatibleLlmClient.kt` | Local LLM 구현체 |
| Delegating Client | `llm/DelegatingLlmClient.kt` | 설정 기반 Provider 선택 |
| Storage | `storage/LocalFileOptimizationResultStorage.kt` | JSON 파일 저장 |
| Error Handler | `web/ApiExceptionHandler.kt` | 전역 예외 처리 |

## Workflow Rules

- Initialize and maintain task breakdown in `docs/tasks.md`.
- Record user-assistant prompt history in `docs/prompt_history.md`.
- Keep implementation aligned with Kotlin + Spring Boot/WebFlux direction.
- **No Kotlin Coroutines**: WebFlux Reactor만 사용 (Mono/Flux).
- **API Key 정책**: Provider별 `api-key`를 우선 사용하고, 공통 `app.llm.api-key`는 fallback으로만 사용.
