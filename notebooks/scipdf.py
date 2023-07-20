# run subprocess to run bash command
# import subprocess
# import os
# command = "bash serve_grobid.sh"
# process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
import scipdf
article_dict = scipdf.parse_pdf_to_dict('/Users/koichiito/Documents/NUS PhD/Academic Matter/2023 Spring/ISM3/visual_perception_review/data/raw/all_papers/Sfc159.pdf') # return dictionary
