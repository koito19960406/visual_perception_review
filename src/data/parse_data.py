import lxml
from lxml import etree
import re
from collections import defaultdict
from tqdm import tqdm
from langchain.text_splitter import CharacterTextSplitter
from nltk.tokenize import sent_tokenize

# helper function
def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

class Parser:
    """This class parse data from a list of xml files and structure strings into a JSON file with the following structure
        - EID
            - title: str
            - Keywords: list
            - Abstract: str
            - Introduction, Background
                - a dict of subsections... (e.g., {"Introduction": "Today's world is facing...", "Background": "The problem is caused..."})
            - data, method, methodology
                - a dict of subsections...
            - results, analysis, discussion, conclusion
                - a dict of subsections...
            - others
                - a dict of subsections...
        The parsing is conducted using regex expressions.
    """
    
    def __init__(self, doc_list: list, unavailable_papers_csv_path: str) -> None:
        self._doc_list = doc_list
        self.unavailable_papers_csv_path = unavailable_papers_csv_path
        
    @property
    def doc_list(self):
        return self._doc_list    
    @doc_list.setter
    def doc_list(self,doc_list):
        self._doc_list = doc_list

    def _split_text(self,text) -> list:
        # use nltk to split the text by sentences
        sentences = sent_tokenize(text)
        text_cleaned = ".\n".join(sentences)
        text_splitter = CharacterTextSplitter(separator=".\n", chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_text(text_cleaned)
        return [t.replace('..\n', '. ') for t in texts if t]
    
    def _categorize_section(self, title: str) -> str:
        """a method to categorize titles

        Args:
            title (_type_): _description_
        """
        patterns = [
            (r'.*intro.*|.*background.*|.*problem statement.*|.*research objective.*', 'Introduction'),
            (r'.*review.*|.*work.*', 'Literature review'),
            (r'(?!.*result.*)(.*method.*|.*data.*|.*experiment.*|.*model.*|.*pipeline.*|.*evaluation.*|.*design.*|.*materials.*)', 'Methodology'),
            (r'.*result.*|.*discussion.*|.*conclusion.*|.*summary.*|.*implication.*', 'Results')
            ]

        title = title.lower()  # convert to lowercase
        for pattern, label in patterns:
            if re.search(pattern, title):
                return label 
        # if it doesn't get caught by any labels, then return as "others"
        return "Others" 
        
    def _parse_single_to_nested_dict(self, doc_xml_root: lxml.etree._Element) -> defaultdict:
        """method to parse a single xml object and return a dictionary

        Args:
            doc_xml_root (etree root object): etree roo object of a single xml file
        
        Return: 
            label_dict (dict): dictionary with the structure stated above
        """
        # initialize the final dict (3 level, i.e. EID -> general sections -> actual sections -> Subsections)
        def create_nested_defaultdict():
            return defaultdict(create_nested_defaultdict)
        label_dict = create_nested_defaultdict()
        
        # get namespace
        ns = doc_xml_root.nsmap

        # get EID (All the elments in the list will be under this EID)
        coredata = doc_xml_root.find("coredata", namespaces={None:ns[None]})
        eid = coredata.find("eid", namespaces={"prism":ns["prism"]}).text

        # get a title
        label_dict[eid]["title"] = coredata.find("dc:title", namespaces={"dc":ns["dc"]}).text

        # get keywords
        head = doc_xml_root.xpath(f"//*[translate(name(), 'FULLTEXTR', 'fulltextr')='head']")[0]
        keywords = [re.sub(" +", " ", etree.tostring(keyword, method="text", encoding="unicode").replace("\n", " ")).strip() for keyword in head.xpath(".//ce:keyword", namespaces={"ce": ns["ce"]})]
        label_dict[eid]["keywords"] = keywords
        
        # get abstract
        abstract = re.sub(" +", " ", "".join(head.xpath(".//ce:abstract//ce:simple-para/text()", namespaces={"ce":ns["ce"]}))).replace("\n", " ").strip()
        label_dict[eid]["abstract"] = abstract
        
        # find sections
        body = doc_xml_root.xpath(f"//*[translate(name(), 'FULLTEXTR', 'fulltextr')='body']")
        section_element_root = body[0].find("ce:sections", namespaces = {"ce":ns["ce"]}).findall("ce:section", namespaces={"ce": ns["ce"]})  

        for section in section_element_root:
            section_title = section.find("ce:section-title",namespaces={"ce": ns["ce"]}).text
            label = self._categorize_section(section_title) 
            section_below_list = section.findall("ce:section",namespaces={"ce": ns["ce"]})
            if len(section_below_list) > 0:
                for section_below in section_below_list:
                    sub_section_title = section_below.find("ce:section-title",namespaces={"ce": ns["ce"]}).text
                    paragraphs = [re.sub(r'\[.*?\]', '', re.sub(" +", " ", etree.tostring(para, method="text", encoding="unicode").\
                        replace("\n", " "))).replace(" .", ".").strip() for para in section_below.xpath(".//ce:para", namespaces={"ce": ns["ce"]})]
                    # send any subsections with "result" in their titles to result label
                    if "result" in sub_section_title:
                        label_dict[eid]["Results"][section_title][sub_section_title] = paragraphs
                    else:
                        # store in the label_dict
                        label_dict[eid][label][section_title][sub_section_title] = paragraphs
            else:
                paragraphs = [re.sub(r'\[.*?\]', '', re.sub(" +", " ", etree.tostring(para, method="text", encoding="unicode").\
                    replace("\n", " "))).replace(" .", ".").strip() for para in section.xpath(".//ce:para", namespaces={"ce": ns["ce"]})]
                # store in the label_dict
                label_dict[eid][label][section_title][section_title] = paragraphs
        return label_dict
    
    def parse_multiple_to_nested_dict(self) -> defaultdict:
        """use self.doc_list to parse them into JSON
        """
        # final dictionary
        label_dict_joined = defaultdict(str)
        
        for doc in self.doc_list:
            root = etree.parse(doc).getroot()
            label_dict = self._parse_single_to_nested_dict(root)
            # check the length of the dictionary
            if len(label_dict) > 0:
                label_dict_joined.update(label_dict)
            
        return label_dict_joined
    
    def _parse_single_to_simple_dict(self, doc_xml_root: lxml.etree._Element) -> defaultdict:
        """Parse xml file and return a simple dictionary containing the paper content

        Args:
            doc_xml_root (lxml.etree._Element): _description_

        Returns:
            _type_: _description_
        """
        # initialize the final dict
        label_dict = defaultdict(str)
        
        # get namespace
        ns = doc_xml_root.nsmap

        # get EID (All the elments in the list will be under this EID)
        coredata = doc_xml_root.find("coredata", namespaces={None:ns[None]})
        doi = coredata.find("prism:doi", namespaces={"prism":ns["prism"]}).text

        # get a title
        title = coredata.find("dc:title", namespaces={"dc":ns["dc"]}).text

        # get keywords
        head = doc_xml_root.xpath(f"//*[translate(name(), 'FULLTEXTR', 'fulltextr')='head']")[0]
        keywords = [re.sub(" +", " ", etree.tostring(keyword, method="text", encoding="unicode").replace("\n", " ")).strip() for keyword in head.xpath(".//ce:keyword", namespaces={"ce": ns["ce"]})]
        
        # get abstract
        abstract = re.sub(" +", " ", "".join(head.xpath(".//ce:abstract//ce:simple-para/text()", namespaces={"ce":ns["ce"]}))).replace("\n", " ").strip()

        # get data availability
        data_availability = re.sub(" +", " ", "".join(head.xpath(".//ce:data-availability//ce:para/text()", namespaces={"ce":ns["ce"]}))).replace("\n", " ").strip() 
        if data_availability == "":
            data_availability = "Not mentioned"
            
        # find sections
        body = doc_xml_root.xpath(f"//*[translate(name(), 'FULLTEXTR', 'fulltextr')='body']")
        # if there is no body, then return an empty dictionary
        if len(body) == 0:
            # open file and append doi to the end of the file in the first column
            with open(self.unavailable_papers_csv_path, "a") as file:
                # append title, doi, and empty strong to the end of the file in the first, second, and third column
                # make sure to escape commas in the title
                file.write(f"{title.replace(',', '')},{doi},\n")
            return label_dict

        section_element_root = body[0].find("ce:sections", namespaces = {"ce":ns["ce"]}).findall("ce:section", namespaces={"ce": ns["ce"]})  
        content_list = body[0].xpath(".//ce:section-title|.//ce:para|.//ce:label", namespaces={"ce": ns["ce"]})
        # store all the text content to text
        text = "DOI: " + doi + "\n\n" + "Title: " + title + "\n\n" + "Keywords: " + ", ".join(keywords) +\
            "\n\n" + "Abstract: " + abstract + "\n\n" + "Data availability: " + data_availability + "\n\n" + "Paper content:\n"    
        # set section title flag and subsection title flag
        section_title_flag = False
        sub_section_title_flag = False
        # initialize section title and subsection title
        section_title = ""
        sub_section_title = "" 
        for content in content_list:
            # check the label of the content
            if content.tag == f'{{{ns["ce"]}}}label':
                # if the label can be an integer, then set a section title flag
                if content.text.isdigit():
                    section_title_flag = True  
                # if the label can be a float, then set a subsection title flag
                elif is_float(content.text):
                    sub_section_title_flag = True
                # finally skip
                continue

            # if the content is a section title, then store it as title and skip
            if content.tag == f'{{{ns["ce"]}}}section-title':
                if section_title_flag:
                    section_title_flag = False
                    section_title = re.sub(r'\[.*?\]', '', re.sub(" +", " ", etree.tostring(content, method="text", encoding="unicode").\
                        replace("\n", " "))).replace(" .", ".").strip()
                    continue
                elif sub_section_title_flag:
                    sub_section_title_flag = False
                    sub_section_title = re.sub(r'\[.*?\]', '', re.sub(" +", " ", etree.tostring(content, method="text", encoding="unicode").\
                        replace("\n", " "))).replace(" .", ".").strip()
                    continue
            if sub_section_title != "":
                title = section_title + ": " + sub_section_title
            else:
                title = section_title
            # get content and store it to text
            _text_temp = re.sub(r'\[.*?\]', '', re.sub(" +", " ", etree.tostring(content, method="text", encoding="unicode").\
                replace("\n", " "))).replace(" .", ".").strip() 
            # split the text into chunks and add the title to each chunk when saving to a list
            _text_temp_chunk_list = self._split_text(_text_temp)
            _text_temp_chunk_list = [title + ": " + _text_chunk + "\n\n" for _text_chunk in _text_temp_chunk_list]
            for _text_chunk in _text_temp_chunk_list:
                text += _text_chunk 
            # else:
            #     text += re.sub(r'\[.*?\]', '', re.sub(" +", " ", etree.tostring(content, method="text", encoding="unicode").\
            #         replace("\n", " "))).replace(" .", ".").strip() + " " 
        label_dict[doi] = text.strip()
        return label_dict

    def parse_multiple_to_simple_dict(self) -> defaultdict:
        """use self.doc_list to parse them into JSON
        """
        # final dictionary
        label_dict_joined = defaultdict(str)
        
        for doc in tqdm(self.doc_list, desc="Parsing papers"):
            root = etree.parse(doc).getroot()
            label_dict = self._parse_single_to_simple_dict(root)
            label_dict_joined.update(label_dict)
            
        return label_dict_joined
    
    
    def _parse_single_abstract_to_simple_dict(self, doc_xml_root: lxml.etree._Element):
        # initialize the final dict
        label_dict = defaultdict(str)
        
        # get namespace
        ns = doc_xml_root.nsmap

        # get EID (All the elments in the list will be under this EID)
        coredata = doc_xml_root.find("coredata", namespaces={None:ns[None]})
        eid = coredata.find("eid", namespaces={None:ns[None]}).text
        # get abstract
        abstract_root = doc_xml_root.xpath(".//dc:description", namespaces={"dc": ns["dc"]})[0].xpath(".//ce:para", namespaces={"ce": ns["ce"]})[0]
        abstract_text = re.sub(r'\[.*?\]', '', re.sub(" +", " ", etree.tostring(abstract_root, method="text", encoding="unicode").\
                replace("\n", " "))).replace(" .", ".").strip() 
        label_dict[eid] = abstract_text
        return label_dict

    def parse_multiple_abstract(self):
         # final dictionary
        label_dict_joined = defaultdict(str)
        
        for doc in tqdm(self.doc_list, desc="Parsing abstracts"):
            root = etree.parse(doc).getroot()
            label_dict = self._parse_single_abstract_to_simple_dict(root)
            label_dict_joined.update(label_dict)
            
        return label_dict_joined