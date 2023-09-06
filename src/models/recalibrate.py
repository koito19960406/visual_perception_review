from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain import PromptTemplate, LLMChain
import os 
import pandas as pd
from tqdm import tqdm
import time 

class Recalibrator:
    """
    class to reclibrate the review
    """
    def __init__(self, openai_api_key: str):
        os.environ['OPENAI_API_KEY'] = openai_api_key
        
    def improve_aspect_row(self, row):
        aspect = row["aspect"]
        summary = row["summary"]
        system_template=f"""Instructions:
        - You will get two inputs: 1. a summary of a scientific paper and 2. categorized aspects of the paper.
        - Your task is to reclassify the aspects of the paper if you think the aspect is not correctly classified, otherwise, you can simply return the original aspect.
        - The current list of predefined aspects are: transportation and mobility, health, landscape, public space, street design, building design, infrastructure, walkability, urban vitality, real estate, greenery, safety, others.
        - Please use the predefined aspects to reclassify the aspects of the paper as much as possible.
        - If you think there needs to be a new aspect, please return the new aspect in the format of "others: *YOUR NEW ASPECT*"
        
        Begin!
        ----------------
        """
        messages = [
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template("Original Aspect: {aspect} \n Summary: {summary} \n Reclassified Aspect: "),
        ]
        prompt = ChatPromptTemplate.from_messages(messages)
        # Start chat
        chat = ChatOpenAI(temperature=0, model="gpt-4", max_tokens=100, client = None)
        chain = LLMChain(llm=chat, prompt=prompt)
        output = chain.run(aspect=aspect, summary=summary)
        return output
            
    def improve_aspect(self, input_csv_path, output_csv_path, summary_csv_path):
        # read input_csv_path
        input_df = pd.read_csv(input_csv_path)
        # read summary_csv_path
        summary_df = pd.read_csv(summary_csv_path)
        # join input_df and summary_df on "0"
        df = pd.merge(input_df, summary_df, on="0")
        
        # initialize an empty list to hold improved aspects
        improved_aspects = []
        
        # use tqdm for loop to show progress bar
        for _, row in tqdm(df.iterrows(), total=df.shape[0]):
            improved_aspect = self.improve_aspect_row(row)
            improved_aspects.append(improved_aspect)
        
        # assign the list to the dataframe column
        df["improved_aspect"] = improved_aspects
        
        # save the output to output_csv_path
        df.to_csv(output_csv_path, index=False)
        
    def improve_image_data_type_row(self, row):
        image_data_type = row["0.1"]
        system_template=f"""Instructions:
        - You will get categorized image data types.
        - Your task is to reclassify the image data types if you think the image_data_type can be reclassified into the defined categories, otherwise, you can simply return the original image data type.
        - The list of predefined image data types are: street view image, geo-tagged photos, aerial image, video, virtual reality, non-geo-tagged photos, others
        - Please use the defined image data types to reclassify the image data types as much as possible.
        - If you think there needs to be a new image data type, please return the original image data type
        
        Begin!
        ----------------
        """
        messages = [
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template("Original image data type: {image_data_type} \n Reclassified image_data_type: "),
        ]
        prompt = ChatPromptTemplate.from_messages(messages)
        # Start chat
        chat = ChatOpenAI(temperature=0, model="gpt-4", max_tokens=20, client = None)
        chain = LLMChain(llm=chat, prompt=prompt)
        output = chain.run(image_data_type=image_data_type)
        print(output)
        return output
            
    def improve_image_data_type(self, input_csv_path, output_csv_path):
        # read input_csv_path
        input_df = pd.read_csv(input_csv_path)

        # initialize an empty list to hold improved image_data_types
        improved_image_data_types = []
        
        # use tqdm for loop to show progress bar
        for _, row in tqdm(input_df.iterrows(), total=input_df.shape[0]):
            # sleep for 1 second to avoid openai api limit
            time.sleep(1)
            improved_image_data_type = self.improve_image_data_type_row(row)
            improved_image_data_types.append(improved_image_data_type)
        
        # assign the list to the dataframe column
        input_df["improved_image_data_type"] = improved_image_data_types
        
        # save the output to output_csv_path
        input_df.to_csv(output_csv_path, index=False)