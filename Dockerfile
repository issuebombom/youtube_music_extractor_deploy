# Python 이미지 사용
FROM python:3.9-slim

# 시스템 패키지 설치 및 yt-dlp 설치
RUN apt-get update && \
    apt-get install -y yt-dlp && \
    apt-get clean

# 작업 디렉토리 설정
WORKDIR /app

# 필요 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# Streamlit 실행
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

