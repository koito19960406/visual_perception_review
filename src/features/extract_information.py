import json
import pandas as pd
from pathlib import Path
from geopy.geocoders import Nominatim, Photon
import requests
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from tqdm import tqdm
from openai import OpenAI

tqdm.pandas()


# Define a function to flatten the dictionary
def flatten_dict(d):
    items = []
    for k, v in d.items():
        if isinstance(v, dict):
            items.extend(flatten_dict(v).items())
        else:
            items.append((k, v))
    return dict(items)


def extract_location(text):
    # remove "not mentioned", "not specified", "not applicable"
    text = text.lower()
    text = (
        text.replace("not mentioned", "")
        .replace("not specified", "")
        .replace("not applicable", "")
    )
    # create a geocoder object
    geolocator = Nominatim(user_agent="my-app")
    try:
        location = geolocator.geocode(text)
    except (
        requests.exceptions.ReadTimeout,
        GeocoderTimedOut,
        TypeError,
        GeocoderUnavailable,
    ):
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


def clean_location_with_gpt4(text, client):
    content = f"""
    Answer city and country based on the institution name.
    ---
    Example
    User input: Department of Geography, University of Cincinnati
    Your output: {{{{"city": "Cincinnati", "country": "USA"}}}}
    ---
    
    User input: {text}
    Your output:
    """
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You are skilled at accurately estimating the city and country of institutions based on their names. Your task is to answer the city and country based on the institution name, adhering to a JSON format for clarity and relevance.",
            },
            {"role": "user", "content": content},
        ],
    )

    response_json = response.choices[0].message.content
    # load the json
    response_dict = json.loads(response_json)
    if "city" in response_dict and "country" in response_dict:
        return response_dict["city"] + ", " + response_dict["country"]
    else:
        print("Got an error for ", text, response_dict)
        return None


