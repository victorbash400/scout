import PyPDF2
from io import BytesIO

def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extracts text from a PDF file's content.

    :param file_content: The content of the PDF file in bytes.
    :return: The extracted text as a single string.
    """
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""
