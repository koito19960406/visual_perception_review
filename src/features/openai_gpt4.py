from openai import OpenAI
from pathlib import Path
import json
import csv
from collections import defaultdict
from tqdm import tqdm
import fitz
from typing import Optional
import re
import io
import ocrmypdf

from .util.log_util import get_logger
logger = get_logger(__name__)
# set level at ERROR to avoid printing too many logs
logger.setLevel("ERROR")


def is_text_readable(text, threshold=0.5):
    """
    Analyze the text to determine if it's meaningfully readable.
    Returns True if the text is deemed readable, False otherwise.
    """
    # Calculate the proportion of printable to total characters
    printable_chars = re.sub(r'[^\x20-\x7E]+', '', text)
    if len(text) == 0: return False
    readability_ratio = len(printable_chars) / len(text)
    return readability_ratio > threshold


class PaperReviewer:
    def __init__(self, question_list_text: str,
                 openai_api_key: Optional[str] = None):
        self.client = OpenAI(api_key=openai_api_key)
        with open(question_list_text, "r") as file:
            self._input_question_list = file.read()

    def load_file(self, file_path):
        # Ensure the version of PyMuPDF is adequate for OCR
        if tuple(map(int, fitz.VersionBind.split("."))) < (1, 19, 1):
            raise ValueError(
                "Need at least v1.19.1 of PyMuPDF for OCR support"
            )

        if file_path.endswith(".pdf"):
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                # First, try to extract text with PyMuPDF
                page_text = page.get_text()
                text += page_text
            # Check if the extracted text is readable
            if not is_text_readable(text):
                ocrpdf = io.BytesIO()  # Prepare buffer for OCR-ed PDF
                ocrmypdf.ocr(file_path, ocrpdf, force_ocr=True, output_type="pdf")
                doc = fitz.open("pdf", ocrpdf)
                text = ""
                for page in doc:
                    text += page.get_text()
            return text

        elif file_path.endswith(".txt"):
            with open(file_path, "r") as file:
                return file.read()

        else:
            raise ValueError(
                "File format not supported. Please use .txt or .pdf"
            )

    def qa_from_file(self, file_path):
        # because the OpenAI API is broken, I'll just load the file from the local system
        paper_content = self.load_file(file_path)
        content = f"""Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.
        Paper Context:
        {paper_content}

        Question: {self._input_question_list}
        
        Important Note:
            - Please answer the question solely based on the Paper Content and follow the specified format.
            - If the information needed to answer a question is not found in the document, respond with 'NA' to prevent misinformation. 
            - In the examples, *XXX* is a placeholder for the actual answer.
            - In the examples, '...' means there could be more than one set of answers.
            - Please answer the questions based on the Paper Content only.
            
        Answer:"""
    
        
        # use chat completions to get the answer instead of the assistant
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are skilled at conducting systematic reviews. Your task is to analyze the input file and answer questions based on it, adhering to a JSON format for clarity and relevance."},
                {"role": "user", "content": content}
            ]
            )
        # print(response.choices[0].message.content)
        return response.choices[0].message.content
    
    def qa_from_folder(self, input_folder_path: str, output_json_file_path: str) -> None:
        # load a list of text or PDF files
        path = Path(input_folder_path)
        txt_files = list(path.glob("*.txt"))
        pdf_files = list(path.glob("*.pdf"))
        file_list = txt_files + pdf_files

        # Load previously processed data if exists
        if Path(output_json_file_path).exists():
            with open(output_json_file_path, "r") as infile:
                output_dict = json.load(infile)
        else:
            output_dict = defaultdict(list)

        # loop through them to ask questions
        for input_file_path in tqdm(file_list, desc="running Q&A with papers"):
            # Checkpointing: skip if the result already exists
            if input_file_path.name not in output_dict:
                output_dict[input_file_path.name] = json.loads(str(self.qa_from_file(str(input_file_path))))
                logger.info("Ran Q&A for " + str(input_file_path.name)) 

                # save intermediary results as json
                with open(output_json_file_path, "w") as outfile:
                    json.dump(output_dict, outfile)

        # save as csv with columns: DOI, questions (answers)
        header = ["file_name"]
        header.extend([self._input_question_list])
        rows = [header]
        for file_name, answers in output_dict.items():
            rows.append([file_name, json.dumps(answers)])
        with open(output_json_file_path.replace(".json", ".csv"), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)