class ExtractInformation:
    def __init__(
        self,
        json_path: str,
        citation_csv_path: str,
        output_dir: str,
        openai_api_key: str = None,
    ) -> None:
        self.json_path = json_path
        self.json = self.load_json()
        self.citation_csv_path = citation_csv_path
        self.citation_df = pd.read_csv(citation_csv_path)
        self.output_dir = Path(output_dir)
        self.ensure_output_dir_exists()
        self.openai_api_key = openai_api_key
        if self.openai_api_key is not None:
            self.client = OpenAI(api_key=self.openai_api_key)
        else:
            self.client = None

    def load_json(self):
        with open(self.json_path, "r") as f:
            return json.load(f)

    def ensure_output_dir_exists(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def __call__(self):
        self.extract_researcher_location()
        self.extract_paper_details()
        self.extract_study_summary()
        self.extract_built_environment_aspect()
        self.extract_study_area()
        self.extract_extent_scale()
        self.extract_spatial_data_aggregation_unit()
        self.extract_image_data()
        self.extract_sampling_interval_distance()
        self.extract_subjective_perception_data()
        self.extract_other_sensory_data()
        self.extract_research_type_and_method()
        self.extract_analysis_type()
        self.extract_computer_vision_models()
        self.extract_code_availability()
        self.extract_data_availability()
        self.extract_ethical_approval()
        self.extract_study_limitations_and_future_research()
        self.extract_country_for_study_areas_researcher_location()

    def extract_section(self, section_name, column_names):
        extracted_list = []
        for key, value in self.json.items():
            filename = key
            if section_name in value:
                section_data = value[section_name]
                if isinstance(
                    section_data, list
                ):  # If the section is a list, handle each item
                    for item in section_data:
                        if isinstance(item, str):
                            row = [filename] + ["" for _ in column_names[1:]]
                            extracted_list.append(row)
                        else:
                            row = [filename] + [
                                item.get(col, "") for col in column_names[1:]
                            ]
                        extracted_list.append(row)
                elif isinstance(section_data, dict):  # If the section is a dictionary
                    section_data = flatten_dict(section_data)
                    row = [filename] + [
                        section_data.get(col, "") for col in column_names[1:]
                    ]
                    extracted_list.append(row)
                else:  # If the section is a string
                    row = [filename] + [section_data] + ["" for _ in column_names[2:]]
                    extracted_list.append(row)
            else:  # Handle cases where the section does not exist in the JSON
                row = [filename] + ["" for _ in column_names[1:]]
                extracted_list.append(row)
        df = pd.DataFrame(extracted_list, columns=column_names)
        df.to_csv(self.output_dir / f"{section_name}.csv", index=False)

    # Example for a generic method to extract and save different sections
    def extract_paper_details(self):
        self.extract_section("paper_details", ["filename", "DOI", "Title"])

    def extract_study_summary(self):
        self.extract_section(
            "study_summary", ["filename", "Purpose", "Method", "Findings"]
        )

    # Add similar methods for other sections as needed,
    # following the structure of extract_paper_details

    # Method to extract 'built_environment_aspect'
    def extract_built_environment_aspect(self):
        self.extract_section(
            "built_environment_aspect", ["filename", "built_environment_aspect"]
        )

    # Method to extract 'study_area'
    def extract_study_area(self):
        # dont run twice
        if (self.output_dir / "study_area.csv").exists():
            return
        self.extract_section("study_area", ["filename", "Country", "City"])
        # load the data
        df = pd.read_csv(self.output_dir / "study_area.csv")
        # fill na with ""
        df.fillna("", inplace=True)
        # combine the country and city
        df["location"] = df["Country"] + ", " + df["City"]
        # extract latitute and longitude
        df[["lat", "lon"]] = df["location"].progress_apply(
            lambda x: pd.Series(extract_location(x))
        )
        # save the data
        df.to_csv(self.output_dir / "study_area.csv", index=False)

    # Method to extract 'extent_scale'
    def extract_extent_scale(self):
        self.extract_section("extent_scale", ["filename", "extent_scale"])

    # Method to extract 'spatial_data_aggregation_unit'
    def extract_spatial_data_aggregation_unit(self):
        self.extract_section(
            "spatial_data_aggregation_unit",
            ["filename", "spatial_data_aggregation_unit"],
        )

    # Method to extract 'image_data'
    def extract_image_data(self):
        self.extract_section(
            "image_data",
            [
                "filename",
                "Type_of_image_data",
                "Image_data_source",
                "Number_Volume_of_images",
            ],
        )

    # Method to extract 'sampling_interval_distance'
    def extract_sampling_interval_distance(self):
        self.extract_section(
            "sampling_interval_distance", ["filename", "sampling_interval_distance"]
        )

    # Method to extract 'subjective_perception_data'
    def extract_subjective_perception_data(self):
        self.extract_section(
            "subjective_perception_data",
            [
                "filename",
                "Subjective_data_source",
                "Subjective_data_collection_method",
                "Number_of_participants",
            ],
        )

    # Method to extract 'other_sensory_data'
    def extract_other_sensory_data(self):
        self.extract_section(
            "other_sensory_data",
            ["filename", "Other_sensory_data_type", "Other_sensory_data_source"],
        )

    # Method to extract 'research_type_and_method'
    def extract_research_type_and_method(self):
        self.extract_section(
            "research_type_and_method",
            [
                "filename",
                "Type_of_research",
                "Data_collection",
                "Data_processing",
                "Analysis",
            ],
        )

    # Method to extract 'analysis_type'
    def extract_analysis_type(self):
        self.extract_section("analysis_type", ["filename", "Type_of_analysis"])

    # Method to extract 'computer_vision_models'
    def extract_computer_vision_models(self):
        self.extract_section(
            "computer_vision_models",
            ["filename", "Model_architecture_name", "Purpose", "Training_procedure"],
        )

    # Method to extract 'code_availability'
    def extract_code_availability(self):
        self.extract_section("code_availability", ["filename", "Code_availability"])

    # Method to extract 'data_availability'
    def extract_data_availability(self):
        self.extract_section("data_availability", ["filename", "Data_availability"])

    # Method to extract 'ethical_approval'
    def extract_ethical_approval(self):
        self.extract_section("ethical_approval", ["filename", "Ethical_approval"])

    # Method to extract 'study_limitations_and_future_research'
    def extract_study_limitations_and_future_research(self):
        self.extract_section(
            "study_limitations_and_future_research",
            ["filename", "Limitations", "Future_research_opportunities"],
        )

    # use self.citation_df to extract the location of the authors from "Affiliations" column with extract_location method
    def extract_researcher_location(self):
        # for this one, don't run twice
        if (self.output_dir / "researcher_location.csv").exists():
            return
        # fill na with ""
        self.citation_df.fillna("", inplace=True)
        # create a new column "fisrt_author_affiliation" by splitting the "Affiliations" column with ";"
        self.citation_df["first_author_affiliation"] = self.citation_df[
            "Affiliations"
        ].apply(lambda x: x.split(";")[0])
        # clean the location with GPT-4
        if self.client is not None:
            self.citation_df["first_author_affiliation"] = self.citation_df[
                "first_author_affiliation"
            ].progress_apply(lambda x: clean_location_with_gpt4(x, self.client))
        # extract latitute and longitude
        self.citation_df[["lat", "lon"]] = self.citation_df[
            "first_author_affiliation"
        ].progress_apply(lambda x: pd.Series(extract_location(x)))
        # only keep "0", "lat", "lon" columns
        self.citation_df = self.citation_df[["0", "lat", "lon"]]
        # save the data
        self.citation_df.to_csv(
            self.output_dir / "researcher_location.csv", index=False
        )

    def extract_country_for_study_areas_researcher_location(self):
        geolocator = Photon(user_agent="geoapiExercises", timeout=None)

        def lat_lon_to_country(latitude, longitude):
            try:
                location = geolocator.reverse(f"{latitude}, {longitude}", exactly_one=True, language = "en")
            except Exception:
                try:
                    location = geolocator.reverse(
                        f"{latitude}, {longitude}", exactly_one=True
                    )
                except Exception as e:
                    print("Got", e, " for ", latitude, longitude)
                    return None
            if location:
                address = location.address
                country = address.split(",")[-1].strip()
                return country
            else:
                return None

        if not (self.output_dir / "study_area_country_clean.csv").exists(): 
            # load the data (both study_area and researcher_location)
            study_area_df = pd.read_csv(self.output_dir / "study_area.csv").dropna(subset=["lat", "lon"])
            # progress_apply to get the country for each row
            study_area_df["Country_clean"] = study_area_df.progress_apply(
                lambda x: lat_lon_to_country(x["lat"], x["lon"]), axis=1
            )
            # save the data
            study_area_df.to_csv(
                self.output_dir / "study_area_country_clean.csv", index=False
            )

        if not (self.output_dir / "researcher_location_country_clean.csv").exists():
            researcher_location_df = pd.read_csv(
                self.output_dir / "researcher_location.csv"
            ).dropna(subset=["lat", "lon"])
            researcher_location_df["Country_clean"] = researcher_location_df.progress_apply(
                lambda x: lat_lon_to_country(x["lat"], x["lon"]), axis=1
            )
            researcher_location_df.to_csv(
                self.output_dir / "researcher_location_country_clean.csv", index=False
            )
