import streamlit as st
import streamlit.components.v1 as components
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

AUTH_SECRET = "aff_hub_secret_key_2026"

def make_token(username: str, password: str) -> str:
    raw = f"{username}:{password}:{AUTH_SECRET}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]

def verify_token(auth_param: str):
    if not auth_param or ":" not in auth_param:
        return None
    username, token = auth_param.split(":", 1)
    if username in USERS and make_token(username, USERS[username]) == token:
        return username
    return None

def play_notification_sound():
    sound_js = """
    <script>
    (function() {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const playTone = (freq, startTime, duration) => {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(freq, startTime);
                gain.gain.setValueAtTime(0.15, startTime);
                gain.gain.exponentialRampToValueAtTime(0.001, startTime + duration);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(startTime);
                osc.stop(startTime + duration);
            };
            const now = ctx.currentTime;
            playTone(587.33, now, 0.15);        // D5
            playTone(880.00, now + 0.12, 0.25); // A5
        } catch (e) {}
    })();
    </script>
    """
    components.html(sound_js, height=0)

@st.dialog("📌 Обязательно сохраните доступ!")
def show_bookmark_dialog():
    play_notification_sound()
    st.markdown(
        """
        Вы успешно вошли в **Affiliate Hub**.

        **Обязательно добавьте эту страницу в закладки прямо сейчас**, чтобы сохранить доступ и больше не вводить логин и пароль:
        * **Windows:** нажмите `Ctrl + D`
        * **Mac:** нажмите `Cmd + D`
        * **Телефон:** нажмите «Поделиться» / «Меню» → «Добавить в закладки»
        """
    )
    if st.button("Понятно, добавил(а) в закладки", type="primary", use_container_width=True):
        st.session_state["show_bookmark_popup"] = False
        st.rerun()

def check_auth():
    # 1. Проверяем токен в адресной строке (переживает F5 и закладки)
    auth_param = st.query_params.get("auth")
    user_from_url = verify_token(auth_param)
    if user_from_url:
        st.session_state["authenticated_user"] = user_from_url
        return True

    # 2. Проверяем текущую сессию
    if st.session_state.get("authenticated_user"):
        return True

    # 3. Форма входа
    st.title("🔒 Вход в систему")
    col1, _ = st.columns([1, 2])
    with col1:
        login = st.text_input("Логин (например, @заливатор3000роя):").strip()
        pwd = st.text_input("Пароль:", type="password")
        if st.button("Войти", type="primary"):
            if login in USERS and USERS[login] == pwd:
                token = make_token(login, pwd)
                st.query_params["auth"] = f"{login}:{token}"
                st.session_state["authenticated_user"] = login
                st.session_state["show_bookmark_popup"] = True
                st.rerun()
            else:
                st.error("❌ Неверный логин или пароль")
    return False


