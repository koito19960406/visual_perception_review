from transformers import GPT2TokenizerFast
import json
import polars as pl
from chatgpt_wrapper import ChatGPT
import copy
from functools import reduce
from tqdm import tqdm

from util.log_util import get_logger

# initialize logger
logger = get_logger(__name__)

class TextCleaner:
    """This class checks and cleans texts so that they can be used for info extraction with a GPT model later
    """
    def __init__(self, paper_json) -> None:     
        self._paper_json = paper_json        
        # initialize tokernizer
        self._tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

    @property
    def paper_json(self):
        return self._paper_json    
    @paper_json.setter
    def paper_json(self,paper_json):
        self._paper_json = paper_json

    def _count_tokens(self,text_str):
        """This function takes strings and return the number of tokens

        Args:
            text_str (str): string of texts 
        """
        num_tokens = len(self._tokenizer(text_str)['input_ids'])
        return(num_tokens)
    
    # def check_count(self,text_str):
    
    def count_check(self, dictionary=None):
        """This function checks number of tokens for each general section
        Args:
            dictionary (dict): a dictionary containing papers' content
        Returns:
            df: polars dataframe that contains: title, keywords, abstract, and number of tokens for each of 
            Introduction, Literature review, Methodology, Results, and Others
        """
        # define helper functions
        def count_tokens(d):
            token_count=0
            for value in d.values():
                if isinstance(value, dict):
                    token_count += count_tokens(value)
                else:
                    # this gets a list of strings, so loop through to get the total tokens
                    for sentence in value:
                        num_tokens = self._count_tokens(sentence)
                        token_count += num_tokens
            return token_count

        def count_nested_dict(d):
            # initialize a dict of lists
            num_tokens_dict = {"doi": [],
                            # "title": [], 
                            # "keywords": [],
                            # "abstract": [],
                            "Introduction": [],
                            "Literature review": [],
                            "Methodology": [],
                            "Results": [],
                            "Others": []}
            
            for doi, dictionary in d.items():
                # append doi
                num_tokens_dict["doi"].append(doi)
                # create a checklist of sections
                check_list = list(num_tokens_dict.keys())[1:] 
                for key, value in dictionary.items():
                    if isinstance(value, dict):
                        token_count = count_tokens(value)
                        num_tokens_dict[key].append(token_count)
                        # check off the key from check_list
                        check_list.remove(key)
                    else:
                        pass
                # append None if there's still leftover in the check_list
                for check_key in check_list:
                    num_tokens_dict[check_key].append(None)  
            # store them in a df: title (str), Introduction (int), Literature review (int), Methodology (int), and Results (int) 
            num_tokens_df = pl.DataFrame(num_tokens_dict) 
            return(num_tokens_df)
        # check if the user provided dictionary. If not, then just use the original json file.
        if dictionary == None: 
            with open(self.paper_json, "r") as f:
                paper_dict = json.load(f)
        else:
            paper_dict = dictionary
        num_tokens_df = count_nested_dict(paper_dict)
        return(num_tokens_df)
        
    def summarize_text(self):
        # define helper functions
        def set_value(d, keys, value):
            """Function to replace a value in a dictionary with a new value based on a list of keys

            Args:
                d (dict): dictionary to retrieve information from
                keys (list): list of keys (string)
                value (_type_): a new value. This could be any data type
            """
            reduce(lambda d, key: d.setdefault(key, {}), keys[:-1], d)[keys[-1]] = value

        def get_summary(d, d_copy, keys, bot):
            """Function to recursively go down a input dictionary and store summaries from ChatGPT in a copied dictionary

            Args:
                d (dict): input dictionary
                d_copy (dict): a copy of d
                keys (list): list of keys. Initially, it should be empty
                bot (ChatGPT instance): an instance of ChatGPT (see: https://github.com/mmabrouk/chatgpt-wrapper)

            Returns:
                d_copy: modified d_copy (replaced paragraphs with summaries)
            """
            # prompt prefix
            prompt_prefix = "summarize this using about 1/3 of the words: "
            if isinstance(d, dict):
                for key, value in d.items():
                    keys.append(key)
                    get_summary(value, d_copy, keys, bot)
                    keys.pop()
            elif isinstance(d, list) & ("keywords" not in keys):
                # get summary
                summary_list = []
                for para in d:
                    prompt = prompt_prefix + para
                    response = bot.ask(prompt)
                    print("- ", response, "\n")
                    summary_list.append(response)
                print("-"*10)
                # store it in d_copy
                set_value(d_copy, keys, summary_list) 
                logger.info("Summarized: " + str(keys))
            else:
                pass
            return d_copy
        # initialize ChatGPT bot
        bot = ChatGPT()
        # load the dictionary
        with open(self.paper_json, "r") as f:
            paper_dict = json.load(f) 
        # make a copy
        paper_dict_copy = copy.deepcopy(paper_dict)
        # loop through doi
        for doi in tqdm(paper_dict.keys()):
            # get a modified paper_dict_copy
            paper_dict_copy[doi] = get_summary(paper_dict[doi], paper_dict_copy[doi], [], bot)
        return(paper_dict_copy)