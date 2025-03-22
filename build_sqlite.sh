#!/bin/bash

# 必要なディレクトリの作成
mkdir -p sqlite
cd sqlite

# 必要なビルドツールのインストール
echo "Installing build tools..."
apt-get update
apt-get install -y build-essential gcc g++ make python3-dev

# SQLite のソースコードをダウンロード
echo "Downloading SQLite source..."
curl -L -o sqlite-autoconf-3490100.tar.gz https://www.sqlite.org/2024/sqlite-autoconf-3490100.tar.gz

# ダウンロードの確認
if [ ! -f sqlite-autoconf-3490100.tar.gz ]; then
    echo "Failed to download SQLite source"
    exit 1
fi

# 解凍
echo "Extracting SQLite source..."
tar xzf sqlite-autoconf-3490100.tar.gz

# ディレクトリの移動
cd sqlite-autoconf-3490100

# ビルドとインストール
echo "Building SQLite..."
./configure --prefix=/usr/local --enable-json1 --enable-fts5
make
make install

# 環境変数の設定
export PATH="/usr/local/bin:$PATH"
export LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"
export PKG_CONFIG_PATH="/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH"

# Python の SQLite モジュールを再ビルド
echo "Rebuilding Python SQLite module..."
pip install --force-reinstall pysqlite3-binary

# Python の SQLite モジュールを上書き
echo "Overriding Python SQLite module..."
PYTHON_PATH=$(python3 -c "import sys; print(sys.executable)")
PYTHON_DIR=$(dirname "$PYTHON_PATH")
cp /usr/local/lib/libsqlite3.so* "$PYTHON_DIR/lib/"
cp /usr/local/bin/sqlite3 "$PYTHON_DIR/bin/"

cd ../..

echo "SQLite installation completed!" 