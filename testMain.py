import streamlit as st
from openai import OpenAI
import time
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# OpenAI API 키 확인
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    st.error("OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
    st.stop()

# OpenAI 클라이언트 설정
try:
    client = OpenAI(api_key=api_key)
except Exception as e:
    st.error(f"OpenAI 클라이언트 초기화 오류: {str(e)}")
    st.stop()

# Assistant 생성 또는 가져오기
if "assistant_id" not in st.session_state:
    try:
        assistant = client.beta.assistants.create(
            name="QA Assistant",
            instructions="You are a helpful QA assistant.",
            model="gpt-4-1106-preview"
        )
        st.session_state.assistant_id = assistant.id
    except Exception as e:
        st.error(f"Assistant 생성 오류: {str(e)}")
        st.stop()

# 세션 상태 초기화
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

if "messages" not in st.session_state:
    st.session_state.messages = []

# 페이지 설정
st.title("QA Chatbot")

# 채팅 히스토리 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 사용자 입력
if prompt := st.chat_input("질문을 입력하세요"):
    try:
        # 사용자 메시지 표시
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # 어시스턴트에 메시지 전송
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt
        )

        # 실행 생성 및 응답 대기
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=st.session_state.assistant_id  # 변경된 부분
        )

        # 실행 완료 대기
        with st.spinner('응답을 기다리는 중...'):
            while run.status not in ["completed", "failed", "expired"]:
                run = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=run.id
                )
                time.sleep(1)
                
            if run.status != "completed":
                st.error(f"실행 오류: {run.status}")
                st.stop()

        # 응답 메시지 가져오기
        messages = client.beta.threads.messages.list(
            thread_id=st.session_state.thread_id
        )

        # 응답 표시
        assistant_message = messages.data[0].content[0].text.value
        st.session_state.messages.append({"role": "assistant", "content": assistant_message})
        with st.chat_message("assistant"):
            st.write(assistant_message)
            
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")
