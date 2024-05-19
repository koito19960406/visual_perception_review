import pandas as pd
import polars as pl
from geopy.geocoders import Nominatim
from geotext import GeoText
import re
from pathlib import Path
import spacy
import ast
from tqdm.auto import tqdm
import requests
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable 

tqdm.pandas()

from util.log_util import get_logger

# initialize logger
logger = get_logger(__name__)

class InfoExtracter:
    def __init__(self, initial_input_csv: str, input_csv_filepath: str, output_folder_path: str):
        self.initial_input_df = pd.read_csv(initial_input_csv)
        self.input_df = pd.read_csv(input_csv_filepath)
        # get the column names as a list
        # rename columns with 0, 1, 2, ...
        new_column_names = [str(i) for i in range(len(self.input_df.columns))]
        self.input_df.columns = new_column_names
        if not Path(output_folder_path).exists():
            Path(output_folder_path).mkdir(parents=True, exist_ok=True)
        self.output_folder_path = output_folder_path
        
    def correct_string_format(self, s):
        # Extract the title part from the string
        match = re.search(r'"title": (.+)}', s)
        if match is not None:  # check if match found
            start, end = match.span(1)
            # Remove existing double quotes
            removed_quotes_s = s[start:end].replace('"', '')
            # Put the value of "title" within quotes and replace the original in s
            corrected_s = s[:start] + '"' + removed_quotes_s + '"' + s[end:]
            return corrected_s
        else:
            return s  # return the original string if no match is found

    def check_unaswered_papers(self):
        # check if the file exists
        if (Path(self.output_folder_path + "unanswered_papers.csv").exists()) and\
            (Path(self.output_folder_path + "input_df_with_title_doi.xlsx").exists()):
            logger.info("unanswered_papers.csv and input_df_with_title_doi.xlsx already exist. Skipping this step.")
            return
        input_df = self.input_df.copy()
        initial_input_df = self.initial_input_df.copy()
        input_df['label_dict'] = input_df["1"].apply(self.correct_string_format)
        input_df["label_dict"] = input_df['label_dict'].apply(lambda x: ast.literal_eval(x))
        input_df = input_df.join(pd.json_normalize(input_df["label_dict"]))
        # replace "," with "" in title
        input_df["title"] = input_df["title"].str.replace(",","")
        initial_input_df["Title"] = initial_input_df["Title"].str.replace(",","").str.replace('"', '')
        remaining_df = initial_input_df[~initial_input_df["DOI"].isin(input_df["doi"]) &\
            ~initial_input_df["DOI"].isin(input_df["0"].str.replace(".txt", "").str.replace('_', '/')) &\
                ~initial_input_df["Title"].isin(input_df["title"])]
        # save as csv
        remaining_df.to_csv(self.output_folder_path + "unanswered_papers.csv")
        logger.info("unanswered_papers.csv saved")
        # save input_df as excel
        input_df["EID"] = ""
        # for those rows with ".txt" in column "0", replace ".txt" with "/" and save to column "EID"
        input_df.loc[input_df["0"].str.contains(".txt"), "doi"] = input_df.loc[input_df["0"].str.contains(".txt"), "0"].str.replace(".txt", "").str.replace("_", "/")
        input_df = input_df[["0", "title", "doi", "EID"]]
        input_df.to_excel(self.output_folder_path + "input_df_with_title_doi.xlsx")
        logger.info("input_df_with_title_doi.xlsx saved")
        
    def get_summary(self):
        # check if the file exists
        if Path(self.output_folder_path + "summary.csv").exists():
            logger.info("summary.csv already exists. Skipping this step.")
            return
        summary_df = self.input_df[["0", "2"]]
        summary_df['label_dict'] = summary_df.iloc[:,1]
        summary_df["label_dict"] = summary_df['label_dict'].apply(lambda x: ast.literal_eval(x))
        summary_df = summary_df.join(pd.json_normalize(summary_df["label_dict"]))
        summary_df["summary"] = summary_df["summary"].apply(lambda x: ' '.join(x))
        summary_df = summary_df[["0", "summary"]]
        # save the output
        summary_df.to_csv(self.output_folder_path + "summary.csv")
        logger.info("summary.csv saved")  

    def get_aspect(self):
        # check if the file exists
        if Path(self.output_folder_path + "aspect.csv").exists():
            logger.info("aspect.csv already exists. Skipping this step.")
            return
        aspect_df = self.input_df[["0", "2"]]
        aspect_df['label_dict'] = aspect_df.iloc[:,1]
        aspect_df["label_dict"] = aspect_df['label_dict'].apply(lambda x: ast.literal_eval(x))
        aspect_df = aspect_df.join(pd.json_normalize(aspect_df["label_dict"]))
        aspect_df = aspect_df[["0", "aspect"]]
        # save the output
        aspect_df.to_csv(self.output_folder_path + "aspect.csv")
        logger.info("aspect.csv saved")  
    
    def get_location(self):
        # define a function to extract location
        def extract_location(text):
            # remove "not mentioned", "not specified", "not applicable"
            text = text.lower()
            text = text.replace("not mentioned", "").replace("not specified", "").replace("not applicable", "")
            # create a geocoder object
            geolocator = Nominatim(user_agent="my-app")
            try:
                location = geolocator.geocode(text)
            except (requests.exceptions.ReadTimeout, GeocoderTimedOut, TypeError, GeocoderUnavailable):
                try:
                    location = geolocator.geocode(text.split(",")[0])
                except:
                    print("Got an error for ", text)
                    return None
            if location is not None:
                lat = location.latitude
                lon = location.longitude
                return lat, lon
            else:
                # try with only the country name
                location = geolocator.geocode(text.split(",")[0])
                if location is not None:
                    lat = location.latitude
                    lon = location.longitude
                    return lat, lon
                else:
                    print("Got an error for ", text)
                    return None
        
        # check if the file exists
        if Path(self.output_folder_path + "location.csv").exists():
            logger.info("location.csv already exists. Skipping this step.")
            return
        
        location_df = self.input_df[["0", "3"]] 
        location_df["label_dict"] = location_df.iloc[:,1].apply(lambda x: ast.literal_eval(x))
        location_df = location_df.join(pd.json_normalize(location_df["label_dict"]))
        # set the first column as index
        location_df.set_index("0", inplace=True)
        location_df = location_df["study_area"].explode().to_frame()
        # create a string of "Country, City" for each paper
        location_df["study_area"] = location_df["study_area"].apply(lambda x: ast.literal_eval(str(x)))
        location_df["study_area"] = location_df["study_area"].apply(lambda x: x["Country"] + ", " + x["City"] if x.get("City") is not None else x["Country"])
        location_df["study_area"] = location_df["study_area"].apply(lambda x: extract_location(str(x)))
        # save the output
        location_df.to_csv(self.output_folder_path + "location.csv")
        logger.info("location.csv saved")
    
    def get_extent(self):        
        # check if the file exists
        if Path(self.output_folder_path + "extent.csv").exists():
            logger.info("extent.csv already exists. Skipping this step.")
            return
        
        extent_df = self.input_df[["0", "3"]]
        extent_df["label_dict"] = extent_df.iloc[:,1].apply(lambda x: ast.literal_eval(x))
        extent_df = extent_df.join(pd.json_normalize(extent_df["label_dict"]))
        extent_df = extent_df[['0', 'extent']]
        # save the output
        extent_df.to_csv(self.output_folder_path + "extent.csv")  
        logger.info("extent.csv saved")
    
    def get_image_data_type(self):
        # Function to parse the string in each row
        def parse_string(row):
            try:
                # Try to parse the row with ast.literal_eval
                if row.startswith('{'):
                    # If the row is a dictionary, parse it and return the value of "image_data"
                    row_dict = ast.literal_eval(row)
                    return row_dict['image_data']
                else:
                    # If the row is a list, parse it directly
                    row_list = [ast.literal_eval(line.lstrip('- ')) for line in row.split('\n')]
                    return row_list
            except SyntaxError:
                try:
                    # Extract all complete inner lists
                    list_strings = re.findall(r'\[.*?\]', row)
                    # Use ast.literal_eval to convert the string representations into actual lists
                    # We use a try-except block to handle cases where the string representation cannot be converted into a list
                    list_objects = []
                    for ls in list_strings:
                        try:
                            list_objects.append(ast.literal_eval(ls))
                        except SyntaxError:
                            pass  # Ignore strings that cannot be converted into lists
                    # Remove duplicates by converting the list of lists into a list of tuples and then into a set
                    unique_list_objects = list(set(tuple(lo) for lo in list_objects))
                    # Convert the tuples back into lists
                    unique_list_objects = [list(ulo) for ulo in unique_list_objects]
                    return unique_list_objects

                except:
                    # If a SyntaxError occurs, add quotes around items in the list and try again
                    quoted_row = re.sub(r'\[([^]]*)\]', lambda m: str(m.group(1).split(', ')), row)
                    row_list = [ast.literal_eval(line.lstrip('- ')) for line in quoted_row.split('\n')]
                    return row_list
            except ValueError:
                return None

        logger.info("Extracting image_data_type")
        
        # check if the file exists
        if Path(self.output_folder_path + "image_data_type.csv").exists():
            logger.info("image_data_type.csv already exists. Skipping this step.")
            return
        
        image_data_type_df = self.input_df[["0", "4"]]
        image_data_type_df["label_dict"] = image_data_type_df.iloc[:,1].apply(lambda x: parse_string(x))
        # Explode the outer list vertically
        image_data_type_df = image_data_type_df.explode('label_dict')

        # Split the inner list into separate columns
        # Find rows where 'label_dict' is a float or None
        invalid_rows = image_data_type_df['label_dict'].apply(lambda x: isinstance(x, float) or x is None)

        # Handle these rows. Here, I'm just dropping these rows, but you might want to handle them differently.
        image_data_type_df = image_data_type_df[~invalid_rows]

        # Then you can convert the 'label_dict' column to a list and create your new DataFrame:
        image_data_type_df = pd.DataFrame(image_data_type_df['label_dict'].to_list(), index=image_data_type_df["0"])
        # only keep the first and 3 columns
        image_data_type_df = image_data_type_df.iloc[:,0:3]

        # save the output
        image_data_type_df.to_csv(self.output_folder_path + "image_data_type.csv")  
        logger.info("image_data_type.csv saved") 
    
    def get_subjective_data_type(self):
        # Function to parse the string in each row
        def parse_string(row):
            try:
                # Try to parse the row with ast.literal_eval
                if row.startswith('{'):
                    # If the row is a dictionary, parse it and return the value of "perception_data"
                    row_dict = ast.literal_eval(row)
                    return row_dict['perception_data']
                else:
                    # If the row is a list, parse it directly
                    row_list = [ast.literal_eval(line.lstrip('- ')) for line in row.split('\n')]
                    return row_list
            except SyntaxError:
                try:
                    # Extract all complete inner lists
                    list_strings = re.findall(r'\[.*?\]', row)
                    # Use ast.literal_eval to convert the string representations into actual lists
                    # We use a try-except block to handle cases where the string representation cannot be converted into a list
                    list_objects = []
                    for ls in list_strings:
                        try:
                            list_objects.append(ast.literal_eval(ls))
                        except SyntaxError:
                            pass  # Ignore strings that cannot be converted into lists
                    # Remove duplicates by converting the list of lists into a list of tuples and then into a set
                    unique_list_objects = list(set(tuple(lo) for lo in list_objects))
                    # Convert the tuples back into lists
                    unique_list_objects = [list(ulo) for ulo in unique_list_objects]
                    return unique_list_objects

                except:
                    # If a SyntaxError occurs, add quotes around items in the list and try again
                    quoted_row = re.sub(r'\[([^]]*)\]', lambda m: str(m.group(1).split(', ')), row)
                    row_list = [ast.literal_eval(line.lstrip('- ')) for line in quoted_row.split('\n')]
                    return row_list
            except ValueError:
                return None

        logger.info("Extracting perception_data_type")
        
        # check if the file exists
        if Path(self.output_folder_path + "perception_data_type.csv").exists():
            logger.info("perception_data_type.csv already exists. Skipping this step.")
            return
        
        perception_data_type_df = self.input_df[["0", "5"]]
        perception_data_type_df["label_dict"] = perception_data_type_df.iloc[:,1].apply(lambda x: parse_string(x))
        # Explode the outer list vertically
        perception_data_type_df = perception_data_type_df.explode('label_dict')

        # Split the inner list into separate columns
        # Find rows where 'label_dict' is a float or None
        invalid_rows = perception_data_type_df['label_dict'].apply(lambda x: isinstance(x, float) or x is None)

        # Handle these rows. Here, I'm just dropping these rows, but you might want to handle them differently.
        perception_data_type_df = perception_data_type_df[~invalid_rows]

        # Then you can convert the 'label_dict' column to a list and create your new DataFrame:
        perception_data_type_df = pd.DataFrame(perception_data_type_df['label_dict'].to_list(), index=perception_data_type_df["0"])
        # only keep the first and 3 columns
        perception_data_type_df = perception_data_type_df.iloc[:,0:3]

        # save the output
        perception_data_type_df.to_csv(self.output_folder_path + "perception_data_type.csv")  
        logger.info("perception_data_type.csv saved") 
    
    def get_other_sensory_data(self):
        def categorize_text(text):
            sound = "sound|acoustic|auditory|audio|noise|volume|loud|pitch|frequency|pitch|tone"
            smell = "smell|odor|olfactory"
            tactile = "touch|tactile|kinesthetic|kinesthesis|kinesthetic sense|kinesthesis|vibration|vibratory|texture"

            sound_pattern = re.compile(sound, re.IGNORECASE)
            smell_pattern = re.compile(smell, re.IGNORECASE)
            tactile_pattern = re.compile(tactile, re.IGNORECASE)
            
            if sound_pattern.search(text):
                return "sound"
            elif smell_pattern.search(text):
                return "smell"
            elif tactile_pattern.search(text):
                return "tactile"
            else:
                return "None"
        
        # function to check if
        # 1. the value is dict. if not return None
        # 2. if so, loop through the keys and check the value. If "not applicable", return None
        # 3. if not, pass the value to categorize_text and return the result
        def check_dict_value(dict_value):
            result_list = []
            if isinstance(dict_value, dict):
                for key, value in dict_value.items():
                    if value.lower() == "not applicable":
                        return None
                    else:
                        result_list.append(categorize_text(key))
            else:
                return None
            return result_list
        
        # check if the file exists
        if Path(self.output_folder_path + "other_sensory_data.csv").exists():
            logger.info("other_sensory_data.csv already exists. Skipping this step.")
            return
        
        other_sensory_data_df = self.input_df[["0", "6"]]
        other_sensory_data_df["label_dict"] = other_sensory_data_df.iloc[:,1].apply(lambda x: ast.literal_eval(str(x)))
        other_sensory_data_df = other_sensory_data_df.join(pd.json_normalize(other_sensory_data_df["label_dict"], max_level=0))
        other_sensory_data_df["label_dict"] = other_sensory_data_df["label_dict"].apply(lambda x: check_dict_value(x["other_data_sources"]))
        # explode the list
        # drop "other_data_sources" column
        other_sensory_data_df.set_index("0", inplace=True)
        other_sensory_data_df = other_sensory_data_df["label_dict"].explode()
        # save the output
        other_sensory_data_df.to_csv(self.output_folder_path + "other_sensory_data.csv")  
        logger.info("other_sensory_data.csv saved") 
        pass
    
    def get_type_of_research(self):
        # define a function to convert literal string to dict by fixing the format
        def convert_to_dict(text):
            # Define replacements for the problematic parts of the strings
            replacements = {
                '"Place Pulse 2.0"': 'Place Pulse 2_0',
                'SYNTHIA': 'SYNTHIA_dataset'
            }
            # Loop through the replacements and replace them in the string
            for key, value in replacements.items():
                text = text.replace(key, value)
            # check if the text starts and ends with curly brackets
            if not text.startswith("{"):
                text = "{" + text
            if not text.endswith("}"):
                text = text + "}"
            # convert to dict
            return ast.literal_eval(text)
        
        # check if the file exists
        if Path(self.output_folder_path + "type_of_research.csv").exists():
            logger.info("type_of_research.csv already exists. Skipping this step.")
            return
        
        type_of_research_df = self.input_df[["0", "7"]]
        type_of_research_df['label_dict'] = type_of_research_df.iloc[:,1]
        type_of_research_df["label_dict"] = type_of_research_df['label_dict'].apply(lambda x: convert_to_dict(x))
        type_of_research_df = type_of_research_df.join(pd.json_normalize(type_of_research_df["label_dict"]))
        type_of_research_df["method"] = type_of_research_df["method"].apply(lambda x: ' '.join(x))
        type_of_research_df = type_of_research_df[["0", "research_type", "method"]]
        # save the output
        type_of_research_df.to_csv(self.output_folder_path + "type_of_research.csv")  
        logger.info("type_of_research.csv saved") 
        pass
    
    def get_type_of_research_detail(self):
        logger.info("Extracting type_of_research_detail")
        
        # check if the file exists
        if Path(self.output_folder_path + "type_of_research_detail.csv").exists():
            logger.info("type_of_research_detail.csv already exists. Skipping this step.")
            return
        
        type_of_research_detail_df = self.input_df[["0", "8"]]
        type_of_research_detail_df["label_dict"] = type_of_research_detail_df.iloc[:,1].apply(lambda x: ast.literal_eval(x))
        type_of_research_detail_df = type_of_research_detail_df.join(pd.json_normalize(type_of_research_detail_df["label_dict"]))
        type_of_research_detail_df.set_index("0", inplace=True)
        type_of_research_detail_df = type_of_research_detail_df["research_types"].explode().to_frame()
        # save the output
        type_of_research_detail_df.to_csv(self.output_folder_path + "type_of_research_detail.csv")  
        logger.info("type_of_research_detail.csv saved") 
        pass

    def get_cv_model(self):
        # add {'cv': } around the string without it
        def add_cv(x):
            if "cv" not in x:
                return "{'cv_models': " + x + "}"
            else:
                return x

        def add_brackets_to_string(s):
            # Locate the first occurrence of ':'
            index = s.find(':')
            if index == -1:
                # If there's no colon, return the original string (This should not happen in your example)
                return s
            # Add the opening bracket after the colon and space
            s = s[:index + 2] + "[" + s[index + 2:]
            # Add the closing bracket just before the last }
            # check if the last character is a }
            if s[-1] == '}':
                # If it is, add the bracket before it
                s = s[:-1] + "]" + s[-1:]
            else:
                s = None
            return s

        def ast_literal_eval(x):
            try:
                return ast.literal_eval(x)
            except:
                x = add_brackets_to_string(x)
                if (x != "{'cv_models': [not applicable]}") & (x != None):
                    return ast.literal_eval(x)
                else:
                    return None
        
        logger.info("Extracting cv_model_name")
        
        # check if the file exists
        if Path(self.output_folder_path + "cv_model.csv").exists():
            logger.info("cv_model.csv already exists. Skipping this step.")
            return
        
        cv_model_df = self.input_df[["0", "9"]]
        cv_model_df["label_dict"] = cv_model_df.iloc[:, 1].apply(lambda x: add_cv(x))
        cv_model_df = cv_model_df[cv_model_df["label_dict"].notnull()]
        cv_model_df["label_dict"] = cv_model_df['label_dict'].apply(lambda x: ast_literal_eval(x))
        cv_model_df = cv_model_df.join(pd.json_normalize(cv_model_df["label_dict"]))
        cv_model_df.set_index("0", inplace=True)
        cv_model_df = cv_model_df["cv_models"].explode().to_frame().reset_index()
        # Filter rows where the list has exactly 3 elements
        cv_model_df = cv_model_df.dropna(subset=['cv_models'])
        cv_model_df = cv_model_df[cv_model_df['cv_models'].apply(len) == 3]
        # Explode the list column into multiple columns
        cv_model_df = pd.DataFrame(cv_model_df['cv_models'].to_list(), index=cv_model_df["0"])
        
        # save the output
        cv_model_df.to_csv(self.output_folder_path + "cv_model.csv")  
        logger.info("cv_model.csv saved") 
        pass

    def get_code_availability(self):
        logger.info("Extracting code_availability")
        
        # check if the file exists
        if Path(self.output_folder_path + "code_availability.csv").exists():
            logger.info("code_availability.csv already exists. Skipping this step.")
            return
        
        code_availability_df = self.input_df[["0", "10"]]
        code_availability_df = code_availability_df[code_availability_df["10"] != 'not mentioned']
        code_availability_df["label_dict"] = code_availability_df.iloc[:,1].apply(lambda x: ast.literal_eval(x))
        code_availability_df = code_availability_df.join(pd.json_normalize(code_availability_df["label_dict"]))
        code_availability_df = code_availability_df[['0', 'code_availability']]
        # save the output
        code_availability_df.to_csv(self.output_folder_path + "code_availability.csv")  
        logger.info("code_availability.csv saved") 
        pass
    
    def get_data_availability(self):
        def extract_data_availability(text):
            return text.replace(".", "").strip().lower()
        
        logger.info("Extracting data_availability")
        
        # check if the file exists
        if Path(self.output_folder_path + "data_availability.csv").exists():
            logger.info("data_availability.csv already exists. Skipping this step.")
            return
        
        data_availability_df = self.input_df[["0", "11"]]
        data_availability_df = data_availability_df[data_availability_df["11"] != 'not mentioned']
        data_availability_df["label_dict"] = data_availability_df.iloc[:,1].apply(lambda x: ast.literal_eval(x))
        data_availability_df = data_availability_df.join(pd.json_normalize(data_availability_df["label_dict"]))
        data_availability_df = data_availability_df[['0', 'data_availability']]
        # save the output
        data_availability_df.to_csv(self.output_folder_path + "data_availability.csv")  
        logger.info("data_availability.csv saved") 
        pass
    
    def get_irb(self):
        logger.info("Extracting irb")
        
        # check if the file exists
        if Path(self.output_folder_path + "irb.csv").exists():
            logger.info("irb.csv already exists. Skipping this step.")
            return
        
        irb_df = self.input_df[["0", "12"]]
        irb_df = irb_df[irb_df["12"] != 'not mentioned']
        irb_df["label_dict"] = irb_df.iloc[:,1].apply(lambda x: ast.literal_eval(x))
        irb_df = irb_df.join(pd.json_normalize(irb_df["label_dict"]))
        irb_df = irb_df[['0', 'irb_approval']]
        # save the output
        irb_df.to_csv(self.output_folder_path + "irb.csv")  
        logger.info("irb.csv saved") 
        pass

    def get_limitation_future_opportunity(self):
        def check_and_fix(x):
            # check if x starts and ends with {}
            if not x.startswith("{"):
                return "{" + x
            if not x.endswith("}"):
                return x + "}"
            return x
                
        def ast_literal_eval(x):
            try:
                return ast.literal_eval(x)
            except:
                x = check_and_fix(x)
                return ast.literal_eval(x)      
        logger.info("Extracting limitation_future_opportunity")
        
        # check if the file exists
        if Path(self.output_folder_path + "limitation_future_opportunity.csv").exists():
            logger.info("limitation_future_opportunity.csv already exists. Skipping this step.")
            return
        
        limitation_future_opportunity_df = self.input_df[["0", "13"]]
        limitation_future_opportunity_df['label_dict'] = limitation_future_opportunity_df.iloc[:,1]
        limitation_future_opportunity_df["label_dict"] = limitation_future_opportunity_df['label_dict'].apply(lambda x: ast_literal_eval(x))
        limitation_future_opportunity_df = limitation_future_opportunity_df.join(pd.json_normalize(limitation_future_opportunity_df["label_dict"]))
        limitation_future_opportunity_df["limitations"] = limitation_future_opportunity_df["limitations"].apply(lambda x: ' '.join(x))
        limitation_future_opportunity_df["future_research_opportunities"] = limitation_future_opportunity_df["future_research_opportunities"].apply(lambda x: ' '.join(x))
        limitation_future_opportunity_df = limitation_future_opportunity_df[["0", "limitations", "future_research_opportunities"]]
        # save the output
        limitation_future_opportunity_df.to_csv(self.output_folder_path + "limitation_future_opportunity.csv")  
        logger.info("limitation_future_opportunity.csv saved") 
        pass 

    # quick and dirty functions for the 3rd round of coding
    def _get_aspect_3rd_round(self):
        # check if the file exists
        if Path(self.output_folder_path + "aspect.csv").exists():
            logger.info("aspect.csv already exists. Skipping this step.")
            return
        aspect_df = self.input_df[["0", "1"]]
        aspect_df['label_dict'] = aspect_df.iloc[:,1]
        aspect_df["label_dict"] = aspect_df['label_dict'].apply(lambda x: ast.literal_eval(x))
        aspect_df = aspect_df.join(pd.json_normalize(aspect_df["label_dict"]))
        aspect_df = aspect_df[["0", "aspect"]]
        # save the output
        aspect_df.to_csv(self.output_folder_path + "aspect.csv")
        logger.info("aspect.csv saved")  
    
        # quick and dirty functions for the 3rd round of coding
    def _get_perception_3rd_round(self):
        # check if the file exists
        if Path(self.output_folder_path + "perception.csv").exists():
            logger.info("perception.csv already exists. Skipping this step.")
            return
        perception_df = self.input_df[["0", "2"]]
        perception_df['label_dict'] = perception_df.iloc[:,1]
        perception_df["label_dict"] = perception_df['label_dict'].apply(lambda x: ast.literal_eval(x))
        perception_df = perception_df.join(pd.json_normalize(perception_df["label_dict"]))
        perception_df = perception_df[["0", "perception"]]
        # save the output
        perception_df.to_csv(self.output_folder_path + "perception.csv")
        logger.info("perception.csv saved")  