import streamlit as st
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
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
# ================= ПАРОЛЬ =================
PASSWORD = "admin" # <-- Впиши свой пароль сюда

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔒 Вход в систему")
        pwd = st.text_input("Введите пароль для доступа к инструментам:", type="password")
        if st.button("Войти", type="primary"):
            if pwd == PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Неверный пароль")
        return False
    return True

# Если пароль верный, показываем весь сайт
if check_password():
    
    # ================= ЛОГИКА ФУНКЦИЙ =================
    def insert_invisible_chars(text: str) -> str:
        return '\u200B'.join(list(text))

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
            # Используем API, которое надежно работает на облачных серверах
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
    st.sidebar.markdown("Рабочая панель для баеров")
    
    if st.sidebar.button("🚪 Выйти"):
        st.session_state["password_correct"] = False
        st.rerun()

    menu = st.sidebar.radio(
        "Выберите инструмент:",
        ["🎭 Уникализатор текста", "🖼 Уникализатор крео", "🔐 2FA Генератор", "🤳 Селфи-генератор", "📥 Скачать видео"]
    )

    if menu == "🎭 Уникализатор текста":
        st.header("Уникализатор текста")
        source_text = st.text_area("Введите исходный текст:", height=150)
        if st.button("Уникализировать", type="primary"):
            if source_text:
                result = insert_invisible_chars(source_text)
                st.success("Готово! Скопируйте текст ниже:")
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
                    try:
                        filename = download_video(url)
                        with open(filename, 'rb') as f:
                            video_bytes = f.read()
                        st.success("Видео загружено!")
                        st.download_button("💾 Сохранить видео", data=video_bytes, file_name=f"video_{uuid.uuid4().hex[:6]}.mp4", mime="video/mp4")
                        os.remove(filename) # Удаляем файл с сервера, чтобы не тратить память
                    except Exception as e:
                        st.error("❌ Ошибка загрузки. Возможно, сервис заблокировал скачивание или ссылка неверна.")
