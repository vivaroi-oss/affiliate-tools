import streamlit as st
import io
import uuid
import random
import requests
import pyotp
import yt_dlp
import os
from PIL import Image, ImageEnhance

# Настройка страницы (широкий формат, заголовок)
st.set_page_config(page_title="Affiliate Hub", page_icon="🎯", layout="wide")

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
    response = requests.get("https://thispersondoesnotexist.com", headers={'User-Agent': 'Mozilla/5.0'})
    return response.content

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
menu = st.sidebar.radio(
    "Выберите инструмент:",
    ["🎭 Уникализатор текста", "🖼 Уникализатор крео", "🔐 2FA Генератор", "🤳 Селфи-генератор", "📥 Скачать видео"]
)

if menu == "🎭 Уникализатор текста":
    st.header("Уникализатор текста (Обход модерации)")
    st.write("Вставляет невидимые символы (Zero-width space) между буквами.")
    
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
    st.write("Меняет контраст, удаляет EXIF-данные (метаданные) и меняет хэш файла.")
    
    uploaded_file = st.file_uploader("Загрузите картинку (JPG/PNG)", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Исходник", width=300)
        if st.button("Уникализировать фото", type="primary"):
            with st.spinner("Обработка..."):
                new_image_bytes = uniqueize_image(uploaded_file.getvalue())
                new_filename = f"creative_{uuid.uuid4().hex[:8]}.jpg"
                
                st.success("Креатив успешно уникализирован!")
                st.download_button(
                    label="💾 Скачать уникальное фото",
                    data=new_image_bytes,
                    file_name=new_filename,
                    mime="image/jpeg"
                )

elif menu == "🔐 2FA Генератор":
    st.header("Генератор 2FA (TOTP)")
    
    secret = st.text_input("Введите секретный ключ (Secret Key):", placeholder="Например: JBSWY3DPEHPK3PXP")
    if st.button("Получить код", type="primary"):
        if secret:
            clean_secret = secret.replace(' ', '').upper()
            try:
                totp = pyotp.TOTP(clean_secret)
                st.info("Ваш код для входа:")
                st.title(totp.now())
            except Exception:
                st.error("❌ Неверный формат секрета.")
        else:
            st.warning("Введите ключ.")

elif menu == "🤳 Селфи-генератор":
    st.header("Генератор уникальных селфи для ЗРД")
    st.write("Каждое нажатие генерирует лицо несуществующего человека.")
    
    if st.button("Сгенерировать селфи", type="primary"):
        with st.spinner("Нейросеть рисует лицо..."):
            photo_bytes = get_random_selfie()
            st.image(photo_bytes, caption="Уникальное селфи", width=400)
            st.download_button(
                label="💾 Скачать селфи",
                data=photo_bytes,
                file_name=f"selfie_{uuid.uuid4().hex[:6]}.jpg",
                mime="image/jpeg"
            )

elif menu == "📥 Скачать видео":
    st.header("Загрузка видео без водяных знаков")
    st.write("Поддерживает TikTok, Instagram Reels, YouTube Shorts.")
    
    url = st.text_input("Вставьте ссылку на видео:")
    if st.button("Скачать", type="primary"):
        if url:
            with st.spinner("Скачиваем видео, пожалуйста подождите..."):
                try:
                    filename = download_video(url)
                    with open(filename, 'rb') as f:
                        video_bytes = f.read()
                    
                    st.success("Видео загружено!")
                    st.download_button(
                        label="💾 Сохранить видео",
                        data=video_bytes,
                        file_name=f"video_{uuid.uuid4().hex[:6]}.mp4",
                        mime="video/mp4"
                    )
                    os.remove(filename) # Удаляем с сервера, чтобы не забивать память
                except Exception as e:
                    st.error("❌ Ошибка загрузки. Возможно, сервис заблокировал скачивание или ссылка неверна.")
        else:
            st.warning("Вставьте ссылку.")