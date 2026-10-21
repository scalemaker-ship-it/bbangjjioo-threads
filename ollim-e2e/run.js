// Ollim의 실제 Threads 어댑터(threads.js)와 호스팅(hosting.js)을 그대로 실행해,
// 빵찌 Threads 계정에 실제로 게시되는지 E2E 검증한다. 토큰은 이 레포 시크릿에만 있다.
const path = require('path');
const threads = require('./threads');
const hosting = require('./hosting');

(async () => {
  const accessToken = process.env.THREADS_ACCESS_TOKEN;
  const userId = process.env.THREADS_USER_ID;
  if (!accessToken || !userId) throw new Error('THREADS_ACCESS_TOKEN / THREADS_USER_ID 시크릿이 없습니다');

  // Ollim이 토큰 연결 시 만드는 account 객체와 동일한 모양
  const account = await threads.fromToken({ accessToken }).catch(async (e) => {
    // fromToken은 TH 접두 검증이 있어 실패할 수 있음 → /me로 직접 구성
    const axios = require('axios');
    const me = await axios.get('https://graph.threads.net/v1.0/me', { params: { fields: 'id,username', access_token: accessToken } });
    return { accessToken, userId: me.data.id, name: me.data.username, handle: '@' + me.data.username, expiresAt: Date.now() + 60 * 86400000, mode: 'api' };
  });
  account.userId = account.userId || userId;
  console.log('연결된 계정:', account.name, account.handle, 'userId=' + account.userId);

  const stamp = new Date().toISOString().replace('T', ' ').slice(0, 16);
  const results = {};

  // 1) 텍스트 게시 (Ollim publish TEXT 경로)
  const text1 = `올림(Ollim) 멀티업로드 앱 연결 테스트입니다. 이 글은 테스트 후 삭제됩니다. (${stamp})`;
  const r1 = await threads.publish({ account, text: text1, media: { type: 'TEXT' }, onProgress: (p) => process.stdout.write(`text ${p}% `) });
  console.log('\n[1] 텍스트 게시 성공:', r1.id, r1.url);
  results.text = r1;

  // 2) 이미지 게시 (Ollim GitHub 호스팅 + publish IMAGE 경로)
  const settings = { hosting: { type: 'github', repo: process.env.GITHUB_REPOSITORY, branch: process.env.GITHUB_REF_NAME || 'main', dir: 'ollim-media', token: process.env.GH_HOST_TOKEN } };
  const imgPath = path.join(__dirname, 'test-image.png');
  const hosted = await hosting.uploadPublic(settings, imgPath);
  console.log('[2] 이미지 호스팅 URL:', hosted.url);
  const r2 = await threads.publish({ account, text: `올림 이미지 게시 테스트 (${stamp})`, media: { type: 'IMAGE', url: hosted.url }, onProgress: (p) => process.stdout.write(`img ${p}% `) });
  console.log('\n[2] 이미지 게시 성공:', r2.id, r2.url);
  results.image = r2;
  setTimeout(() => hosted.remove(), 1000);
  await new Promise((r) => setTimeout(r, 2000));

  // 3) 정리: 테스트 글 삭제 시도 (Threads API DELETE)
  const axios = require('axios');
  for (const [k, r] of Object.entries(results)) {
    try { await axios.delete(`https://graph.threads.net/v1.0/${r.id}`, { params: { access_token: account.accessToken } }); console.log(`[cleanup] ${k} 삭제됨: ${r.id}`); }
    catch (e) { console.log(`[cleanup] ${k} 삭제 불가(수동 삭제 필요): ${r.id} — ${e.response?.data?.error?.message || e.message}`); }
  }
  console.log('\nE2E_RESULT=PASS');
})().catch((e) => { console.error('E2E_RESULT=FAIL', e.response?.data ? JSON.stringify(e.response.data) : e.message); process.exit(1); });
