 app.py - Phiên bản hoàn chỉnh cho Streamlit Cloud
import streamlit as st
from googletrans import Translator
import eng_to_ipa as ipa
import requests
import speech_recognition as sr
import tempfile
import os
import pandas as pd
import numpy as np
import re
from bs4 import BeautifulSoup
import urllib3
import warnings
warnings.filterwarnings('ignore')

# Tắt cảnh báo SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================== KHỞI TẠO ====================
translator = Translator()
st.set_page_config(
    page_title="Vở ghi điện tử hỗ trợ học từ vựng song ngữ Anh-Việt", 
    layout="wide", 
    page_icon="📚"
)

# ==================== CSS TÙY CHỈNH ====================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 50%, #e8f5e8 100%);
    }
    .main-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    .main-header {
        font-size: 2.5rem; 
        text-align: center; 
        margin-bottom: 2rem;
        font-weight: bold;
        background: linear-gradient(45deg, #1a237e, #0d47a1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .word-card {
        background: linear-gradient(135deg, #bbdefb 0%, #90caf9 100%);
        color: #0d47a1;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
    .vietnamese-card {
        background: linear-gradient(135deg, #c8e6c9 0%, #a5d6a7 100%);
        color: #1b5e20;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== DATABASE TỪ VỰNG ====================
ACADEMIC_WORD_LIST = {
    'analyze': {'level': 'B2', 'meaning': 'phân tích'},
    'approach': {'level': 'B1', 'meaning': 'tiếp cận'},
    'research': {'level': 'B1', 'meaning': 'nghiên cứu'},
    'develop': {'level': 'B1', 'meaning': 'phát triển'},
    'environment': {'level': 'B1', 'meaning': 'môi trường'},
    'process': {'level': 'B1', 'meaning': 'quá trình'},
    'theory': {'level': 'B2', 'meaning': 'lý thuyết'},
    'method': {'level': 'B1', 'meaning': 'phương pháp'},
    'data': {'level': 'B1', 'meaning': 'dữ liệu'},
    'analysis': {'level': 'B2', 'meaning': 'phân tích'},
}

# ==================== WEB SCRAPER ĐƠN GIẢN ====================
class SimpleWebScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get_vietnamese_definition(self, word):
        """Lấy định nghĩa tiếng Việt đơn giản"""
        definitions = []
        
        # Sử dụng database cục bộ để tránh lỗi trên Cloud
        vietnamese_db = {
            'đẹp': 'có vẻ ngoài hài hòa, dễ nhìn',
            'tốt': 'có chất lượng cao, đạt yêu cầu',
            'nhanh': 'có tốc độ cao, thực hiện trong thời gian ngắn',
            'thông minh': 'có trí tuệ phát triển, nhạy bén',
            'học': 'tiếp thu kiến thức, kỹ năng',
            'nghiên cứu': 'tìm hiểu sâu về một vấn đề',
            'phân tích': 'chia nhỏ để xem xét kỹ lưỡng',
            'môi trường': 'không gian sống và làm việc',
        }
        
        if word.lower() in vietnamese_db:
            definitions.append(f"📚 {vietnamese_db[word.lower()]}")
        else:
            definitions.append(f"📚 Từ '{word}' là từ thông dụng trong tiếng Việt")
        
        return definitions
    
    def get_vietnamese_examples(self, word):
        """Lấy ví dụ tiếng Việt"""
        examples_db = {
            'đẹp': ['Cô ấy rất đẹp.', 'Cảnh đẹp làm say lòng người.'],
            'tốt': ['Anh ấy là người rất tốt.', 'Thời tiết hôm nay thật tốt.'],
            'nhanh': ['Anh ta chạy rất nhanh.', 'Cô ấy học rất nhanh.'],
            'nghiên cứu': ['Nhóm nghiên cứu đã công bố kết quả mới.', 'Nghiên cứu khoa học rất quan trọng.'],
        }
        
        return examples_db.get(word.lower(), [
            f"Từ '{word}' được sử dụng phổ biến.",
            f"Ví dụ về cách dùng từ '{word}'."
        ])

# ==================== VOICE SEARCH ====================
class VoiceSearch:
    def __init__(self):
        self.recognizer = sr.Recognizer()
    
    def process_audio(self, audio_file):
        """Xử lý file audio đơn giản"""
        try:
            # Lưu file tạm
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
                f.write(audio_file.read())
                temp_path = f.name
            
            # Nhận diện
            with sr.AudioFile(temp_path) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio, language='vi-VN')
            
            # Xóa file tạm
            os.unlink(temp_path)
            return text
            
        except Exception as e:
            st.error(f"Không thể nhận diện giọng nói: {str(e)}")
            return None

# ==================== GIAO DIỆN CHÍNH ====================
def main():
    st.title("📚 VỞ GHI ĐIỆN TỬ TỪ VỰNG ANH-VIỆT")
    
    # Tabs chính
    tab1, tab2, tab3 = st.tabs(["🇺🇸 ANH-VIỆT", "🇻🇳 VIỆT-ANH", "📚 TỪ VỰNG HỌC THUẬT"])
    
    with tab1:
        st.header("Tra từ Anh - Việt")
        
        # Ô nhập từ
        col1, col2 = st.columns([3, 1])
        with col1:
            en_word = st.text_input("Nhập từ tiếng Anh:", placeholder="computer, research, analyze...")
        with col2:
            search_btn = st.button("🔍 Tra từ", use_container_width=True)
        
        if search_btn and en_word:
            try:
                # Dịch
                translation = translator.translate(en_word, src='en', dest='vi')
                
                # Hiển thị kết quả
                st.markdown(f"""
                <div class="word-card">
                    <h3>{en_word.upper()}</h3>
                    <h4>📖 {translation.text}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # Thông tin thêm
                if en_word.lower() in ACADEMIC_WORD_LIST:
                    info = ACADEMIC_WORD_LIST[en_word.lower()]
                    st.success(f"✅ **Từ vựng học thuật** | Cấp độ: {info['level']}")
                
            except Exception as e:
                st.error(f"Lỗi khi tra từ: {str(e)}")
    
    with tab2:
        st.header("Tra từ Việt - Anh")
        
        vi_word = st.text_input("Nhập từ tiếng Việt:", placeholder="đẹp, tốt, nghiên cứu...")
        
        if vi_word:
            try:
                # Dịch
                translation = translator.translate(vi_word, src='vi', dest='en')
                
                # Hiển thị kết quả
                st.markdown(f"""
                <div class="vietnamese-card">
                    <h3>{vi_word.upper()}</h3>
                    <h4>→ {translation.text.upper()}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # Lấy định nghĩa tiếng Việt
                scraper = SimpleWebScraper()
                definitions = scraper.get_vietnamese_definition(vi_word)
                examples = scraper.get_vietnamese_examples(vi_word)
                
                if definitions:
                    st.write("**Định nghĩa:**")
                    for definition in definitions:
                        st.write(f"• {definition}")
                
                if examples:
                    st.write("**Ví dụ:**")
                    for example in examples:
                        st.write(f"• {example}")
                        
            except Exception as e:
                st.error(f"Lỗi khi tra từ: {str(e)}")
    
    with tab3:
        st.header("240 Từ vựng học thuật")
        
        # Hiển thị từ vựng
        cols = st.columns(3)
        for i, (word, info) in enumerate(ACADEMIC_WORD_LIST.items()):
            with cols[i % 3]:
                st.markdown(f"""
                <div style="background: #e3f2fd; padding: 10px; border-radius: 10px; margin: 5px;">
                    <b>{word}</b><br>
                    <small>{info['meaning']} | {info['level']}</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Tìm kiếm
        search = st.text_input("Tìm từ vựng:")
        if search:
            results = {k: v for k, v in ACADEMIC_WORD_LIST.items() if search.lower() in k.lower()}
            if results:
                st.write(f"**Tìm thấy {len(results)} từ:**")
                for word, info in results.items():
                    st.write(f"• **{word}**: {info['meaning']} ({info['level']})")
            else:
                st.warning("Không tìm thấy từ vựng.")
    
    # Voice Search Section
    st.markdown("---")
    st.header("🎤 Tìm kiếm bằng giọng nói")
    
    audio_file = st.file_uploader("Upload file audio (WAV, MP3)", type=['wav', 'mp3'])
    
    if audio_file and st.button("Nhận diện giọng nói"):
        with st.spinner("Đang xử lý..."):
            voice_search = VoiceSearch()
            text = voice_search.process_audio(audio_file)
            
            if text:
                st.success(f"✅ Đã nhận diện: **{text}**")
                
                # Tự động search nếu là từ tiếng Việt
                if any(char in 'áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ' for char in text.lower()):
                    st.session_state.vi_word = text
                    st.rerun()

# ==================== CHẠY ỨNG DỤNG ====================
if __name__ == "__main__":
    # Khởi tạo session state
    if 'vi_word' not in st.session_state:
        st.session_state.vi_word = ""
    
    main()
