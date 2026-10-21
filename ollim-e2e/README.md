# Ollim Threads E2E

Ollim 멀티업로드 앱의 실제 Threads 어댑터(`threads.js`)와 GitHub 호스팅(`hosting.js`)을
이 레포 시크릿으로 그대로 실행해, 빵찌 Threads 계정에 실제 게시되는지 검증한다.

실행: `gh workflow run ollim-e2e.yml -R scalemaker-ship-it/bbangjjioo-threads`

2026-10-22 결과: Ollim 코드가 Threads API까지 정상 도달했으나 `THREADS_ACCESS_TOKEN`이
2026-09-18 만료(OAuthException 190)되어 게시 실패. 토큰 재발급 후 재실행하면 통과한다.
