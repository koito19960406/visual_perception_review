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
        initial_input_filepath: str = '', 
        abstract_filtered_input_filepath: str = '',
        filtered_input_filepath: str = '',
        ris_filepath: str = ''):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = get_logger(__name__)
    logger.info('making final data set from raw data')
    
    # initialize PaperDownloader
    paper_downloader = PaperDownloader(api_key, inst_token) 
    
    if initial_input_filepath != '':
        # read csv
        abs_df = pl.read_csv(initial_input_filepath)
        abs_eid_list = (abs_df.
                    select("EID").
                    to_series().
                    to_list())
        
        # make output folders
        abstract_output_folder = Path(output_path) / "abstracts"
        abstract_output_folder.mkdir(parents=True, exist_ok=True)
        
        # download abstracts
        paper_downloader.abstract_download(abs_eid_list, str(abstract_output_folder))
        logger.info('downloaded papers')

        # initialize Parser
        doc_list = list(abstract_output_folder.glob("*.xml"))
        parser = Parser(doc_list)
        label_dict_joined = parser.parse_multiple_abstract()
        label_dict_joined = dict(label_dict_joined)
        
        # convert to polars to df and join  save to csv
        df = (pl.DataFrame(list(label_dict_joined.items()), ["DOI", "abstract"]).
            join(abs_df, on="DOI", how="left"))
        df.write_csv(f"{abstract_output_folder}/abstracts.csv") 
    
    if (abstract_filtered_input_filepath != ''):
        # load the filtered papers
        paper_filter = PaperFilter(abstract_filtered_input_filepath)
        input_paper_df = paper_filter.filter_paper()
        
        # save to csv and convert to ris
        if abstract_filtered_input_filepath[-5:] == ".xlsx":
            input_paper_df.write_csv(abstract_filtered_input_filepath[:-5] + ".csv")
            csv2ris = CSV2RISConverter(abstract_filtered_input_filepath[:-5] + ".csv", ris_filepath)
            csv2ris.run()
            
        
    if filtered_input_filepath != '':
        input_paper_df = pl.read_csv(filtered_input_filepath)
        # save to csv and convert to ris
        if filtered_input_filepath[-5:] == ".xlsx":
            input_paper_df.write_csv(filtered_input_filepath[:-5] + ".csv")
            csv2ris = CSV2RISConverter(filtered_input_filepath[:-5] + ".csv", ris_filepath)
            csv2ris.run()
        
    if (abstract_filtered_input_filepath != '') | (filtered_input_filepath != ''):
        # get DOI and link to dowlnoad full text and store link for unavailable papers
        full_doi_link_df = (input_paper_df.
                    select(["DOI","Link"]))
        # make output folders
        raw_paper_output_folder = Path(output_path) / "raw_papers"
        raw_paper_output_folder.mkdir(parents=True, exist_ok=True)
        paper_output_folder = Path(output_path) / "papers"
        paper_output_folder.mkdir(parents=True, exist_ok=True)

        # download papers
        paper_downloader.fulldoc_download(full_doi_link_df, str(raw_paper_output_folder))
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
    filtered_input_filepath = "data/external/scopus_filtered.csv"
    abstract_filtered_input_filepath = "data/external/asreview_dataset_visual-urban-perception-2022-2023.xlsx"
    initial_input_filepath = "data/external/scopus_initial.csv"
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
        # initial_input_filepath=initial_input_filepath, 
        abstract_filtered_input_filepath = abstract_filtered_input_filepath,
        ris_filepath = ris_filepath
        )