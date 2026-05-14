# পাইথন বেস ইমেজ
FROM python:3.9-slim

# প্রয়োজনীয় সিস্টেম লাইব্রেরি এবং গুগল ক্রোম ইনস্টল করা
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    apt-transport-https \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# পাইথন ডিপেন্ডেন্সি ইনস্টল
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# সব ফাইল কপি করা
COPY . .

# পোর্ট এক্সপোজ (Render-এর জন্য)
EXPOSE 8080

# বট রান করা
CMD ["python", "bot.py"]
