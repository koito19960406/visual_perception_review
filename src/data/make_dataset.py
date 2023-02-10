# -*- coding: utf-8 -*-
import click
import logging
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
import polars as pl
import os 
from glob import glob
import json

from download_paper import PaperDownloader
from parse_data import Parser
from util.log_util import get_logger

# @click.command()
# @click.argument('input_filepath', type=click.Path(exists=True))
# @click.argument('output_filepath', type=click.Path())
def main(input_filepath: str, output_path: str, api_key: str, inst_token: str):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = get_logger(__name__)
    logger.info('making final data set from raw data')

    # read csv
    doi_list = (pl.read_csv(input_filepath).
                select("DOI").
                to_series().
                to_list())
    # make output folders
    raw_paper_output_folder = Path(output_path) / "raw_papers"
    raw_paper_output_folder.mkdir(parents=True, exist_ok=True)
    paper_output_folder = Path(output_path) / "papers"
    paper_output_folder.mkdir(parents=True, exist_ok=True)
    
    # initialize PaperDownloader
    paper_downloader = PaperDownloader(doi_list, api_key, inst_token, str(raw_paper_output_folder))
    paper_downloader.download()
    logger.info('downloaded papers')

    # initialize Parser
    doc_list = list(raw_paper_output_folder.glob("*.xml"))
    parser = Parser(doc_list)
    label_dict_joined = parser.parse_multiple_to_simple_dict()
    label_dict_joined = dict(label_dict_joined)
    # use the map function to write each paper content to a file
    list(map(lambda x: open(f"{str(paper_output_folder)}/{x[0].replace('/', '_')}.txt", "w").write(x[1]), label_dict_joined.items()))
    logger.info('saved papers as text files')

if __name__ == '__main__':
    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # input and output path
    input_path = "data/external/scopus.csv"
    output_path = "data/raw/"
    if not os.path.exists(output_path):
        os.makedirs(output_path, exist_ok=True)
    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())
    api_key = os.getenv('API_KEY')
    inst_token = os.getenv('INST_TOKEN')
    main(input_path, output_path, api_key, inst_token)
