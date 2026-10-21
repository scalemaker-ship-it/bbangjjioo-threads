// Threads(및 URL 기반 업로드)용 임시 공개 URL. S3 호환(R2, S3, MinIO) 버킷에 올리고 공개 URL 반환.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// GitHub 공개 저장소에 커밋해 raw URL로 호스팅(무료). 토큰: repo 권한 PAT 또는 `gh auth token`
async function uploadGithub(h, filePath) {
  const axios = require('axios');
  const ext = path.extname(filePath).toLowerCase() || '.mp4';
  const key = `${(h.dir || 'ollim').replace(/^\/|\/$/g, '')}/${Date.now()}-${crypto.randomBytes(4).toString('hex')}${ext}`;
  const [owner, repo] = String(h.repo || '').split('/');
  if (!owner || !repo) throw new Error('GitHub 호스팅 저장소를 owner/repo 형식으로 입력하세요');
  const size = fs.statSync(filePath).size;
  if (size > 95 * 1024 * 1024) throw new Error('GitHub 호스팅은 95MB 이하 파일만 가능합니다');
  const branch = h.branch || 'main';
  const api = `https://api.github.com/repos/${owner}/${repo}/contents/${key}`;
  const headers = { Authorization: `Bearer ${h.token}`, Accept: 'application/vnd.github+json' };
  const put = await axios.put(api, { message: `ollim: ${path.basename(key)}`, content: fs.readFileSync(filePath).toString('base64'), branch }, { headers, maxBodyLength: Infinity });
  const sha = put.data.content.sha;
  const url = `https://raw.githubusercontent.com/${owner}/${repo}/${branch}/${key}`;
  // raw CDN 반영 대기
  for (let i = 0; i < 20; i++) { try { const r = await axios.head(url, { timeout: 10000 }); if (r.status === 200) break; } catch {} await new Promise((r) => setTimeout(r, 3000)); }
  return { url, remove: async () => { try { await axios.delete(api, { headers, data: { message: `ollim: remove ${path.basename(key)}`, sha, branch } }); } catch {} } };
}
async function uploadPublic(settings, filePath) {
  const h = settings.hosting || {};
  if (h.type === 'github') return uploadGithub(h, filePath);
  if (h.type !== 's3') throw new Error('미디어 호스팅이 설정되지 않았습니다. Threads 영상/이미지는 설정 > 미디어 호스팅(GitHub 또는 S3/R2)이 필요합니다.');
  const { S3Client, PutObjectCommand, DeleteObjectCommand } = require('@aws-sdk/client-s3');
  const client = new S3Client({ region: h.region || 'auto', endpoint: h.endpoint || undefined, forcePathStyle: !!h.endpoint, credentials: { accessKeyId: h.accessKeyId, secretAccessKey: h.secretAccessKey } });
  const ext = path.extname(filePath).toLowerCase() || '.mp4';
  const key = `ollim/${Date.now()}-${crypto.randomBytes(6).toString('hex')}${ext}`;
  const type = ['.jpg', '.jpeg'].includes(ext) ? 'image/jpeg' : ext === '.png' ? 'image/png' : ext === '.mov' ? 'video/quicktime' : 'video/mp4';
  await client.send(new PutObjectCommand({ Bucket: h.bucket, Key: key, Body: fs.createReadStream(filePath), ContentType: type, ACL: h.endpoint ? undefined : 'public-read' }));
  const base = (h.publicBase || '').replace(/\/$/, '');
  if (!base) throw new Error('미디어 호스팅의 공개 URL(publicBase)이 비어 있습니다.');
  return { url: `${base}/${key}`, remove: async () => { try { await client.send(new DeleteObjectCommand({ Bucket: h.bucket, Key: key })); } catch {} } };
}
module.exports = { uploadPublic };
