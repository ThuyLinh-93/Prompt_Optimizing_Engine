# AI Optimize Agent

평가 기준(rubric)을 반영하여 프롬프트를 개선하고,  
회의 음성(STT)을 구조화된 요약으로 변환하는 AI 서비스입니다.

---

## 기술 스택

- **Backend**: Kotlin + Spring Boot 3.5.12 + WebFlux
- **AI**: Moonshot API / OpenAI / Local OpenAI-compatible LLM

---

## 사용 흐름

1. **프롬프트 최적화** → 2. **회의 요약 생성**

```
rubric + prompt ──▶ improved prompt ──▶ meeting script ──▶ summary.json
       │                  │                                    │
   /optimize          (다운로드)                          /summarize
```

---

## API 목록

### 1. 프롬프트 최적화

**엔드포인트**: `POST /api/v1/optimize`

평가 기준(rubric)을 참고하여 프롬프트를 개선합니다.

**요청 파일**:
- `rubric` - 평가 기준 텍스트 파일
- `prompt` - 개선할 프롬프트 파일

**응답**: 개선된 프롬프트 텍스트 파일 (`improved_prompt_v{N}.txt`)

```bash
curl -F "rubric=@rubric.txt" \
     -F "prompt=@prompt.txt" \
     http://localhost:8080/api/v1/optimize \
     --output improved.txt
```

---

### 2. 회의 요약 생성

**엔드포인트**: `POST /api/v1/summarize`

회의 스크립트를 구조화된 JSON 요약으로 변환합니다.

**요청 파일**:
- `script` - STT 변환된 회의 음성 텍스트
- `improvedPrompt` - 1단계에서 생성된 개선된 프롬프트

**응답**: 회의 요약 JSON 파일 (`summary_{uuid}.json`)

```bash
curl -F "script=@meeting.txt" \
     -F "improvedPrompt=@improved.txt" \
     http://localhost:8080/api/v1/summarize \
     --output summary.json
```

---

## 설정

`application.properties`:

```properties
app.llm.provider=moonshot
app.llm.model=kimi-k2.5
app.llm.timeout-seconds=60

# Optional shared fallback
app.llm.api-key=

app.llm.moonshot.base-url=https://api.moonshot.ai/v1
app.llm.moonshot.api-key=

app.llm.openai.base-url=https://api.openai.com/v1
app.llm.openai.model=gpt-4o-mini
app.llm.openai.api-key=

app.llm.local.base-url=http://localhost:11434/v1
app.llm.local.model=local-model
app.llm.local.api-key=
```

---

## 실행 방법

```bash
# 서버 시작
./gradlew bootRun

# 테스트 실행
./gradlew test
```

---

## AI Agent 활용 전략

### 사용 도구

- **AI IDE**: [opencode](https://opencode.ai)
- **AI Model**: Kimi-k2.5
- **방식**: 바이브 코딩 (Vibe Coding)

### 개발 프로세스 (opencode 기반)

```
컨텍스트 설정 → 태스크 분리 → Sisyphus orchestration(opencode) → 병렬 실행 → 통합 검증 → 완료
```

**1. 컨텍스트 설정**
- `AGENTS.md`에 프로젝트 목적, 아키텍처, 기술 스택 문서화
- AI 에이전트에게 초기 컨텍스트 제공

**2. 태스크 분리**
- Sisyphus가 기능을 독립적인 작업 단위로 분해
- `tasks.md`에 Phase별 작업 목록 관리
- opencode의 todo 도구로 작업 상태 추적

**3. Sisyphus Orchestration 및 병렬 실행**

Sisyphus가 하위 Agent를 자동으로 할당하고 병렬 처리:

| 하위 Agent | 역할 | Sisyphus가 호출하는 시점 |
|-----------|------|------------------------|
| `explore` | 코드베이스 탐색 | 구현 전 패턴/구조 파악이 필요할 때 |
| `librarian` | 외부 레퍼런스 검색 | 새로운 라이브러리나 패턴 조사가 필요할 때 |
| `oracle` | 아키텍처 컨설팅 | 설계 결정이 필요할 때 |

**4. 통합 검증**
- Sisyphus가 각 Agent 결과물을 통합
- `./gradlew test`로 빌드/테스트 검증
- 사람이 최종 코드 리뷰

### 협업 패턴

**Sisyphus 중심 컨텍스트 유지**
```
[Session 시작] (Auto) Sisyphus에게 AGENTS.md 제공
     ↓
[요청 1] "평가표로 프롬프트 개선하는 AI Agent 만들어줘. Spring WebFlux 기반이고 LLM은 Moonshot 쓸 거야."
     ↓
    Sisyphus → 필요시 explore/librarian/oracle Agent 호출
     ↓
    Sisyphus가 직접 구현 진행
     ↓
[요청 2] "이전 거 롤백하고 AGENTS.md부터 만들어. 작업은 Task 단위로 기록해줘."
     ↓
    Sisyphus → AGENTS.md 생성, tasks.md에 Phase별 작업 분리
     ↓
[요청 3] "Phase 완료 승인할게. Coroutine은 쓰지 말고 공통 apiKey로 변경해줘."
      ↓
     Sisyphus → 제약사항 반영 및 리뷰 프로세스 확립
     ↓
[요청 4] "Provider별 api key가 필요할 것 같아. local은 optional이면 좋겠어."
     ↓
    Sisyphus → provider별 key + shared fallback 구조로 재정비
      ↓
[완료] Sisyphus가 전체 컨텍스트 보존
```

**병렬 처리 예시**
```
사용자: "summarize 기능 구현해줘"
     ↓
Sisyphus가 병렬로 실행:
  ├─ explore: "summarize API 구조 찾기"
  ├─ librarian: "WebFlux 파일 처리 패턴 검색"
  └─ oracle: "아키텍처 검토"
     ↓
Sisyphus가 결과 통합 후 구현 진행
```

### 핵심 인사이트

- **Orchestrator 자동화**: 메인 에이전트가 적절한 Agent를 자동으로 선택/호출
- **Agent 병렬화**: 메인 에이전트가 여러 하위 Agent를 동시에 활용해 탐색/구현/검증 병행
- **문서화된 컨텍스트(AGENTS.md)**: 세션 시작 시 한 번 제공으로 일관된 품질 확보
