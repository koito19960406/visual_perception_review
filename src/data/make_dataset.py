# -*- coding: utf-8 -*-
import click
import logging
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
import polars as pl
import os 
from glob import glob
import json
from typing import Union
from datetime import date

from download_paper import PaperDownloader
from parse_data import Parser
from filter_paper import PaperFilter
from util.log_util import get_logger
from asr_csv2ris import CSV2RISConverter

# @click.command()
# @click.argument('input_filepath', type=click.Path(exists=True))
# @click.argument('output_filepath', type=click.Path())
def main(output_path: str, 
        api_key: Union[str, None], 
        inst_token: Union[str, None],
        initial_input_folder: str = '', 
        abstract_filtered_input_filepath: str = '',
        ris_filepath: str = ''):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = get_logger(__name__)
    logger.info('making final data set from raw data')
    
    # initialize PaperDownloader
    unavailable_paper_csv_path = str(Path(output_path) / "unavailable_papers.csv")
    paper_downloader = PaperDownloader(api_key, inst_token, unavailable_paper_csv_path) 
    
    # loop through initial_input_folder and get unique list of papers
    paper_list = [pl.read_csv(f, infer_schema_length=10000) for f in glob(initial_input_folder + "/*.csv")]
    # read csv files and concatenate
    paper_df = pl.concat(paper_list)
    # drop duplicates
    paper_df = paper_df.unique(subset=["EID"])
    # save to the same folder as abstract_filtered_input_filepath
    paper_df.write_csv(Path(abstract_filtered_input_filepath).parent / ("scopus_input.csv"))
    
    if abstract_filtered_input_filepath != '':
        # load the filtered papers
        paper_filter = PaperFilter(abstract_filtered_input_filepath)
        input_paper_df = paper_filter.filter_paper()
        
        # save to csv and convert to ris
        if abstract_filtered_input_filepath[-5:] == ".xlsx":
            input_paper_df.write_csv(abstract_filtered_input_filepath[:-5] + ".csv")
            csv2ris = CSV2RISConverter(abstract_filtered_input_filepath[:-5] + ".csv", ris_filepath)
            csv2ris.run()
        
        # get DOI and link to dowlnoad full text and store link for unavailable papers
        full_doi_link_df = (input_paper_df.
                    select(["DOI","Link", "Title"]))
        # make output folders
        xml_paper_output_folder = Path(output_path) / "xml"
        xml_paper_output_folder.mkdir(parents=True, exist_ok=True)
        pdf_paper_output_folder = Path(output_path) / "pdf"
        pdf_paper_output_folder.mkdir(parents=True, exist_ok=True)
        paper_output_folder = Path(output_path) / "papers"
        paper_output_folder.mkdir(parents=True, exist_ok=True)

        # download papers
        paper_downloader.fulldoc_download(full_doi_link_df, str(xml_paper_output_folder), str(pdf_paper_output_folder))
        logger.info('downloaded papers')

        # initialize Parser
        doc_list = list(xml_paper_output_folder.glob("*.xml"))
        parser = Parser(doc_list, unavailable_paper_csv_path)
        label_dict_joined = parser.parse_multiple_to_simple_dict()
        label_dict_joined = dict(label_dict_joined)
        # use the map function to write each paper content to a file
        list(map(lambda x: open(f"{str(paper_output_folder)}/{x[0].replace('/', '_')}.txt", "w").write(x[1]), label_dict_joined.items()))
        logger.info('saved papers as text files')

if __name__ == '__main__':
    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # input and output path
    initial_input_folder = "data/external/scopus/"
    abstract_filtered_input_filepath = "data/external/asreview_dataset_all_visual-urban-perception-2023-07-09-2023-07-17.xlsx"
    ris_filepath = "data/external/scopus_filtered.ris"
    output_path = "data/raw/"
    if not os.path.exists(output_path):
        os.makedirs(output_path, exist_ok=True)
    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())
    elsevier_api_key = os.getenv('ELSEVIER_API_KEY')
    inst_token = os.getenv('INST_TOKEN')
    main(output_path, elsevier_api_key, inst_token, 
        initial_input_folder=initial_input_folder, 
        abstract_filtered_input_filepath = abstract_filtered_input_filepath,
        ris_filepath = ris_filepath
        )