# SQLiteをpysqlite3で上書き
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    print("Successfully overrode sqlite3 with pysqlite3")
except ImportError:
    print("Failed to override sqlite3 with pysqlite3")

import streamlit as st

# 最初のStreamlitコマンドとしてページ設定を行う
st.set_page_config(page_title='🦜🔗 Ask the Doc App', layout="wide")

from langchain_openai import OpenAI
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
# --- LLM --- (componentsフォルダにllm.pyを配置する)---
from components.llm import llm
from components.llm import oai_embeddings
# --- LLM ---
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tempfile
import os
import pandas as pd
# ChromaDBとVectorStoreのインポートは後で行う (SQLite修正後)
import io

# グローバル変数の初期化
vector_store = None
vector_store_available = False

# VectorStoreのインスタンスを初期化する関数
def initialize_vector_store():
    global vector_store, vector_store_available
    if vector_store is not None:
        return vector_store
        
    try:
        from src.vector_store import VectorStore
        vector_store = VectorStore()
        vector_store_available = True
        print("VectorStore successfully initialized")
        return vector_store
    except Exception as e:
        vector_store_available = False
        print(f"Error initializing VectorStore: {e}")
        return None

# 初期化を試みる
initialize_vector_store()

def register_document(uploaded_file):
    """
    アップロードされたファイルをChromaDBに登録する関数。
    """
    if not vector_store_available:
        st.error("データベース接続でエラーが発生しました。ChromaDBが使用できません。")
        return
    
    if uploaded_file is not None:
        try:
            # ファイルの内容を文字列として読み込み
            content = uploaded_file.getvalue().decode('utf-8')
            
            # メモリ内でテキストを分割
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=512,
                chunk_overlap=10,
                add_start_index=True,
                separators=["\n\n", "\n", ".", " ", ""],
            )
            
            # ドキュメントを作成
            from langchain_core.documents import Document
            raw_document = Document(
                page_content=content,
                metadata={'source': uploaded_file.name}
            )
            
            # ドキュメントを分割
            documents = text_splitter.split_documents([raw_document])

            # IDsの作成
            original_ids = []
            for doc in documents:
                source_ = os.path.splitext(doc.metadata['source'])[0]  # 拡張子を除く
                start_ = doc.metadata['start_index']
                id_str = f"{source_}_{start_:08}" #0パディングして8桁に
                original_ids.append(id_str)

            # グローバルのVectorStoreインスタンスを使用
            global vector_store
            
            # ドキュメントの追加（UPSERT）
            vector_store.upsert_documents(documents=documents, ids=original_ids)

            st.success(f"{uploaded_file.name} をデータベースに登録しました。")
            st.info(f"{len(documents)}件のチャンクに分割されました")
        except Exception as e:
            st.error(f"ドキュメントの登録中にエラーが発生しました: {e}")
            st.error("エラーの詳細:")
            st.exception(e)

def manage_chromadb():
    """
    ChromaDBを管理するページの関数。
    """
    st.header("ChromaDB 管理")

    if not vector_store_available:
        st.error("ChromaDBの接続でエラーが発生しました。現在、ベクトルデータベースは使用できません。")
        st.warning("これはSQLiteのバージョンの非互換性によるものです。Streamlit Cloudでの実行には制限があります。")
        return

    # グローバルのvector_storeを使用
    global vector_store

    # 1.ドキュメント登録
    st.subheader("ドキュメントをデータベースに登録")
    uploaded_file = st.file_uploader('テキストをアップロードしてください', type='txt')
    if uploaded_file:
        if st.button("登録する"):
            with st.spinner('登録中...'):
                register_document(uploaded_file)

    st.markdown("---")

    # 2.登録状況確認
    st.subheader("ChromaDB 登録状況確認")
    if st.button("登録済みドキュメントを表示"):
        with st.spinner('取得中...'):
            try:
                # グローバルのVectorStoreインスタンスを使用
                dict_data = vector_store.get_documents(ids=None)
                
                if dict_data and len(dict_data.get('ids', [])) > 0:
                    tmp_df = pd.DataFrame({
                        "IDs": dict_data['ids'],
                        "Documents": dict_data['documents'],
                        "Metadatas": dict_data['metadatas']
                    })
                    st.dataframe(tmp_df)
                    st.success(f"合計 {len(dict_data['ids'])} 件のドキュメントが登録されています")
                else:
                    st.info("データベースに登録されたデータはありません。")
            except Exception as e:
                st.error(f"データの取得中にエラーが発生しました: {e}")
                st.error("エラーの詳細:")
                st.exception(e)

    st.markdown("---")

    # 3.全データ削除
    st.subheader("ChromaDB 登録データ全削除")
    if st.button("全データを削除する"):
        with st.spinner('削除中...'):
            try:
                # グローバルのVectorStoreインスタンスを使用
                current_ids = vector_store.get_documents(ids=None).get('ids', [])
                if current_ids:
                    vector_store.delete_documents(ids=current_ids)
                    st.success(f"データベースから {len(current_ids)} 件のドキュメントが削除されました")
                else:
                    st.info("削除するデータがありません。")
            except Exception as e:
                st.error(f"データの削除中にエラーが発生しました: {e}")
                st.error("エラーの詳細:")
                st.exception(e)

