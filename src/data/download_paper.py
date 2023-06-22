import polars as pl
from elsapy_wrapper.elsclient import ElsClient
from elsapy_wrapper.elsprofile import ElsAuthor, ElsAffil
from elsapy_wrapper.elsdoc import FullDoc, AbsDoc
from elsapy_wrapper.elssearch import ElsSearch
import json
import sys
from util.log_util import get_logger
from typing import Union
from pathlib import Path

class PaperDownloader:
    def __init__(self, api_key:  Union[str, None], inst_token:  Union[str, None]):
        # Initialize client
        self.client = ElsClient(api_key, accept = "text/xml")
        self.client.inst_token = inst_token
        
    def abstract_download(self, eid_list: list, output_folder: str) -> None:
        # set local_dir to output_folder
        self.client.local_dir = output_folder
        logger = get_logger(__name__)
        ## ScienceDirect (abstract) document example using DOI
        for eid in eid_list:
            # input eid to get abstract     
            eid_doc = AbsDoc(eid = eid) 
            if eid_doc.read(self.client):
                logger.info("Read eid_doc.title: " + eid_doc.title)
                eid_doc.write()   
            else:
                logger.info("Failed to read: " + eid)

    def fulldoc_download(self, doi_link_df: pl.DataFrame, output_folder: str) -> None: 
        # store unavailable papers' links to save as text file
        unavailable_papers = []
        # set local_dir to output_folder
        self.client.local_dir = output_folder
        logger = get_logger(__name__)
        ## ScienceDirect (full-text) document example using DOI
        for row in doi_link_df.rows(named=True):
            if row.DOI == "":
                unavailable_papers.append(row.Link)
                continue
            # input eid to get full text     
            doi_doc = FullDoc(doi = row.DOI) 
            if doi_doc.read(self.client):
                logger.info("Read doi_doc.title: " + doi_doc.title)
                doi_doc.write()   
            else:
                logger.info("Failed to read: " + row.DOI)
                unavailable_papers.append(row.Link) 

        # save unavailable papers' links to text file
        with open(Path(output_folder) / 'unavailable_papers_links.txt', 'w') as file:
            for item in unavailable_papers:
                file.write("%s\n" % item)   