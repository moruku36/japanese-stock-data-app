#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
診断用の最小 Streamlit アプリ。
目的: 実行環境/依存/ネットワークなどの簡易チェック。
本ファイルはテスト/診断用途であり、本番コードの一部ではありません。
"""

import streamlit as st
import os
import sys
import random
import time
import socket

st.write('# Minimal Streamlit Diagnostic')
st.write('RANDOM_TOKEN:', random.random())
st.write('PID:', os.getpid())
st.write('CWD:', os.getcwd())
st.write('FILE:', os.path.abspath(__file__))
st.write('PYTHON:', sys.version)
st.write('ENV PATH LEN:', len(os.environ.get('PATH','')))
st.write('Hostname:', socket.gethostname())

if 'counter' not in st.session_state:
    st.session_state.counter = 0

if st.button('Increment'):
    st.session_state.counter += 1

st.write('Counter:', st.session_state.counter)


