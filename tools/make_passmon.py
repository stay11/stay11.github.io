#!/usr/bin/env python3
"""パスモンシリーズの一覧ページ（passmon/index.html）を作る。

App Store の公開情報（iTunes Lookup API）から、開発者のアプリのうち
「〜のたまご」「パスモン」を含むものだけを集め、分野ごとに並べる。
アプリを足したり名前を変えたりしたら、これを実行し直して push するだけでよい。

    python3 tools/make_passmon.py
"""
import html, json, re, urllib.request
from datetime import date
from pathlib import Path

DEVELOPER_ID = 1584980968
OUT = Path(__file__).resolve().parent.parent / "passmon" / "index.html"

# 分野の判定（上から順に見て、最初に当てはまった分野に入れる）
CATEGORIES = [
    ("medical", "医療・福祉・栄養", ["看護", "医師", "歯科", "薬", "登録販売者", "介護", "ケアマネ", "保健師", "助産師", "理学療法",
                               "作業療法", "柔道整復", "鍼灸", "あん摩", "臨床", "放射線", "救急救命", "栄養", "心理", "獣医", "調理師"]),
    ("build", "建設・設備・電気・機械", ["施工管理", "ボイラー", "冷凍", "電気", "危険物", "消防", "測量", "建築", "クレーン", "エックス線",
                                 "管工事", "土木", "建設機械", "下水道", "浄化槽", "給水装置", "高圧ガス", "機械保全", "発破", "潜水",
                                 "公害防止", "小型船舶"]),
    ("law", "法律・不動産・会計・ビジネス", ["宅建", "管理業務", "不動産", "土地家屋", "弁理士", "知的財産", "行政書士", "社労士", "FP",
                                    "会計", "簿記", "勘定科目", "衛生管理者", "ビジネス", "ショートカット"]),
    ("it", "IT・情報処理", ["IT", "システム", "ネットワーク", "プロジェクトマネージャ", "エンベデッド", "情報処理", "基本情報"]),
    ("life", "美容・生活", ["美容", "理容"]),
    ("teach", "教育・受験", ["教員", "小学", "古文", "元素"]),
    ("lang", "語学・単語", ["語", "英単語", "TOEIC", "英検"]),
    ("culture", "教養・脳トレ", [""]),
]


def fetch_apps():
    url = f"https://itunes.apple.com/lookup?id={DEVELOPER_ID}&entity=software&country=jp&limit=300"
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.load(r)["results"]
    apps = [a for a in data if a.get("wrapperType") == "software"]
    return [a for a in apps if "たまご" in a["trackName"] or "パスモン" in a["trackName"]]


def display_name(name: str) -> str:
    import unicodedata
    name = unicodedata.normalize("NFKC", name)
    name = re.sub(r"[-ー－]\s*パスモン$", "", name)
    return name.strip()


def category_of(name: str) -> str:
    import unicodedata
    name = unicodedata.normalize("NFKC", name)   # 濁点が分かれた文字（ボ＝ホ＋゛）などをそろえてから見る
    # 「語」は「用語」「単語」などにも入るので、語学は国の名前つき・英単語・TOEIC だけにする
    for key, _, words in CATEGORIES:
        for w in words:
            if key == "lang" and w == "語" and not re.search(r"(英|中国|韓国|スペイン|フランス|ドイツ|イタリア|ロシア|ポルトガル|タイ|ベトナム|ヒンディー|インドネシア)語", name):
                continue
            if w in name:
                return key
    return "culture"


def main():
    apps = fetch_apps()
    groups = {key: [] for key, _, _ in CATEGORIES}
    for a in apps:
        groups[category_of(a["trackName"])].append(a)
    for g in groups.values():
        g.sort(key=lambda a: display_name(a["trackName"]))

    chips, sections = [], []
    for key, label, _ in CATEGORIES:
        items = groups[key]
        if not items:
            continue
        chips.append(f'<a class="chip" href="#{key}">{html.escape(label)}<span>{len(items)}</span></a>')
        cards = []
        for a in items:
            name = display_name(a["trackName"])
            icon = a.get("artworkUrl100", "").replace("100x100bb", "120x120bb")
            link = f"https://apps.apple.com/jp/app/id{a['trackId']}"
            cards.append(
                f'<a class="app" href="{link}" data-name="{html.escape(name)}">'
                f'<img src="{html.escape(icon)}" alt="" width="56" height="56" loading="lazy">'
                f'<span class="name">{html.escape(name)}</span>'
                f'<span class="get">入手</span></a>')
        sections.append(f'<section id="{key}"><h2>{html.escape(label)}<span>{len(items)}本</span></h2>'
                        f'<div class="grid">{"".join(cards)}</div></section>')

    page = TEMPLATE.replace("{{COUNT}}", str(len(apps))) \
                   .replace("{{CHIPS}}", "".join(chips)) \
                   .replace("{{SECTIONS}}", "".join(sections)) \
                   .replace("{{UPDATED}}", date.today().strftime("%Y年%-m月%-d日"))
    OUT.write_text(page, encoding="utf-8")
    print(f"{len(apps)} apps → {OUT}")


TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>パスモンシリーズ</title>
<meta name="description" content="過去問・単語・教養を、たまごからモンスターを育てながら学べる「パスモン」シリーズのアプリ一覧です。">
<style>
:root{--bg:#F3F5FA;--card:#FFFFFF;--border:#DCE3F0;--text:#1C2845;--sub:#5B6785;--accent:#4263EB;--chip:#E7EDFF}
@media (prefers-color-scheme: dark){:root{--bg:#00071F;--card:#1A2442;--border:#28355E;--text:#FFFFFF;--sub:#A9B4D0;--accent:#6F8BFF;--chip:#1D2D66}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Hiragino Kaku Gothic ProN",sans-serif;line-height:1.6}
header{padding:28px 16px 8px;max-width:960px;margin:0 auto}
h1{font-size:26px;margin:0 0 4px;font-weight:800}
.lead{color:var(--sub);font-size:14px;margin:0}
.search{position:sticky;top:0;z-index:2;background:var(--bg);padding:12px 16px;max-width:960px;margin:0 auto}
.search input{width:100%;font-size:16px;padding:12px 14px;border-radius:14px;border:1px solid var(--border);background:var(--card);color:var(--text)}
.chips{display:flex;gap:8px;overflow-x:auto;padding:4px 16px 12px;max-width:960px;margin:0 auto;scrollbar-width:none}
.chip{flex:none;text-decoration:none;color:var(--text);background:var(--chip);border-radius:999px;padding:6px 12px;font-size:13px;font-weight:700}
.chip span{margin-left:6px;color:var(--sub);font-weight:600}
main{max-width:960px;margin:0 auto;padding:0 16px 40px}
section{margin-top:18px;scroll-margin-top:72px}
h2{font-size:17px;margin:0 0 10px;display:flex;align-items:baseline;gap:8px}
h2 span{font-size:12px;color:var(--sub);font-weight:600}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px}
.app{display:flex;align-items:center;gap:12px;padding:10px 12px;background:var(--card);border:1px solid var(--border);border-radius:16px;text-decoration:none;color:var(--text)}
.app img{border-radius:13px;flex:none;background:var(--border)}
.name{flex:1;font-size:15px;font-weight:700;min-width:0}
.get{flex:none;font-size:13px;font-weight:800;color:var(--accent);background:var(--chip);border-radius:999px;padding:5px 14px}
.empty{color:var(--sub);text-align:center;padding:24px 0;display:none}
footer{max-width:960px;margin:0 auto;padding:0 16px 32px;color:var(--sub);font-size:12px}
</style>
</head>
<body>
<header>
<h1>パスモンシリーズ</h1>
<p class="lead">問題を解くほど、たまごからモンスターが育つ学習アプリです。全{{COUNT}}本。気になる資格や科目を探してみてください。</p>
</header>
<div class="search"><input id="q" type="search" placeholder="資格名・科目名で探す（例：看護、宅建、英単語）" aria-label="アプリを探す"></div>
<nav class="chips">{{CHIPS}}</nav>
<main>{{SECTIONS}}<p class="empty" id="empty">見つかりませんでした。別の言葉でお試しください。</p></main>
<footer>App Store の情報をもとに作成（{{UPDATED}}更新）。リンク先は App Store です。</footer>
<script>
const q=document.getElementById('q'),empty=document.getElementById('empty');
const norm=s=>s.normalize('NFKC').toLowerCase().replace(/[\\u3041-\\u3096]/g,c=>String.fromCharCode(c.charCodeAt(0)+0x60));
q.addEventListener('input',()=>{const v=norm(q.value.trim());let any=false;
document.querySelectorAll('section').forEach(sec=>{let n=0;sec.querySelectorAll('.app').forEach(a=>{const hit=!v||norm(a.dataset.name).includes(v);a.style.display=hit?'':'none';if(hit)n++;});sec.style.display=n?'':'none';if(n)any=true;});
empty.style.display=any?'none':'block';document.querySelector('.chips').style.display=v?'none':'';});
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
