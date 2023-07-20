from datetime import datetime, timedelta, timezone
import pandas as pd

import streamlit as st
import plost
from colorama import Fore, Back, Style

from bp_katakita.utils.handler import chat_history as chat_history_handler
from bp_katakita.config import load_config

# ----------------- #

# Assuming you have some sort of DataFrame
data = {'column1': [1, 2, 3, 4, 5],
        'column2': [10, 20, 30, 40, 50]}
df = pd.DataFrame(data)

# ----------------- #

# Styling
st.set_page_config(layout="wide")

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

card_style = """
    <style>
    div.css-12w0qpk {
        background-color: #FFFFFF;
        border: 1px solid #CCCCCC;
        padding: 2% 2% 2% 2%;
        border-radius: 5px;
        
        border-left: 0.5rem solid #9AD8E1 !important;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15) !important; 
    }
    label.css-mkogse.e16fv1kl2 {
        color: #36b9cc !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
    }
    </style>
"""
st.markdown(card_style, unsafe_allow_html=True)

chart_style = """
<style>
    div.chart-wrapper.fit-x.fit-y {
        background-color: #FFFFFF;
        border: 1px solid #CCCCCC;
        border-radius: 5px;
        
        border-left: 0.5rem solid #fa978c !important;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15) !important; 
    }
    canvas.marks {
        width: 100%;
        height: 100%;
        padding: 1%;
    }
    </style>
"""
st.markdown(chart_style, unsafe_allow_html=True)

# ----------------- #

# Sidebar
sidebar_bottom_html = f"""
    <style>
        [data-testid="stSidebarNav"] + div {{
            position:relative;
            background-position-x: center;
            background-position-y: bottom;
            height:50%;
            background-size: 85% auto;
            bottom:0;
        }}
    </style>
"""
st.sidebar.markdown(sidebar_bottom_html, unsafe_allow_html=True)

# ----------------- #

# Main Panel

## Metrics
df = chat_history_handler.read_as_df(query={"bot_id": "testing_18-07-23"})
num_msg_exchanged = len(df)
num_questions = len(df[df["author"] == "User"])
num_conversations = len(df["session_id"].unique())
num_unanswered_question = len(df[df["answered"] == "no"])
percent_answered_question = 100 - (num_unanswered_question / num_questions) * 100

col1, col2, col3, col4 = st.columns(4)
col1.metric("Messages Exchanged", f"{num_msg_exchanged}")
col2.metric("Questions", f"{num_questions}")
col3.metric("Conversations", f"{num_conversations}")
col4.metric("Answered Questions", f"{percent_answered_question:.2f}%")

## Graphs
df_convo_per_day = df.groupby(pd.Grouper(key='datetime', freq='D')).agg({'session_id': 'nunique'})
df_messages_per_day = df.groupby(pd.Grouper(key='datetime', freq='D')).count()['message']
topic_counts = df['topic'].value_counts().to_frame().reset_index().rename(columns={'index': 'topic'})
topic_counts = topic_counts[topic_counts['topic'] != '']

c1, c2 = st.columns((6,4), gap="medium")
with c1:
    st.markdown('#### Conversations')
    st.line_chart(df_convo_per_day, use_container_width=True)
with c2:
    st.markdown('#### Topics')
    plost.donut_chart(
        data=topic_counts,
        theta="count",
        color="topic",
        legend="bottom", 
        use_container_width=True)
st.markdown('#### Messages')
st.line_chart(df_messages_per_day)

    