# RAGを使ったLLM回答生成
def generate_response(query_text):
    """
    質問に対する回答を生成する関数。
    """
    if not vector_store_available:
        return "申し訳ありません。現在、ベクトルデータベースに接続できないため、質問に回答できません。"
    
    if query_text:
        try:
            # グローバルのVectorStoreインスタンスを使用
            global vector_store

            # リトリーバーとQAチェーンの設定
            prompt = hub.pull("rlm/rag-prompt")

            def format_docs(docs):
                return "\n\n".join(doc.page_content for doc in docs)

            # 検索結果を取得
            search_results = vector_store.search(query_text)
            
            # 検索結果をドキュメント形式に変換
            from langchain_core.documents import Document
            docs = [
                Document(page_content=doc) 
                for doc in search_results['documents'][0]
            ]

            qa_chain = (
                {
                    "context": lambda x: format_docs(docs),
                    "question": RunnablePassthrough(),
                }
                | prompt
                | llm
                | StrOutputParser()
            )
            return qa_chain.invoke(query_text)
        except Exception as e:
            st.error(f"質問の処理中にエラーが発生しました: {e}")
            st.error("エラーの詳細:")
            st.exception(e)
            return None

def ask_question():
    """
    質問するページの関数。
    """
    st.header("ドキュメントに質問する")

    if not vector_store_available:
        st.error("ChromaDBの接続でエラーが発生しました。現在、ベクトルデータベースは使用できません。")
        st.warning("これはSQLiteのバージョンの非互換性によるものです。Streamlit Cloudでの実行には制限があります。")
        st.info("ローカル環境での実行をお試しください。")
        return

    # Query text
    query_text = st.text_input('質問を入力:', 
                               placeholder='簡単な概要を記入してください')

    # 質問送信ボタン
    if st.button('Submit') and query_text:
        with st.spinner('回答を生成中...'):
            response = generate_response(query_text)
            if response:
                st.success("回答:")
                st.info(response)
            else:
                st.error("回答の生成に失敗しました。")

def fallback_mode():
    """
    ChromaDBが使用できない場合のフォールバックモード
    """
    st.header("ChromaDBが使用できません")
    st.error("SQLiteのバージョンの問題により、ChromaDBを使用できません。")
    st.info("このアプリは、SQLite 3.35.0以上が必要です。Streamlit Cloudでは現在、SQLite 3.34.1が使用されています。")
    
    st.markdown("""
    ## 解決策
    
    1. **ローカル環境での実行**: 
       - このアプリをローカル環境でクローンして実行してください
       - 最新のSQLiteがインストールされていることを確認してください
    
    2. **代替のベクトルデータベース**:
       - ChromaDBの代わりに、他のベクトルデータベース（FAISS、Milvusなど）を使用することも検討できます
    
    3. **インメモリモードでの使用**:
       - 現在、DuckDB+Parquetバックエンドでの実行を試みていますが、これも失敗しています
       - 詳細については、ログを確認してください
    """)
    
    # 技術的な詳細
    with st.expander("技術的な詳細"):
        st.code("""
# エラーの原因
ChromaDBは内部でSQLite 3.35.0以上を必要としていますが、
Streamlit Cloudでは現在、SQLite 3.34.1が使用されています。

# 試みた解決策
1. pysqlite3-binaryのインストール
2. SQLiteのソースからのビルド
3. DuckDB+Parquetバックエンドの使用
4. モンキーパッチの適用

いずれも環境制限により成功していません。
        """)

def main():
    """
    アプリケーションのメイン関数。
    """
    # タイトルを表示
    st.title('🦜🔗 Ask the Doc App')

    if not vector_store_available:
        fallback_mode()
        return

    # サイドバーでページ選択
    st.sidebar.title("メニュー")
    page = st.sidebar.radio("ページを選択してください", ["ChromaDB 管理", "質問する",])

    # 各ページへ移動
    if page == "質問する":
        ask_question()
    elif page == "ChromaDB 管理":
        manage_chromadb()

if __name__ == "__main__":
    main()
