#!/usr/bin/env python3
"""
í¬í¸í´ë¦¬ì¤ ë´ì¤ ìë ìë°ì´í¸
- Naver Financeìì ìµì  ë´ì¤ ìì§
- GitHub Gist ìë°ì´í¸
- Telegram ìë¦¼ ì ì¡
"""

import os, sys, json, base64, requests, re
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

# ââ ì¤ì  ââââââââââââââââââââââââââââââââââââââââââââââââââââââ
GIST_ID    = "98bfbf3fcd5e4d45f1f1eab66f069a89"
GIST_TOKEN = os.environ["GIST_TOKEN"]
TG_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
TG_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).strftime("%Y.%m.%d")

STOCKS = [
    {"id":"kodex",   "name":"KODEX ì¦ê¶",   "code":"278540", "theme":"blue",   "icon":"ð¦", "tag":"ì¦ê¶/ê¸ìµ ETF Â· 278540"},
    {"id":"samsung", "name":"ì¼ì±ì ì",      "code":"005930", "theme":"green",  "icon":"ð±", "tag":"KOSPI Â· ë°ëì²´/ì ì Â· 005930"},
    {"id":"tiger",   "name":"TIGER ë°ëì²´", "code":"091230", "theme":"purple", "icon":"â¡", "tag":"ë°ëì²´ì¥ë¹ ETF Â· 091230"},
]

HDRS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Referer": "https://finance.naver.com",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# ââ ë´ì¤ ìì§ âââââââââââââââââââââââââââââââââââââââââââââââââ
def get_news(code: str, count: int = 5) -> list:
    url = f"https://finance.naver.com/item/news.nhn?code={code}&page=1"
    try:
        r = requests.get(url, headers=HDRS, timeout=20)
        r.encoding = "euc-kr"
        soup = BeautifulSoup(r.text, "html.parser")
        items, seen = [], set()
        for row in soup.select("table.type5 tr"):
            a = row.select_one("td.title a")
            dt = row.select_one("td.date")
            src = row.select_one("td.info")
            if not a:
                continue
            title = a.get_text(strip=True)
            if not title or title in seen:
                continue
            seen.add(title)
            href = a.get("href", "")
            if href.startswith("/"):
                href = "https://finance.naver.com" + href
            items.append({
                "title":  title,
                "url":    href,
                "date":   dt.get_text(strip=True) if dt else "",
                "source": src.get_text(strip=True) if src else "",
                "desc":   "",
            })
            if len(items) >= count:
                break
        print(f"[{code}] ë´ì¤ {len(items)}ê±´ ìì§")
        return items
    except Exception as e:
        print(f"[ERROR] {code}: {e}", file=sys.stderr)
        return []

# ââ HTML ìì± ââââââââââââââââââââââââââââââââââââââââââââââââââ
def news_item_html(item: dict, num: int, theme: str) -> str:
    title = item["title"].replace("<","&lt;").replace(">","&gt;")
    desc  = item["desc"].replace("<","&lt;").replace(">","&gt;") if item["desc"] else ""
    url   = item["url"]
    date  = item["date"]
    src   = item["source"]
    desc_block = f'<div class="news-desc">{desc}</div>' if desc else ""
    return f"""
      <div class="news-item">
        <div class="news-num">{num}</div>
        <div>
          <a class="news-title-link" href="{url}" target="_blank">
            <div class="news-title">{title}</div>
          </a>
          {desc_block}
          <div class="news-meta">
            <span class="news-date">{date} Â· {src}</span>
            <a class="news-link-btn" href="{url}" target="_blank">ê¸°ì¬ ë³´ê¸° â</a>
          </div>
        </div>
      </div>"""

