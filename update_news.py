#!/usr/bin/env python3
"""
포트폴리오 뉴스 자동 업데이트
- Naver Finance에서 최신 뉴스 수집
- GitHub Gist 업데이트
- Telegram 알림 전송
"""

import os, sys, requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

GIST_ID    = "98bfbf3fcd5e4d45f1f1eab66f069a89"
GIST_TOKEN = os.environ["GIST_TOKEN"]
TG_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
TG_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).strftime("%Y.%m.%d")

STOCKS = [
    {"id":"kodex",   "name":"KODEX 증권",   "code":"278540", "theme":"blue",   "icon":"🏦", "tag":"증권/금융 ETF · 278540"},
    {"id":"samsung", "name":"삼성전자",      "code":"005930", "theme":"green",  "icon":"📱", "tag":"KOSPI · 반도체/전자 · 005930"},
    {"id":"tiger",   "name":"TIGER 반도체", "code":"091230", "theme":"purple", "icon":"⚡", "tag":"반도체장비 ETF · 091230"},
]

HDRS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://finance.naver.com",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def get_news(code: str, count: int = 5) -> list:
    # 네이버 금융 뉴스 URL (모바일도 시도)
    urls = [
        f"https://finance.naver.com/item/news.nhn?code={code}&page=1",
        f"https://m.stock.naver.com/api/news/list?code={code}&page=1&pageSize={count}",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=HDRS, timeout=20)
            # JSON API 시도
            if "m.stock.naver.com" in url:
                try:
                    data = r.json()
                    items = []
                    for item in data.get("list", [])[:count]:
                        items.append({
                            "title":  item.get("title", ""),
                            "url":    item.get("url", ""),
                            "date":   item.get("datetime", "")[:10],
                            "source": item.get("officeName", ""),
                            "desc":   "",
                        })
                    if items:
                        print(f"[{code}] 뉴스 {len(items)}건 수집 (모바일 API)")
                        return items
                except Exception:
                    pass
            # 일반 HTML 파싱
            r.encoding = "euc-kr"
            soup = BeautifulSoup(r.text, "html.parser")
            items, seen = [], set()
            # 여러 셀렉터 시도
            selectors = [
                ("table.type5 tr", "td.title a", "td.date", "td.info"),
                ("ul.newsList li", "a", "span.date", "span.company"),
            ]
            for (row_sel, a_sel, dt_sel, src_sel) in selectors:
                for row in soup.select(row_sel):
                    a = row.select_one(a_sel)
                    dt = row.select_one(dt_sel)
                    src = row.select_one(src_sel)
                    if not a:
                        continue
                    title = a.get_text(strip=True)
                    if not title or title in seen or len(title) < 5:
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
                if items:
                    break
            if items:
                print(f"[{code}] 뉴스 {len(items)}건 수집")
                return items
        except Exception as e:
            print(f"[WARN] {code} ({url}): {e}", file=sys.stderr)
    print(f"[{code}] 뉴스 0건 수집")
    return []


def news_item_html(item, num, theme):
    title = item["title"].replace("<","&lt;").replace(">","&gt;")
    url   = item["url"]
    date  = item["date"]
    src   = item["source"]
    return f"""      <div class="news-item">
        <div class="news-num">{num}</div>
        <div style="flex:1;min-width:0;">
          <a class="news-title-link" href="{url}" target="_blank">
            <div class="news-title">{title}</div>
          </a>
          <div class="news-meta">
            <span class="news-date">{date} · {src}</span>
            <a class="news-link-btn" href="{url}" target="_blank">기사 보기 →</a>
          </div>
        </div>
      </div>"""


def build_card(stock, news_list):
    theme   = stock["theme"]
    sid     = stock["id"]
    name    = stock["name"]
    code    = stock["code"]
    icon    = stock["icon"]
    tag     = stock["tag"]
    visible = "visible" if sid == "kodex" else ""
    naver_url = f"https://finance.naver.com/item/main.naver?code={code}"
    if news_list:
        news_html = "\n".join(news_item_html(n, i+1, theme) for i, n in enumerate(news_list))
    else:
        news_html = '      <div class="news-empty"><div class="news-empty-icon">📭</div><div class="news-empty-msg">수집된 뉴스가 없습니다.</div></div>'
    return f"""  <div class="stock-card {theme}-theme {visible}" id="card-{sid}">
    <div class="card-header">
      <div class="card-left">
        <div class="card-icon">{icon}</div>
        <div class="card-info">
          <a class="card-name-link" href="{naver_url}" target="_blank">
            <span class="card-name">{name}</span><span class="naver-icon">N</span>
          </a>
          <div><span class="card-tag">{tag}</span></div>
        </div>
      </div>
    </div>
    <div class="news-wrap">
      <div class="news-label">📰 오늘의 주요 뉴스 ({TODAY})</div>
{news_html}
    </div>
  </div>"""


