FROM python:3.11-slim

# 必要なパッケージとGCCをインストール
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    make \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# SQLite のソースコードをダウンロードしてビルド
RUN mkdir -p /tmp/sqlite && \
    cd /tmp/sqlite && \
    curl -L -o sqlite-autoconf-3490100.tar.gz https://www.sqlite.org/2024/sqlite-autoconf-3490100.tar.gz && \
    tar xzf sqlite-autoconf-3490100.tar.gz && \
    cd sqlite-autoconf-3490100 && \
    ./configure --prefix=/usr/local --enable-json1 --enable-fts5 && \
    make && \
    make install

# 環境変数の設定
ENV PATH="/usr/local/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/lib:${LD_LIBRARY_PATH}"
ENV PKG_CONFIG_PATH="/usr/local/lib/pkgconfig:${PKG_CONFIG_PATH}"

# 作業ディレクトリを指定
WORKDIR /app

# 依存関係ファイルをコピー
COPY requirements.txt .

# 依存関係をインストール
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルのコピー
COPY . .

# Streamlit アプリケーションを実行
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"] 