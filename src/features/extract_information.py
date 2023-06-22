import pandas as pd
import polars as pl
from geopy.geocoders import Nominatim
from geotext import GeoText
import re
from pathlib import Path
import spacy
import ast

from util.log_util import get_logger

# initialize logger
logger = get_logger(__name__)

class InfoExtracter:
    def __init__(self, input_csv_filepath: str, output_folder_path: str):
        input_json_path = input_csv_filepath.replace(".csv", ".json")
        self.input_df = pl.read_ndjson(input_json_path)
        # get the column names as a list
        # rename columns with 0, 1, 2, ...
        new_column_names = [str(i) for i in range(len(self.input_df.columns))]
        self.input_df.columns = new_column_names
        self.output_folder_path = output_folder_path
        
    def get_summary(self):
        def extract_summary(text):
            pattern = r'\d+\. .*'  # matches lines starting with a number followed by a period
            matches = re.findall(pattern, text)
            return " ".join(matches).replace("\n", " ")
            
        logger.info("Extracting summary")
        
        # check if the file exists
        if Path(self.output_folder_path + "summary.csv").exists():
            logger.info("summary.csv already exists. Skipping this step.")
            return
        
        summary_df = (self.input_df.with_columns([
            pl.col("0").alias("DOI"),
            pl.col("1")
                .apply(lambda x: extract_summary(x))
                .alias("summary")
            ])
            .select(["DOI", "summary"]))
        # save the output
        summary_df.write_csv(self.output_folder_path + "summary.csv")
        logger.info("summary.csv saved")  

    def get_aspect(self):
        def extract_aspect(text):
            # Regular expression pattern to match any words after "Aspect:"
            pattern = r"Aspect:\s*(.*)"
            # Extract words after "Aspect:"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                words_after_aspect = match.group(1)
                return words_after_aspect.lower().replace(".", "").strip()
            else:
                return "None"
            
        logger.info("Extracting aspect")
        
        # check if the file exists
        if Path(self.output_folder_path + "aspect.csv").exists():
            logger.info("aspect.csv already exists. Skipping this step.")
            return
        
        aspect_df = (self.input_df.with_columns([
            pl.col("0").alias("DOI"),
            pl.col("1")
                .apply(lambda x: extract_aspect(x))
                .alias("aspect")
            ])
            .select(["DOI", "aspect"]))
        # save the output
        aspect_df.write_csv(self.output_folder_path + "aspect.csv")
        logger.info("aspect.csv saved") 
    
    def get_location(self):
        # define a function to extract location
        def extract_location(text):
            # create a list of cities and countries
            city_country_list = []
            places = GeoText(text)
            cities = places.cities
            countries = places.countries
            if len(countries) > 0:
                for country in countries:
                    # get cities in the country
                    _cities = GeoText(text, country).cities
                    # store in city_country_list
                    if len(_cities) > 0:
                        city_country_list.extend([_city + ", " + country for _city in _cities])
                    else:
                        city_country_list.append(country)
                    # remove cities from cities list
                    cities = [x for x in cities if x not in _cities]        
            if len(cities) > 0:
                city_country_list.extend(cities)
            # create a geocoder object
            geolocator = Nominatim(user_agent="my-app")
            
            # loop through cities and get coordinates
            coordinates_list = []
            for city_country in city_country_list:
                # geocode the city
                location = geolocator.geocode(city_country)
                # get the latitude and longitude
                if location is not None:
                    lat = location.latitude
                    lon = location.longitude
                    # store in city_country_list
                    coordinates_list.append(str(lat) + ", " + str(lon))
                else:
                    print("Got an error for ", city_country)    
            if len(coordinates_list) == 0:
                coordinates_list.append("None")
            return coordinates_list
        
        logger.info("Extracting location")
        
        # check if the file exists
        if Path(self.output_folder_path + "location.csv").exists():
            logger.info("location.csv already exists. Skipping this step.")
            return
        
        location_df = (self.input_df.with_columns([
            pl.col("0").alias("DOI"),
            pl.col("2")
                .apply(lambda x: extract_location(x))
                .alias("location")
            ])
            .explode("location")
            .select(["DOI", "location"])
            .filter(pl.col("location") != "None")
            .with_row_count('id')
            .with_column(pl.col("location").str.split(",")
                .alias("split_str"))
            .explode("split_str")
            .with_column(
                ("string_" + pl.arange(0, pl.count()).cast(pl.Utf8).str.zfill(2))
                .over("id")
                .alias("col_nm")
                .str.replace(r"string_00", "longitude")
                .str.replace(r"string_01", "latitude"))
            .pivot(
                index=['id', "DOI", 'location'],
                values='split_str',
                columns='col_nm')
            .select(["DOI", "longitude", "latitude"])
        )
        # save the output
        location_df.write_csv(self.output_folder_path + "location.csv")
        logger.info("location.csv saved")
    
    def get_extent(self):
        def extract_extent(text):
            # Regular expression pattern to match the string after "Extent/scale of the study area:"
            pattern = r"Extent/scale of the study area:\s*(.*-level)"

            # Extract the matched string
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extent_string = match.group(1)
                return extent_string.lower().strip()
            else:
                return "None"
        
        logger.info("Extracting extent")
        
        # check if the file exists
        if Path(self.output_folder_path + "extent.csv").exists():
            logger.info("extent.csv already exists. Skipping this step.")
            return
        
        extent_df = (self.input_df.with_columns([
            pl.col("0").alias("DOI"),
            pl.col("2")
                .apply(lambda x: extract_extent(x))
                .alias("extent")
            ])
            .select(["DOI", "extent"]))
        # save the output
        extent_df.write_csv(self.output_folder_path + "extent.csv")  
        logger.info("extent.csv saved")
    
    def get_image_data_type(self):
        def extract_image_data_type(text):
            nlp = spacy.load("en_core_web_sm")
            # final list of image data types
            final_list = []
            text_list = text.split("\n")
            for text_line in text_list:
                type_source_size = text_line.split(":")
                # if the length of the list is 1, then there's likely no information about type, source and size
                if len(type_source_size) == 1:
                    continue
                else:
                    # check if the second element contains "not"
                    # check if there're more than one "not" in the text_line
                    if text_line.lower().count("not") > 1:
                        continue
                    if "not" not in type_source_size[1].strip().lower():
                        # image type
                        image_data_type = type_source_size[0].strip()
                    else:
                        continue
                # remove the digits and the period at the start of the string
                pattern = "^\d+\.\s" # pattern to match one or more digits followed by a period and a space at the start of the string
                replacement = ""
                image_data_type = re.sub(pattern, replacement, image_data_type).lower() 
                final_list.append(image_data_type)
            return final_list
        
        def str_to_list(text):
            return ast.literal_eval(text)
        
        logger.info("Extracting image_data_type")
        
        # check if the file exists
        if Path(self.output_folder_path + "image_data_type.csv").exists():
            logger.info("image_data_type.csv already exists. Skipping this step.")
            return
        
        image_data_type_df = (self.input_df.with_columns([
            pl.col("0").alias("DOI"),
            pl.col("3")
                .apply(lambda x: extract_image_data_type(x))
                .alias("image_data_type")
            ])
            .explode("image_data_type")
            .select(["DOI", "image_data_type"]))
        # save the output
        image_data_type_df.write_csv(self.output_folder_path + "image_data_type.csv")  
        logger.info("image_data_type.csv saved") 
    
    # # def get_image_data_source(self):
    # #     def extract_image_data_source(text):
    # #         # final list of image data types
    # #         final_list = []
    # #         text_list = text.split("\n")
    # #         for text_line in text_list:
    # #             type_source_size = text_line.split(":")
    # #             # if the length of the list is 1, then there's likely no information about type, source and size
    # #             if len(type_source_size) == 1:
    # #                 continue
    # #             elif len(type_source_size) == 2:
    # #                 # check if the second element contains "not"
    # #                 if "not" not in type_source_size[1].strip().lower():
    # #                     image_data_source = type_source_size[1].strip()
    # #                 else:
    # #                     continue
    # #             else:
    # #                 # check if there're more than one "not" in the text_line
    # #                 if text.lower().count("not") > 1:
    # #                     continue
    # #                 else:
    # #                     image_data_source = type_source_size[1].strip()
    # #             final_list.append(image_data_source)
    # #         return final_list
        
    # #     logger.info("Extracting image_data_source")
        
    # #     # check if the file exists
    # #     if Path(self.output_folder_path + "image_data_source.csv").exists():
    # #         logger.info("image_data_source.csv already exists. Skipping this step.")
    # #         return
        
    # #     image_data_source_df = (self.input_df.with_columns([
    # #         pl.col("0").alias("DOI"),
    # #         pl.col("3")
    # #             .apply(lambda x: extract_image_data_source(x))
    # #             .alias("image_data_source")
    # #         ])
    # #         .explode("image_data_source")
    # #         .select(["DOI", "image_data_source"]))
    # #     # save the output
    # #     image_data_source_df.write_csv(self.output_folder_path + "image_data_source.csv")  
    # #     logger.info("image_data_source.csv saved")  
    # #     pass
    
    # # def get_image_data_size(self):
    #     def extract_image_data_size(text):
    #         # final list of image data types
    #         final_list = []
    #         text_list = text.split("\n")
    #         for text_line in text_list:
    #             type_size_size = text_line.split(":")
    #             # if the length of the list is 1, then there's likely no information about type, size and size
    #             if len(type_size_size) == 1:
    #                 continue
    #             elif len(type_size_size) == 2:
    #                 # check if the second element contains "not"
    #                 if "not" not in type_size_size[1].strip().lower():
    #                     # get entity names from the text
    #                     image_data_size = type_size_size[1].strip()
    #                 else:
    #                     continue
    #             else:
    #                 # check if there're more than one "not" in the text_line
    #                 if text.lower().count("not") > 1:
    #                     continue
    #                 else:
    #                     image_data_size = type_size_size[0].strip()
    #             final_list.append(image_data_size)
    #         return final_list
        
    #     logger.info("Extracting image_data_size")
        
    #     # check if the file exists
    #     if Path(self.output_folder_path + "image_data_size.csv").exists():
    #         logger.info("image_data_size.csv already exists. Skipping this step.")
    #         return
        
    #     image_data_size_df = (self.input_df.with_columns([
    #         pl.col("0").alias("DOI"),
    #         pl.col("3")
    #             .apply(lambda x: extract_image_data_size(x))
    #             .alias("image_data_size")
    #         ])
    #         .explode("image_data_size")
    #         .select(["DOI", "image_data_size"]))
    #     # save the output
    #     image_data_size_df.write_csv(self.output_folder_path + "image_data_size.csv")  
    #     logger.info("image_data_size.csv saved")  
    #     pass
    
    def get_subjective_data_type(self):
        def extract_subjective_data_type(text):
            # final list of subjective data types
            final_list = []
            text_list = text.split("\n")
            for text_line in text_list:
                type_source_size = text_line.split(":")
                # if the length of the list is 1, then there's likely no information about type, source and size
                if len(type_source_size) == 1:
                    continue
                else:
                    # check if the second element contains "not"
                    # check if there're more than one "not" in the text_line
                    if text_line.lower().count("not") > 1:
                        continue
                    if "not" not in type_source_size[1].strip().lower():
                        # subjective type
                        subjective_data_type = type_source_size[0].strip()
                        # this is a quick fix for the case where the subjective data type is "subjective perception data"
                        if subjective_data_type.lower() == "subjective perception data":
                            subjective_data_type = type_source_size[1].strip() 
                    else:
                        continue
                # remove the digits and the period at the start of the string
                pattern = "^\d+\.\s" # pattern to match one or more digits followed by a period and a space at the start of the string
                replacement = ""
                subjective_data_type = re.sub(pattern, replacement, subjective_data_type).lower() 
                final_list.append(subjective_data_type)
            return final_list
        
        logger.info("Extracting subjective_data_type")
        
        # check if the file exists
        if Path(self.output_folder_path + "subjective_data_type.csv").exists():
            logger.info("subjective_data_type.csv already exists. Skipping this step.")
            return
        
        subjective_data_type_df = (self.input_df.with_columns([
            pl.col("0").alias("DOI"),
            pl.col("4")
                .apply(lambda x: extract_subjective_data_type(x))
                .alias("subjective_data_type")
            ])
            .explode("subjective_data_type")
            .select(["DOI", "subjective_data_type"]))
        # save the output
        subjective_data_type_df.write_csv(self.output_folder_path + "subjective_data_type.csv")  
        logger.info("subjective_data_type.csv saved") 
        pass
    
    def get_subjective_data_source(self):
        def extract_subjective_data_source(text):
            # final list of subjective data sources
            final_list = []
            text_list = text.split("\n")
            for text_line in text_list:
                type_source_size = text_line.split(":")
                # if the length of the list is 1, then there's likely no information about source, source and size
                if len(type_source_size) == 1:
                    continue
                else:
                    # check if the second element contains "not"
                    # check if there're more than one "not" in the text_line
                    if text_line.lower().count("not") > 1:
                        continue
                    if "not" not in type_source_size[1].strip().lower():
                        # subjective source
                        subjective_data_source = type_source_size[1].strip()
                    else:
                        continue
                final_list.append(subjective_data_source)
            return final_list
        
        logger.info("Extracting subjective_data_source")
        
        # check if the file exists
        if Path(self.output_folder_path + "subjective_data_source.csv").exists():
            logger.info("subjective_data_source.csv already exists. Skipping this step.")
            return
        
        subjective_data_source_df = (self.input_df.with_columns([
            pl.col("0").alias("DOI"),
            pl.col("4")
                .apply(lambda x: extract_subjective_data_source(x))
                .alias("subjective_data_source")
            ])
            .explode("subjective_data_source")
            .select(["DOI", "subjective_data_source"]))
        # save the output
        subjective_data_source_df.write_csv(self.output_folder_path + "subjective_data_source.csv")  
        logger.info("subjective_data_source.csv saved") 
        pass

    def get_subjective_data_size(self):
        def extract_subjective_data_size(text):
            # final list of subjective data sizes
            final_list = []
            text_list = text.split("\n")
            for text_line in text_list:
                type_source_size = text_line.split(":")
                # if the length of the list is 1, then there's likely no information about size, size and size
                if len(type_source_size) == 1:
                    continue
                else:
                    # check if the second element contains "not"
                    # check if there're more than one "not" in the text_line
                    if text_line.lower().count("not") > 1:
                        subjective_data_size = "None"
                    if "not" not in type_source_size[1].strip().lower():
                        # subjective size
                        pattern = r'(\d{1,3}(,\d{3})*|\d+)\s*(?:\D*\s*)?(participant|respondent)(s)?'
                        matches = re.findall(pattern, type_source_size[len(type_source_size)-1])
                        match_list = [match[0].replace(',', '') for match in matches]
                        if len(match_list) > 0:
                            subjective_data_size = match_list[0]
                        else:
                            subjective_data_size = "None"
                    else:
                        subjective_data_size = "None"
                final_list.append(subjective_data_size)
            return final_list
        
        logger.info("Extracting subjective_data_size")
        
        # check if the file exists
        if Path(self.output_folder_path + "subjective_data_size.csv").exists():
            logger.info("subjective_data_size.csv already exists. Skipping this step.")
            return
        
        subjective_data_size_df = (self.input_df.with_columns([
            pl.col("0").alias("DOI"),
            pl.col("4")
                .apply(lambda x: extract_subjective_data_size(x))
                .alias("subjective_data_size")
            ])
            .explode("subjective_data_size")
            .select(["DOI", "subjective_data_size"])
            .filter(pl.col("subjective_data_size") != "None"))
        # save the output
        subjective_data_size_df.write_csv(self.output_folder_path + "subjective_data_size.csv")  
        logger.info("subjective_data_size.csv saved") 
        pass
    
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

        def extract_other_sensory_data(text):
            # final list of other sensory data
            final_list = []
            text_list = text.split("\n")
            for text_line in text_list:
                # if the length of the list is 1, then there's likely no information about size, size and size
                if "not" in text_line.lower():
                    continue
                else:
                    # categorize the text
                    category = categorize_text(text_line)
                final_list.append(category)
            return final_list
        
        logger.info("Extracting other_sensory_data")
        
        # check if the file exists
        if Path(self.output_folder_path + "other_sensory_data.csv").exists():
            logger.info("other_sensory_data.csv already exists. Skipping this step.")
            return
        
        other_sensory_data_df = (self.input_df.with_columns([
            pl.col("0").alias("DOI"),
            pl.col("5")
                .apply(lambda x: extract_other_sensory_data(x))
                .alias("other_sensory_data")
            ])
            .explode("other_sensory_data")
            .select(["DOI", "other_sensory_data"]))
        # save the output
        other_sensory_data_df.write_csv(self.output_folder_path + "other_sensory_data.csv")  
        logger.info("other_sensory_data.csv saved") 
        pass
    
    def get_type_of_research(self):
        def extract_type_of_research(text):
            pattern = r"Type of research:\s*(Quantitative|Qualitative)"
            match = re.search(pattern, text)
            if match is None:
                return "None"
            else:
                return match.group(1)
        
        logger.info("Extracting type_of_research")
        
        # check if the file exists
        if Path(self.output_folder_path + "type_of_research.csv").exists():
            logger.info("type_of_research.csv already exists. Skipping this step.")
            return
        
        type_of_research_df = (self.input_df.with_columns([
            pl.col("0").alias("DOI"),
            pl.col("6")
                .apply(lambda x: extract_type_of_research(x))
                .alias("type_of_research")
            ])
            .select(["DOI", "type_of_research"])
            .filter(pl.col("type_of_research") != "None"))
        # save the output
        type_of_research_df.write_csv(self.output_folder_path + "type_of_research.csv")  
        logger.info("type_of_research.csv saved") 
        pass
    
    def get_type_of_research_detail(self):
        def categorize_text(text):
            regression = re.compile("regression", re.IGNORECASE)
            model_development = re.compile("model development", re.IGNORECASE)
            index_construction = re.compile("index construction", re.IGNORECASE)
            exploratory_analysis = re.compile("exploratory analysis", re.IGNORECASE)
            others = re.compile("others", re.IGNORECASE)

            if regression.search(text):
                return "regression"
            elif model_development.search(text):
                return "model development"
            elif index_construction.search(text):
                return "index construction"
            elif exploratory_analysis.search(text):
                return "exploratory analysis"
            elif others.search(text):
                return "others"
            else:
                return "None"

        def extract_type_of_research_detail(text):
            # final list of other sensory data
            final_list = []
            text_list = text.split("\n")
            for text_line in text_list:
                # if the length of the list is 1, then there's likely no information about size, size and size
                if "not" in text_line.lower():
                    continue
                else:
                    # categorize the text
                    category = categorize_text(text_line)
                final_list.append(category)
            return final_list
        
        logger.info("Extracting type_of_research_detail")
        
        # check if the file exists
        if Path(self.output_folder_path + "type_of_research_detail.csv").exists():
            logger.info("type_of_research_detail.csv already exists. Skipping this step.")
            return
        
        type_of_research_detail_df = (self.input_df.with_columns([
            pl.col("0").alias("DOI"),
            pl.col("7")
                .apply(lambda x: extract_type_of_research_detail(x))
                .alias("type_of_research_detail")
            ])
            .explode("type_of_research_detail")
            .select(["DOI", "type_of_research_detail"])
            .filter(pl.col("type_of_research_detail") != "None"))
        # save the output
        type_of_research_detail_df.write_csv(self.output_folder_path + "type_of_research_detail.csv")  
        logger.info("type_of_research_detail.csv saved") 
        pass

    def get_cv_model_name(self):
        def extract_cv_model_name(text):
            # final list of cv_model_name
            final_list = []
            text_list = text.split("\n")
            for text_line in text_list:
                type_source_size = text_line.split(":")
                # if the length of the list is 1, then there's likely no information about type, source and size
                if len(type_source_size) == 1:
                    continue
                else:
                    # check if the second element contains "not"
                    # check if there're more than one "not" in the text_line
                    if text_line.lower().count("not") > 1:
                        continue
                    if "not" not in type_source_size[1].strip().lower():
                        # subjective type
                        cv_model_name = type_source_size[0].strip()
                    else:
                        continue
                # remove the digits and the period at the start of the string
                pattern = "^\d+\.\s" # pattern to match one or more digits followed by a period and a space at the start of the string
                replacement = ""
                cv_model_name = re.sub(pattern, replacement, cv_model_name).lower() 
                final_list.append(cv_model_name)
            return final_list
        
        logger.info("Extracting cv_model_name")
        
        # check if the file exists
        if Path(self.output_folder_path + "cv_model_name.csv").exists():
            logger.info("cv_model_name.csv already exists. Skipping this step.")
            return
        
        cv_model_name_df = (self.input_df.with_columns([
            pl.col("0").alias("DOI"),
            pl.col("8")
                .apply(lambda x: extract_cv_model_name(x))
                .alias("cv_model_name")
            ])
            .explode("cv_model_name")
            .select(["DOI", "cv_model_name"]))
        # save the output
        cv_model_name_df.write_csv(self.output_folder_path + "cv_model_name.csv")  
        logger.info("cv_model_name.csv saved") 
        pass
    
    def get_cv_model_purpose(self):
        def extract_cv_model_purpose(text):
            # final list of cv_model_purpose
            final_list = []
            text_list = text.split("\n")
            for text_line in text_list:
                type_source_size = text_line.split(":")
                # if the length of the list is 1, then there's likely no information about source, source and size
                if len(type_source_size) == 1:
                    continue
                else:
                    # check if the second element contains "not"
                    # check if there're more than one "not" in the text_line
                    if text_line.lower().count("not") > 1:
                        continue
                    if "not" not in type_source_size[1].strip().lower():
                        # subjective source
                        cv_model_purpose = type_source_size[1].strip().lower()
                    else:
                        continue
                final_list.append(cv_model_purpose.lower())
            return final_list
        
        logger.info("Extracting cv_model_purpose")
        
        # check if the file exists
        if Path(self.output_folder_path + "cv_model_purpose.csv").exists():
            logger.info("cv_model_purpose.csv already exists. Skipping this step.")
            return
        
        cv_model_purpose_df = (self.input_df.with_columns([
            pl.col("0").alias("DOI"),
            pl.col("8")
                .apply(lambda x: extract_cv_model_purpose(x))
                .alias("cv_model_purpose")
            ])
            .explode("cv_model_purpose")
            .select(["DOI", "cv_model_purpose"]))
        # save the output
        cv_model_purpose_df.write_csv(self.output_folder_path + "cv_model_purpose.csv")  
        logger.info("cv_model_purpose.csv saved") 
        pass
    
    def get_cv_model_training(self):
        def extract_cv_model_training(text):
            # final list of cv_model_training
            final_list = []
            text_list = text.split("\n")
            for text_line in text_list:
                type_source_size = text_line.split(":")
                # if the length of the list is 1, then there's likely no information about source, source and size
                if len(type_source_size) < 3:
                    continue
                else:
                    # check if the second element contains "not"
                    # check if there're more than one "not" in the text_line
                    if text_line.lower().count("not") > 1:
                        continue
                    if "not" not in type_source_size[2].strip().lower():
                        # subjective source
                        cv_model_training = type_source_size[2].strip()
                    else:
                        continue
                final_list.append(cv_model_training.lower())
            return final_list
        
        logger.info("Extracting cv_model_training")
        
        # check if the file exists
        if Path(self.output_folder_path + "cv_model_training.csv").exists():
            logger.info("cv_model_training.csv already exists. Skipping this step.")
            return
        
        cv_model_training_df = (self.input_df.with_columns([
            pl.col("0").alias("DOI"),
            pl.col("8")
                .apply(lambda x: extract_cv_model_training(x))
                .alias("cv_model_training")
            ])
            .explode("cv_model_training")
            .select(["DOI", "cv_model_training"]))
        # save the output
        cv_model_training_df.write_csv(self.output_folder_path + "cv_model_training.csv")  
        logger.info("cv_model_training.csv saved") 
        pass
    
    def get_code_availability(self):
        def extract_code_availability(text):
            return text.replace(".", "").strip().lower()
        
        logger.info("Extracting code_availability")
        
        # check if the file exists
        if Path(self.output_folder_path + "code_availability.csv").exists():
            logger.info("code_availability.csv already exists. Skipping this step.")
            return
        
        code_availability_df = (self.input_df.with_columns([
            pl.col("0").alias("DOI"),
            pl.col("9")
                .apply(lambda x: extract_code_availability(x))
                .alias("code_availability")
            ])
            .select(["DOI", "code_availability"]))
        # save the output
        code_availability_df.write_csv(self.output_folder_path + "code_availability.csv")  
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
        
        data_availability_df = (self.input_df.with_columns([
            pl.col("0").alias("DOI"),
            pl.col("10")
                .apply(lambda x: extract_data_availability(x))
                .alias("data_availability")
            ])
            .select(["DOI", "data_availability"]))
        # save the output
        data_availability_df.write_csv(self.output_folder_path + "data_availability.csv")  
        logger.info("data_availability.csv saved") 
        pass
    
    def get_irb(self):
        logger.info("Extracting irb")
        
        # check if the file exists
        if Path(self.output_folder_path + "irb.csv").exists():
            logger.info("irb.csv already exists. Skipping this step.")
            return
        
        irb_df = (self.input_df.with_columns([
            pl.col("0").alias("DOI"),
            pl.col("11")
                .alias("irb")
            ])
            .select(["DOI", "irb"]))
        # save the output
        irb_df.write_csv(self.output_folder_path + "irb.csv")  
        logger.info("irb.csv saved") 
        pass

    def get_limitation_future_opportunity(self):
        logger.info("Extracting limitation_future_opportunity")
        
        # # check if the file exists
        # if Path(self.output_folder_path + "limitation_future_opportunity.csv").exists():
        #     logger.info("limitation_future_opportunity.csv already exists. Skipping this step.")
        #     return
        
        limitation_future_opportunity_df = (self.input_df.with_columns([
            pl.col("0").alias("DOI"),
            pl.col("12")
                .str.replace_all("\n", " ")
                .alias("limitation_future_opportunity")
            ])
            .select(["DOI", "limitation_future_opportunity"]))
        # save the output
        limitation_future_opportunity_df.write_csv(self.output_folder_path + "limitation_future_opportunity.csv")  
        logger.info("limitation_future_opportunity.csv saved") 
        pass 