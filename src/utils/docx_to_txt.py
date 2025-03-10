import os
from docx import Document
import sys
import fitz  
import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter


def convert_docs_to_markdown(folder_path):
    # Initialize a string to hold the combined Markdown content
    combined_markdown_content = ""

    # Iterate through all files in the specified folder
    for filename in os.listdir(folder_path):
        if filename.endswith('.docx'):
            docx_path = os.path.join(folder_path, filename)
            print(f"Processing file: {docx_path}")
            
            # Load the Word document
            doc = Document(docx_path)

            # Initialize a list to hold the Markdown lines for the current document
            markdown_lines = []

            # Iterate through the paragraphs in the document
            for para in doc.paragraphs:
                # Initialize a line to hold the formatted text
                line = ""

                # Check for list items
                if para.style.name.startswith('List'):
                    line += "- " + para.text  # Convert list items to Markdown format
                else:
                    # Process text for bold and italic formatting
                    for run in para.runs:
                        if run.bold:
                            line += f"**{run.text}**"  # Bold text
                        elif run.italic:
                            line += f"*{run.text}*"  # Italic text
                        else:
                            line += run.text  # Normal text

                # Add the formatted line to markdown_lines with two newlines
                markdown_lines.append(line + '\n\n')

            # Join the lines into a single Markdown string for the current document
            document_markdown_content = ''.join(markdown_lines)
            combined_markdown_content += document_markdown_content + '\n\n'  # Separate documents with two newlines
            with open(os.path.join('data', 'output.txt'), 'a') as output_file:  # Open output.txt in append mode
                output_file.write(document_markdown_content + '\n\n')  # Write the current document's content to the file

    return combined_markdown_content


def read_folder_to_text_df(directory_path):
    texts = []  # Initialize texts list outside the loop
    for filename in os.listdir(directory_path):
        if filename.endswith(".pdf"):
            filepath = os.path.join(directory_path, filename)
            print(f"Processing file: {filename}")  # Print only the file name
            pdf_document = fitz.open(filepath)  # Corrected to use fitz.open

            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                page_text = page.get_text()
                
                # Split page text with overlap of 50 characters
                text_splitter = RecursiveCharacterTextSplitter(chunk_overlap=100, chunk_size=600)
                split_texts = text_splitter.split_text(page_text)
                
                # Collect each chunk into the texts list
                texts.extend(split_texts)  # Use extend to add chunks directly to the list

            pdf_document.close()
    # Write the collected chunks to output.txt, deleting it if it exists
    output_file_path = os.path.join('data', 'output.txt')
    if os.path.exists(output_file_path):
        os.remove(output_file_path)  # Delete the existing file

    with open(output_file_path, 'w', encoding='utf-8') as output_file:  # Create a new file with UTF-8 encoding
        for text in texts:
            output_file.write(text + '\n')  # Write each chunk to the file               

    if not texts:
        print(f"No documents found in: {directory_path}")
    else:
        print(f"Processed {len(texts)} chunks from the documents in: {directory_path}")

    return texts