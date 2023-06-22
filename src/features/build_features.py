# -*- coding: utf-8 -*-
import click
import logging
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
import polars as pl
import os 
import glob
import json
from datetime import date

from util.log_util import get_logger
from summarize_text import TextSummarizer
from extract_information import InfoExtracter

def main(input_filepath: str, temp_output_path: str, final_output_path: str, question_text_path: str, openai_api_key, huggingface_api_key):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    # initialize logger
    logger = get_logger(__name__)
    
    # summarize texts
    text_summarizer = TextSummarizer(question_text_path, 
                                    openai_api_key=openai_api_key, 
                                    huggingface_api_key=huggingface_api_key, 
                                    cache_path=temp_output_path)
    print(text_summarizer.openai_api_key)
    logger.info('summarizing texts')
    text_summarizer.summarize_text_from_folder(input_filepath)
    output_csv_path = Path(temp_output_path) / ("papers_extracted_" + str(date.today()) + ".csv")
    if not output_csv_path.exists():
        text_summarizer.put_output_in_files(str(output_csv_path))
        
    # extract information
    info_extracter = InfoExtracter(str(output_csv_path), final_output_path)
    info_extracter.get_summary()
    info_extracter.get_aspect()
    info_extracter.get_location()
    info_extracter.get_extent()
    info_extracter.get_image_data_type()
    info_extracter.get_subjective_data_type()
    info_extracter.get_subjective_data_source()
    info_extracter.get_subjective_data_size()
    info_extracter.get_other_sensory_data()
    info_extracter.get_type_of_research()
    info_extracter.get_type_of_research_detail()
    info_extracter.get_cv_model_name()
    info_extracter.get_cv_model_purpose()
    info_extracter.get_cv_model_training()
    info_extracter.get_code_availability()
    info_extracter.get_data_availability()
    info_extracter.get_irb()
    info_extracter.get_limitation_future_opportunity()
    
if __name__ == '__main__':
    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # input and output path
    question_text_path = "data/external/question_list_text copy.txt"
    input_path = "data/raw/papers/"
    temp_output_path = "data/interim/"
    final_output_path = "data/processed/"
    # get api keys for openai and huggingface
    load_dotenv(find_dotenv())
    openai_api_key = os.getenv('OPENAI_API_KEY')
    huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY')
    main(input_path, temp_output_path, final_output_path, question_text_path, openai_api_key, huggingface_api_key)
