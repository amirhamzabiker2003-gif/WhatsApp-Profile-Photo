FROM python:3.9

# ক্রোম এবং ড্রাইভার ইনস্টল করা
RUN apt-get update && apt-get install -y \
    wget gnupg unzip \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# পাইথন লাইব্রেরি ইনস্টল
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

# বট রান করা
CMD ["python", "bot.py"]
