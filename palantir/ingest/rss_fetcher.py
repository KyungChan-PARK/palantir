import json
import os
from datetime import datetime

import feedparser
import requests

# RSS 피드 목록 (향후 yaml/json 등 외부 파일로 관리 가능)
RSS_FEEDS = [
    # 예시: Seeking Alpha 종목별/뉴스/프리미엄 피드
    "https://seekingalpha.com/symbol/AAPL/news?rss=1",
    "https://seekingalpha.com/symbol/TSLA/news?rss=1",
    "https://seekingalpha.com/market-news/all?rss=1",
    # 필요시 추가
]

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
    "Cookie": "machine_cookie=fkn4kwlgut1749371974; _gcl_au=1.1.262979470.1749371972; _fbp=fb.1.1749371971944.102461898473930704; _ga=GA1.1.480945793.1749371972; sa-r-source=www.google.com; sa-user-id=s%253A0-11e1f8a6-1381-5356-5ea0-5735c6572732.nsMKVwAupzaa3U8CpVOkfBD58DpV6SEKjQJ9vfkyPOQ; sa-user-id-v2=s%253AEeH4phOBU1ZeoFc1xlcnMnCe9Ko.Il6%252B3xD1uYwemC0bZJirwET7fLYEv2FliMJ%252FPcOy3vs; sa-user-id-v3=s%253AAQAKINHcCUgXkdmiUHG97_2amFzrFxhrjQVLJDqaGSVtuirPEAEYAyDcqfvBBjABOgS0oh7QQgQa9lME.BLPlIY4v7MCV74TgCAUayIL2R%252BFrwT%252BJMvnZjI3Wsss; hubspotutk=eb6848ff1a4985d19c07841e0202694d; _pxvid=1d33f682-4444-11f0-a660-542f32d09b81; user_id=61491218; user_nick=; user_devices=1; u_voc=; has_paid_subscription=true; ever_pro=1; user_remember_token=eec34b5d78572d1309c801f283b28d15342f2f11; sailthru_hid=f6fa0fe4e9f7b1fb6fd857ef9bf6d9a467543341621dc89ec70a4665499311cc8a811654bd11e1dcf30b4fe6; __stripe_mid=0c17dca0-0936-497c-9b34-4db5c60bc3a6c1b11e; _hjSessionUser_65666=eyJpZCI6ImExODZlMDYwLTQwNTAtNTEyMC04ODRmLTFjNTFiNGM4N2IzZiIsImNyZWF0ZWQiOjE3NDkzNzE5NzIzNTQsImV4aXN0aW5nIjp0cnVlfQ==; sa-r-date=2025-06-08T08:54:44.867Z; sapu=12; ubvt=v2%7C4cb0eae8-db5d-4c02-8eb9-c07b9729b29b%7Cb99c4311-2a19-471c-9120-0333adb5d42b%3Af%3Asingle%3Asingle; session_id=2a51a8c1-83e6-4665-83c0-97eadb080fd0; _sasource=; _hjSession_65666=eyJpZCI6ImRiMzFjY2U5LWFhZTItNGYyOC1iMzRkLTRjN2Y3YzUwZGM5NSIsImMiOjE3NDk5MDc3MjAyNDIsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=; _hjHasCachedUserAttributes=true; __hstc=234155329.eb6848ff1a4985d19c07841e0202694d.1749371973336.1749808452708.1749907721945.6; __hssrc=1; pxcts=7d65a3a9-4923-11f0-98d7-4acf90ac2806; _igt=482aa066-fdc2-4ea5-98ac-e25a55f512de; __stripe_sid=fe61b738-036f-4951-bc24-1315be1b62bf9f5213; user_cookie_key=giayme; gk_user_access=1*premium.archived*1749908805; gk_user_access_sign=17aa9be350d6b849038febca88105262569d8156; _ig=61491218; sailthru_pageviews=3; _uetsid=7bf0fd00492311f0981f0f74427248cb|r888xy|2|fwr|0|1991; sailthru_visitor=389139a2-b6b7-4738-8a94-0c7a53986791; __hssc=234155329.3.1749907721945; userLocalData_mone_session_lastSession=%7B%22machineCookie%22%3A%22fkn4kwlgut1749371974%22%2C%22machineCookieSessionId%22%3A%22fkn4kwlgut1749371974%261749907718098%22%2C%22sessionStart%22%3A1749907718098%2C%22sessionEnd%22%3A1749912242366%2C%22firstSessionPageKey%22%3A%22d770bc8a-a715-48fe-a2d8-e7e77e866099%22%2C%22isSessionStart%22%3Afalse%2C%22lastEvent%22%3A%7B%22event_type%22%3A%22mousemove%22%2C%22timestamp%22%3A1749910442366%7D%7D; LAST_VISITED_PAGE=%7B%22pathname%22%3A%22https%3A%2F%2Fseekingalpha.com%2Fbasic-search%22%7D; sailthru_content=c2b306243299cf46c67ba517b897bbdff91dbe4262df3b8733a4b45b11c1c21d12f0cf19bae9ed1b04e69b3fe5c53d9c9e7d0fc72b96c5784193dc4cf27c570184a044f7651eb9c7d9ea0f75ede6955b7c3781d29813fb2fd823326f67b8e756a6868281678e0269f2e30c72a59520f8cee9f6e97844b2d50c1a0176d4b403dcf0251524d6c5bdfecb6f06af6381eace2ac00beb60bb78d7359c727667d9ca5713741877443965e34ffe5c6c9be5b0a2d336ff2bdab2770099e746360c3b2e4a0024a75f302d6af06d1d7e50162cf1c7721c557e8a4ed5e463aff787795f49ac3c5f57e561d9315a8a9a86be8720511e50d1ea7aed4473f0c48c1c3f2432be71; _uetvid=192f5170444411f08a9231282989f361|nqhc19|1749910444385|6|1|bat.bing-int.com/p/insights/c/e; _px3=116153213f3386583a08a95544341fa7f7a58f6f6b6495db8c081747db9e73ec:sjZAsd1+yVPCvr6VZ10X20SokJ6MatM6BHcYh99lnZx9dYrKqb8/OsYEqVHSaHJtLCdrfphdUY3vcklhV57jVw==:1000:hbaHmiDdvow60oB8un7SAvZuUUpuDF+qNlDYEp8iqMwcZEsVxnQvw4hPlJB2LQEF3LmPSK/A0XwmMSVF4mA7wB+vpG3kVxCjav6nTVUIb0r5qX9FkGd/KvdTyHlZmDC9LM3le2aT+om1iGFlhxjrGm3GipKRFoIQCTgAoyfGQubQpb9jLgzpduDcNC1oHUSJz7kXPoc6Fh4w3Qf4Ty5P/dElM0OT0YDhDDJNy6E9FtM=; _pxde=d02f60253f81e0a292cacaa55f9e570abba55925c12ab741bf4a0ae58899b6e4:eyJ0aW1lc3RhbXAiOjE3NDk5MTA0NTAwMDUsImZfa2IiOjB9; _ga_KGRFF2R2C5=GS2.1.s1749907720$o7$g1$t1749910451$j19$l0$h0",
}