def build_card(stock: dict, news_list: list) -> str:
    theme = stock["theme"]
    sid   = stock["id"]
    name  = stock["name"]
    code  = stock["code"]
    icon  = stock["icon"]
    tag   = stock["tag"]

    visible = "visible" if sid == "kodex" else ""
    naver_url = f"https://finance.naver.com/item/main.naver?code={code}"

    if news_list:
        news_html = "\n".join(news_item_html(n, i+1, theme) for i, n in enumerate(news_list))
    else:
        news_html = """
      <div class="news-empty">
        <div class="news-empty-icon">ð­</div>
        <div class="news-empty-msg">ìì§ë ë´ì¤ê° ììµëë¤.</div>
      </div>"""

    return f"""
  <div class="stock-card {theme}-theme {visible}" id="card-{sid}">
    <div class="card-header">
      <div class="card-left">
        <div class="card-icon">{icon}</div>
        <div class="card-info">
          <a class="card-name-link" href="{naver_url}" target="_blank">
            <span class="card-name">{name}</span>
            <span class="naver-icon">N</span>
          </a>
          <div><span class="card-tag">{tag}</span></div>
        </div>
      </div>
    </div>
    <div class="news-wrap">
      <div class="news-label">ð° ì¤ëì ì£¼ì ë´ì¤ ({TODAY})</div>
      {news_html}
    </div>
  </div>"""

