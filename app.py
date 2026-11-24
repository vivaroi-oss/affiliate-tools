import streamlit as st
import extra_streamlit_components as stx
import datetime
import hashlib
import io
import uuid
import random
import requests
import pyotp
import yt_dlp
import os
from PIL import Image, ImageEnhance

# Настройка страницы
st.set_page_config(page_title="Affiliate Hub", page_icon="🎯", layout="wide")

hide_streamlit_style = """
<style>
header {visibility: hidden !important;}
.stApp > header {display: none !important;}
[data-testid="stToolbar"] {visibility: hidden !important;}
footer {visibility: hidden !important;}
.stApp > footer {display: none !important;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ================= ПОЛЬЗОВАТЕЛИ И АВТОРИЗАЦИЯ =================
USERS = {
    "@fitspin": "Fs9#kL2p",
    "@guinness_house": "Gh4!mN8x",
    "@oldtraffer": "Ot7@vB3q",
    "@EL7Muchacho": "Em5$zW9r",
    "@pokomokoloko": "Pk2&cX6t",
    "@atreidespaul2": "Ap8*dF4y",
    "@parisior": "Pr3%hJ7u",
    "@Hanzzo_Hasashi": "Hh6^gK2v",
    "@apexpulse1": "Ax9!bM5w",
    "@Randombykva": "Rb4#nQ8z",
    "@fashionkillerr3": "Fk7@pS3c",
    "@jesusfromsion": "Jf2$tV6m",
}

# Секретная соль для генерации токена в cookies
COOKIE_SECRET = "aff_hub_secret_key_2026"
COOKIE_NAME = "aff_hub_auth"

cookie_manager = stx.CookieManager(key="auth_cookie_manager")

def make_token(username: str, password: str) -> str:
    raw = f"{username}:{password}:{COOKIE_SECRET}"
    return hashlib.sha256(raw.encode()).hexdigest()

def verify_cookie(cookie_val: str):
    if not cookie_val or ":" not in cookie_val:
        return None
    username, token = cookie_val.split(":", 1)
    if username in USERS and make_token(username, USERS[username]) == token:
        return username
    return None

def check_auth():
    # 1. Проверяем текущую сессию
    if st.session_state.get("authenticated_user"):
        return True

    # 2. Проверяем сохраненные cookies (на 35 дней)
    saved_cookie = cookie_manager.get(COOKIE_NAME)
    user_from_cookie = verify_cookie(saved_cookie)
    if user_from_cookie:
        st.session_state["authenticated_user"] = user_from_cookie
        return True

    # 3. Форма входа
    st.title("🔒 Вход в систему")
    col1, _ = st.columns([1, 2])
    with col1:
        login = st.text_input("Логин (например, @fitspin):").strip()
        pwd = st.text_input("Пароль:", type="password")
        if st.button("Войти", type="primary"):
            if login in USERS and USERS[login] == pwd:
                token = make_token(login, pwd)
                expires = datetime.datetime.now() + datetime.timedelta(days=35)
                cookie_manager.set(COOKIE_NAME, f"{login}:{token}", expires_at=expires)
                st.session_state["authenticated_user"] = login
                st.rerun()
            else:
                st.error("❌ Неверный логин или пароль")
    return False


# Если авторизация пройдена, показываем панель
if check_auth():
    current_user = st.session_state["authenticated_user"]

    # ================= ЛОГИКА ФУНКЦИЙ =================
    HOMOGLYPHS = {
        # Кириллица -> Латиница
        'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'у': 'y', 'х': 'x',
        'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H', 'О': 'O',
        'Р': 'P', 'С': 'C', 'Т': 'T', 'Х': 'X',
        # Латиница -> Кириллица
        'a': 'а', 'e': 'е', 'o': 'о', 'p': 'р', 'c': 'с', 'y': 'у', 'x': 'х',
        'A': 'А', 'B': 'В', 'E': 'Е', 'K': 'К', 'M': 'М', 'H': 'Н', 'O': 'О',
        'P': 'Р', 'C': 'С', 'T': 'Т', 'X': 'Х',
    }
    INVISIBLE_CHARS = ['\u200B', '\u200C', '\u200D']

    def uniqueize_text(text: str, use_homoglyphs: bool = True, use_invisible: bool = True, intensity: float = 0.6) -> str:
        result = []
        for char in text:
            new_char = char
            # Замена на визуально идентичную букву (гомоглиф)
            if use_homoglyphs and char in HOMOGLYPHS and random.random() < intensity:
                new_char = HOMOGLYPHS[char]
            result.append(new_char)

            # Точечная вставка невидимого символа внутри слов
            if use_invisible and char.isalpha() and random.random() < (intensity * 0.5):
                result.append(random.choice(INVISIBLE_CHARS))

        return ''.join(result)

    def uniqueize_image(image_bytes: bytes) -> bytes:
        img = Image.open(io.BytesIO(image_bytes))
        enhancer = ImageEnhance.Contrast(img)
        factor = random.uniform(0.95, 1.05)
        img = enhancer.enhance(factor)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        out = io.BytesIO()
        img.save(out, format='JPEG', quality=95)
        return out.getvalue()

    def get_random_selfie() -> bytes:
        try:
            api_url = "https://fakeface.rest/face/json"
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                image_url = response.json().get("image_url")
                if image_url:
                    img_response = requests.get(
