import streamlit as st
from google import genai
import pandas as pd

# --- 1. 初期設定 ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("APIキーが設定されていません。Streamlit CloudのSettingsから設定してください。")
    st.stop()

client = genai.Client(api_key=API_KEY)

# --- 2. システム指示 (System Instructions) ---
SYSTEM_PROMPT = """
【指示】
中国語会話練習支援ツールとして動作してください。

【ルール】
入力されたテーマに関連する中国語単語を20個、以下の5列のみで構成されるMarkdown表で出力してください。
| 中国語 | 拼音 | 品詞 | 日本語訳 | 例文 |

その後、最後に「### 会話のヒント」という見出しを付け、そのテーマに沿った練習用の質問（中国語と日本語訳）を3つ箇条書きで出力してください。

【禁止事項】
「備考」欄の追加、表以外のテキスト（挨拶や説明）の出力、列の追加・削除。
質問は学習者が回答しやすい具体的な内容にすること。

単語内訳: 名詞8個以上、動詞・形容詞8個以上を含むこと。

難易度: HSK3-4級レベルを5個、テーマに関連する具体的な語を15個。

例文: 用法がわかる単純な構文にすること。

入力を受け取ったら、即座に表のみを出力し、次の入力を待機してください。
"""

# --- 3. UI構築 ---
st.set_page_config(page_title="中国語単語ジェネレータ", page_icon="🇨🇳")
st.title("🇨🇳 中国語単語ジェネレータ")
st.write("テーマを入力すると、会話に役立つ単語20個を表にします。")

#履歴を保持するためのセッション状態
if "history" not in st.session_state:
    st.session_state.history = []

# 入力フォーム
with st.form("input_form"):
    theme = st.text_input("会話テーマ", placeholder="夏の思い出、好きなたぬき、食パンの美味しい食べ方...")
    submit_button = st.form_submit_button("単語表を生成")

# 生成処理
if submit_button and theme:
    with st.spinner('生成中...'):
        response_text = None

        try:
            res = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"{SYSTEM_PROMPT}\n\nテーマ: {theme}"
            )
            response_text = res.text

        except Exception as e:
            if "429" in str(e):
                try:
                    res = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=f"{SYSTEM_PROMPT}\n\nテーマ: {theme}"
                    )
                    response_text = res.text
                except Exception as e2:
                    st.error("全ての無料枠を使い切りました。少し時間を置いてください。")
                    st.stop()
            else:
                st.error(f"エラー: {e}")
                st.stop()
        if response_text:
            st.session_state.history.insert(0, {"theme": theme, "content": response_text})

#結果の表示
if st.session_state.history:
    for i, item in enumerate(st.session_state.history):
        with st.expander(f"結果: {item['theme']}", expanded=(i==0)):
            st.markdown(item['content'])

        # CSV出力用の変換
        table_only = item['content'].split("###")[0]
        csv_data = table_only.replace('|', ',').strip()

        st.download_button(
            label=f"「{item['theme']}」をCSVで保存",
            data=csv_data,
            file_name=f"{item['theme']}.csv",
            mime="text/csv",
            key=f"dl_{i}"
        )

else:
    st.warning("テーマを入力してください。")