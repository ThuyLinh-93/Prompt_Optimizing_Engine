# Runbook

## 사전 점검
- Review/Optimizer/Summary API URL 확인
- 입력 파일 4종 존재 확인
- 출력 디렉토리 쓰기 권한 확인(`/home/node/.n8n-files/final`)

## 실행 절차
1. n8n workflow import
2. Start 실행
3. Review 결과 확인 (`totalScore`, `result_file_path`)
4. Stop? 분기 확인
5. False면 루프 1회 수행 후 재평가
6. True면 final 3파일 저장 확인

## 성공 기준
- 루프가 조건에 맞게 종료
- 최종 파일 3개 생성
- 파일 내용이 최신 루프 결과와 일치

## 실패 시 즉시 확인
- IF 조건 값/타입
- result_file_path 경로 치환
- 각 Write 노드의 dataPropertyName
