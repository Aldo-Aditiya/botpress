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
st.set_page_config(layout="wide", )

from bp_katakita.utils.handler import conversation_analytics as conversation_analytics_handler

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
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
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
                    f"Substring or regex in {column}",
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

middle_card_1_style = """
    <style>
    div.css-ocqkz7.esravye3 {
        background-color: #FFFFFF;
        border: 1px solid #CCCCCC;
        padding: 2% 2% 2% 2%;
        border-radius: 5px;
        
        border-left: 0.5rem solid #9AD8E1 !important;
        box-shadow: 0 0.15rem 1.0rem 0 rgba(58, 59, 69, 0.15) !important; 
    }
    </style>
"""
st.markdown(middle_card_1_style, unsafe_allow_html=True)

# ----------------- #

st.markdown(f'<div style="text-align: right">Last Refreshed: {(datetime.now() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")}</style>', unsafe_allow_html=True)
st.markdown("### Conversation Analytics")   


df = conversation_analytics_handler.read_as_df(query={"bot_id": "testing_18-07-23"})
df.drop(columns=['_id', 'bot_id'], inplace=True)
df["datetime"] = pd.to_datetime(df["datetime"])
df = df.rename(columns={'session_id': 'conversation_id'})

posneutral_sentiment_pct = round((len(df[df["sentiment"] == "positive"]) + len(df[df["sentiment"] == "neutral"]))/ len(df) * 100, 2)
negative_sentiment_pct = round(len(df[df["sentiment"] == "negative"]) / len(df) * 100, 2)

insight_text = ""
insight_count = 0
for index, row in df.iterrows():
    if row["summary"] != "":
        insight_text += f"[{row['datetime']}] " + row["summary"] + "\n"
        insight_count += 1
    if insight_count == 5:
        break


c1, c2 = st.columns((8,2), gap="medium")
with c1:
    st.markdown('#### Recent Conversation Summary')
    st.code(insight_text, language="markdown", line_numbers=False)
with c2:
    st.markdown('#### Sentiment')
    st.metric("Neutral/Positive Sentiment", f"{posneutral_sentiment_pct}%")
    st.metric("Negative Sentiment", f"{negative_sentiment_pct}%")

st.dataframe(filter_dataframe(df), use_container_width=True, height=300)