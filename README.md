# 황은화 의원 2026 행정사무감사 질의서 누리집

감사 일자별 질의서만 올리는 정적 누리집이다. GitHub Pages로 배포한다.

- 예시 주소: `https://bsm-prog.github.io/2026gamsa-hwang/`
- 구조

```
index.html               누리집 본체(질의서 목록·보기)
queries-manifest.json    일자·기관·질의서 목록
queries/                 변환된 질의서 HTML (+ media/ 근거 이미지)
tools/add_query.py       docx → HTML 변환·등록 도구
tools/query-style.css    질의서 본문 서식(이미정 의원 누리집과 동일)
```

## 1. 처음 배포 (한 번만)

### 방법 A — 누리집 화면에서 (프로그램 설치 불필요)
1. github.com 로그인(bsm-prog) → 오른쪽 위 **+ → New repository**
2. Repository name: `2026gamsa-hwang` / **Public** 선택 → **Create repository**
3. 새 저장소 화면에서 **uploading an existing file** 클릭 → 압축을 푼 폴더 안의 파일·폴더를 모두 끌어다 놓기 → **Commit changes**
4. **Settings → Pages** → Source: **Deploy from a branch**, Branch: **main / (root)** → **Save**
5. 1~2분 뒤 `https://bsm-prog.github.io/2026gamsa-hwang/` 접속 확인

### 방법 B — 명령줄(git)
```bash
cd hwang-gamsa
git init -b main
git add -A && git commit -m "황은화 의원 행감질의서 누리집 초기 배포"
git remote add origin https://github.com/bsm-prog/2026gamsa-hwang.git
git push -u origin main
```
이후 Settings → Pages 설정은 방법 A의 4번과 같다.

## 2. 질의서 올리기

pandoc 설치가 필요하다(https://pandoc.org/installing.html).

```bash
# 파일명으로 일자·기관·유형 자동 판별
python3 tools/add_query.py 질의서원본/최종발언_경기도체육회_선거공정성.docx --push

# 판별이 안 되면 직접 지정
python3 tools/add_query.py 파일.docx --day org2 --inst 경기도체육회 --type 최종발언 --title "제목" --push
```

### 파일명 규칙(권장)
`[일자코드_]최종발언_기관명_주제.docx`

| 일자코드 | 일차 | 대상 |
|---|---|---|
| exec1 | 집행부 1일차 | 문화정책과·종교협력과·콘텐츠산업과·예술정책과 |
| exec2 | 집행부 2일차 | 체육진흥과·문화유산과·관광산업과·전국체전추진단·남한산성세계유산센터 |
| org1 | 기관 1일차 | 경기문화재단·경기아트센터 |
| org2 | 기관 2일차 | 경기도체육회·경기도장애인체육회·수원월드컵경기장관리재단 |
| org3 | 기관 3일차 | 경기관광공사·한국도자재단 |
| org4 | 기관 4일차 | 경기콘텐츠진흥원·DMZ다큐멘터리영화제 |
| org5 | 종합 | 종합감사 |

- 기관명만 들어 있어도 일자가 자동으로 정해진다(일자코드 생략 가능).
- 파일명에 `최종발언`이 있으면 최종발언, `최종발언v2`면 최종발언 v2, 없으면 대체로 분류된다.
- 같은 파일명으로 다시 올리면 덮어쓴다.

## 3. 그 밖의 관리

```bash
python3 tools/add_query.py --set-date exec1 2026-11-10 --push   # 감사 일자 표시
python3 tools/add_query.py --remove queries/org2_xxx.html --push  # 질의서 내리기
```

- 질의서별 바로가기 주소: 목록에서 질의서를 열면 주소창이 `…/#q=queries/파일명.html` 로 바뀐다. 이 주소를 그대로 공유하면 해당 질의서가 바로 열린다.
- 인쇄 버튼을 누르면 질의서 본문만 인쇄된다.
- 예약 작업(에이전시)으로 자동 등록할 때도 `tools/add_query.py 파일.docx --push` 한 줄이면 된다.
