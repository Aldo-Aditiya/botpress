from datetime import datetime, timedelta
import pandas as pd

import streamlit as st
st.set_page_config(page_title='Dashboard', page_icon = "/home/researcher-1/botpress/packages/katakita_addons/src/bp_katakita/dashboard/assets/favicon.png", layout = 'wide', initial_sidebar_state = 'auto')
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
        
        border-left: 0.5rem solid #3981db !important;
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
        
        border-left: 0.5rem solid #3981db !important;
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
        
        border-left: 0.5rem solid #3981db !important;
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

# Sidebar Panel
sidebar_style = """
    <style>
    .css-6qob1r.e1akgbir3 {
        background-image: linear-gradient(to right, #0c59ba, #05336f);
        color: white;
    }
    .css-pkbazv.e1akgbir5 {
        color: white;
    }
    .css-17lntkn.e1akgbir5 {
        color: white;
    }
    </style>
"""
st.markdown(sidebar_style, unsafe_allow_html=True)

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
st.markdown('<div style="text-align: right"><a href="http://108.143.51.70:55555/">Menuju Chatbot →</style>', unsafe_allow_html=True)
st.markdown('#### Informasi Umum') #Overview
c1, c2, c3, c4 = st.columns(4)
c1.metric("Pesan", f"{num_msg_exchanged}") #Messages Exchanged
c2.metric("Pesan Pengguna", f"{num_questions}") #User Messages
c3.metric("Percakapan", f"{num_conversations}") #Conversations
c4.metric("Jawaban Terjawab", f"{percent_answered_question:.2f}%") #Answered Questions

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
    st.markdown('##### Performa Chatbot')
    c11, c12 = st.columns(2)
    c11.metric("Rata-rata Waktu Respon Pertama", f"{avg_first_response_time} s") #Avg. First Response Time
    c12.metric("Rata-rata Waktu Respon", f"{avg_response_time} s") #Avg. Response Time
    c11.metric("Rata-rata Durasi Percakapan", f"{avg_conversation_duration} s") #Avg. Conversation Duration
    c12.metric("Rata-rata Waktu Tunggu", f"{avg_wait_time} s") #Avg. Wait Time
    c11.metric("Rasio Defleksi Bot", "--%") #Bot Deflection Rate
    c12.metric("Rasio Eskalasi Bot", "--%") #Bot Escalation Rate
with c2:
    st.markdown('##### Kepuasan Pengguna') #Customer Satisfaction
    c21, c22 = st.columns(2)
    c21.metric("Rata-rata Nilai Kepuasan", "-/5") #Avg. CSAT
    c21.metric("Sentimen Positif/Netral", f"{posneutral_sentiment_pct}%") #Neutral/Positive Sentiment
    c21.metric("Sentimen Negatif", f"{negative_sentiment_pct}%") #Negative Sentiment

## Graphs
df_convo_per_day = df.groupby(pd.Grouper(key='datetime', freq='D')).agg({'session_id': 'nunique'})
df_messages_per_day = df.groupby(pd.Grouper(key='datetime', freq='D')).count()['message']

c1, c2 = st.columns((5,5), gap="medium")
with c1:
    st.markdown('#### Percakapan') #Conversations
    st.line_chart(df_convo_per_day, use_container_width=True)
with c2:
    st.markdown('#### Pesan') #Messages
    st.line_chart(df_messages_per_day, use_container_width=True)

## Bar Charts
topic_counts = df['topic'].value_counts().to_frame().reset_index().rename(columns={'index': 'topic'})
topic_counts = topic_counts[topic_counts['topic'] != '']

answered_counts = df['answered'].value_counts().to_frame().reset_index().rename(columns={'index': 'answered'})

c1, c2 = st.columns((5,5), gap="medium")
with c1:
    st.markdown('#### Topik') #Topics
    plost.bar_chart(
        data=topic_counts,
        bar='topic',
        value='count',
        use_container_width=True
    )
with c2:
    st.markdown('#### Terjawab') #Answered
    plost.bar_chart(
        data=answered_counts,
        bar='answered',
        value='count',
        use_container_width=True
    )
    
