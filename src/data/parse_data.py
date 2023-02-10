import lxml
import re
from collections import defaultdict

class Parser:
    """This class parse data from a list of xml files and structure strings into a JSON file with the following structure
        - DOI
            - title
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
    
    def __init__(self, doc_list) -> None:
        self._doc_list = doc_list
        
    @property
    def doc_list(self):
        return self._doc_list    
    @doc_list.setter
    def doc_list(self,doc_list):
        self._doc_list = doc_list

    def categorize_section(self, title):
        """a method to categorize titles

        Args:
            title (_type_): _description_
        """
        patterns = [
            (r'.*intro.*|.*background.*', 'Introduction'),
            (r'.*review.*|.*work.*', 'Literature review'),
            (r'.*method.*', 'Methodology'),
            (r'.*result.*|.*discussion.*|.*conclusion.*', 'Results')
            ]

        title = title.lower()  # convert to lowercase
        for pattern, label in patterns:
            if re.search(pattern, title):
                return(label)

    def parse_single(self, doc_xml_root):
        """method to parse a single xml object and return a dictionary

        Args:
            doc_xml_root (etree root object): etree roo object of a single xml file
        
        Return: 
            label_dict (dict): dictionary with the structure stated above
        """
        # initialize the final dict (3 level, i.e. DOI->Intro->Subsections)
        label_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(str)))
        
        # get namespace
        ns = doc_xml_root.nsmap

        # get DOI (All the elments in the list will be under this DOI)
        coredata = doc_xml_root.find("coredata", namespaces={None:ns[None]})
        doi = coredata.find("prism:doi", namespaces={"prism":ns["prism"]}).text

        # get a title
        label_dict[doi]["title"] = coredata.find("dc:title", namespaces={"dc":ns["dc"]}).text
        
        # find sections
        sections_element_root = doc_xml_root.xpath(f"//*[translate(name(), 'FULLTEXTR', 'fulltextr')='ce:sections']")

        # get a list of section 
        section_element_root = sections_element_root[0].findall("ce:section", namespaces={"ce": ns["ce"]})  
        
        # loop through and classify
        for section in section_element_root:
            # get section title and label
            section_title = section.find("ce:section-title",namespaces={"ce": ns["ce"]})
            label = self.categorize_section(section_title)
            
            # get all the text
            
            label_dict[doi][label][section_title]
            print(section_title.text)
        
        # 