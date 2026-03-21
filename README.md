# AI Repoto Prompt Optimizing Engine (Sprint 1~4 완료)

> 본 문서는 프로젝트 종료 시점(발표 준비 단계)에 맞춰 최종 성과 기준으로 정리되었습니다.

## 1) 프로젝트 한 줄 요약

**AI 기반 Review/Optimizer Agent를 개발하고, Spec 기반 바이브코딩 구현 + PL의 n8n 연동으로 업무 적용 가능한 자동화 파이프라인을 완성한 프로젝트**

## 2) 핵심 성과 (Top 3)

### 1. AI Agent 개발 완료 (BE 중심)
- Review Agent: 요약 품질 평가 및 결과 리포트 생성
- Optimizer Agent: 감점 원인 기반 프롬프트 개선
- Summary Agent: 개선 프롬프트 기반 재요약 생성

### 2. Spec 기반 바이브코딩 실증 (FE 중심)
- BE가 정의한 `spec.md` 기반으로 FE가 바이브코딩 방식 구현
- 설계 문서 중심 협업으로 구현 속도와 커뮤니케이션 효율 검증

### 3. 업무 적용 가능한 파이프라인 완성 (PL 중심)
- PL이 n8n으로 Agent 간 연동/반복/종료/산출물 저장 자동화
- 운영 가능한 형태의 end-to-end 흐름 확보

## 3) 팀 구성 및 역할

- **BE 1**: Review Agent 설계/스펙/품질
- **BE 2**: Optimizer Agent 설계/스펙/품질
- **BE 3**: Agent 구현 보강 및 API 안정화
- **FE 1**: `spec.md` 기반 바이브코딩 구현
- **PL 1**: n8n 오케스트레이션 설계 및 업무 연동 완성

## 4) Sprint별 진행 결과

### Sprint 1 — 평가/리뷰 POC
- 모델 검증 및 리뷰 흐름 1차 확인
- 단방향 평가 파이프라인 시연

### Sprint 2 — API 설계 + Loop 검증
- Agent API 스펙 확정
- n8n 루프/분기/종료 조건 동작 검증
- Mock 및 실연동 혼합 테스트

### Sprint 3 — End-to-End 연동
- Review ↔ Optimizer ↔ Summary 연계
- 결과 파일 생성/저장 체계 정리

### Sprint 4 — 안정화/QA
- 반복 실행 안정성 점검
- 예외 케이스 보완
- 발표 가능한 최종 구조 확정

## 5) 시스템 구성 개요

### Agent 레이어
- Review Agent (평가)
- Optimizer Agent (개선)
- Summary Agent (재생성)

### Workflow 레이어 (n8n)
- 입력 파일 로드
- Agent API 호출 오케스트레이션
- 반복/종료 조건 제어
- 최종 산출물 저장

## 6) 주요 동작 흐름

1. 입력(script, summary, prompt, rubric) 로드  
2. Review Agent 평가 수행  
3. 목표 점수 미달 시 Optimizer → Summary → 재평가 루프  
4. 종료 조건 충족 시 최종 결과 저장

종료 조건 예시(운영 설정):
- 목표 점수 도달 또는 최대 반복 횟수 도달

## 7) 최종 산출물

프로젝트 최종 실행 기준 산출물:

1. 최종 평가표 (`final_review_result_*.json`)
2. 최종 프롬프트 (`final_prompt_*.json`)
3. 최종 요약본 (`final_summary_*.json`)

## 8) 프로젝트 의미

- AI Agent를 단순 PoC가 아니라 **실업무 적용 가능한 체계**로 연결
- `spec → 구현 → 오케스트레이션` 협업 모델을 검증
- PL/BE/FE 협업에서 **바이브코딩 기반 개발 생산성** 가능성 확인

## 9) 후속 확장 계획

- 현재 자동화 엔진을 AIrepoto 실제 프로젝트(운영 흐름)에 단계적으로 연동합니다.
- Sandbox 검증 결과를 기반으로 운영 환경에서 안정적으로 동작하도록 고도화합니다.
- 실제 데이터 기준으로 품질 개선 효과를 측정하고 지속 개선 체계를 구축합니다.
- 이번 협업 방식(spec 기반 구현 + 파이프라인 연동)을 후속 과제에도 확장 적용합니다.

## 10) 참고 문서

- `docs/workflow-architecture.md`
- `docs/node-spec.md`
- `docs/troubleshooting.md`
- `docs/runbook.md`
- `docs/demo-script.md`