def build_html(all_news):
    cards = "\n".join(build_card(s, all_news.get(s["id"], [])) for s in STOCKS)
    tabs  = ""
    for s in STOCKS:
        active = "active" if s["id"] == "kodex" else ""
        tabs += f'<button class="tab-btn {active}" data-color="{s["theme"]}" data-target="card-{s["id"]}" onclick="showCard(this)"><span class="tab-dot" style="background:var(--{s["theme"]})"></span>{s["name"]}</button>\n      '
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>📊 보유종목 뉴스 브리핑</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    :root{{--bg:#0d1117;--surface:#161b27;--border:#252d42;--text:#e2e8f0;--muted:#64748b;
      --blue:#60a5fa;--blue-dim:rgba(96,165,250,.13);
      --green:#34d399;--green-dim:rgba(52,211,153,.13);
      --purple:#a78bfa;--purple-dim:rgba(167,139,250,.13);--naver:#03c75a;}}
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
    body{{font-family:'Noto Sans KR',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;padding-bottom:60px;font-size:13px;}}
    .sticky-header{{position:sticky;top:0;z-index:100;background:rgba(13,17,23,.95);backdrop-filter:blur(16px);border-bottom:1px solid var(--border);padding:0 16px;}}
    .header-inner{{max-width:860px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:9px 0;flex-wrap:wrap;}}
    .brand{{display:flex;align-items:center;gap:7px;}}
    .brand-title{{font-size:.8rem;font-weight:700;}}
    .brand-date{{font-size:.6rem;color:var(--muted);}}
    .tab-bar{{display:flex;gap:5px;flex-wrap:wrap;}}
    .tab-btn{{display:flex;align-items:center;gap:5px;padding:5px 12px;border-radius:999px;border:1px solid var(--border);background:transparent;color:var(--muted);font-size:.72rem;font-weight:500;cursor:pointer;transition:all .15s;font-family:'Noto Sans KR',sans-serif;white-space:nowrap;}}
    .tab-btn:hover{{color:var(--text);border-color:#4b5563;}}
    .tab-dot{{width:6px;height:6px;border-radius:50%;flex-shrink:0;}}
    .tab-btn[data-color="blue"].active{{background:var(--blue);border-color:var(--blue);color:#0d1117;font-weight:700;}}
    .tab-btn[data-color="green"].active{{background:var(--green);border-color:var(--green);color:#0d1117;font-weight:700;}}
    .tab-btn[data-color="purple"].active{{background:var(--purple);border-color:var(--purple);color:#0d1117;font-weight:700;}}
    .page-body{{max-width:860px;margin:0 auto;padding:18px 14px 0;display:flex;flex-direction:column;gap:16px;}}
    .stock-card{{display:none;border-radius:16px;border:1px solid var(--border);overflow:hidden;background:var(--surface);box-shadow:0 4px 24px rgba(0,0,0,.4);animation:fadeIn .2s ease;}}
    .stock-card.visible{{display:block;}}
    @keyframes fadeIn{{from{{opacity:0;transform:translateY(5px)}}to{{opacity:1;transform:translateY(0)}}}}
    .card-header{{padding:18px 20px 15px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;}}
    .card-left{{display:flex;align-items:center;gap:12px;}}
    .card-icon{{width:44px;height:44px;border-radius:13px;display:flex;align-items:center;justify-content:center;font-size:1.35rem;flex-shrink:0;}}
    .blue-theme .card-icon{{background:var(--blue-dim);}}
    .green-theme .card-icon{{background:var(--green-dim);}}
    .purple-theme .card-icon{{background:var(--purple-dim);}}
    .card-name-link{{display:inline-flex;align-items:center;gap:5px;text-decoration:none;cursor:pointer;}}
    .card-name{{font-size:1.15rem;font-weight:700;color:var(--text);transition:opacity .15s;}}
    .card-name-link:hover .card-name{{opacity:.8;}}
    .naver-icon{{display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;border-radius:5px;background:var(--naver);font-size:.6rem;font-weight:800;color:#fff;}}
    .card-tag{{display:inline-block;margin-top:5px;font-size:.63rem;font-weight:500;padding:2px 8px;border-radius:999px;}}
    .blue-theme .card-tag{{background:var(--blue-dim);color:#93c5fd;border:1px solid rgba(96,165,250,.25);}}
    .green-theme .card-tag{{background:var(--green-dim);color:#6ee7b7;border:1px solid rgba(52,211,153,.25);}}
    .purple-theme .card-tag{{background:var(--purple-dim);color:#c4b5fd;border:1px solid rgba(167,139,250,.25);}}
    .news-wrap{{padding:2px 0;}}
    .news-label{{font-size:.61rem;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);padding:12px 20px 7px;}}
    .news-item{{display:flex;gap:10px;align-items:flex-start;padding:10px 20px;border-top:1px solid #1a2030;transition:background .14s;}}
    .news-item:hover{{background:rgba(255,255,255,.025);}}
    .news-num{{min-width:19px;height:19px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:.6rem;font-weight:700;color:#0d1117;flex-shrink:0;margin-top:1px;}}
    .blue-theme .news-num{{background:var(--blue);}}
    .green-theme .news-num{{background:var(--green);}}
    .purple-theme .news-num{{background:var(--purple);}}
    .news-title-link{{text-decoration:none;color:inherit;display:block;margin-bottom:4px;}}
    .news-title{{font-size:.79rem;font-weight:500;color:var(--text);line-height:1.45;transition:color .14s;}}
    .news-title-link:hover .news-title{{color:#93c5fd;}}
    .news-meta{{display:flex;align-items:center;gap:8px;margin-top:4px;}}
    .news-date{{font-size:.61rem;color:#475569;}}
    .news-link-btn{{font-size:.58rem;color:var(--naver);border:1px solid rgba(3,199,90,.3);background:rgba(3,199,90,.07);padding:1px 6px;border-radius:4px;text-decoration:none;font-weight:600;transition:background .14s;}}
    .news-link-btn:hover{{background:rgba(3,199,90,.18);}}
    .news-empty{{display:flex;flex-direction:column;align-items:center;padding:28px 20px;text-align:center;border-top:1px solid #1a2030;}}
    .news-empty-icon{{font-size:1.7rem;margin-bottom:8px;opacity:.45;}}
    .news-empty-msg{{font-size:.74rem;color:var(--muted);}}
    .footer{{max-width:860px;margin:24px auto 0;padding:0 14px;text-align:center;font-size:.62rem;color:#374151;line-height:1.9;}}
  </style>
</head>
<body>
<div class="sticky-header">
  <div class="header-inner">
    <div class="brand">
      <span style="font-size:1.1rem">📊</span>
      <div>
        <div class="brand-title">보유종목 뉴스 브리핑 대시보드</div>
        <div class="brand-date">{TODAY} · 저녁 7시 자동 업데이트</div>
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
  <p>뉴스 출처: 네이버 파이낸스 · 자동 수집 ({TODAY})</p>
  <p>🤖 Generated by Claude · Cowork Mode · GitHub Actions</p>
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


def update_gist(html: str):
    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {
        "Authorization": f"Bearer {GIST_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {
        "description": f"보유종목 뉴스 브리핑 대시보드 ({TODAY})",
        "files": {{"portfolio_news.html": {{"content": html}}}},
    }
    r = requests.patch(url, headers=headers, json=payload, timeout=30)
    if r.status_code == 200:
        print("✅ Gist 업데이트 완료")
    else:
        print(f"❌ Gist 업데이트 실패: {r.status_code} {r.text[:200]}", file=sys.stderr)
        sys.exit(1)


def send_telegram():
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    text = (
        f"📊 *보유종목 뉴스 브리핑* 업데이트!\n"
        f"🗓 {TODAY} 저녁 7시\n\n"
        f"🔗 https://gist.githack.com/qualityboy972/{GIST_ID}/raw/portfolio\_news.html"
    )
    r = requests.post(url, json={{"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "Markdown"}}, timeout=15)
    if r.json().get("ok"):
        print("✅ Telegram 전송 완료")
    else:
        print(f"❌ Telegram 실패: {r.text}", file=sys.stderr)


def main():
    print(f"=== 포트폴리오 뉴스 업데이트 시작 ({TODAY}) ===")
    all_news = {{}}
    for s in STOCKS:
        all_news[s["id"]] = get_news(s["code"])
    html = build_html(all_news)
    print(f"HTML 생성 완료: {{len(html):,}} chars")
    update_gist(html)
    send_telegram()
    print("=== 완료 ===")

if __name__ == "__main__":
    main()

