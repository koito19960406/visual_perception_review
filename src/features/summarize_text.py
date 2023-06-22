import os
import pickle
import warnings
from pathlib import Path
from typing import Any
from glob import glob 
from tqdm import tqdm
import csv
import json
from collections import defaultdict

import faiss  # type: ignore
import openai
import torch
from langchain.llms import OpenAIChat
from langchain import OpenAI, VectorDBQA
from langchain.embeddings import HuggingFaceEmbeddings, HuggingFaceHubEmbeddings
from langchain.embeddings.base import Embeddings
from langchain.embeddings.cohere import CohereEmbeddings
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
from rich import print
from transformers import pipeline  # type: ignore

from util.decorator import retry
from util.log_util import get_logger

warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")
os.environ["TOKENIZERS_PARALLELISM"] = "false"
logger = get_logger(__name__)

def create_faiss_db_path(cache_path: Path, text_file_name: str) -> Path:
    output_dir = cache_path / "index" / text_file_name
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / "index.pkl"


def create_index_path(cache_path: Path, text_file_name: str) -> Path:
    output_dir = cache_path / "index" / text_file_name
    output_dir.mkdir(parents=True,exist_ok=True)
    return output_dir / "docsearch.index"


class TextSummarizer:
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
                huggingface_api_key = None, 
                cache_path: str = "", 
                embedding: str = "openai",
                llm: str = "openai",
                overwrite_index: bool = True) -> None:
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
        if huggingface_api_key != None:
            os.environ['HUGGINGFACEHUB_API_TOKEN'] = huggingface_api_key
            self._huggingface_api_key = huggingface_api_key
        with open(question_list_text, "r") as file:
            self._input_question_list: list = file.read().split("\n\n")
        self._embedding = embedding
        self._llm = llm
        self._cache_path = Path(cache_path)
        self._overwrite_index = overwrite_index
        pass

    @property
    def openai_api_key(self) -> str:
        return self._openai_api_key    
    @openai_api_key.setter
    def openai_api_key(self, openai_api_key: str)  -> None:
        self._openai_api_key = str(openai_api_key)
        
    @property
    def huggingface_api_key(self) -> str:
        return self._huggingface_api_key    
    @huggingface_api_key.setter
    def huggingface_api_key(self, huggingface_api_key: str)  -> None:
        self._huggingface_api_key = str(huggingface_api_key)
        
    @property
    def input_question_list(self) -> list:
        return self._input_question_list    
    @input_question_list.setter
    def input_question_list(self, input_question_list: list)  -> None:
        self._input_question_list = input_question_list
    
    @property
    def embedding(self) -> str:
        return self._embedding    
    @embedding.setter
    def embedding(self, embedding)  -> None:
        self._embedding = embedding

    @property
    def llm(self) -> str:
        return self._llm    
    @llm.setter
    def llm(self, llm)  -> None:
        self._llm = llm

    @property
    def cache_path(self) -> Path:
        return self._cache_path    
    @cache_path.setter
    def cache_path(self, cache_path: str)  -> None:
        self._cache_path = Path(cache_path)
    
    @property
    def overwrite_index(self) -> bool:
        return self._overwrite_index    
    @overwrite_index.setter
    def overwrite_index(self, overwrite_index: bool)  -> None:
        self._overwrite_index = overwrite_index

    def _split_text(self,text) -> list:
        text_splitter = CharacterTextSplitter(separator=".\n\n", chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_text(text)
        return [t for t in texts if t]

    @retry(exceptions=openai.error.RateLimitError, tries=2, delay=60, back_off=2)
    def _append_to_index(self, docsearch: FAISS, text: str) -> None:
        docsearch.add_texts([text])
    
    def _embedding_from_selection(self) -> Embeddings:
        if self.embedding == "huggingface":
            return HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        elif self.embedding == "huggingface-hub":
            return HuggingFaceHubEmbeddings(repo_id="sentence-transformers/all-mpnet-base-v2",
                                            huggingfacehub_api_token=self.huggingface_api_key)
        elif self.embedding == "cohere":
            return CohereEmbeddings()
        else:
            return OpenAIEmbeddings(openai_api_key=self.openai_api_key)

    def _create_index(self, text_file_name: str, chunked_text_list: list) -> dict:
        # set paths to faiss database and index
        faiss_db = create_faiss_db_path(self.cache_path, text_file_name)
        index_path = create_index_path(self.cache_path, text_file_name)

        if not self.overwrite_index and faiss_db.exists():
            logger.info("Index already exists at %s", faiss_db)
            return {"index_path": index_path, "faiss_db": faiss_db}
        else:
            logger.info(
                "Creating index at %s either because overwrite_index == %s or index file exists == %s",
                faiss_db,
                self.overwrite_index,
                faiss_db.exists(),
            )

        embeddings = self._embedding_from_selection()
        docsearch: FAISS = FAISS.from_texts(chunked_text_list, embeddings)

        faiss.write_index(docsearch.index, index_path.as_posix())
        with open(faiss_db, "wb") as f:
            pickle.dump(docsearch, f)

        return {"index_path": index_path, "faiss_db": faiss_db}

    def _load_index(self, faiss_db: Path, index_path: Path) -> int:
        if not faiss_db.exists():
            raise FileNotFoundError(f"FAISS DB file not found: {faiss_db}")

        print(f"[bold]Loading[/bold] index from {faiss_db}")
        index = faiss.read_index(index_path.as_posix())
        with open(faiss_db, "rb") as f:
            search_index = pickle.load(f)

        search_index.index = index
        return search_index
        
    def _prompt_from_question(self) -> ChatPromptTemplate:
        system_template="""Instructions:
        - Provide keywords and summary which should be relevant to answer the question strictly based on the provided context.
        - Provide detailed responses that relate to the question.
        - Answer "Not sure" if you are not sure about the answer.
        - Some questions have “Example Answer:” to give a format for you to answer in, some of which are bullet points. Unless question specifies the number of bullet points you need to provide, the number of bullet points may vary depending on the information in the source document. Don't simply follow the number of bullet points provided in “Example Answer:”.
        - “Example Answer:” might have dummy answers like “*XXX*” or “*TYPE*”. They are meant to be place-holders. So replace them with your own answers.

        Begin!
        ----------------
        {context}"""
        messages = [
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template("{question}")
        ]
        prompt = ChatPromptTemplate.from_messages(messages)
        return prompt
    
    def _llm_provider(self) -> BaseLLM:
        if self.llm == "huggingface":
            pipe = pipeline(
                "text2text-generation",
                model="pszemraj/long-t5-tglobal-base-16384-book-summary",
                device=0 if torch.cuda.is_available() else -1,
            )
            return HuggingFacePipeline(pipeline=pipe)
        else:
            return ChatOpenAI(temperature=0)
    
    @retry(exceptions=openai.error.RateLimitError, tries=2, delay=60, back_off=2)
    def _send_prompt(self, qa: VectorDBQA, input_question: str) -> Any:
        result = qa({"query": input_question})
        return result
        # return qa.run(query=input_question)
    
    def _ask_question(self, text_file_name: str, chunked_text_list: list) -> str:
        # creat index
        index_dict = self._create_index(text_file_name, chunked_text_list)
        # load index
        search_index = self._load_index(index_dict["faiss_db"], index_dict["index_path"])
        llm = self._llm_provider()
        prompt = self._prompt_from_question()
        chain_type_kwargs = {"prompt": prompt}
        qa = VectorDBQA.from_chain_type(llm=llm, 
                                        chain_type="stuff", 
                                        vectorstore=search_index, 
                                        chain_type_kwargs=chain_type_kwargs,
                                        return_source_documents = True)
        output_aggregated = ""
        for input_question in self.input_question_list:
            output = self._send_prompt(qa, input_question)
            source_documents = " ".join([doc.page_content.replace("\n"," ") for doc in output["source_documents"]])
            # append input question, source document, and answers to output_aggregated
            output_aggregated += input_question + "\n" + "Source documents: " + source_documents + "\n" + "Output:" + "\n" + output["result"].strip() + "\n\n"
        return output_aggregated
    
    def summarize_text_from_file(self, input_file_path: str) -> None:
        # load input_file_path as strings
        with open(input_file_path, "r") as file:
            text = file.read() 
        text_file_name = Path(input_file_path).name
        # create output_file_path
        output_dir = self.cache_path / ("embedding_" + self.embedding + "_llm_" + self.llm)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / text_file_name
        # stop here if the output file already exists
        if output_file.exists():
            return
        # get chunked text
        chunked_text_list = self._split_text(text) 
        # ask questions
        output = self._ask_question(text_file_name, chunked_text_list)
        # save the output to output_file_path as text file
        with open(output_file, "w") as file:
            file.write(output)

    def summarize_text_from_folder(self, input_folder_path: str) -> None:
        # load a list of text files
        text_list = list(Path(input_folder_path).glob("*.txt"))
        # loop through them to ask questions
        for input_file_path in tqdm(text_list, desc="summarizing papers"):
            self.summarize_text_from_file(str(input_file_path))
            logger.info("Summarized: " + str(input_file_path.name)) 

    def put_output_in_files(self, output_file_path: str) -> None:
        # define helper function
        def extract_questions_sources_answers(file_path):
            questions = []
            sources = []
            answers = []

            with open(file_path, 'r') as f:
                lines = f.readlines()
                answer = []
                question = []
                output_flag = False
                for line in lines:
                    if line.startswith('Q: '):
                        output_flag = False 
                        if answer:
                            answers.append("\n".join(answer))
                            answer = []
                        question.append(line.strip().replace('Q: ', ''))
                    elif line.startswith("Source documents: "):
                        sources.append(line.strip().replace('Source documents: ', ''))
                        if question:
                            questions.append("\n".join(question))
                            question = []
                    elif line.startswith('Output:'):
                        output_flag = True
                    elif output_flag:
                        answer.append(line.strip())
                    elif not output_flag and not line.startswith('Q: '):
                        question.append(line.strip())
                if answer:
                    answers.append("\n".join(answer))
            return questions, sources, answers
        # initialize dictionary
        data = {}
        # get files as list
        input_path = self.cache_path / ("embedding_" + self.embedding + "_llm_" + self.llm)
        file_paths = input_path.glob("*.txt")
        for file_path in file_paths:
            questions, sources, answers = extract_questions_sources_answers(file_path)
            doi = file_path.name.replace(".txt","").replace("_","/")
            data[doi] = {"questions": questions, "sources": sources, "answers": answers}
            
        header = ["DOI"]
        header.extend([question for question in data[str(list(data.keys())[0])]["questions"]])
        rows_questions_answer = [header]
        rows_questions_source = [header]    
        final_dict_list = []
        
        for key, value in data.items():
            # append a row for QA
            row_questions_answer = [key]
            row_questions_answer.extend(value["answers"])
            rows_questions_answer.append(row_questions_answer)

            # append a row for question and source
            row_questions_source = [key]
            row_questions_source.extend(value["sources"])
            rows_questions_source.append(row_questions_source) 
            
            # create dictionary for json
            _final_dict = {_header: _row for _header, _row in zip(header, row_questions_answer)}
            final_dict_list.append(_final_dict)
        
        # save to the output_file_path: rows_questions_answer 
        with open(output_file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows_questions_answer)
            
        # save to the output_file_path: rows_questions_source 
        with open(output_file_path.replace(".csv", "_source.csv"), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows_questions_source)
            
        # save to json
        with open(output_file_path.replace(".csv", ".json"), "w") as outfile:
            for d in final_dict_list:
                json.dump(d, outfile)
                outfile.write('\n')

