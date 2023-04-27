# Import the necessary libraries and modules
import os
import hashlib
import glob
from dotenv import load_dotenv
from langchain.document_loaders import PyPDFLoader
from langchain.chat_models import ChatOpenAI
# from langchain import OpenAI
from langchain.docstore.document import Document
from langchain.chains.summarize import load_summarize_chain
from modify import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA

from rich import print
from rich.console import Console
from rich.table import Table

# pip install code -> pip install -r requirements.txt --upgrade

load_dotenv()  # load variables from .env file
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


# Create a Console instance for custom Styling
console = Console()


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

        if page_range:
            new_docs = [Document(Page_content=t.page_content) for t in self.pages
                        [page_range[0]:page_range[1]]]
        else:
            new_docs = [Document(page_content=t.page_content) for t in self.pages]
        
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
        

# Main script starts here
if __name__ == "__main__":
    chat = Chat_With_PDFs_and_Summarize()

    # Search the 'documents' folder for PDF files
    document_list = glob.glob("documents/*.pdf")

    # Prepare a Rich Table for diplaying available PDF documents
    docs_table = Table(title="Available documents", show_header=True,
                       header_style="bold magenta")
    docs_table.add_column("Index", justify="right", style="dim")
    docs_table.add_column("Document", justify="right", style="bright_yellow")

    for index, document in enumerate(document_list):
        docs_table.add_row(str(index), document)

    console.print(docs_table)

    # Get user input for selecting the document to load
    document_index = int(console.input("Enter the index of the document you want to load: "))
    selected_document = document_list[document_index]

    # Get user input the range of pages to index
    page_range_option = console.input("Select pages to index: (A)ll pages or (C)ustom range: ").strip()

    if page_range_option.lower == "c":
        start_page = int(console.input("Start page (0-indexed): "))
        end_page = int(console.input("End page: "))
        page_range = (start_page, end_page)
    
    elif page_range_option.lower() == "a":
        page_range = None

    # Load the selected document with the specified page range
    chat.load_document(selected_document, page_range=page_range)

    console.rule("Document loaded")

    # Get user input for generating a summary
    summary_option = console.input("Do you want to generate a summary? (Y)es or (N)o: ").strip()

    if summary_option.lower() == "y":
        summary = chat.summarize()
        console.print(f"\nSummary: {summary}", style="bold")
        console.print('\n')

    # Ask questions and get answers in a Loop
    while True:
        query = console.input("Question: ")
        answer = chat.ask_question(query)
        console.print(f"Answer: {answer}", style="green")

