# Taken mostly from: https://blog.streamlit.io/auto-generate-a-dataframe-filtering-ui-in-streamlit-with-filter_dataframe/

from datetime import datetime, timedelta
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
import pandas as pd
import streamlit as st
st.set_page_config(page_title='Basis Pengetahuan', page_icon = "/home/researcher-1/botpress/packages/katakita_addons/src/bp_katakita/dashboard/assets/favicon.png", layout = 'wide', initial_sidebar_state = 'auto')

from bp_katakita.utils.handler import chat_history as chat_history_handler

# ----------------- #

def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """

    df = df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filter Tabel:", df.columns) #Filter dataframe on
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                user_cat_input = right.multiselect(
                    f"Nilai untuk {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Nilai untuk {column}",
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Nilai untuk {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Sub-String {column}",
                )
                if user_text_input:
                    df = df[df[column].astype(str).str.contains(user_text_input)]

    return df

# ----------------- #

# Styling

padding_top_html = """
    <style>
    .appview-container .main .block-container {
            padding-top: 2rem;    
            padding-bottom: 2rem; 
        }
    </style>
"""
st.markdown(padding_top_html, unsafe_allow_html=True)
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ----------------- #

st.markdown(f'<div style="text-align: right">Last Refreshed: {(datetime.now() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")}</style>', unsafe_allow_html=True)
st.markdown("### Basis Pengetahuan") #Knowledge Base

df = pd.read_csv("/home/researcher-1/botpress/packages/katakita_addons/data/bank_dki/bank_dki.csv")
df.drop(columns=['question_id'], inplace=True)
df.dropna(inplace=True)

column_rename = {
    'question_group': 'Kelompok Pertanyaan',
    'question': 'Pertanyaan',
    'answer': 'Jawaban'
}
df.rename(columns=column_rename, inplace=True)

st.dataframe(filter_dataframe(df), use_container_width=True, height=450)
uploaded_file = st.file_uploader("Perbarukan Basis Pengetahuan", type="csv")
if uploaded_file is not None:
    bytes_data = uploaded_file.read()
    with open("/home/researcher-1/botpress/packages/katakita_addons/data/bank_dki/bank_dki.csv", "wb") as f:
        f.write(bytes_data) 