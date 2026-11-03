#!/usr/bin/env python3
"""황은화 의원 행감질의서 누리집 — 질의서 등록 도구

docx 질의서를 HTML로 변환해 queries/ 에 넣고 queries-manifest.json 에 등록한다.

사용 예
  python3 tools/add_query.py 질의서원본/exec1_최종발언_예술정책과_예술인기회소득.docx
  python3 tools/add_query.py 파일.docx --day org2 --inst 경기도체육회 --type 최종발언 --title "제목"
  python3 tools/add_query.py 파일1.docx 파일2.docx --push        # 등록 후 바로 git push
  python3 tools/add_query.py --remove queries/org2_xxx.html        # 등록 해제
  python3 tools/add_query.py --set-date exec1 2026-11-10           # 감사 일자 입력

자동 판별 규칙 (파일명 기준)
  - 일자: 파일명 앞 'exec1_' 같은 접두어, 없으면 파일명 안의 기관명으로 institutionMap 조회
  - 기관: 파일명 안에 들어 있는 기관명(가장 긴 일치)
  - 유형: '최종발언v2'/'최종발언 v2' → 최종발언 v2, '최종발언' → 최종발언, 그 밖 → 대체
  - 제목: 문서 첫 제목(Heading) 또는 첫 줄, 없으면 파일명

필요 프로그램: pandoc (https://pandoc.org/installing.html)
"""
import argparse, datetime, html, json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "queries-manifest.json"
QDIR = ROOT / "queries"
STYLE = (Path(__file__).resolve().parent / "query-style.css").read_text(encoding="utf-8")


def load():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def save(m):
    m["updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def detect(stem, m):
    day = None
    mm = re.match(r"^(exec\d|org\d)[_\-]", stem)
    if mm:
        day = mm.group(1)
    imap = m["institutionMap"]
    inst_key = max((k for k in imap if k in stem), key=len, default=None)
    inst = None
    if inst_key:
        d = imap[inst_key]
        day = day or d
        # 별칭을 정식 기관명으로 바꾼다
        for s in m["schedule"]:
            if s["id"] == d:
                inst = next((i for i in s["institutions"] if inst_key in i or i in inst_key), s["institutions"][0])
    s = stem.replace(" ", "")
    if re.search(r"최종발언v2", s, re.I):
        typ = "최종발언 v2"
    elif "최종발언" in s:
        typ = "최종발언"
    else:
        typ = "대체"
    return day, inst, typ


def safe_name(stem):
    return re.sub(r'[\\/:*?"<>|\s]+', "_", stem).strip("_")


def convert(docx: Path, out_html: Path, title_override=None):
    media_dir = QDIR / "media" / out_html.stem
    if media_dir.exists():
        shutil.rmtree(media_dir)
    body = subprocess.run(
        ["pandoc", str(docx), "-f", "docx", "-t", "html5", "--wrap=none",
         f"--extract-media={media_dir}"],
        check=True, capture_output=True, text=True).stdout
    # 이미지 경로를 queries/ 기준 상대경로로 바꾼다
    body = body.replace(str(media_dir) + "/", f"media/{out_html.stem}/")
    # 외부 링크는 새 창
    body = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', body)
    title = title_override
    if not title:
        mt = re.search(r"<h[1-3][^>]*>(.*?)</h[1-3]>", body, re.S) or re.search(r"<p[^>]*>(.*?)</p>", body, re.S)
        title = re.sub(r"<[^>]+>", "", mt.group(1)).strip() if mt else ""
        title = html.unescape(title)[:120] or docx.stem
    doc = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>
{STYLE}
img {{ max-width: 100%; height: auto; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""
    out_html.write_text(doc, encoding="utf-8")
    return title


def git_push(msg):
    def run(*a):
        subprocess.run(["git", "-C", str(ROOT), *a], check=True)
    run("add", "-A")
    if subprocess.run(["git", "-C", str(ROOT), "diff", "--cached", "--quiet"]).returncode == 0:
        print("바뀐 내용이 없어 push하지 않았다.")
        return
    run("commit", "-m", msg)
    run("push")
    print("배포 완료 — 1~2분 뒤 누리집에 반영된다.")


def main():
    ap = argparse.ArgumentParser(description="황은화 의원 행감질의서 등록")
    ap.add_argument("files", nargs="*", help="등록할 .docx 파일")
    ap.add_argument("--day", help="exec1 exec2 org1 org2 org3 org4 org5")
    ap.add_argument("--inst", help="기관(과)명")
    ap.add_argument("--type", help="최종발언 / 최종발언 v2 / 핵심 / 대체")
    ap.add_argument("--title", help="제목(파일 1개일 때만)")
    ap.add_argument("--remove", metavar="HTML", help="등록 해제할 queries/xxx.html")
    ap.add_argument("--set-date", nargs=2, metavar=("DAY", "YYYY-MM-DD"), help="감사 일자 입력")
    ap.add_argument("--push", action="store_true", help="등록 후 git commit·push")
    a = ap.parse_args()

    if not shutil.which("pandoc") and a.files:
        sys.exit("pandoc이 없다. https://pandoc.org/installing.html 에서 설치한다.")

    m = load()
    days = {s["id"]: s for s in m["schedule"]}
    msgs = []

    if a.set_date:
        d, dt = a.set_date
        if d not in days:
            sys.exit(f"알 수 없는 일자: {d}")
        days[d]["date"] = dt
        msgs.append(f"{days[d]['label']} 일자 {dt}")

    if a.remove:
        f = a.remove if a.remove.startswith("queries/") else "queries/" + a.remove
        before = len(m["queries"])
        m["queries"] = [q for q in m["queries"] if q["file"] != f]
        (ROOT / f).unlink(missing_ok=True)
        shutil.rmtree(QDIR / "media" / Path(f).stem, ignore_errors=True)
        msgs.append(f"삭제 {f}" if len(m["queries"]) < before else f"목록에 없음 {f}")

    for fp in a.files:
        src = Path(fp)
        if src.suffix.lower() != ".docx" or not src.exists():
            print(f"건너뜀(없거나 docx 아님): {fp}")
            continue
        day, inst, typ = detect(src.stem, m)
        day = a.day or day
        inst = a.inst or inst
        typ = a.type or typ
        if day not in days:
            sys.exit(f"[{src.name}] 일자를 판별하지 못했다. --day exec1 처럼 지정한다.")
        if not inst:
            inst = days[day]["institutions"][0] if len(days[day]["institutions"]) == 1 else None
        if not inst or inst not in days[day]["institutions"]:
            sys.exit(f"[{src.name}] 기관을 판별하지 못했다. --inst 로 지정한다. 가능: {', '.join(days[day]['institutions'])}")
        stem = safe_name(src.stem)
        if not stem.startswith(day + "_"):
            stem = f"{day}_{stem}"
        out = QDIR / f"{stem}.html"
        title = convert(src, out, a.title if len(a.files) == 1 else None)
        rel = f"queries/{out.name}"
        entry = {
            "id": stem, "institution": inst, "title": title, "type": typ,
            "file": rel, "original": src.name, "day": day,
            "convertedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        m["queries"] = [q for q in m["queries"] if q["file"] != rel] + [entry]
        msgs.append(f"{days[day]['shortLabel']} · {inst} · [{typ}] {title}")

    if not msgs:
        ap.print_help()
        return
    save(m)
    for s in msgs:
        print("✔", s)
    if a.push:
        git_push("질의서 갱신: " + "; ".join(msgs)[:200])


if __name__ == "__main__":
    main()
