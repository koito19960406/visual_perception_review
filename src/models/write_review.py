from typing import List, Union, Any
import os 
import tqdm
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain import PromptTemplate, LLMChain
from langchain.text_splitter import CharacterTextSplitter

from src.models.util.log_util import get_logger
logger = get_logger(__name__)

class ReviewWriter:
    def __init__(self, openai_api_key: str, input_text: Union[List[str], str, Any], citation_style: str = "normal", model = "gpt-3.5-turbo-16k"):
        os.environ['OPENAI_API_KEY'] = openai_api_key
        self.input_text = input_text
        self.citation_style = citation_style
        self.first_run_output_list = []
        if model == "gpt-3.5-turbo-16k":
            self.chunk_size = 48000
            self.max_tokens = 2000
        if model == "gpt-4":
            self.chunk_size = 23000
            self.max_tokens = 2000
        self.model = model
        
    def _get_citations(self) -> List[str]:
        if self.citation_style == "normal":
            return ["(Author, Year)", "Author (Year)", "(Author, Year; Author, Year; Author, Year)"]
        elif self.citation_style == "latex":
            return [r"\citep{{abbrerviation}}", r"\citet{{abbrerviation}}", r"\citep{{abbrerviation, abbrerviation, abbrerviation}}"]
        else:
            raise ValueError("citation_style must be either 'normal' or 'latex'")

    def _get_citation_style(self) -> str:
        if self.citation_style == "normal":
            return "APA"
        elif self.citation_style == "latex":
            return "LaTeX natbib"
        else:
            raise ValueError("citation_style must be either 'normal' or 'latex'")

    def _split_text(self,text, separator) -> list:
        if len(text) > self.chunk_size:
            text_splitter = CharacterTextSplitter(separator=separator, chunk_size=self.chunk_size, chunk_overlap=0)
            texts = text_splitter.split_text(text)
            logger.info("Split text into %d chunks", len(texts))
            output = [t for t in texts if t]
            return output
        else:
            return [text]
    
    def _create_prompt_first(self):
        system_template=f"""Instructions:
        - You are a professional academic writer to write a summary of papers in a chronologically-ordered and organized format.
        - You will receive a list of academic papers with author names, purposes, methods, findings, limitations, and future research opportunities.
        - You can only use the information provided in the original list of papers.
        - Your task is to write a literature review that summarizes them by rigorously formatting them into sections as follows:
            1. Common trend in the research purpose, methods, and findings: Start this section with "Research purpose, methods, and findings: ". Then, start off with a summary sentence; for example, "Topic XXX has been studied with the focus on YYY". After that, describe each study's purpose, methods, and findings in a single sentence. For example, "{self._get_citations()[1]} investigated the effect of X on Y.". For example, if there are multiple similar studies, you can summarize them by saying "The effect of X on Y has been investigated {self._get_citations()[2]}.". Make sure to mention older studies first and newer studies last and highlight the temporal temporal evolution of the research over time over time.
            2. Common trend in limitations: Start this section with "Limitations: ". Then, start off with a summary sentence; for example, "A few studies have faced some limitations". After that, describe each study's limitations in a single sentence. For example, "{self._get_citations()[1]} had a small sample size.". For example, if there are multiple similar studies, you can summarize them by saying "A few studies had a small sample size {self._get_citations()[2]}.".
            3. Common trend in future research opportunities: Start this section with "Future research opportunities: ". Then, start off with a summary sentence; for example, "Based on the previous studies and their limitations, some future opportunities have been identified". After that, describe each study's future research opportunities in a single sentence. For example, "{self._get_citations()[1]} suggested that future research should investigate the effect of X on Y.". For example, if there are multiple similar studies, you can summarize them by saying "It has been suggested that future research should investigate the effect of X on Y {self._get_citations()[2]}.".
        - Do not just list or copy/paste the content from the papers, you need to make a cohesive paragraph that summarizes the papers.
        - You need to provide citations from the provided list of papers for each claim and sentence you make. The citation format is {self._get_citation_style()}: {self._get_citations()[2]} for parenthetical citation (i.e. citations AT THE END OF SENTENCES) or {self._get_citations()[1]} for textual citation (i.e. citations in the middle of sentences).
        - Make sure to mention studies in chronological order (older studies first and newer studies last) and highlight the temporal evolution of the research over time.

        Begin!
        ----------------
        """
        messages = [
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template("{text}")
        ]
        prompt = ChatPromptTemplate.from_messages(messages)
        return prompt
    
    def _create_prompt_second(self):
        system_template=f"""Instructions:
        - You are a professional academic writer who can summarize multiple literature reviews into one.
        - Your task is to integrate a list of 3 sections (research purpose, methods, and findings; limitations; and future research opportunities) flawlessly and cohesively in a chronologically-ordered format.
        - You must preserve citations and specific information for EACH SENTENCE. The citation format is {self._get_citation_style()}: {self._get_citations()[2]} for citations AT THE END OF SENTENCES or {self._get_citations()[1]} for citations in the middle of sentences.
        - You can only use the information provided in the original paragraphs.
        - Your task is to re-organize multiple corresponding sections into one section that smoothly combines each sentence in the provided texts by rigorously formatting them into unified sections as follows:
            1. Common trend in the research purpose, methods, and findings: Start this section with "Research purpose, methods, and findings: ". Then, start off with a summary sentence; for example, "Topic XXX has been studied with the focus on YYY". After that, describe each study's purpose, methods, and findings in a single sentence. Make sure to mention older studies first and newer studies last and highlight the temporal evolution of the research over time.
            2. Common trend in limitations: Start this section with "Limitations: ". Then, start off with a summary sentence; for example, "A few studies have faced some limitations". After that, describe each study's limitations in a single sentence. 
            3. Common trend in future research opportunities: Start this section with "Future research opportunities: ". Then, start off with a summary sentence; for example, "Based on the previous studies and their limitations, some future opportunities have been identified". After that, describe each study's future research opportunities in a single sentence. 
        - For example, if you receive two paragraphs of "Research purpose, methods, and findings: ", then integrate them into one paragraph. 
        - Again, remember to preserve citations in {self._get_citation_style()} style and specific information for EACH SENTENCE.
        - Make sure to mention studies in chronological order (older studies first and newer studies last) and highlight the temporal evolution of the research over time.
        - PRESERVE ORIGINAL SENTENCE STRUCTURE, GRAMMAR, CITATIONS as much as possible WITHOUT summarizing them excessively.
        
        Begin!
        ----------------
        """
        messages = [
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template("{text}")
        ]
        prompt = ChatPromptTemplate.from_messages(messages)
        return prompt
    
    def _ask_gpt(self, text, is_first_run=True, first_run_output=None):
        # Split text
        text_chunk = self._split_text(text, "\\n---\\n")

        # Choose the prompt based on whether this is the first run or a recursive run
        if is_first_run:
            chat_prompt = self._create_prompt_first()
        else:
            chat_prompt = self._create_prompt_second()

        if is_first_run:
            model = self.model
        else:
            model = "gpt-3.5-turbo-16k"
        # Start chat
        chat = ChatOpenAI(temperature=0, model=model, max_tokens=self.max_tokens, client = None)
        chain = LLMChain(llm=chat, prompt=chat_prompt)

        # Run the chain
        _output_list = []
        for chunk in tqdm.tqdm(text_chunk, desc=f"Running {model}"):
            output = chain.run(text=chunk)
            _output_list.append(output)

        if is_first_run:
            first_run_output = "\\n---\\n".join(_output_list)  # store the first run output
        
        # If _output_list has more than one element, then we need to run the chain again to summarize the result
        if len(_output_list) > 1:
            text = "\\n---\\n" + "\\n---\\n".join(_output_list)
            # Recursively call _ask_gpt
            first_run_output, output = self._ask_gpt(text, is_first_run=False, first_run_output=first_run_output)
        else:
            output = _output_list[0]
            
        return first_run_output, output  # Return both the first run output and the final output

    def execute(self):
        # check if the input is a list or a string
        if isinstance(self.input_text, str):
            self.input_text = [self.input_text]
        # loop through the list of texts
        final_output_list = []
        for text in tqdm.tqdm(self.input_text):
            logger.info(f"Asking {self.model} for review...")
            first_run_output, _output = self._ask_gpt(text)  # Unpack the two return values
            self.first_run_output_list.append(first_run_output)  # Append the first run output to the list
            logger.info(f"{self.model} output: " + _output)
            final_output_list.append(_output)
        return self.first_run_output_list, final_output_list  # Return both lists as a tuple