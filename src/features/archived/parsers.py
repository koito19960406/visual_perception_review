from pydantic import BaseModel, Field, validator
from typing import List, Dict, Union
import re

from typing import List
from pydantic import BaseModel, validator

class StudySummary(BaseModel):
    summary: List[str]
    aspect: str

    # @validator('summary')
    # def validate_summary(cls, v):
    #     if len(v) != 3:
    #         raise ValueError('Summary must contain exactly 3 bullet points')
    #     for point in v:
    #         if not isinstance(point, str):
    #             raise ValueError('Each bullet point in the summary must be a string')
    #     return v

    # @validator('aspect')
    # def validate_aspect(cls, v):
    #     valid_aspects = ['transportation and mobility', 'health', 'landscape', 'public space', 
    #                      'street design', 'building design', 'infrastructure', 'walkability', 
    #                      'urban vitality', 'real estate', 'greenery']
    #     if v.startswith('others:'):
    #         if len(v.split(':')) < 2 or not v.split(':')[1]:
    #             raise ValueError('When aspect is "others", a new aspect must follow after ":"')
    #     elif v not in valid_aspects:
    #         raise ValueError(f'Invalid aspect. Must be one of {valid_aspects} or start with "others:"')
    #     return v
class Aspect(BaseModel):
    aspect: str
    
class Perception(BaseModel):
    perception: str
    
class StudyArea(BaseModel):
    study_area: List[Dict[str, str]]
    extent: str

    # @validator('study_area')
    # def validate_study_area(cls, v):
    #     # make sure the keys are valid (Country and City)
    #     valid_keys = ['Country', 'City']
    #     for item in v:
    #         if not isinstance(item, dict):
    #             raise ValueError('Each item in the study_area list must be a dictionary')
    #         if not all(isinstance(i, str) for i in item.values()):
    #             raise ValueError('Each value in the study_area dictionary must be a string')
    #         if not all(key in valid_keys for key in item.keys()):
    #             raise ValueError(f'Invalid key. Must be one of {valid_keys}')
    #     return v

    # @validator('extent')
    # def validate_extent(cls, v):
    #     valid_extents = ["individual image", 'building', 'neighborhood', 'district', 'city', 'country', 'not applicable']
    #     if v not in valid_extents:
    #         raise ValueError(f'Invalid extent. Must be one of {valid_extents}')
    #     return v

class ImageData(BaseModel):
    image_data: List[List[str]]

    # @validator('image_data')
    # def validate_image_data(cls, v):
    #     valid_types = ['street view image', 'geo-tagged photos', 'aerial image', 'video', 'virtual reality', 'others']
    #     for item in v:
    #         if len(item) != 3:
    #             raise ValueError('Each item in the image_data list must contain exactly 3 items: type, source, and number/volume')
    #         if not all(isinstance(i, str) for i in item):
    #             raise ValueError('Each item in the image_data list must be a string')
    #         if item[0] not in valid_types:
    #             raise ValueError(f'Invalid image type. Must be one of {valid_types}')
    #     return v

class PerceptionData(BaseModel):
    perception_data: List[List[str]]

    # @validator('perception_data')
    # def validate_perception_data(cls, v):
    #     valid_sources = ['their own collection', 'publicly available data', 'others']
    #     valid_methods = ['survey/questionnaire', 'observation', 'physiological signals', 'others']
    #     for item in v:
    #         if len(item) != 3:
    #             raise ValueError('Each item in the perception_data list must contain exactly 3 items: source, method, and number of participants')
    #         if not all(isinstance(i, str) for i in item):
    #             raise ValueError('Each item in the perception_data list must be a string')
    #         if item[0] not in valid_sources:
    #             raise ValueError(f'Invalid data source. Must be one of {valid_sources}')
    #         if item[1] not in valid_methods:
    #             raise ValueError(f'Invalid collection method. Must be one of {valid_methods}')
    #         if not item[2].isdigit() or int(item[2]) < 0:
    #             raise ValueError('Number of participants must be a non-negative integer')
    #     return v


class OtherSensoryData(BaseModel):
    other_data_sources: Union[str, Dict[str, List[str]]]

    # @validator('other_data_sources')
    # def validate_other_data_sources(cls, v):
    #     valid_keys = ['smell', 'texture', 'sound', "not applicable"]
    #     if isinstance(v, str) and v.lower() != 'not applicable':
    #         raise ValueError('If a string, other_data_sources must be "not applicable"')
    #     elif isinstance(v, dict):
    #         for key, values in v.items():
    #             if key not in valid_keys:
    #                 raise ValueError(f'Invalid key. Must be one of {valid_keys}')
    #             if not isinstance(values, list):
    #                 raise ValueError(f'{key} must have a list of data sources')
    #             if not all(isinstance(value, str) for value in values):
    #                 raise ValueError(f'Each data source under {key} must be a string')
    #     else:
    #         raise ValueError('other_data_sources must be a dictionary or the string "not applicable"')
    #     return v


