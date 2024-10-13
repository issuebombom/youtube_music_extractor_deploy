import streamlit as st
import subprocess
import os

def download_audio_from_youtube(url):
    try:
        # yt-dlp 명령어를 사용하여 YouTube에서 오디오 추출
        command = [
            'yt-dlp',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--output', '%(title)s.%(ext)s',  # 파일 이름 포맷 설정
            url
        ]
        subprocess.run(command, check=True)

        # 생성된 파일 이름 가져오기
        audio_files = [f for f in os.listdir('.') if f.endswith('.mp3')]
        
        return audio_files  # MP3 파일 목록 반환

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return []

# 음원 파일 목록을 세션 상태로 관리
if "audio_files" not in st.session_state:
    st.session_state.audio_files = []

st.title("YouTube Audio Downloader")

# 입력된 YouTube URL 저장
youtube_url = st.text_input("Enter YouTube URL:")

# 음원 다운로드 버튼
if st.button("Extract Audio"):
    if youtube_url:
        st.session_state.audio_files = download_audio_from_youtube(youtube_url)
        if st.session_state.audio_files:  # 파일이 정상적으로 생성되었는지 확인
            st.success("Audio downloaded successfully!")
        else:
            st.error("No audio file found.")
    else:
        st.error("Please enter a valid YouTube URL.")

# 곡 제목 표시 및 다운로드 버튼 생성
if st.session_state.audio_files:
    for audio_file in st.session_state.audio_files:
        st.markdown(f"**{audio_file}**")  # 곡 제목을 기본 라벨 형태로 표시

        # 다운로드 버튼 생성
        with open(audio_file, "rb") as f:
            st.download_button(
                label=f"Download Audio",
                data=f,
                file_name=audio_file,
                mime="audio/mpeg"
            )

# 페이지가 리랜더링될 때 음원 파일 삭제
def cleanup_audio_files():
    for audio_file in st.session_state.audio_files:
        if os.path.exists(audio_file):
            os.remove(audio_file)
    st.session_state.audio_files = []  # 목록 초기화

# 페이지가 리랜더링되면 음원 파일 삭제
if st.session_state.audio_files:
    cleanup_audio_files()