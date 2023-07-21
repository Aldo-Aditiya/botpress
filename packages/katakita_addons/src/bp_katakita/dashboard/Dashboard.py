from datetime import datetime, timedelta
import pandas as pd

import streamlit as st
from streamlit_star_rating import st_star_rating
import plost
from colorama import Fore, Back, Style

from bp_katakita.utils.handler import chat_history as chat_history_handler
from bp_katakita.utils.handler import conversation_analytics as conversation_analytics_handler
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

## Cards

top_card_style = """
    <style>
    div.css-12w0qpk {
        background-color: #FFFFFF;
        border: 1px solid #CCCCCC;
        padding: 2% 2% 2% 2%;
        border-radius: 5px;
        
        border-left: 0.5rem solid #9AD8E1 !important;
        box-shadow: 0 0.15rem 1.0rem 0 rgba(58, 59, 69, 0.15) !important; 
    }
    label.css-mkogse.e16fv1kl2 {
        color: #36b9cc !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
    }
    </style>
"""
st.markdown(top_card_style, unsafe_allow_html=True)

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

chart_style = """
<style>
    div.chart-wrapper.fit-x.fit-y {
        background-color: #FFFFFF;
        border: 1px solid #CCCCCC;
        border-radius: 5px;
        
        border-left: 0.5rem solid #fa978c !important;
        box-shadow: 0 0.15rem 1.0rem 0 rgba(58, 59, 69, 0.15) !important; 
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

# Main Panel

df = chat_history_handler.read_as_df(query={"bot_id": "testing_18-07-23"})
num_msg_exchanged = len(df)
num_questions = len(df[df["author"] == "User"])
num_conversations = len(df["session_id"].unique())
num_unanswered_question = len(df[df["answered"] == "no"])
percent_answered_question = 100 - (num_unanswered_question / num_questions) * 100

## Overview Metrics
st.markdown(f'<div style="text-align: right">Last Refreshed: {(datetime.now() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")}</style>', unsafe_allow_html=True)
st.markdown('')
st.markdown('<div style="text-align: right"><a href="http://108.143.51.70:55555/">Go to Chatbot →</style>', unsafe_allow_html=True)
st.markdown('#### Overview')
c1, c2, c3, c4 = st.columns(4)
c1.metric("Messages Exchanged", f"{num_msg_exchanged}")
c2.metric("Questions", f"{num_questions}")
c3.metric("Conversations", f"{num_conversations}")
c4.metric("Answered Questions", f"{percent_answered_question:.2f}%")

## Performance Metrics
st.markdown('#### Performance')
df_convo = conversation_analytics_handler.read_as_df(query={"bot_id": "testing_18-07-23"})
df_convo.drop(columns=['_id', 'bot_id'], inplace=True)
df_convo["datetime"] = pd.to_datetime(df_convo["datetime"])
df_convo = df_convo.rename(columns={'session_id': 'conversation_id'})

avg_first_response_time = round(df_convo["first_response_time"].mean(), 2)
avg_response_time = round(df_convo["avg_response_time"].mean(), 2)
avg_conversation_duration = round(df_convo["duration"].mean(), 2)
avg_wait_time = round(df_convo["wait_time"].mean(), 2)
posneutral_sentiment_pct = round((len(df_convo[df_convo["sentiment"] == "positive"]) + len(df_convo[df_convo["sentiment"] == "neutral"]))/ len(df_convo) * 100, 2)
negative_sentiment_pct = round(len(df_convo[df_convo["sentiment"] == "negative"]) / len(df_convo) * 100, 2)

c1, c2 = st.columns(2)
with c1:
    st.markdown('##### Chat Performance')
    c11, c12 = st.columns(2)
    c11.metric("Avg. First Response Time", f"{avg_first_response_time} s")
    c12.metric("Avg. Response Time", f"{avg_response_time} s")
    c11.metric("Avg. Conversation Duration", f"{avg_conversation_duration} s")
    c12.metric("Avg. Wait Time", f"{avg_wait_time} s")
    c11.metric("Bot Deflection Rate", "--%")
    c12.metric("Bot Escalation Rate", "--%")
with c2:
    st.markdown('##### Customer Satisfaction')
    c21, c22 = st.columns(2)
    c21.metric("Avg. CSAT", "-/5")
    c21.metric("Neutral/Positive Sentiment", f"{posneutral_sentiment_pct}%")
    c21.metric("Negative Sentiment", f"{negative_sentiment_pct}%")

## Graphs
df_convo_per_day = df.groupby(pd.Grouper(key='datetime', freq='D')).agg({'session_id': 'nunique'})
df_messages_per_day = df.groupby(pd.Grouper(key='datetime', freq='D')).count()['message']

c1, c2 = st.columns((5,5), gap="medium")
with c1:
    st.markdown('#### Conversations')
    st.line_chart(df_convo_per_day, use_container_width=True)
with c2:
    st.markdown('#### Messages')
    st.line_chart(df_messages_per_day, use_container_width=True)

## Bar Charts
topic_counts = df['topic'].value_counts().to_frame().reset_index().rename(columns={'index': 'topic'})
topic_counts = topic_counts[topic_counts['topic'] != '']

answered_counts = df['answered'].value_counts().to_frame().reset_index().rename(columns={'index': 'answered'})

c1, c2 = st.columns((5,5), gap="medium")
with c1:
    st.markdown('#### Topics')
    plost.bar_chart(
        data=topic_counts,
        bar='topic',
        value='count',
        use_container_width=True
    )
with c2:
    st.markdown('#### Answered')
    plost.bar_chart(
        data=answered_counts,
        bar='answered',
        value='count',
        use_container_width=True
    )
    
