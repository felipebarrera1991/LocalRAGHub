import argparse
import os
import shutil
import psycopg2
from get_embedding_function import get_embedding_function

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from langchain_community.vectorstores import PGVector

# Folder with Documents
DATA_PATH = "data"

DBNAME = "rh"
USER = "postgres"
PASSWORD = "test"
HOST = "localhost"
PORT = "5432"

CONNECTION_STRING = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"
COLLECTION_NAME = f"{DBNAME}_dataset"

def main():

    # Check if the database should be cleared (using the --clear flag).
    # create_database()
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--reset", action="store_true", help="Reset the database.")
    # args = parser.parse_args()
    # if args.reset:
    #     print("✨ Clearing Database")
    #     clear_database()

    # Create (or update) the data store.
    documents = load_documents()
    chunks = split_documents(documents)
    add_to_pgvector(chunks)


def load_documents():
    document_loader = PyPDFDirectoryLoader(DATA_PATH)
    return document_loader.load()


def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)


def add_to_pgvector(chunks: list[Document]):

    # Load the existing database.
    db = PGVector.from_documents(
        embedding=get_embedding_function(), 
        documents=chunks,
        collection_name=COLLECTION_NAME,
        connection_string=CONNECTION_STRING,
    )

    # Calculate Page IDs.
    chunks_with_ids = calculate_chunk_ids(chunks)

    # conn = psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST, port=PORT)

    # Add or Update the documents.
    # existing_items = db.get(include=[])  # IDs are always included by default
    # existing_ids = set(existing_items["ids"])
    # print(f"Number of existing documents in DB: {len(existing_ids)}")

    # Only add documents that don't exist in the DB.
    # new_chunks = []
    # for chunk in chunks_with_ids:
    #     if chunk.metadata["id"] not in existing_ids:
    #         new_chunks.append(chunk)

    # if len(new_chunks):
        # print(f"👉 Adding new documents: {len(new_chunks)}")
        # new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        # db.add_documents(new_chunks, ids=new_chunk_ids)
        # db.persist()
    # else:
        # print("✅ No new documents to add")

    # doc_vectors = embeddings.embed_documents([t.page_content for t in chunks])

def create_database():
    conn = psycopg2.connect(dbname="postgres", user=USER, password=PASSWORD, host=HOST, port=PORT)
    
    # conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS {DBNAME}")
        cur.execute(f"CREATE DATABASE {DBNAME}")
    conn.close()



def calculate_chunk_ids(chunks):

    # This will create IDs like "data/monopoly.pdf:6:2"
    # Page Source : Page Number : Chunk Index

    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        # If the page ID is the same as the last one, increment the index.
        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        # Calculate the chunk ID.
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        # Add it to the page meta-data.
        chunk.metadata["id"] = chunk_id

    return chunks


def clear_database():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)


if __name__ == "__main__":
    main()







