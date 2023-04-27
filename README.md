# Langchain_pdf_chroma

### FastAPI 형태 main.py 개발 완료.

* CLI 환경에서 작동하는 skeleton code : main_prototype.py

### 기능
* .pdf 파일을 읽어 유저 질문에 대한 것은 ChatGPT가 답변한다.
    * .pdf 파일 한정 메모리 기능 탑재했다.(이전에 임베딩한 것 불러오기.) - txt는 지원안함.
* .txt 파일을 읽어 유저 질문에 답한다.
* embedding한 파일을 해시 인코딩 후 저장 - 다음 ChromaDB를 불러올 때 기존에 했던 Embedding 중복 작업 방지
* 질문 범위 지정 가능(페이지 별)

### 추가할 기능들
* .csv 파일(및 엑셀 파일) QA 답변 추가 (단독 개발은 완료 상태)
* FastAPI - React 구조로 변환

