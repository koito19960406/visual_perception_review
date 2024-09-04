import os
import pickle
import warnings
from pathlib import Path
from typing import Any, List, Union
from glob import glob 
from tqdm import tqdm
import csv
import json
from collections import defaultdict
import pandas as pd
import faiss  # type: ignore
import openai
import torch
from langchain.output_parsers import PydanticOutputParser
from langchain.llms import OpenAIChat
from langchain import OpenAI, VectorDBQA
from langchain.chains import RetrievalQA
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms.base import BaseLLM
from langchain.llms.huggingface_pipeline import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.faiss import FAISS
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains.qa_with_sources.base import BaseQAWithSourcesChain
from langchain.chains import VectorDBQAWithSourcesChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
from langchain.document_loaders import TextLoader, UnstructuredPDFLoader
from langchain.output_parsers import RetryWithErrorOutputParser, OutputFixingParser
from rich import print
from transformers import pipeline  # type: ignore

from util.decorator import retry
from util.log_util import get_logger

warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")
os.environ["TOKENIZERS_PARALLELISM"] = "false"
logger = get_logger(__name__)
# set level at ERROR to avoid printing too many logs
logger.setLevel("ERROR")

def create_faiss_db_path(cache_path: Path, text_file_name: str) -> Path:
    output_dir = cache_path / "index" / text_file_name
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / "index.pkl"


def create_index_path(cache_path: Path, text_file_name: str) -> Path:
    output_dir = cache_path / "index" / text_file_name
    output_dir.mkdir(parents=True,exist_ok=True)
    return output_dir / "docsearch.index"


