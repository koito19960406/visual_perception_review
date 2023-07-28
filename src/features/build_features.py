# -*- coding: utf-8 -*-
import click
import logging
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
import polars as pl
import pandas as pd
import os 
import glob
import json
from datetime import date
from langchain.output_parsers import PydanticOutputParser

from util.log_util import get_logger
from summarize_text import QAWithSourceReviwer
from extract_information import InfoExtracter
from parsers import (
    DOITitle,
    StudySummary,
    StudyArea,
    ImageData,
    PerceptionData,
    OtherSensoryData,
    ResearchTypeAndMethod,
    ResearchType,
    CVModelsData,
    CodeAvailability,
    DataAvailability,
    IRBApproval,
    StudyFeedback
)

def main(initial_input_csv: str, input_filepath: str, temp_output_path: str, final_output_path: str, question_text_path: str, openai_api_key: str, parser_classes: list):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    # initialize logger
    logger = get_logger(__name__)
    # set level at ERROR to avoid printing too many logs
    logger.setLevel("ERROR")
    
    # summarize texts
    reviewer = QAWithSourceReviwer(question_text_path, 
                                    openai_api_key=openai_api_key, 
                                    cache_path=temp_output_path,
                                    output_parsers=parser_classes)
    print(reviewer.openai_api_key)
    logger.info('Running Q&A')
    # save qa results with today's date
    # today = date.today()
    reviewer.qa_from_folder(input_filepath, os.path.join(temp_output_path, "qa_result_2023-07-19.json"))
    
    # extract information
    info_extracter = InfoExtracter(initial_input_csv, 
                                os.path.join(temp_output_path,"qa_result_2023-07-19.csv"), 
                                final_output_path)
    info_extracter.check_unaswered_papers()
    info_extracter.get_summary()
    info_extracter.get_aspect()
    info_extracter.get_location()
    info_extracter.get_extent()
    info_extracter.get_image_data_type()
    info_extracter.get_subjective_data_type()
    info_extracter.get_other_sensory_data()
    # info_extracter.get_type_of_research()
    # info_extracter.get_type_of_research_detail()
    # info_extracter.get_cv_model_name()
    # info_extracter.get_cv_model_purpose()
    # info_extracter.get_cv_model_training()
    # info_extracter.get_code_availability()
    # info_extracter.get_data_availability()
    # info_extracter.get_irb()
    # info_extracter.get_limitation_future_opportunity()
    
if __name__ == '__main__':
    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # input and output path
    initial_input_csv = "data/external/asreview_dataset_all_visual-urban-perception-2023-07-09-2023-07-17.csv"
    question_text_path = "data/external/question_list_text copy.txt"
    input_path = "data/raw/all_papers"
    # Create list of classes
    classes = [
        DOITitle,
        StudySummary,
        StudyArea,
        ImageData,
        PerceptionData,
        OtherSensoryData,
        ResearchTypeAndMethod,
        ResearchType,
        CVModelsData,
        CodeAvailability,
        DataAvailability,
        IRBApproval,
        StudyFeedback
    ]
    output_parsers = [PydanticOutputParser(pydantic_object = cls) for cls in classes]
    temp_output_path = "data/interim/"
    final_output_path = "data/processed/2nd_run/"
    # get api keys for openai and huggingface
    load_dotenv(find_dotenv())
    openai_api_key = os.getenv('OPENAI_API_KEY')
    huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY')
    main(initial_input_csv, input_path, temp_output_path, final_output_path, question_text_path, str(openai_api_key), output_parsers)
