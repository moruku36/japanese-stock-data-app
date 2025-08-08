import streamlit as st, os, sys, random, time, socket
st.write('# Minimal Streamlit Diagnostic')
st.write('RANDOM_TOKEN:', random.random())
st.write('PID:', os.getpid())
st.write('CWD:', os.getcwd())
st.write('FILE:', os.path.abspath(__file__))
st.write('PYTHON:', sys.version)
st.write('ENV PATH LEN:', len(os.environ.get('PATH','')))
# Simple latency loop to keep app alive
st.write('Hostname:', socket.gethostname())
if 'counter' not in st.session_state:
    st.session_state.counter = 0
if st.button('Increment'):
    st.session_state.counter += 1
st.write('Counter:', st.session_state.counter)
