import streamlit as st

SITES = [
    {
        "name": "금감원-감독원장 제공자료",
        "url": "https://www.fss.or.kr/fss/bbs/B0000318/list.do?menuNo=200760",
    },
    {
        "name": "금감원-업무자료",
        "url": "https://www.fss.or.kr/fss/bbs/B0000123/list.do?menuNo=200424",
    },
    {
        "name": "금감원-보험업무자료",
        "url": "https://www.fss.or.kr/fss/bbs/B0000114/list.do?menuNo=200142",
    },
    {
        "name": "KIRI 리포트",
        "url": "https://www.kiri.or.kr/publication/subIntro.do?parentCatId=13",
    },
    {
        "name": "KIDI 보도자료",
        "url": "https://www.kidi.or.kr/user/nd11592.do",
    },
]


def main() -> None:
    st.set_page_config(page_title="보험/금융권 원문 모니터링", layout="wide")
    st.title("보험/금융권 통합 모니터링 (원문 보기)")
    st.write("각 출처 페이지를 한 화면에서 탭으로 확인합니다.")

    all_names = [site["name"] for site in SITES]
    site_map = {site["name"]: site for site in SITES}

    selected = all_names
    iframe_height = 1400

    tabs = st.tabs(selected)
    for tab, name in zip(tabs, selected):
        site = site_map[name]
        with tab:
            st.markdown(f"**원문 링크:** {site['url']}")
            st.components.v1.iframe(site["url"], width="100%", height=iframe_height, scrolling=True)

    st.caption("일부 사이트는 X-Frame-Options 설정으로 임베드가 차단될 수 있습니다. 링크를 통해 직접 여세요.")


if __name__ == "__main__":
    main()
