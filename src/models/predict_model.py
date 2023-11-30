import polars as pl
from typing import List, Union
from dotenv import find_dotenv, load_dotenv
import os
import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
from nltk.tokenize import word_tokenize
import pandas as pd
from pathlib import Path
import unidecode

from src.models.write_review import ReviewWriter
from src.models.recalibrate import Recalibrator

def remove_articles_and_prepositions(text):
    # Tokenize the text into individual words
    words = word_tokenize(text)

    # Perform POS tagging to identify the parts of speech for each word
    tagged_words = nltk.pos_tag(words)

    # Filter out articles and prepositions
    filtered_words = [unidecode.unidecode(word) for word, pos in tagged_words if pos not in ['DT', 'IN'] and\
        word not in ['a', 'an', 'the', '“', "'", "``","."]]

    # Join the remaining words back into a string
    filtered_text = ' '.join(filtered_words)

    return filtered_text

def get_latex_abbreviations(author: str, title: str, year: str) -> str:
    author_first_name = unidecode.unidecode(author.split("., ")[0].split(" ")[0].lower())
    title_first_word = remove_articles_and_prepositions(title).split(" ")[0].lower()
    return f"Abbreviation: {author_first_name}_{title_first_word}_{year} \n"
    
def get_latex_citation(author: str, title: str, year: str) -> str:
    author_first_name = unidecode.unidecode(author.split("., ")[0].split(" ")[0].lower())
    title_first_word = remove_articles_and_prepositions(title).split(" ")[0].lower().replace("-", "")
    return f"\\citet{{{author_first_name}_{title_first_word}_{year}}}"

def save_citations_by_aspect(df: pd.DataFrame, output_path: str):
    df['citations'] = df[['Authors', 'Year', 'Title']].apply(
        lambda row: get_latex_citation(row["Authors"], row["Title"], row["Year"]), axis=1)
    df = df.groupby('aspect').agg({'citations': list, 'aspect': 'count'})
    df['citations'] = df['citations'].apply(lambda x: ', '.join(map(str, x)))
    df.to_csv(output_path)

# define a custom function to combine the columns
def combine_cols(row, citation_style):
    author = f"Authors: {row['Authors']} \n"
    year = f"Year: {row['Year']} \n"
    title = f"Title: {row['Title']} \n"
    aspect = f"Aspect: {row['aspect']} \n"
    summary = f"Summary: {row['summary']} \n"
    limitations = f"Limitations: {row['limitations']} \n"
    future_research_opportunities = f"Future Research Opportunities: {row['future_research_opportunities']} \n"
    border = "---\n"
    abbreviation = get_latex_abbreviations(row['Authors'], row['Title'], row['Year'])
    if citation_style == "plain":
        return author + year + title + aspect + summary + limitations + future_research_opportunities + border
    elif citation_style == "latex":
        return abbreviation + aspect + summary + limitations + future_research_opportunities + border
    else:
        raise ValueError("citation_style must be either 'plain' or 'latex'")

def recombine_cols(list_):
    return "".join(list_)