class QAWithSourceReviwer:
    """
    Input: 
        folder that contains text files
        a text file that contains a list of questions
    Output:
        responses from LLMs and return. 
    """
    
    def __init__(self, 
                question_list_text: str, 
                openai_api_key = None,
                cache_path: str = "",
                output_parsers: Union[List[PydanticOutputParser], None] = None) -> None:
        """Input for the summarizer

        Args:
            question_list_text (str): a file path to a text file of a list of questions to ask about papers
            openai_api_key (str): api key for openai 
            huggingface_api_key (str): api key for huggingface 
            cache_path (str, optional): a path to a folder to store cache files. Defaults to "".
            embedding (str, optional): a type of embedding to use. Defaults to "" (i.e. openai).
                Options are: "huggingface", "huggingface-hub", "cohere" 
            llm (str, optional): a type of large language model to use. Defaults to "" (i.e. openai).
                Options are: "huggingface"
            overwrite_index (bool, optional): whether to overwrite saved indexes
        """
        openai.api_key = openai_api_key
        openai.debug = False
        if openai_api_key != None:
            os.environ['OPENAI_API_KEY'] = openai_api_key
            self._openai_api_key = openai_api_key
        with open(question_list_text, "r") as file:
            self._input_question_list: list = file.read().split("\n\n")
        self._cache_path = Path(cache_path)
        self._output_parsers = output_parsers
        self.error_files = []
        pass

    @property
    def openai_api_key(self) -> str:
        return self._openai_api_key    
    @openai_api_key.setter
    def openai_api_key(self, openai_api_key: str)  -> None:
        self._openai_api_key = str(openai_api_key)
        
    @property
    def input_question_list(self) -> list:
        return self._input_question_list    
    @input_question_list.setter
    def input_question_list(self, input_question_list: list)  -> None:
        self._input_question_list = input_question_list

    @property
    def cache_path(self) -> Path:
        return self._cache_path    
    @cache_path.setter
    def cache_path(self, cache_path: str)  -> None:
        self._cache_path = Path(cache_path)

    def get_loader(self, input_file_path: str) -> Any:
        if input_file_path.endswith(".pdf"):
            loader = UnstructuredPDFLoader(input_file_path)
        elif input_file_path.endswith(".txt"):
            loader = TextLoader(input_file_path)
        else:
            raise ValueError("File type not supported")
        return loader

    @property
    def output_parsers(self) -> Any:
        # make sure it has the same length as input_question_list
        if self._output_parsers == None:
            self._output_parsers = [None for i in range(len(self.input_question_list))]
        else:
            if len(self._output_parsers) != len(self.input_question_list):
                raise ValueError("output_parsers must have the same length as input_question_list")
        return self._output_parsers
    @output_parsers.setter
    def output_parsers(self, output_parsers: list)  -> None:
        self._output_parsers = output_parsers
    
    def qa_from_file(self, input_file_path: str) -> list:
        # get loader and split text
        loader = self.get_loader(input_file_path)
        documents = loader.load()
        text_splitter = CharacterTextSplitter(chunk_size=5000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)
        # embed text and create index
        embeddings = OpenAIEmbeddings(client=None)
        persistent_directory = self.cache_path / "index" / Path(input_file_path).name 
        persistent_directory.mkdir(parents=True, exist_ok=True)
        docsearch = Chroma.from_documents(texts, embeddings, persist_directory = str(persistent_directory))
        
        prompt_template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

        {context}

        Question: {question}
        {format_instructions}
        Answer:"""
        output_list = []
        for input_question, output_parser in zip(self.input_question_list, self.output_parsers):
            # set up qa
            if output_parser != None:
                format_instructions = output_parser.get_format_instructions()
            else:
                format_instructions = ""
            PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"],
                                    partial_variables={"format_instructions": format_instructions})
            chain_type_kwargs = {"prompt": PROMPT}
            retriever = docsearch.as_retriever()
            from openai import OpenAIError

            max_tokens = 2000
            step = 100

            while max_tokens > step:
                try:
                    qa = RetrievalQA.from_chain_type(llm=ChatOpenAI(client=None, openai_api_key=self.openai_api_key, temperature=0, model="gpt-3.5-turbo-16k", max_tokens=max_tokens),
                                                    chain_type="stuff", retriever=retriever, chain_type_kwargs=chain_type_kwargs, return_source_documents=True)
                    # If the API call is successful, break the loop
                    break
                except OpenAIError as e:
                    print(f"Error at max_tokens = {max_tokens}: {str(e)}")
                    max_tokens -= step
            try:
                output = qa({"query":input_question})
            except:
                if input_file_path not in self.error_files:
                    self.error_files.append(input_file_path)
                output_list.append({"result": "Error", "source_documents": "Error"})
                continue
            # parse the output with RetryWithErrorOutputParser
            # retry_output_parser = OutputFixingParser.from_llm(parser=output_parser, llm=ChatOpenAI(client = None, openai_api_key=self.openai_api_key, temperature = 0, model = "gpt-3.5-turbo"))

            # output["result"] = retry_output_parser.parse_with_prompt(output["result"], PROMPT.format_prompt(context=retriever.get_relevant_documents(input_question), question=input_question)).\
            #     json()
            output["source_documents"] = " ".join([doc.page_content.replace("\n"," ") for doc in output["source_documents"]])
            # append to output_list
            output_list.append(output)
        return output_list
    

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
                output_dict[input_file_path.name] = self.qa_from_file(str(input_file_path))
                logger.info("Ran Q&A for " + str(input_file_path.name)) 

                # save intermediary results as json
                with open(output_json_file_path, "w") as outfile:
                    json.dump(output_dict, outfile)

        # save as csv with columns: DOI, questions (answers)
        header = ["file_name"]
        header.extend([question for question in self.input_question_list])
        rows = [header]
        for key, value in output_dict.items():
            row = [key]
            row.extend([qa["result"] for qa in value])
            rows.append(row)
        with open(output_json_file_path.replace(".json", ".csv"), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        
        # save as csv with columns: DOI, questions (sources)
        header = ["file_name"]
        header.extend([question for question in self.input_question_list])
        rows = [header]
        for key, value in output_dict.items():
            row = [key]
            row.extend([qa["source_documents"] for qa in value])
            rows.append(row)
        with open(output_json_file_path.replace(".json", "_source.csv"), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        # save self.error_files as csv
        with open(output_json_file_path.replace(".json", "_error.csv"), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(self.error_files)