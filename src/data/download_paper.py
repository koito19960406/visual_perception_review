import polars as pl
from elsapy_wrapper.elsclient import ElsClient
from elsapy_wrapper.elsprofile import ElsAuthor, ElsAffil
from elsapy_wrapper.elsdoc import FullDoc, AbsDoc
from elsapy_wrapper.elssearch import ElsSearch
import json
import sys

class PaperDownloader:
    def __init__(self, doi_list, api_key, inst_token=None, output_folder=None):
        self.doi_list = doi_list
        
        # Initialize client
        self.client = ElsClient(api_key, accept = "text/xml")
        if inst_token != None:
            self.client.inst_token = inst_token
        if output_folder != None:
            self.client.local_dir = output_folder

    def download(self): 
        ## ScienceDirect (full-text) document example using DOI
        for doi in self.doi_list:
            # input doi to get full text     
            doi_doc = FullDoc(doi = doi) 
            if doi_doc.read(self.client):
                print ("doi_doc.title: ", doi_doc.title)
                doi_doc.write()   
            else:
                print ("Read document failed.")

