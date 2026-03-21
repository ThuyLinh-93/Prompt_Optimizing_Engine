# Workflow Architecture (n8n Pipeline)

## 목적
Review/Optimizer/Summary Agent를 n8n에서 오케스트레이션하여, 요약 품질을 반복 개선하고 종료 시 최종 산출물 3종을 저장한다.

## 구성
- Agent Layer: Review Agent, Optimizer Agent, Summary Agent
- Orchestration Layer: n8n workflow (분기, 루프, 저장)

## 메인 흐름
1. 입력 파일 로드 (`script`, `summary`, `prompt`, `rubric`)
2. `Prepare Payload`
3. `Review Agent` 평가
4. `Normalize Review Response`
5. `Stop?` 분기
   - True: 최종 저장 경로
   - False: 개선 루프 경로

## 개선 루프
1. `Read review_result`
2. `Optimizer Agent` (prompt 개선)
3. `Summary Agent` (요약 재생성)
4. `Loop_count +1`
5. `Prepare Payload` 복귀

## 종료/저장
True 분기에서 아래 3개 파일 저장:
- `final_review_result_*.json`
- `final_prompt_*.json`
- `final_summary_*.json`

## 종료 조건
- `totalScore >= 목표 점수` OR `loop_count >= 최대 반복 횟수`
