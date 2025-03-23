# SQLiteの互換性問題を解決するために、最初にインポート
try:
    import sqlite_fix
except ImportError:
    print("SQLite fix module not found, continuing without it")

import streamlit as st
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
from src.vector_store import VectorStore
import io

def register_document(uploaded_file):
    """
    アップロードされたファイルをChromaDBに登録する関数。
    """
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

            # VectorStoreの初期化
            vector_store = VectorStore()

            # ドキュメントの追加（UPSERT）
            vector_store.upsert_documents(
                documents=[doc.page_content for doc in documents],
                ids=original_ids
            )

            st.success(f"{uploaded_file.name} をデータベースに登録しました。")
        except Exception as e:
            st.error(f"ドキュメントの登録中にエラーが発生しました: {e}")
            st.error("エラーの詳細:")
            st.exception(e)

def manage_chromadb():
    """
    ChromaDBを管理するページの関数。
    """
    st.header("ChromaDB 管理")

    # VectorStoreの初期化
    vector_store = VectorStore()

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
                dict_data = vector_store.get_documents()
                if dict_data['ids']:
                    tmp_df = pd.DataFrame({
                        "IDs": dict_data['ids'],
                        "Documents": dict_data['documents'],
                        "Metadatas": dict_data['metadatas']
                    })
                    st.dataframe(tmp_df)
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
                current_ids = vector_store.get_documents()['ids']
                if current_ids:
                    vector_store.delete_documents(ids=current_ids)
                    st.success("データベースの登録がすべて削除されました")
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
    if query_text:
        try:
            # VectorStoreの初期化
            vector_store = VectorStore()

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

def main():
    """
    アプリケーションのメイン関数。
    """
    # ページの設定
    st.set_page_config(page_title='🦜🔗 Ask the Doc App', layout="wide")
    st.title('🦜🔗 Ask the Doc App')

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
