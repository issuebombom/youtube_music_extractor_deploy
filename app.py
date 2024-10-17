import streamlit as st
import os
import yt_dlp
import subprocess
from pydub import AudioSegment
from io import BytesIO

# Streamlit 앱 구성
st.title('YouTube Downloader & Editor')

# 탭 구성
tab1, tab2, tab3 = st.tabs(['YouTube Audio/Video Extractor', 'Audio Edit & Merge', 'Video Converter'])

# !탭 1: YouTube 음원 추출기
with tab1:
    st.subheader('Extract and Download Audio/Video from YouTube')

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

# !탭 2: 오디오 편집 후 합치기
with tab2:
    st.subheader('Adjust Audio Length and Merge Files')

    # MP3 파일 업로드 기능
    uploaded_files = st.file_uploader("Upload MP3 files", type="mp3", accept_multiple_files=True)

    # 편집된 오디오를 저장할 리스트
    edited_segments = []

    def format_duration(ms):
        """밀리초를 분:초 형식으로 변환하는 함수"""
        total_seconds = ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02}"

    def ms_to_time_list(ms):
        """밀리초를 분:초 리스트로 변환"""
        total_seconds = ms // 1000
        time_list = []
        for sec in range(total_seconds + 1):  # +1 to include the last second
            minutes = sec // 60
            seconds = sec % 60
            time_list.append(f"{minutes}:{seconds:02}")
        return time_list

    def time_to_ms(time_str):
        """분:초 형식의 문자열을 밀리초로 변환"""
        minutes, seconds = map(int, time_str.split(":"))
        return (minutes * 60 + seconds) * 1000

    if uploaded_files:
        for uploaded_file in uploaded_files:
            audio = AudioSegment.from_file(uploaded_file)  # 파일을 AudioSegment로 변환
            
            st.subheader(f"Editing {uploaded_file.name}")
            
            # 음원의 길이를 밀리초로 계산
            duration_ms = len(audio)

            # 분:초 형식 리스트 생성
            time_options = ms_to_time_list(duration_ms)

            # select_slider: 분:초 단위로 구간 설정
            start_end_time = st.select_slider(
                f"Select start and end time (total duration: {format_duration(duration_ms)})",
                options=time_options,
                value=(time_options[0], time_options[-1])
            )

            # 선택한 시간을 밀리초로 변환
            start_time_ms = time_to_ms(start_end_time[0])
            end_time_ms = time_to_ms(start_end_time[1])

            # 오디오 편집 후 메모리 상에서 처리 (BytesIO 사용)
            if start_time_ms < end_time_ms:
                edited_audio = audio[start_time_ms:end_time_ms]

                # 메모리 상에서 편집된 오디오 저장
                buffer = BytesIO()
                edited_audio.export(buffer, format="mp3")
                buffer.seek(0)  # 스트림 시작점으로 이동

                # 미리듣기 플레이어 추가
                st.audio(buffer, format="audio/mp3")

                # 편집된 오디오 리스트에 추가
                edited_segments.append((uploaded_file.name, edited_audio))

            else:
                st.warning("Start time must be less than end time.")

    # 음원 합치기
    if edited_segments:
        st.subheader("Set the order of audio files")
        order = st.multiselect("Select the order of files", [name for name, _ in edited_segments])

        if len(order) == len(edited_segments):  # 순서가 모두 지정된 경우
            final_audio = AudioSegment.empty()
            crossfade_duration = 250  # 크로스페이드 지속 시간 250ms (0.25초)

            for i, selected_file in enumerate(order):
                for file_name, audio_segment in edited_segments:
                    if file_name == selected_file:
                        if i == 0:
                            final_audio = audio_segment  # 첫 번째 음원은 크로스페이드 없이 추가
                        else:
                            final_audio = final_audio.append(audio_segment, crossfade=crossfade_duration)

            # 합쳐진 음원을 MP3로 저장
            output_file = "merged_audio_with_crossfade.mp3"
            final_audio.export(output_file, format="mp3")

            st.subheader("Download final merged audio with crossfade")
            with open(output_file, "rb") as f:
                st.download_button(label="Download MP3", data=f, file_name=output_file, mime="audio/mp3")

# !탭 3: 비디오 변환기
with tab3:
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
