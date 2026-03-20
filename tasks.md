# Tasks

## Phase 1 - Foundation

- [x] Add Spring WebFlux dependencies (without Kotlin coroutine dependencies).
- [x] Define configuration properties for provider selection, model, timeouts, and storage path.
- [x] Add base package structure (`web`, `optimize`, `llm`, `storage`, `error`, `config`).

## Phase 2 - Optimize API

- [x] Implement `POST /api/v1/optimize` endpoint.
- [x] Accept `multipart/form-data` with `rubric` and `prompt` file parts.
- [x] Validate file size and empty-file conditions.
- [x] Return JSON response with improved prompt and metadata.

## Phase 3 - LLM Abstraction

- [x] Define provider-agnostic `LlmClient` interface.
- [x] Implement Moonshot adapter (OpenAI-compatible chat completions).
- [x] Implement local LLM adapter with compatible API shape.
- [x] Add provider switch logic from configuration.

## Phase 4 - Persistence

- [x] Define artifact model for optimization result.
- [x] Persist optimization artifacts as JSON files in local output directory.
- [x] Include request id, timestamps, provider/model, input and output text.

## Phase 5 - Quality and Verification

- [x] Add controller/use-case unit tests.
- [x] Add error handling for bad input and upstream failures.
- [x] Run `./gradlew test` and `./gradlew build`.
- [x] Update `docs/prompt_history.md` with major requirement decisions.

## Phase 6 - Meeting Summary Generation

### Planning
- [x] AGENTS.md 업데이트 - 새로운 회의 요약 기능 아키텍처 및 스펙 문서화
- [x] tasks.md 업데이트 - Phase 6 작업 목록 정리

### Implementation
- [x] template_schema.json 분석 및 데이터 모델 설계 (MeetingSummary, TaskItem 등)
- [x] POST /api/v1/summarize 엔드포인트 구현 (SummarizeMeetingController)
- [x] SummarizeMeetingUseCase 구현 - script + improved prompt 조합 및 LLM 호출
- [x] MeetingSummaryStorage 인터페이스 및 LocalFileMeetingSummaryStorage 구현
- [x] Docker/Local 환경 호환되는 파일 저장 경로 설정 (SummarizeProperties)
- [x] LLM JSON 출력 설정 (response_format=json_schema 지원)

### Testing & Verification
- [x] SummarizeMeetingController 단위 테스트
- [x] SummarizeMeetingUseCase 단위 테스트 (통합 테스트로 커버됨)
- [x] 통합 테스트 (end-to-end)
- [x] `./gradlew test` 및 `./gradlew build` 성공 확인

## Phase 7 - OpenAI Provider Support

### Implementation
- [x] `app.llm.provider`에 `openai` 선택지 추가
- [x] OpenAI 전용 base URL/model 설정 프로퍼티 추가
- [x] `DelegatingLlmClient`에 OpenAI provider 라우팅 추가
- [x] OpenAI chat completions 어댑터 구현 및 기존 요청 DTO 재사용
- [x] use case 모델 선택 로직을 provider별로 확장

### Documentation & Verification
- [x] 설정 예시 및 운영 문서에 OpenAI provider 지원 내용 반영
- [x] `./gradlew test` 및 `./gradlew build`로 OpenAI provider 변경 포함 검증

## Phase 8 - Provider-Specific API Key Support

### Implementation
- [x] `LlmProperties`에 provider별 `api-key` 설정 및 공통 fallback 해석 로직 추가
- [x] Moonshot/OpenAI/Local 클라이언트가 provider별 키 해석을 사용하도록 갱신
- [x] Local provider는 API key 미설정 시 Authorization 헤더 없이 호출하도록 유지
- [x] API key 해석 우선순위 검증 테스트 추가

### Documentation & Verification
- [x] 설정 예시와 운영 문서를 provider별 API key 구조로 갱신
- [x] `./gradlew test` 및 `./gradlew build`로 API key 리팩터링 검증
