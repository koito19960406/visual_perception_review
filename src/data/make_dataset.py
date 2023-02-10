# -*- coding: utf-8 -*-
import click
import logging
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
from download_paper import PaperDownloader
import polars as pl
import os 

# @click.command()
# @click.argument('input_filepath', type=click.Path(exists=True))
# @click.argument('output_filepath', type=click.Path())
def main(input_filepath, output_filepath, api_key, inst_token = None):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)
    logger.info('making final data set from raw data')

    # read csv
    doi_list = (pl.read_csv(input_filepath).
                select("DOI").
                to_series().
                to_list())
    print(doi_list)
    # initialize PaperDownloader
    paper_download = PaperDownloader(doi_list, api_key, inst_token=inst_token, output_folder=output_filepath)
    paper_download.download()

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # input and output path
    input_path = "data/external/scopus.csv"
    output_path = "data/raw/papers/"
    if not os.path.exists(output_path):
        os.makedirs(output_path, exist_ok=True)
    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())
    api_key = os.getenv('API_KEY')
    inst_token = os.getenv('INST_TOKEN')
    print(type(api_key),type(inst_token))
    main(input_path, output_path, api_key,inst_token)
