# Troubleshooting (개발자 최종 피드백 기준)

## 1) 루프가 멈추지 않음
- 증상: 10회 이상 반복
- 원인: IF 조건에서 loop_count 참조 불일치
- 최종 해결:
  - `Stop?`에서 `totalScore >= 90 OR loop_count >= 2` 고정
  - `Loop_count +1` 노드에서 증가값을 `Prepare Payload` 기준으로 계산
- 검증: 2회 루프 후 True 분기 진입

## 2) review_result 버전 충돌 (v1/v2 혼재)
- 증상: 최신 평가 파일이 아닌 이전 파일 참조
- 원인: 루프 중 이전 review_result가 계속 남아 충돌
- 최종 해결:
  - 루프마다 `Read review_result`로 현재 `result_file_path`를 다시 읽어 사용
  - Optimizer 입력에서 `review_result`만 참조하도록 단순화
- 검증: 각 루프에서 `result_file_path` 파일명이 증가하는지 확인

## 3) Review 이후 binary 유실
- 증상: Review 응답 이후 binary 없음
- 원인: Review Agent가 JSON 응답 반환
- 최종 해결:
  - final prompt/summary는 Review 출력이 아닌 Optimizer/Summary 출력 참조
  - 최종 review_result는 경로 기반 read 후 write
- 검증: True 분기에서 최종 3파일 모두 생성

## 4) total_score 파싱 오류 (`"75점"`)
- 증상: float_parsing 에러
- 원인: 숫자 필드에 문자열 점수 입력
- 최종 해결:
  - Review 응답 스키마에서 `total_score`를 숫자로 통일
  - n8n IF는 숫자형 점수만 비교
- 검증: IF 조건 비교 시 타입 에러 없음

## 5) IF True 저장 시 파일 없음
- 증상: Write 단계에서 binary not found
- 원인: 종료 경로에서 참조 키 불일치
- 최종 해결:
  - review_result는 `Normalize final review result file` -> `Read review result File` 경유
  - prompt/summary는 Optimizer/Summary 출력 참조
- 검증: 최종 파일 3종 생성 확인