class ResearchTypeAndMethod(BaseModel):
    research_type: str
    method: List[str]

    # @validator('research_type')
    # def validate_research_type(cls, v):
    #     valid_types = ['quantitative', 'qualitative']
    #     if v not in valid_types:
    #         raise ValueError(f'Invalid research type. Must be one of {valid_types}')
    #     return v

    # @validator('method')
    # def validate_method(cls, v):
    #     if not isinstance(v, list):
    #         raise ValueError('method must be a list')
    #     if not all(isinstance(i, str) for i in v):
    #         raise ValueError('Each item in the method list must be a string')
    #     return v


class ResearchType(BaseModel):
    research_types: List[str] = Field(..., min_items=1)

    # @validator('research_types')
    # def validate_research_types(cls, v):
    #     valid_types = ['regression', 'model development', 'index construction', 'exploratory analysis']
    #     for item in v:
    #         if not isinstance(item, str):
    #             raise ValueError('Each item in the research_types list must be a string')
    #         if item.startswith('others:'):
    #             if len(item.split(':')) < 2 or not item.split(':')[1]:
    #                 raise ValueError('When research type is "others", a description must follow after ":"')
    #         elif item not in valid_types:
    #             raise ValueError(f'Invalid research type. Must be one of {valid_types} or start with "others:"')
    #     return v


class CVModelsData(BaseModel):
    cv_models: List[List[str]]

    # @validator('cv_models')
    # def validate_cv_models(cls, v):
    #     valid_purposes = ['object detection', 'semantic/instance segmentation', 'image classification', 'feature extraction', 'others', "not applicable"]
    #     valid_procedures = ['pre-trained without fine-tuning', 'pre-trained with fine-tuning', 'trained from scratch by themselves', 'others']
    #     for item in v:
    #         if len(item) != 3:
    #             raise ValueError('Each item in the cv_models list must contain exactly 3 items: name, purpose, and training procedure')
    #         if not all(isinstance(i, str) for i in item):
    #             raise ValueError('Each item in the cv_models list must be a string')
    #         if item[1] not in valid_purposes:
    #             raise ValueError(f'Invalid purpose. Must be one of {valid_purposes}')
    #         if item[2] not in valid_procedures:
    #             raise ValueError(f'Invalid training procedure. Must be one of {valid_procedures}')
    #     return v


class CodeAvailability(BaseModel):
    code_availability: str

    # @validator('code_availability')
    # def validate_code_availability(cls, v):
    #     valid_options = ['code available upon request', 'code available with restrictions', 'code is not available', 'not mentioned', 'others']
    #     if re.match(r'^https?://(?:www\.)?github.com/', v):
    #         return v
    #     elif v not in valid_options:
    #         raise ValueError(f'Invalid code_availability. Must be a URL starting with "https://github.com/" or one of {valid_options}')
    #     return v


class DataAvailability(BaseModel):
    data_availability: str

    # @validator('data_availability')
    # def validate_data_availability(cls, v):
    #     valid_options = ['data available upon request', 'data available with restrictions', 'data is not available', 'not mentioned', 'others']
    #     data_host_services = [r'^https?://(?:www\.)?drive.google.com/', 
    #                           r'^https?://(?:www\.)?dataverse.harvard.edu/', 
    #                           r'^https?://(?:www\.)?figshare.com/',
    #                           r'^https?://(?:www\.)?kaggle.com/',
    #                           r'^https?://(?:www\.)?data.world/',
    #                           r'^https?://(?:www\.)?zenodo.org/',
    #                           r'^https?://(?:www\.)?osf.io/',
    #                           r'^https?://(?:www\.)?data.gov/']
    #     if any(re.match(service, v) for service in data_host_services):
    #         return v
    #     elif v not in valid_options:
    #         raise ValueError(f'Invalid data_availability. Must be a URL from a data host service or one of {valid_options}')
    #     return v


class IRBApproval(BaseModel):
    irb_approval: str

    # @validator('irb_approval')
    # def validate_irb_approval(cls, v):
    #     if v not in ['Yes', 'No']:
    #         raise ValueError('Invalid irb_approval. Must be "Yes" or "No"')
    #     return v


class StudyFeedback(BaseModel):
    limitations: List[str] = Field(..., min_items=1)
    future_research_opportunities: List[str] = Field(..., min_items=1)


class DOITitle(BaseModel):
    doi: str
    title: str

    # @validator('doi')
    # def is_doi(cls, v):
    #     # Modify this regex as needed to suit the DOI format you're working with
    #     pattern = re.compile(r"^10.\d{4,9}/[-._;()/:A-Z0-9]+$", re.I)
    #     if not pattern.match(v) and v.lower() != 'not mentioned':
    #         raise ValueError('Invalid DOI format')
        
    #     return v