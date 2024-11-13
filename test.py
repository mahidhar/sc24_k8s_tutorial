#Imports
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.memory import ConversationSummaryMemory
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import TextLoader
from chromadb.utils import embedding_functions
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings

#Load the textbook and split up for vector database
loader = TextLoader('pg55084.txt')
documents = loader.load()
text_splitter = CharacterTextSplitter(chunk_size=300, chunk_overlap=70)
texts = text_splitter.split_documents(documents)

#Setup embedding model
embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
db = Chroma.from_documents(texts, embeddings)

#Setup prompt template
template = """<s>[INST] Given the context - {context} </s>[INST] [INST] Answer the following question - {question}[/INST]"""
pt = PromptTemplate(
            template=template, input_variables=["context", "question"]
        )

#RAG
rag = RetrievalQA.from_chain_type(
            llm=Ollama(model="mistral"),
            retriever=db.as_retriever(),
            memory=ConversationSummaryMemory(llm = Ollama(model="mistral")),
            chain_type_kwargs={"prompt": pt, "verbose": True},)

#Questions come after this point
