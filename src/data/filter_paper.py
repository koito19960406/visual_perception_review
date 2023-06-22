import polars as pl

class PaperFilter:
    def __init__(self, 
                initial_input_filepath: str, 
                include_col_name = "included"):
        self.initial_input_filepath = initial_input_filepath
        self.include_col_name = include_col_name

    def filter_paper(self):
        if self.initial_input_filepath[-4:] == ".csv":
            input_paper_df = pl.read_csv(self.initial_input_filepath)
        elif self.initial_input_filepath[-5:] == ".xlsx":
            input_paper_df = pl.read_excel(self.initial_input_filepath, sheet_id=1, read_csv_options={"infer_schema_length":0})
        else:
            raise ValueError("Input file must be either .csv or .xlsx")
        # filter papers
        input_paper_df = input_paper_df.filter(pl.col(self.include_col_name) == "1")
        return input_paper_df