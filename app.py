from typing import Dict, Optional
from urllib.parse import urljoin

import requests
import streamlit as st
from bs4 import BeautifulSoup

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) "
        "Gecko/20100101 Firefox/117.0"
    )
}

SITES = [
    {
        "name": "금감원-감독원장 제공자료",
        "url": "https://www.fss.or.kr/fss/bbs/B0000318/list.do?menuNo=200760",
        "kind": "fss",
    },
    {
        "name": "금감원-업무자료",
        "url": "https://www.fss.or.kr/fss/bbs/B0000123/list.do?menuNo=200424",
        "kind": "fss",
    },
    {
        "name": "금감원-보험업무자료",
        "url": "https://www.fss.or.kr/fss/bbs/B0000114/list.do?menuNo=200142",
        "kind": "fss",
    },
    {
        "name": "KIRI 리포트",
        "url": "https://www.kiri.or.kr/publication/subIntro.do?parentCatId=13",
        "kind": "kiri",
    },
    {
        "name": "KIDI 보도자료",
        "url": "https://www.kidi.or.kr/user/nd11592.do",
        "kind": "kidi",
    },
]


def fetch_latest_fss(url: str) -> Optional[Dict[str, str]]:
    resp = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    row = soup.select_one("div.bd-list table tbody tr")
    if not row:
        return None
    tds = row.find_all("td")
    title_el = row.select_one("td.title a")
    date_text = tds[3].get_text(strip=True) if len(tds) >= 4 else ""
    title = title_el.get_text(strip=True) if title_el else ""
    link = urljoin(url, title_el.get("href", "")) if title_el else url
    return {"title": title, "date": date_text, "link": link}


def fetch_latest_kiri(url: str) -> Optional[Dict[str, str]]:
    resp = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    container = soup.select_one("div.pub_intobox_rep")
    if not container:
        return None
    children = container.find_all("div", recursive=False)
    if len(children) < 2:
        return None
    content = children[1]
    header = content.find("div")
    edition = header.find("h3").get_text(strip=True) if header and header.find("h3") else ""
    raw_date = header.find("span").get_text(strip=True) if header and header.find("span") else ""
    date_text = raw_date.split(":")[-1].strip() if ":" in raw_date else raw_date
    first_link = content.select_one("ul li a")
    title = first_link.get_text(strip=True) if first_link else edition
    link = urljoin(url, first_link.get("href", "")) if first_link else url
    merged_title = f"{edition} - {title}" if edition and title else title or edition
    return {"title": merged_title or "", "date": date_text, "link": link}


def fetch_latest_kidi(url: str) -> Optional[Dict[str, str]]:
    resp = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    row = soup.select_one("div.list_table tbody tr")
    if not row:
        return None
    tds = row.find_all("td")
    title_el = row.select_one("td.le a")
    date_text = tds[2].get_text(strip=True) if len(tds) >= 3 else ""
    title = title_el.get_text(strip=True) if title_el else ""
    href = title_el.get("href", "") if title_el else ""
    link = url if not href or href.startswith("javascript") else urljoin(url, href)
    return {"title": title, "date": date_text, "link": link}


def fetch_latest(site: Dict[str, str]) -> Optional[Dict[str, str]]:
    kind = site.get("kind")
    if kind == "fss":
        return fetch_latest_fss(site["url"])
    if kind == "kiri":
        return fetch_latest_kiri(site["url"])
    if kind == "kidi":
        return fetch_latest_kidi(site["url"])
    return None


@st.cache_data(ttl=300, show_spinner=False)
def cached_latest(kind: str, url: str, name: str) -> Optional[Dict[str, str]]:
    site = {"kind": kind, "url": url, "name": name}
    return fetch_latest(site)


def main() -> None:
    st.set_page_config(page_title="보험/금융권 원문 모니터링", layout="wide")
    st.title("보험/금융권 통합 모니터링 (원문 보기)")
    st.write("각 출처 페이지를 한 화면에서 확인하고, 최신 글을 요약 테이블로 봅니다.")

    st.markdown(
        """
        <style>
        .source-btn {
            background: linear-gradient(135deg, #1f6feb, #1b4b9c);
            color: white;
            padding: 14px 18px;
            border-radius: 10px;
            border: 0;
            font-weight: 700;
            width: 100%;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            cursor: pointer;
        }
        .source-btn:hover { background: linear-gradient(135deg, #1a5bcc, #163f82); }
        .source-btn:active { transform: translateY(1px); }
        </style>
        """,
        unsafe_allow_html=True,
    )

    all_names = [site["name"] for site in SITES]
    site_map = {site["name"]: site for site in SITES}

    # Latest summary table across all sources (cached to avoid 반복 요청 on clicks).
    st.subheader("최신 글 요약")
    summary_rows = []
    for site in SITES:
        latest = None
        try:
            latest = cached_latest(site["kind"], site["url"], site["name"])
        except Exception as exc:  # noqa: BLE001
            st.warning(f"{site['name']} 최신 글 조회 실패: {exc}")
        if latest:
            summary_rows.append(
                {
                    "출처": site["name"],
                    "제목": latest.get("title", ""),
                    "날짜": latest.get("date", ""),
                    "링크": latest.get("link", site["url"]),
                }
            )
    if summary_rows:
        st.dataframe(
            summary_rows,
            hide_index=True,
            column_config={
                "출처": "출처",
                "제목": "제목",
                "날짜": "날짜",
                "링크": st.column_config.LinkColumn("링크"),
            },
            use_container_width=True,
        )
    else:
        st.info("최신 글 정보를 불러오지 못했습니다.")

    # Ensure a selected site lives across reruns.
    if "selected_site" not in st.session_state:
        st.session_state["selected_site"] = all_names[0]

    # Quick buttons to pick a site.
    st.subheader("웹사이트 바로보기")
    cols = st.columns(len(SITES))
    for col, site in zip(cols, SITES):
        with col:
            if st.button(site["name"], key=f"btn_{site['name']}", use_container_width=True):
                st.session_state["selected_site"] = site["name"]

    selected = [st.session_state["selected_site"]]
    iframe_height = 800

    # Show selected site iframe.
    name = selected[0]
    site = site_map[name]
    latest_selected = None
    try:
        latest_selected = cached_latest(site["kind"], site["url"], site["name"])
    except Exception as exc:  # noqa: BLE001
        st.warning(f"{name} 최신 글 조회 실패: {exc}")

    st.markdown(f"### {name}")
    st.markdown(f"**원문 링크:** {site['url']}")
    if latest_selected:
        st.info(f"최신: {latest_selected.get('date', '')} · [{latest_selected.get('title', '')}]({latest_selected.get('link', site['url'])})")
    else:
        st.info("최신 글 정보를 불러오지 못했습니다.")
    iframe_html = f"""
    <div style="display:flex; justify-content:center;">
        <iframe src="{site['url']}" style="width:70%; height:{iframe_height}px; border:1px solid #ddd;" scrolling="yes"></iframe>
    </div>
    """
    st.components.v1.html(iframe_html, height=iframe_height + 40)

    st.caption("일부 사이트는 X-Frame-Options 설정으로 임베드가 차단될 수 있습니다. 링크를 통해 직접 여세요.")


if __name__ == "__main__":
    main()