def build_html(all_news: dict) -> str:
    cards = "\n".join(build_card(s, all_news.get(s["id"], [])) for s in STOCKS)
    tabs  = ""
    for s in STOCKS:
        color = s["theme"]
        sid   = s["id"]
        active = "active" if sid == "kodex" else ""
        tabs += f'<button class="tab-btn {active}" data-color="{color}" data-target="card-{sid}" onclick="showCard(this)"><span class="tab-dot" style="background:var(--{color})"></span>{s["name"]}</button>\n      '

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>ð ë³´ì ì¢ëª© ë´ì¤ ë¸ë¦¬í</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    :root {{
      --bg:#0d1117; --surface:#161b27; --surface2:#1e2436; --border:#252d42;
      --text:#e2e8f0; --muted:#64748b;
      --blue:#60a5fa; --blue-dim:rgba(96,165,250,.13);
      --green:#34d399; --green-dim:rgba(52,211,153,.13);
      --purple:#a78bfa; --purple-dim:rgba(167,139,250,.13);
      --up:#22c55e; --dn:#ef4444; --naver:#03c75a;
    }}
    *, *::before, *::after {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{ font-family:'Noto Sans KR',sans-serif; background:var(--bg); color:var(--text); min-height:100vh; padding-bottom:60px; font-size:13px; }}
    .sticky-header {{ position:sticky; top:0; z-index:100; background:rgba(13,17,23,.95); backdrop-filter:blur(16px); border-bottom:1px solid var(--border); padding:0 16px; }}
    .header-inner {{ max-width:860px; margin:0 auto; display:flex; align-items:center; justify-content:space-between; gap:10px; padding:9px 0; flex-wrap:wrap; }}
    .brand {{ display:flex; align-items:center; gap:7px; }}
    .brand-title {{ font-size:.8rem; font-weight:700; }}
    .brand-date {{ font-size:.6rem; color:var(--muted); }}
    .tab-bar {{ display:flex; gap:5px; flex-wrap:wrap; }}
    .tab-btn {{ display:flex; align-items:center; gap:5px; padding:5px 12px; border-radius:999px; border:1px solid var(--border); background:transparent; color:var(--muted); font-size:.72rem; font-weight:500; cursor:pointer; transition:all .15s; font-family:'Noto Sans KR',sans-serif; white-space:nowrap; }}
    .tab-btn:hover {{ color:var(--text); border-color:#4b5563; }}
    .tab-dot {{ width:6px; height:6px; border-radius:50%; flex-shrink:0; }}
    .tab-btn[data-color="blue"].active   {{ background:var(--blue);   border-color:var(--blue);   color:#0d1117; font-weight:700; }}
    .tab-btn[data-color="green"].active  {{ background:var(--green);  border-color:var(--green);  color:#0d1117; font-weight:700; }}
    .tab-btn[data-color="purple"].active {{ background:var(--purple); border-color:var(--purple); color:#0d1117; font-weight:700; }}
    .page-body {{ max-width:860px; margin:0 auto; padding:18px 14px 0; display:flex; flex-direction:column; gap:16px; }}
    .stock-card {{ display:none; border-radius:16px; border:1px solid var(--border); overflow:hidden; background:var(--surface); box-shadow:0 4px 24px rgba(0,0,0,.4); animation:fadeIn .2s ease; }}
    .stock-card.visible {{ display:block; }}
    @keyframes fadeIn {{ from{{opacity:0;transform:translateY(5px)}} to{{opacity:1;transform:translateY(0)}} }}
    .card-header {{ padding:18px 20px 15px; border-bottom:1px solid var(--border); display:flex; align-items:center; justify-content:space-between; gap:14px; flex-wrap:wrap; }}
    .card-left {{ display:flex; align-items:center; gap:12px; }}
    .card-icon {{ width:44px; height:44px; border-radius:13px; display:flex; align-items:center; justify-content:center; font-size:1.35rem; flex-shrink:0; }}
    .blue-theme   .card-icon {{ background:var(--blue-dim); }}
    .green-theme  .card-icon {{ background:var(--green-dim); }}
    .purple-theme .card-icon {{ background:var(--purple-dim); }}
    .card-name-link {{ display:inline-flex; align-items:center; gap:5px; text-decoration:none; cursor:pointer; }}
    .card-name {{ font-size:1.15rem; font-weight:700; color:var(--text); transition:opacity .15s; }}
    .card-name-link:hover .card-name {{ opacity:.8; }}
    .naver-icon {{ display:inline-flex; align-items:center; justify-content:center; width:18px; height:18px; border-radius:5px; background:var(--naver); font-size:.6rem; font-weight:800; color:#fff; }}
    .card-tag {{ display:inline-block; margin-top:5px; font-size:.63rem; font-weight:500; padding:2px 8px; border-radius:999px; }}
    .blue-theme   .card-tag {{ background:var(--blue-dim);   color:#93c5fd; border:1px solid rgba(96,165,250,.25); }}
    .green-theme  .card-tag {{ background:var(--green-dim);  color:#6ee7b7; border:1px solid rgba(52,211,153,.25); }}
    .purple-theme .card-tag {{ background:var(--purple-dim); color:#c4b5fd; border:1px solid rgba(167,139,250,.25); }}
    .news-wrap {{ padding:2px 0; }}
    .news-label {{ font-size:.61rem; font-weight:600; letter-spacing:.07em; text-transform:uppercase; color:var(--muted); padding:12px 20px 7px; }}
    .news-item {{ display:flex; gap:10px; align-items:flex-start; padding:10px 20px; border-top:1px solid #1a2030; transition:background .14s; }}
    .news-item:hover {{ background:rgba(255,255,255,.025); }}
    .news-num {{ min-width:19px; height:19px; border-radius:6px; display:flex; align-items:center; justify-content:center; font-size:.6rem; font-weight:700; color:#0d1117; flex-shrink:0; margin-top:1px; }}
    .blue-theme   .news-num {{ background:var(--blue); }}
    .green-theme  .news-num {{ background:var(--green); }}
    .purple-theme .news-num {{ background:var(--purple); }}
    .news-title-link {{ text-decoration:none; color:inherit; display:block; margin-bottom:4px; }}
    .news-title-link:hover .news-title {{ color:#93c5fd; }}
    .news-title {{ font-size:.79rem; font-weight:500; color:var(--text); line-height:1.45; transition:color .14s; }}
    .news-desc {{ font-size:.69rem; color:var(--muted); line-height:1.55; }}
    .news-meta {{ display:flex; align-items:center; gap:8px; margin-top:4px; }}
    .news-date {{ font-size:.61rem; color:#475569; }}
    .news-link-btn {{ font-size:.58rem; color:var(--naver); border:1px solid rgba(3,199,90,.3); background:rgba(3,199,90,.07); padding:1px 6px; border-radius:4px; text-decoration:none; font-weight:600; transition:background .14s; cursor:pointer; }}
    .news-link-btn:hover {{ background:rgba(3,199,90,.18); }}
    .news-empty {{ display:flex; flex-direction:column; align-items:center; justify-content:center; padding:28px 20px; text-align:center; border-top:1px solid #1a2030; }}
    .news-empty-icon {{ font-size:1.7rem; margin-bottom:8px; opacity:.45; }}
    .news-empty-msg {{ font-size:.74rem; color:var(--muted); }}
    .footer {{ max-width:860px; margin:24px auto 0; padding:0 14px; text-align:center; font-size:.62rem; color:#374151; line-height:1.9; }}
  </style>
</head>
<body>

<div class="sticky-header">
  <div class="header-inner">
    <div class="brand">
      <span style="font-size:1.1rem">ð</span>
      <div>
        <div class="brand-title">ë³´ì ì¢ëª© ë´ì¤ ë¸ë¦¬í ëìë³´ë</div>
        <div class="brand-date">{TODAY} Â· ì ë 7ì ìë ìë°ì´í¸</div>
      </div>
    </div>
    <div class="tab-bar">
      {tabs}
    </div>
  </div>
</div>

<div class="page-body">
{cards}
</div>

<div class="footer">
  <p>ë´ì¤ ì¶ì²: ë¤ì´ë² íì´ë¸ì¤ Â· ìë ìì§ ({TODAY})</p>
  <p><span>ð¤ Generated by Claude Â· Cowork Mode Â· GitHub Actions</span></p>
</div>

<script>
  function showCard(btn) {{
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.stock-card').forEach(c => c.classList.remove('visible'));
    btn.classList.add('active');
    const t = document.getElementById(btn.dataset.target);
    if (t) t.classList.add('visible');
  }}
</script>
</body>
</html>"""

# ââ Gist ìë°ì´í¸ âââââââââââââââââââââââââââââââââââââââââââââ
def update_gist(html: str):
    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {
        "Authorization": f"Bearer {GIST_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {
        "description": f"ë³´ì ì¢ëª© ë´ì¤ ë¸ë¦¬í ëìë³´ë ({TODAY})",
        "files": {"portfolio_news.html": {"content": html}},
    }
    r = requests.patch(url, headers=headers, json=payload, timeout=30)
    if r.status_code == 200:
        print(f"â Gist ìë°ì´í¸ ìë£")
    else:
        print(f"â Gist ìë°ì´í¸ ì¤í¨: {r.status_code} {r.text[:200]}", file=sys.stderr)
        sys.exit(1)

# ââ Telegram ì ì¡ âââââââââââââââââââââââââââââââââââââââââââââ
def send_telegram():
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    text = (
        f"ð *ë³´ì ì¢ëª© ë´ì¤ ë¸ë¦¬í* ìë°ì´í¸!\n"
        f"ð {TODAY} ì ë 7ì\n\n"
        f"ð https://gist.githack.com/qualityboy972/{GIST_ID}/raw/portfolio\\_news.html"
    )
    r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=15)
    if r.json().get("ok"):
        print("â Telegram ì ì¡ ìë£")
    else:
        print(f"â Telegram ì¤í¨: {r.text}", file=sys.stderr)

# ââ ë©ì¸ ââââââââââââââââââââââââââââââââââââââââââââââââââââââ
def main():
    print(f"=== í¬í¸í´ë¦¬ì¤ ë´ì¤ ìë°ì´í¸ ìì ({TODAY}) ===")

    all_news = {}
    for s in STOCKS:
        all_news[s["id"]] = get_news(s["code"])

    html = build_html(all_news)
    print(f"HTML ìì± ìë£: {len(html):,} chars")

    update_gist(html)
    send_telegram()

    print("=== ìë£ ===")

if __name__ == "__main__":
    main()
