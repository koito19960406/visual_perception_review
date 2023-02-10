"""The (abstract) base entity module for elsapy. Used by elsprofile, elsdoc.
    Additional resources:
    * https://github.com/ElsevierDev/elsapy
    * https://dev.elsevier.com
    * https://api.elsevier.com"""

import requests, json, urllib
from abc import ABCMeta, abstractmethod
from lxml import etree
from . import log_util
import os

logger = log_util.get_logger(__name__)

class ElsEntity(metaclass=ABCMeta):
    """An abstract class representing an entity in Elsevier's data model"""

    # constructors
    @abstractmethod
    def __init__(self, uri):
        """Initializes a data entity with its URI"""
        self._uri = uri
        self._data = None
        self._client = None

    # properties
    @property
    def uri(self):
        """Get the URI of the entity instance"""
        return self._uri

    @uri.setter
    def uri(self, uri):
        """Set the URI of the entity instance"""
        self._uri = uri
    
    @property
    def id(self):
        """Get the dc:identifier of the entity instance"""
        return self.data["coredata"]["dc:identifier"]
    
    @property
    def int_id(self):
        """Get the (non-URI, numbers only) ID of the entity instance"""
        dc_id = self.data["coredata"]["dc:identifier"]
        return dc_id[dc_id.find(':') + 1:]

    @property
    def data(self):
        """Get the full JSON data for the entity instance"""
        return self._data

    @property
    def client(self):
        """Get the elsClient instance currently used by this entity instance"""
        return self._client

    @client.setter
    def client(self, elsClient):
        """Set the elsClient instance to be used by thisentity instance"""
        self._client = elsClient

    # modifier functions
    @abstractmethod
    def read(self, payloadType, elsClient):
        """Fetches the latest data for this entity from api.elsevier.com.
            Returns True if successful; else, False."""
        if elsClient:
            self._client = elsClient;
        elif not self.client:
            raise ValueError('''Entity object not currently bound to elsClient instance. Call .read() with elsClient argument or set .client attribute.''')
        try:
            api_response = self.client.exec_request(self.uri)
            if self._client.accept == "application/json":
                if isinstance(api_response[payloadType], list):
                    self._data = api_response[payloadType][0]
                else:
                    self._data = api_response[payloadType]
            elif self._client.accept == "text/xml": 
                root = etree.fromstring(api_response)
                elements = root.xpath(f"//*[translate(name(), 'FULLTEXTR', 'fulltextr')='{payloadType}']")
                if isinstance(elements, list):
                    self._data = elements[0]
                else:
                    self._data = elements
            ## TODO: check if URI is the same, if necessary update and log warning.
            logger.info("Data loaded for " + self.uri)
            return True
        except (requests.HTTPError, requests.RequestException) as e:
            for elm in e.args:
                logger.warning(elm)
            return False

    def write(self):
        """If data exists for the entity, writes it to disk as a .JSON file with
             the url-encoded URI as the filename and returns True. Else, returns
             False."""
        if self.data is not None:
            if self._client.accept == "application/json":
                dataPath = self.client.local_dir / (urllib.parse.quote_plus(self.uri)+'.json')
                with dataPath.open(mode='w') as dump_file:
                    json.dump(self.data, dump_file)
                    dump_file.close()
            elif self._client.accept == "text/xml":
                dataPath = self.client.local_dir / (urllib.parse.quote_plus(self.uri)+'.xml')
                if not os.path.exists(dataPath):
                    tree = etree.ElementTree(self.data)
                    with open(dataPath, "wb") as f:
                        tree.write(f, pretty_print=True)
            logger.info('Wrote ' + self.uri + ' to file')
            return True
        else:
            logger.warning('No data to write for ' + self.uri)
            return False