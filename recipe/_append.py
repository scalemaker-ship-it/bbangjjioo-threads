import pathlib, sys, ast
block = sys.stdin.read()
p = pathlib.Path("topics_spec.py"); s = p.read_text(encoding="utf-8").rstrip()
assert s.endswith("]"), "파일이 ']' 로 끝나지 않음"
s = s[:-1].rstrip() + "\n" + block.rstrip() + "\n]\n"
ast.parse(s)
p.write_text(s, encoding="utf-8")
import topics_spec, importlib; importlib.reload(topics_spec)
print(len(topics_spec.TOPICS), "건")
