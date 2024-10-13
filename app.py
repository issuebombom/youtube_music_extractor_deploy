import streamlit as st
import os
import yt_dlp
import subprocess

# Streamlit 앱 구성
st.title('YouTube Downloader & Video Converter')

# 탭 구성
tab1, tab2 = st.tabs(['YouTube Audio/Video Extractor', 'Video Converter'])

# 탭 1: YouTube 음원 추출기
with tab1:
    # URL 입력
    url = st.text_input('Enter YouTube URL')

    # 라디오 버튼으로 오디오 또는 비디오 선택
    option = st.radio('Select output format', ('Audio (mp3)', 'Video (mp4)'))

    # 다운로드 버튼 생성
    if st.button('Extract'):
        if url:
            # yt-dlp 옵션 설정
            if option == 'Audio (mp3)':
                # 오디오 다운로드 옵션
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': '%(title)s.%(ext)s',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }
            elif option == 'Video (mp4)':
                # 비디오 다운로드 옵션 (코덱 설정: 비디오 H.264, 오디오 AAC)
                ydl_opts = {
                    'format': 'bestvideo[height<=1080]+bestaudio[ext=m4a]/mp4',
                    'outtmpl': '%(title)s.%(ext)s',
                    'merge_output_format': 'mp4',  # mp4로 병합
                    'postprocessor_args': [
                        '-c:v', 'libx264',  # 비디오 코덱을 H.264로 설정
                        '-c:a', 'aac',      # 오디오 코덱을 AAC로 설정
                        '-b:a', '192k'      # 오디오 비트레이트 설정
                    ],
                }

            # yt-dlp 다운로드 작업 중 스피너 표시
            with st.spinner('Extracting... Please wait...'):
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

            # 다운로드한 파일 찾기
            file_name = max([f for f in os.listdir('.') if f.endswith(('.mp3', '.mp4'))], key=os.path.getctime)

            # 파일 다운로드 버튼을 통해 제공
            with open(file_name, 'rb') as f:
                st.download_button(
                    label="Click to Download",
                    data=f,
                    file_name=file_name,
                    mime="audio/mpeg" if option == 'Audio (mp3)' else "video/mp4"
                )

            st.success(f'{option} downloaded successfully!')
            st.balloons()  # 성공적으로 다운로드가 완료되면 풍선 효과
        else:
            st.warning('Please enter a valid YouTube URL.')

# 탭 2: 비디오 변환기
with tab2:
    st.subheader('Change Video Resolution and Bitrate')

    # 비디오 파일 업로드
    uploaded_file = st.file_uploader("Upload a video file (mp4)", type=['mp4'])

    # 해상도 및 비트레이트 입력
    resolution = st.text_input("Enter resolution (e.g., 1920x1080)", "1920x1080")
    bitrate = st.text_input("Enter bitrate (e.g., 4000k)", "4000k")

    # 변환 버튼 생성
    if st.button('Convert'):
        if uploaded_file is not None:
            # 임시 파일 저장
            temp_input = 'temp_video.mp4'
            with open(temp_input, 'wb') as f:
                f.write(uploaded_file.getbuffer())

            # 출력 파일 이름
            output_file = f'converted_{resolution}_{bitrate}.mp4'

            # FFmpeg 명령어 구성
            ffmpeg_command = [
                'ffmpeg',
                '-i', temp_input,
                '-s', resolution,
                '-b:v', bitrate,
                '-c:a', 'aac',
                output_file
            ]

            # 변환 작업 중 스피너 표시
            with st.spinner('Converting video... Please wait...'):
                subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # 변환된 파일 다운로드 버튼
            with open(output_file, 'rb') as f:
                st.download_button(
                    label="Download Converted Video",
                    data=f,
                    file_name=output_file,
                    mime="video/mp4"
                )

            st.success(f'Video converted to {resolution} at {bitrate}!')
            st.balloons()  # 성공적으로 변환 완료 시 풍선 효과
        else:
            st.warning('Please upload a video file.')
