import polars as pl
from elsapy_wrapper.elsclient import ElsClient
from elsapy_wrapper.elsprofile import ElsAuthor, ElsAffil
from elsapy_wrapper.elsdoc import FullDoc, AbsDoc
from elsapy_wrapper.elssearch import ElsSearch
import json
import sys
from util.log_util import get_logger

class PaperDownloader:
    def __init__(self, doi_list: list, api_key: str, inst_token: str, output_folder: str):
        self.doi_list = doi_list
        
        # Initialize client
        self.client = ElsClient(api_key, accept = "text/xml")
        self.client.inst_token = inst_token
        self.client.local_dir = output_folder

    def download(self): 
        logger = get_logger(__name__)
        ## ScienceDirect (full-text) document example using DOI
        for doi in self.doi_list:
            # input doi to get full text     
            doi_doc = FullDoc(doi = doi) 
            if doi_doc.read(self.client):
                logger.info("Read doi_doc.title: " + doi_doc.title)
                doi_doc.write()   
            else:
                logger.info("Failed to read: " + doi)