def fetch_rss_with_requests(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        print(f"HTTP {resp.status_code} for {url}")
        if resp.status_code != 200:
            print(f"Response text (truncated): {resp.text[:200]}")
            return None
        return resp.content
    except Exception as e:
        print(f"requests error: {e}")
        return None


def parse_rss_feed(url):
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries:
        articles.append(
            {
                "title": entry.title,
                "link": entry.link,
                "summary": entry.get("summary", ""),
                "published": (
                    datetime(*entry.published_parsed[:6]).isoformat()
                    if hasattr(entry, "published_parsed")
                    else None
                ),
                "category": entry.get("category", ""),
                "content": (
                    entry.get("content", [{}])[0].get("value", "")
                    if "content" in entry
                    else ""
                ),
            }
        )
    return articles


def save_articles(articles, filename):
    with open(os.path.join(DATA_DIR, filename), "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)


def main():
    for url in RSS_FEEDS:
        if "symbol/" in url:
            symbol = url.split("symbol/")[1].split("/")[0]
        elif "market-news" in url:
            symbol = "all"
        else:
            symbol = "misc"
        print(f"==== {symbol} ====")
        xml = fetch_rss_with_requests(url)
        if not xml:
            print(f"{symbol}: RSS fetch 실패, 건너뜀\n")
            continue
        feed = feedparser.parse(xml)
        print(f"status: {getattr(feed, 'status', 'N/A')}")
        print(f"bozo: {feed.bozo}")
        if feed.bozo:
            print(f"bozo_exception: {feed.bozo_exception}")
        print(f"entries: {len(feed.entries)}")
        articles = []
        for entry in feed.entries:
            articles.append(
                {
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.get("summary", ""),
                    "published": (
                        datetime(*entry.published_parsed[:6]).isoformat()
                        if hasattr(entry, "published_parsed")
                        else None
                    ),
                    "category": entry.get("category", ""),
                    "content": (
                        entry.get("content", [{}])[0].get("value", "")
                        if "content" in entry
                        else ""
                    ),
                }
            )
        with open(
            os.path.join(DATA_DIR, f"rss_{symbol}.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        print(f"{symbol}: {len(articles)} articles saved.\n")


if __name__ == "__main__":
    main()
