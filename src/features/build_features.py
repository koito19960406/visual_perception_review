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
from clean_text import TextCleaner
from summarize_text import TextSummarizer

def main(input_filepath: str, output_path: str, question_text_path: str, openai_api_key, huggingface_api_key):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    # initialize logger
    logger = get_logger(__name__)
    # logger.info('cleaning texts')
    
    # The section below was commented out because I decided to use embedding instead of summarizing each paragraph with ChatGPT
    # due to its slow proecessing
    # # initialize TextCleaner
    # text_cleaner = TextCleaner(input_filepath)
    # num_tokens_df_pre_summary = text_cleaner.count_check()
    # num_tokens_df_pre_summary.write_csv(os.path.join(output_filepath, "num_tokens_pre_summary.csv"))
    # logger.info('counted tokens before summarizing')    

    # # get summaries
    # summary_dict = text_cleaner.summarize_text() 
    # json_path = "data/interim/papers_summary.json"
    # with open(json_path, 'w') as dump_file:
    #     json.dump(summary_dict, dump_file)
    #     dump_file.close()
    # logger.info('saved paper summaries as json file')
    
    # # check the tokens again
    # num_tokens_df_post_summary = text_cleaner.count_check(summary_dict)
    # num_tokens_df_post_summary.write_csv(os.path.join(output_filepath, "num_tokens_post_summary.csv"))
    # logger.info('counted tokens after summarizing')     
    # summarize texts
    text_summarizer = TextSummarizer(question_text_path, 
                                    openai_api_key=openai_api_key, 
                                    huggingface_api_key=huggingface_api_key, 
                                    cache_path=output_path)
    print(text_summarizer.openai_api_key)
    logger.info('summarizing texts')
    text_summarizer.summarize_text_from_folder(input_filepath)
    output_csv_path = Path(output_path) / ("papers_extracted_" + str(date.today()) + ".csv")
    text_summarizer.put_output_in_csv(str(output_csv_path))

if __name__ == '__main__':
    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # input and output path
    question_text_path = "data/external/question_list_text.txt"
    input_path = "data/raw/papers/"
    output_path = "data/interim/"
    if not os.path.exists(output_path):
        os.makedirs(output_path, exist_ok=True)
    # get api keys for openai and huggingface
    load_dotenv(find_dotenv())
    openai_api_key = os.getenv('OPENAI_API_KEY')
    huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY')
    main(input_path, output_path, question_text_path, openai_api_key, huggingface_api_key)
