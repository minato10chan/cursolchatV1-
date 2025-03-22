@echo off

:: SQLite のソースコードをダウンロード
cd sqlite
curl -O https://www.sqlite.org/2024/sqlite-autoconf-3490100.tar.gz
tar xzf sqlite-autoconf-3490100.tar.gz
cd sqlite-autoconf-3490100

:: ビルドとインストール
:: 注意: Windows では Visual Studio と CMake が必要です
cmake -B build
cmake --build build --config Release

:: Python の SQLite モジュールを再ビルド
pip install --force-reinstall pysqlite3-binary

cd ../.. 