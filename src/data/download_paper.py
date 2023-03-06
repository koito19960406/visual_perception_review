import polars as pl
from elsapy_wrapper.elsclient import ElsClient
from elsapy_wrapper.elsprofile import ElsAuthor, ElsAffil
from elsapy_wrapper.elsdoc import FullDoc, AbsDoc
from elsapy_wrapper.elssearch import ElsSearch
import json
import sys
from util.log_util import get_logger
from typing import Union

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

    def fulldoc_download(self, eid_list: list, output_folder: str) -> None: 
        # set local_dir to output_folder
        self.client.local_dir = output_folder
        logger = get_logger(__name__)
        ## ScienceDirect (full-text) document example using DOI
        for eid in eid_list:
            # input eid to get full text     
            eid_doc = FullDoc(eid = eid) 
            if eid_doc.read(self.client):
                logger.info("Read eid_doc.title: " + eid_doc.title)
                eid_doc.write()   
            else:
                logger.info("Failed to read: " + eid)
