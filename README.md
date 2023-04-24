# Langchain_pdf_chroma

### 현재 아직 FastAPI로 구현해놓지 않아 단독 실행해서 체크 할 수 있는 것은 main_prototype.py이다.
* CLI 환경에서 작동하게 작성

### 기능
* .pdf 파일을 읽어 유저 질문에 대한 것은 ChatGPT가 답변한다.
* embedding한 파일을 해시 인코딩 후 저장 - 다음 ChromaDB를 불러올 때 기존에 했던 Embedding 중복 작업 방지
* 질문 범위 지정 가능(페이지 별)

### 추가할 기능들
* .txt 파일 인식 후 답변 (단독 개발은 완료 상태) 
* .csv 파일(및 엑셀 파일) QA 답변 추가 (단독 개발은 완료 상태)
* FastAPI - React 구조로 변환

