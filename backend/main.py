import os
import hashlib
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from langchain.document_loaders import TextLoader, PyPDFLoader
from langchain.chat_models import ChatOpenAI
from langchain.docstore.document import Document
from langchain.chains.summarize import load_summarize_chain
from modify import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.text_splitter import CharacterTextSplitter
from PyPDF2 import PdfReader
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# Add CORS support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()  # load variables from .env file
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


class Chat_With_PDFs_and_Summarize:

    def __init__(self, model_name="gpt-3.5-turbo", temperature=0):

        # Initialize ChatOpenAI for summary and chat
        self.llm_summarize = ChatOpenAI(model_name=model_name, temperature=temperature)
        self.llm_chat = ChatOpenAI(model_name=model_name, temperature=temperature)

        # Initialize varaibles to store document, pages and index information
        self.loader = None
        self.pages = None
        self.docs = None
        self.db_index = None
        self.embeddings = OpenAIEmbeddings()
        self.persist_directory = "db_index"
        self.doc_hash = None

    # Load a PDF document and split it into pages
    def load_document(self, file_path, page_range=None):
        # Load the document using PyPDFLoader
        self.loader = PyPDFLoader(file_path)
        # Split the document into pages
        self.pages = self.loader.load_and_split()

        if page_range is None:
            new_docs = [Document(page_content=t.page_content) for t in self.pages]
        else:
            new_docs = [Document(page_content=t.page_content) for t in self.pages[page_range[0]:page_range[1]]]
        
        # Calculate a hash for the Loaded documents
        new_hash = hashlib.md5(''.join([doc.page_content for doc in new_docs]).encode
                               ()).hexdigest()
        
        # Check whether the db index already exists
        if not os.path.exists(self.persist_directory):
            os.makedirs(self.persist_directory)
        
        if os.path.exists(os.path.join(self.persist_directory, 'doc_hash.txt')):
            with open(os.path.join(self.persist_directory, 'doc_hash.txt'), 'r') as f:
                stored_hash = f.read().strip()
            
            if new_hash == stored_hash:
                # Loading an existing index from disk
                print("Loading the index from the disk...")
                self.db_index = Chroma(persist_directory=self.persist_directory,
                                       embedding_function=self.embeddings)
            else:
                self.docs = new_docs
                self.doc_hash = new_hash
                # Create a new index
                print("Creating a new index...")
                self.db_index = Chroma.from_documents(self.docs, self.embeddings,
                                                      persist_directory=self.persist_directory)
                
                # Save the new Hash in the index directory
                with open(os.path.join(self.persist_directory, 'doc_hash.txt'), 'w') as f:
                    f.write(self.doc_hash)
        else:
            self.docs = new_docs
            self.doc_hash = new_hash
            # Create a new Index
            print("Creating a new index...")
            self.db_index = Chroma.from_documents(self.docs, self.embeddings,
                                                  persist_directory=self.persist_directory)
            # Save the new Hash in the index directory
            with open(os.path.join(self.persist_directory, 'doc_hash.txt'), 'w') as f:
                f.write(self.doc_hash)

    # Generate a summary of the loaded document
    def summarize(self, chain_type="map_reduce"):
        if not self.docs:
            raise ValueError("No document loaded. Please load a document first using 'load_document' method.")
        
        # Load the summarization chain an run it on the loaded documents
        chain = load_summarize_chain(self.llm_summarize, chain_type=chain_type)
        return chain.run(self.docs)
        
    # Print test pages for reference
    def print_test_pages(self, page_indices):
        if not self.pages:
            raise ValueError("No document loaded. Please load a document first using 'load_document' method.")
        
        for index in page_indices:
            print(f"Page {index}:")
            print(self.pages[index])
            print("\n")
        
    # Ask a question and get an answer from the model
    def ask_question(self, query):
        if not self.db_index:
            raise ValueError("No document index. Please load a document first using 'load_document' method")
        
        # Initialize the RetrievalQA object and run the query
        qa = RetrievalQA.from_chain_type(
            llm=self.llm_chat,
            chain_type="stuff",
            retriever=self.db_index.as_retriever()
        )

        # Get the response from the model based on the query
        response = qa.run(query)
        return response
    

    # txt function 위해서 새로 만든 것.
    def load_txt(self, file_path):
        # Load the document using TextLoader
        self.loader = TextLoader(file_path)
        documents = self.loader.load()
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        self.db_index = Chroma.from_documents(texts, embeddings)


chat = Chat_With_PDFs_and_Summarize()


@app.post("/load_document/")
async def load_document(
    file: UploadFile = File(...), 
    start_page: Optional[int] = None, 
    end_page: Optional[int] = None
):
    # Save the uploaded file to the "documents" directory
    file_path = os.path.join("documents", file.filename)
    with open(file_path, 'wb') as buffer:
        buffer.write(file.file.read())

    # Set the end_page to the length of the PDF file if it is None
    if end_page is None:
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PdfReader(pdf_file)
            end_page = len(pdf_reader.pages)

    chat.load_document(file_path, page_range=(start_page, end_page))
    
    # Remove the uploaded file from the "documents" directory
    # os.remove(file_path)

    return {"message": "Document loaded successfully."}


@app.post("/ask_question")
async def ask_question(query: str):
    try:
        answer = chat.ask_question(query)
        return {"answer": answer}
    except ValueError as e:
        return {"error": str(e)}
    

@app.post("/load_txt/")
async def load_txt(file: UploadFile = File(...)):
    # Save the uploaded file to the "documents" directory
    file_path = os.path.join("documents", file.filename)
    with open(file_path, 'wb') as buffer:
        buffer.write(file.file.read())

    chat.load_txt(file_path)

    # Remove the uploaded file from the "documents" directory
    # os.remove(file_path)

    return {"message": "Text file loaded successfully."}

