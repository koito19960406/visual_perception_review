from collections import OrderedDict
import csv

import rispy

################################################################################
# USER INPUT

# Insert path to file within the double quotes. Make sure that the file path has 
# no spaces or ASCII characters.
# (Input)
csv_file_name = "asreview_dataset.csv" 

# Insert path to file within the double quotes. Make sure that the file path has 
# no spaces or ASCII characters.
# (Output)
ris_file_name = "dataset.ris"

################################################################################
class CSV2RISConverter:
    def __init__(self, csv_file_name: str, ris_file_name: str) -> None:
        self.csv_file_name = csv_file_name
        self.ris_file_name = ris_file_name
    
        # remap selected fields to rispy tag mapping
        self.remap = {
            "record_id": "id",
            "included": "custom1",
            "asreview_ranking": "custom2"
        }

    # process lists
    def process(self, instr: str, key: str):
        if len(instr) == 0:
            return instr
        elif instr.strip()[0] == '[' and instr.strip()[-1] == "]":
            return eval(instr)
        elif key == "Authors": 
            return instr.split(".,") 
        else:
            return instr

    def run(self):
        # csv --> ris
        entries = []

        print("Reading CSV...")
        with open(self.csv_file_name) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                ris_dict = OrderedDict([(self.remap[k], self.process(v,k)) if k in self.remap.keys() else (k, self.process(v,k)) for k, v in row.items()])
                entries.append(ris_dict)

        print("Writing RIS...")
        with open(self.ris_file_name, "w") as risfile:
            rispy.dump(entries, risfile)