def main(citation_csv, complementary_excel, aspect_csv, summary_csv, limitation_opportunity_csv, output_csv_file_path, openai_api_key, citation_style="latex"):
    # load csv files
    citation_df = pd.read_csv(citation_csv)
    complementary_df = pd.read_excel(complementary_excel)
    aspect_df = pd.read_csv(aspect_csv)
    summary_df = pd.read_csv(summary_csv)
    limitation_opportunity_df = pd.read_csv(limitation_opportunity_csv)
    
    # convert aspect to lowercase
    aspect_df = aspect_df[['0', 'improved_aspect']]
    aspect_df['aspect'] = aspect_df['improved_aspect'].str.lower()
    # split aspect by "," and use the first one. Also make sure there is no space in the beginning and end
    aspect_df['aspect'] = aspect_df['aspect'].apply(lambda x: x.split(",")[0].strip())
    # check the sum of all the columns
    # convert complementary_df's title to lowercase
    complementary_df['title'] = complementary_df['title'].str.lower()
    # convert citation_df's Title to lowercase
    citation_df['Title'] = citation_df['Title'].str.lower()
    
    # join citation_df and complementary_df on DOI first and then on EID and then on Title
    citation_df = citation_df.merge(complementary_df[["doi", "0"]], left_on="DOI", right_on="doi", how="left")
    citation_df = citation_df.merge(complementary_df[["EID", "0"]], on="EID", how="left")
    citation_df = citation_df.merge(complementary_df[["title", "0"]], left_on="Title", right_on="title", how="left")
    # drop duplicates
    citation_df = citation_df.drop_duplicates(subset=['DOI', "EID", "Title"])
    # combine "0_x" and "0_y" into "0"
    citation_df['0'] = citation_df['0'].fillna(citation_df['0_x']).fillna(citation_df['0_y'])
    # get rows with no values in column '0'
    citation_df_no_filename = citation_df[citation_df['0'].isna()]
    # get rows with values in column '0'
    citation_df = citation_df[citation_df['0'].notna()]
    
    # save citation_df to csv
    citation_df.to_csv(os.path.join(os.path.dirname(output_csv_file_path), "citation_df.csv"))
    
    # merge dataframes
    joined_df = citation_df.merge(aspect_df, on="0", how="inner")
    save_citations_by_aspect(joined_df, os.path.join(os.path.dirname(aspect_csv), "citations_by_aspect.csv"))
    
    joined_df = joined_df.merge(summary_df, on="0", how="left")
    joined_df = joined_df.merge(limitation_opportunity_df, on="0", how="left")
    
    # apply the custom function to each row and create a new column
    joined_df['combined_col'] = joined_df.apply(
        lambda x: combine_cols(x, citation_style), axis=1)
    
    grouped_df = joined_df.groupby("aspect").agg(combined_col_list=('combined_col', list), aspect_count=('aspect', 'count')).reset_index()
    grouped_df['aspect'] = grouped_df.apply(lambda x: x["aspect"] if (x["aspect_count"] > 1) and ("others" not in x["aspect"]) else "others", axis=1)
    # group by aspect and combine the list of strings in combined_col_list again
    grouped_df = grouped_df.groupby("aspect").agg(combined_col_list=('combined_col_list', list)).reset_index()
    grouped_df['combined_col_list'] = grouped_df['combined_col_list'].apply(lambda x: ' '.join(map(str, x)))
    
    output_series = grouped_df['combined_col_list'].apply(lambda x: ReviewWriter(openai_api_key, x, citation_style=citation_style).execute())
    grouped_df['first_run_output'], grouped_df['final_output'] = zip(*output_series)

    # write the output csv file
    grouped_df.to_csv(output_csv_file_path)
    # save citation_df_no_filename to csv
    citation_df_no_filename.to_csv(os.path.join(os.path.dirname(output_csv_file_path), "citation_df_no_filename.csv"))

def reclibrate(openai_api_key, aspect_csv, summary_csv,
            image_data_type_csv
            ):
    recalibrated_aspect_csv = Path(aspect_csv).parent / "recalibrated_aspect.csv"
    recalibrated_image_data_type_csv = Path(image_data_type_csv).parent / "recalibrated_image_data_type.csv"
    recalibrator = Recalibrator(openai_api_key)
    if not Path(recalibrated_aspect_csv).exists():
        recalibrator.improve_aspect(aspect_csv, recalibrated_aspect_csv, summary_csv)
    if not Path(recalibrated_image_data_type_csv).exists():
        recalibrator.improve_image_data_type(image_data_type_csv, recalibrated_image_data_type_csv)
    
if __name__ == "__main__":
    # input and output path
    citation_csv = "data/external/asreview_dataset_all_visual-urban-perception-2023-07-09-2023-07-17.csv"
    complementary_excel = "data/processed/2nd_run/input_df_with_title_doi_edited.xlsx"
    aspect_csv = "data/processed/2nd_run/aspect.csv"
    reclibrated_aspect_csv = "data/processed/2nd_run/recalibrated_aspect.csv"
    summary_csv = "data/processed/2nd_run/summary.csv"
    limitation_opportunity_csv = "data/processed/2nd_run/limitation_future_opportunity.csv"
    output_csv_file_path = "data/processed/2nd_run/review_by_aspect.csv"
    image_data_type_csv = "data/processed/2nd_run/image_data_type.csv"
    
    # get api keys for openai and huggingface
    load_dotenv(find_dotenv())
    openai_api_key = str(os.getenv('OPENAI_API_KEY'))
    # reclibrate the review
    reclibrate(openai_api_key, aspect_csv, summary_csv, image_data_type_csv)
    # get review by aspect
    if not Path(output_csv_file_path).exists():
        main(citation_csv, complementary_excel, reclibrated_aspect_csv, summary_csv, limitation_opportunity_csv, output_csv_file_path, openai_api_key)
    
    
    