# Если авторизация пройдена, показываем панель
if check_auth():
    current_user = st.session_state["authenticated_user"]

    # Показываем всплывающее окно со звуком сразу после логина
    if st.session_state.get("show_bookmark_popup"):
        show_bookmark_dialog()

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
            if use_homoglyphs and char in HOMOGLYPHS and random.random() < intensity:
                new_char = HOMOGLYPHS[char]
            result.append(new_char)

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
                    img_response = requests.get(image_url, timeout=10)
                    if img_response.status_code == 200:
                        return img_response.content
        except Exception:
            pass
        return b""

    def download_video(url: str) -> str:
        filename = f"vid_{uuid.uuid4().hex[:8]}.mp4"
        ydl_opts = {
            'outtmpl': filename,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return filename

    # ================= ИНТЕРФЕЙС (UI) =================
    st.sidebar.title("🎯 Affiliate Hub")
    st.sidebar.markdown(f"👤 Аккаунт: **{current_user}**")
    st.sidebar.caption("💡 Добавьте эту страницу в закладки, чтобы не вводить пароль снова.")

    if st.sidebar.button("🚪 Выйти"):
        st.query_params.clear()
        st.session_state["authenticated_user"] = None
        st.session_state["show_bookmark_popup"] = False
        st.rerun()

    menu = st.sidebar.radio(
        "Выберите инструмент:",
        ["🎭 Уникализатор текста", "🖼 Уникализатор крео", "🔐 2FA Генератор", "🤳 Селфи-генератор", "📥 Скачать видео"]
    )

    if menu == "🎭 Уникализатор текста":
        st.header("Уникализатор текста")
        source_text = st.text_area("Введите исходный текст:", height=150)

        col1, col2, col3 = st.columns(3)
        with col1:
            use_homoglyphs = st.checkbox("Подмена букв (кириллица ↔ латиница)", value=True)
        with col2:
            use_invisible = st.checkbox("Невидимые символы", value=True)
        with col3:
            intensity = st.slider("Сила уникализации", min_value=0.1, max_value=1.0, value=0.6, step=0.1)

        if st.button("Уникализировать", type="primary"):
            if source_text:
                result = uniqueize_text(source_text, use_homoglyphs, use_invisible, intensity)
                st.success("Готово! Для глаза текст не изменился, для ботов — полностью другой:")
                st.code(result, language="text")
            else:
                st.warning("Сначала введите текст.")

    elif menu == "🖼 Уникализатор крео":
        st.header("Уникализатор креативов (Изображения)")
        uploaded_file = st.file_uploader("Загрузите картинку (JPG/PNG)", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Исходник", width=300)
            if st.button("Уникализировать фото", type="primary"):
                with st.spinner("Обработка..."):
                    new_image_bytes = uniqueize_image(uploaded_file.getvalue())
                    new_filename = f"creative_{uuid.uuid4().hex[:8]}.jpg"
                    st.success("Креатив успешно уникализирован!")
                    st.download_button("💾 Скачать уникальное фото", data=new_image_bytes, file_name=new_filename, mime="image/jpeg")

    elif menu == "🔐 2FA Генератор":
        st.header("Генератор 2FA (TOTP)")
        secret = st.text_input("Введите секретный ключ:")
        if st.button("Получить код", type="primary"):
            if secret:
                try:
                    totp = pyotp.TOTP(secret.replace(' ', '').upper())
                    st.info("Ваш код для входа:")
                    st.title(totp.now())
                except Exception:
                    st.error("❌ Неверный формат секрета. Убедитесь, что скопировали его правильно.")

    elif menu == "🤳 Селфи-генератор":
        st.header("Генератор уникальных селфи для ЗРД")
        if st.button("Сгенерировать селфи", type="primary"):
            with st.spinner("Нейросеть рисует лицо..."):
                photo_bytes = get_random_selfie()
                if photo_bytes:
                    st.image(photo_bytes, caption="Уникальное селфи", width=400)
                    st.download_button("💾 Скачать селфи", data=photo_bytes, file_name=f"selfie_{uuid.uuid4().hex[:6]}.jpg", mime="image/jpeg")
                else:
                    st.error("❌ Не удалось получить фото от нейросети. Попробуйте еще раз.")

    elif menu == "📥 Скачать видео":
        st.header("Загрузка видео без водяных знаков")
        url = st.text_input("Вставьте ссылку на видео:")
        if st.button("Скачать", type="primary"):
            if url:
                with st.spinner("Скачиваем видео, пожалуйста подождите..."):
                    filename = None
                    try:
                        filename = download_video(url)
                        with open(filename, 'rb') as f:
                            video_bytes = f.read()
                        st.success("Видео загружено!")
                        st.download_button("💾 Сохранить видео", data=video_bytes, file_name=f"video_{uuid.uuid4().hex[:6]}.mp4", mime="video/mp4")
                    except Exception as e:
                        st.error(f"❌ Ошибка при загрузке видео: {e}")
                    finally:
                        if filename and os.path.exists(filename):
                            os.remove(filename)
            else:
                st.warning("Сначала вставьте ссылку.")
