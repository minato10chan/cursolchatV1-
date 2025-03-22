#!/bin/bash

# 必要なディレクトリの作成
mkdir -p sqlite
cd sqlite

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
./configure --prefix=/usr/local
make
make install

# 環境変数の設定
export PATH="/usr/local/bin:$PATH"
export LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"
export PKG_CONFIG_PATH="/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH"

cd ../..

echo "SQLite installation completed!" 