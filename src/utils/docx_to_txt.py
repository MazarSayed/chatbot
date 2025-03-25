import os
from docx import Document
import sys
import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
import PyPDF2

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
            combined_markdown_content += document_markdown_content + '\n\n\n'  # Separate documents with two newlines
            with open(os.path.join('data', 'output.txt'), 'a') as output_file:  # Open output.txt in append mode
                output_file.write(document_markdown_content + '\n\n')  # Write the current document's content to the file

    return combined_markdown_content


def read_folder_to_text_df(directory_path):
    texts = []  # Initialize texts list outside the loop
    output_file_path = os.path.join(directory_path, '..', 'output.txt')
    if os.path.exists(output_file_path):
        os.remove(output_file_path)  # Delete the existing file

    for filename in os.listdir(directory_path):
        if filename.endswith(".pdf"):
            filepath = os.path.join(directory_path, filename)
            print(f"Processing file: {filename}")  # Print only the file name
            markdown_text = pymupdf4llm.to_markdown(filepath)

            # Collect each page's text into the texts list
                       
            split_texts = markdown_text.split('new paragraph')  # Split the text at each 'new paragraph'
            texts.extend(split_texts)  # Add the split text directly to the list

    #print("full texts :", texts)        
    # Write the collected chunks to output.txt, deleting it if it exists
    with open(output_file_path, 'w', encoding='utf-8') as output_file:  # Create a new file with UTF-8 encoding
        for index, text in enumerate(texts, start=1):  # Add a number for the chunks
            output_file.write(f"Chunk {index}:\n{text}\n\n---------------------\n\n")  # Write each chunk to the file with two line breaks and a separator

    if not texts:
        print(f"No documents found in: {directory_path}")
    else:
        print(f"Processed {len(texts)} chunks from the documents in: {directory_path}")

    return texts


def extract_pdf_content(pdf_file_path):
    """
    Extract content from a PDF file and split it by 'new paragraph'
    
    Args:
        pdf_file_path (str): Path to the PDF file
        
    Returns:
        list: List of text chunks split by 'new paragraph'
    """
    if not os.path.exists(pdf_file_path):
        print(f"Error: File not found - {pdf_file_path}")
        return []
        
    if not pdf_file_path.endswith(".pdf"):
        print(f"Error: File is not a PDF - {pdf_file_path}")
        return []
    
    try:
        # Extract text from PDF using pymupdf4llm
        markdown_text = pymupdf4llm.to_markdown(pdf_file_path)
        
        # Split the text at each 'new paragraph'
        split_texts = markdown_text.split('new paragraph')
        
        # Clean and filter the text chunks
        cleaned_texts = [text.strip() for text in split_texts if text.strip()]
        
        print(f"Extracted {len(cleaned_texts)} chunks from {os.path.basename(pdf_file_path)}")
        return cleaned_texts
        
    except Exception as e:
        print(f"Error processing {pdf_file_path}: {str(e)}")
        return []


def extract_pdf_content_with_fitz(pdf_file_path, paragraph_separator="new paragraph"):
    """
    Extract content from a PDF file and split it by paragraph using PyMuPDF (fitz)
    directly without relying on pymupdf4llm.
    
    Args:
        pdf_file_path (str): Path to the PDF file
        paragraph_separator (str): Text to use when detecting paragraph breaks (default: "new paragraph")
        
    Returns:
        list: List of text chunks split by paragraphs
    """
    if not os.path.exists(pdf_file_path):
        print(f"Error: File not found - {pdf_file_path}")
        return []
        
    if not pdf_file_path.endswith(".pdf"):
        print(f"Error: File is not a PDF - {pdf_file_path}")
        return []
    
    try:
        # Open the PDF file with PyMuPDF
        pdf_document = fitz.open(pdf_file_path)
        full_text = ""
        
        # Extract text from each page
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            page_text = page.get_text()
            
            # Replace multiple newlines with paragraph separator
            page_text = page_text.replace('\n\n', f' {paragraph_separator} ')
            
            # Add to full text
            full_text += page_text + " "
        
        # Close the document
        pdf_document.close()
        
        # Split the text by the paragraph separator
        split_texts = full_text.split(paragraph_separator)
        
        # Clean and filter the text chunks
        cleaned_texts = []
        for text in split_texts:
            # Clean up whitespace and normalize text
            cleaned = " ".join(text.split())
            if cleaned:
                cleaned_texts.append(cleaned)
        
        print(f"Extracted {len(cleaned_texts)} chunks from {os.path.basename(pdf_file_path)}")
        return cleaned_texts
        
    except Exception as e:
        print(f"Error processing {pdf_file_path}: {str(e)}")
        return []


def extract_pdf_content_with_pypdf(pdf_file_directory, paragraph_separator="new paragraph"):
    """
    Extract content from all PDF files in a directory and split it by paragraph using PyPDF2
    
    Args:
        pdf_file_directory (str): Path to the directory containing PDF files
        paragraph_separator (str): Text to use when detecting paragraph breaks
        
    Returns:
        list: List of text chunks split by paragraphs from all PDFs
    """
    extracted_chunks = []  # List to hold chunks from all PDFs

    try:
        # Normalize the path
        pdf_file_directory = os.path.abspath(pdf_file_directory)
        
        if not os.path.exists(pdf_file_directory):
            print(f"Error: Directory not found - {pdf_file_directory}")
            return []
        
        if not os.path.isdir(pdf_file_directory):
            print(f"Error: Path is not a directory - {pdf_file_directory}")
            return []

        # Iterate through all PDF files in the directory
        for filename in os.listdir(pdf_file_directory):
            if filename.endswith(".pdf"):
                pdf_file_path = os.path.join(pdf_file_directory, filename)
                full_text = ""

                try:
                    with open(pdf_file_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        
                        # Extract text from each page
                        for page_num in range(len(pdf_reader.pages)):
                            page = pdf_reader.pages[page_num]
                            page_text = page.extract_text()
                            
                            if page_text:
                                # Replace multiple newlines with paragraph separator
                                page_text = page_text.replace('\n\n', f' {paragraph_separator} ')
                                page_text = page_text.replace('\n', ' ')  # Replace single newlines with spaces
                                
                                # Add to full text
                                full_text += page_text + " "
                except PermissionError as pe:
                    print(f"Permission denied accessing file: {pdf_file_path}")
                    print("Please ensure the file is not open in another program")
                    continue
                
                # Split the text by the paragraph separator
                split_texts = full_text.split(paragraph_separator)
                
                # Clean and filter the text chunks
                for text in split_texts:
                    # Clean up whitespace and normalize text
                    cleaned = " ".join(text.split())
                    if cleaned:
                        extracted_chunks.append(cleaned)

                print(f"Successfully extracted {len(split_texts)} chunks from {os.path.basename(pdf_file_path)}")

        return extracted_chunks
        
    except Exception as e:
        print(f"Error processing directory {pdf_file_directory}: {str(e)}")
        return []
    