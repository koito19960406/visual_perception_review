import polars as pl
from typing import List, Union
from dotenv import find_dotenv, load_dotenv
import os
import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
from nltk.tokenize import word_tokenize

from write_review import ReviewWriter

def remove_articles_and_prepositions(text):
    # Tokenize the text into individual words
    words = word_tokenize(text)

    # Perform POS tagging to identify the parts of speech for each word
    tagged_words = nltk.pos_tag(words)

    # Filter out articles and prepositions
    filtered_words = [word for word, pos in tagged_words if pos not in ['DT', 'IN']]

    # Join the remaining words back into a string
    filtered_text = ' '.join(filtered_words)

    return filtered_text

def get_latex_abbreviations(author: str, title: str, year: str) -> str:
    author_first_name = author.split(", ")[0].lower()
    title_first_word = remove_articles_and_prepositions(title).split(" ")[0].lower()
    return f"Abbreviation: {author_first_name}_{title_first_word}_{year} \n"
    
def get_latex_citation(author: str, title: str, year: str) -> str:
    author_first_name = author.split(", ")[0].lower()
    title_first_word = remove_articles_and_prepositions(title).split(" ")[0].lower().replace("-", "")
    return f"\\citet{{{author_first_name}_{title_first_word}_{year}}}"

def save_citations_by_aspect(df: pl.DataFrame, output_path: str):
    df = (df.with_columns(pl.struct(["Authors", "Year", "Title"])
                                    .apply(lambda row: get_latex_citation(row["Authors"], row["Title"], row["Year"]))
                                    .alias("citations"))
                                    .groupby("aspect")
                                    .agg([pl.col("citations")
                                    .list()
                                    .alias("citations"),
                                    pl.col(['aspect']).count().alias('count')])
                                    .with_columns(pl.col("citations")
                                    .apply(lambda x: ''.join(', '.join(map(str, i)) for i in x))
                                    .alias("citations"))
        )
    df.write_csv(output_path)
    pass

# define a custom function to combine the columns
def combine_cols(row, citation_style):
    author = f"Authors: {row['Authors']} \n"
    year = f"Year: {row['Year']} \n"
    title = f"Title: {row['Title']} \n"
    aspect = f"Aspect: {row['aspect']} \n"
    summary = f"Summary: {row['summary']} \n"
    limitation_future_opportunity = f"Limitation and Future Opportunity: {row['limitation_future_opportunity']} \n"
    border = "---\n"
    abbreviation = get_latex_abbreviations(row['Authors'], row['Title'], row['Year'])
    if citation_style == "plain":
        return author + year + title + aspect + summary + limitation_future_opportunity + border
    elif citation_style == "latex":
        return abbreviation + aspect + summary + limitation_future_opportunity + border
    else:
        raise ValueError("citation_style must be either 'plain' or 'latex'")

def recombine_cols(list):
    joiend_list = [i for i in list] 
    return "".join(joiend_list)

def main(citation_csv: str, 
        aspect_csv: str, 
        summary_csv: str,
        limitation_opportunity_csv: str,
        output_csv_file_path: str,
        openai_api_key: str,
        citation_style = "latex"):
    # load csv files
    citation_df = pl.read_csv(citation_csv)
    aspect_df = pl.read_csv(aspect_csv)
    summary_df = pl.read_csv(summary_csv)
    limitation_opportunity_df = pl.read_csv(limitation_opportunity_csv)
    # merge dataframes
    joined_df = citation_df.join(aspect_df, on="DOI", how="inner")
    # save to csv 
    save_citations_by_aspect(joined_df, os.path.join(os.path.dirname(aspect_csv), "citations_by_aspect.csv"))
    joined_df = joined_df.join(summary_df, on="DOI", how="left")
    joined_df = joined_df.join(limitation_opportunity_df, on="DOI", how="left")
    # apply the custom function to each row and create a new column
    joined_df = joined_df.with_columns(pl.struct(["Authors", "Year", "Title", "aspect", "summary", "limitation_future_opportunity"])
                                    .apply(lambda x: combine_cols(x, citation_style))
                                    .alias("combined_col"))
    # group by aspect and combine the text
    joined_df = (joined_df
                .groupby("aspect")
                .agg([pl.col("combined_col")
                    .list()
                    .alias("combined_col"),
                    pl.col(['aspect']).count().alias('count')])
                .with_columns(pl.struct(["aspect","count"])
                            .apply(lambda x: x["aspect"] if x["count"] > 1 else "others")
                            .alias("aspect")
                            )
                .with_columns(pl.col("combined_col")
                            .apply(lambda x: ''.join(' '.join(map(str, i)) for i in x))
                            .alias("combined_col")
                            )
                # group by modified aspect and aggregate the summary column into a single list
                .groupby('aspect')
                .agg(pl.col("combined_col").list().alias("combined_col"))
                .with_columns(pl.col("combined_col")
                            .apply(lambda x: ''.join(' '.join(map(str, i)) for i in x))
                            .apply(lambda x: "".join(ReviewWriter(openai_api_key, x, citation_style = citation_style).execute()))
                            .alias("combined_col")
                            ) 
                )
    # # create a list of texts
    # input_text = joined_df["combined_col"].to_list()
    # aspect_list = joined_df["aspect"].to_list()
    # writer = ReviewWriter(openai_api_key, input_text)
    # output_list = writer.execute()
    # final_df = pl.DataFrame({"aspect": aspect_list, "review": output_list})
    # write the output csv file
    joined_df.write_csv(output_csv_file_path) 
    
if __name__ == "__main__":
    # input and output path
    citation_csv = "data/external/scopus_initial.csv"
    aspect_csv = "data/processed/aspect.csv"
    summary_csv = "data/processed/summary.csv"
    limitation_opportunity_csv = "data/processed/limitation_future_opportunity.csv"
    output_csv_file_path = "data/processed/review_by_aspect.csv"
    # get api keys for openai and huggingface
    load_dotenv(find_dotenv())
    openai_api_key = str(os.getenv('OPENAI_API_KEY'))
    main(citation_csv, aspect_csv, summary_csv, limitation_opportunity_csv, output_csv_file_path, openai_api_key)

    
    
