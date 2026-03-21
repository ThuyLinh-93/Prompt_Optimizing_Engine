# Node Spec (Final)

## 핵심 노드

### Prepare Payload
- 역할: loop_count, summary/prompt 입력 컨텍스트 구성
- 출력: 다음 Review 호출에 필요한 json/binary 참조값

### Review Agent
- Method: POST multipart/form-data
- Required parts: `script`, `summary`, `prompt`, `rubric`
- Response(JSON): `total_score`, `result_file_path`

### Normalize Review Response
- 역할: 결과 경로 치환
- 경로 치환:
  - `/DATA/WEB/airnote-agent/squad` -> `/home/node/.n8n-files`
- 출력: `totalScore`, `result_file_path`

### Stop? (IF)
- 조건:
  - `totalScore >= 90`
  - `loop_count >= 2`
- combinator: OR

### Read review_result
- fileSelector: `{{$json.result_file_path}}`
- output property: `review_result`

### Optimizer Agent
- Required parts: `prompt`, `rubric(review_result)`
- Response(file): `prompt`

### Summary Agent
- Required parts: `script`, `improvedPrompt(prompt)`
- Response(file): `summary`

### Loop_count +1
- loop_count 1 증가 후 Prepare로 복귀

### Final Write Nodes
- Write Final review result
- Write Final Prompt
- Write Final Summary
