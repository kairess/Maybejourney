import streamlit as st
from helpers import *
from footer import footer

st.set_page_config(page_title="Credits", page_icon="ℹ")

st.title("Credits")

st.markdown("""
- 개발자: 빵형의 개발도상국 이태희
- 자문위원: 동명대학교 원종윤
- 지원
    - 사단법인 에이아이프렌즈학회 - ChatGPT, Midjourney API 지원
    - 주식회사 더매트릭스 - 데이터베이스 서버 지원

문의 : 이태희 kairess87@gmail.com
""")

footer(*footer_content)
