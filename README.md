# Urban Perception Analysis

This project aims to analyze urban perception using various data sources, including images, surveys, and academic papers. It employs machine learning techniques, natural language processing, and data visualization to extract insights about how people perceive urban environments.

![Perception Diagram](reports/diagrams/perception%20diagram.002.png)

## Project Structure

The project is organized into several main directories:

- `src/`: Contains the source code for the project
  - `data/`: Scripts for data acquisition and processing
  - `features/`: Feature extraction and processing scripts
  - `models/`: Machine learning models and prediction scripts
  - `visualization/`: Data visualization scripts

## Key Components

### Data Processing

- `src/data/make_dataset.py`: Main script for data preparation
- `src/data/parse_data.py`: Parses XML data from academic papers
- `src/data/asr_csv2ris.py`: Converts CSV files to RIS format for reference management

### Feature Extraction

- `src/features/build_features.py`: Extracts features from processed data
- `src/features/openai_gpt4.py`: Utilizes OpenAI's GPT-4 for text analysis

### Models

- `src/models/write_review.py`: Generates literature reviews
- `src/models/recalibrate.py`: Recalibrates and improves aspect classification
- `src/models/predict_model.py`: Makes predictions using trained models

### Visualization

- `src/visualization/visualization.R`: Creates various visualizations including word clouds, heatmaps, and bar plots

## Setup and Installation

1. Clone the repository
2. Install the required dependencies (list them or refer to a requirements.txt file)
3. Set up environment variables:
   - Create a `.env` file in the project root
   - Add the following variables:
     ```
     OPENAI_API_KEY=your_openai_api_key
     ELSEVIER_API_KEY=your_elsevier_api_key
     INST_TOKEN=your_institution_token
     ```

## Usage

1. Data Preparation:
   ```
   python src/data/make_dataset.py
   ```

2. Feature Extraction:
   ```
   python src/features/build_features.py
   ```

3. Model Training and Prediction:
   ```
   python src/models/predict_model.py
   ```

4. Visualization:
   Run the R scripts in `src/visualization/` to generate various plots and charts.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Paper and Citation

For more information, please refer to the paper: [Understanding urban perception with visual data: A systematic review](https://doi.org/10.1016/j.cities.2024.105169).

Citation:
```bibtex
@article{ITO2024105169,
title = {Understanding urban perception with visual data: A systematic review},
journal = {Cities},
volume = {152},
pages = {105169},
year = {2024},
issn = {0264-2751},
doi = {https://doi.org/10.1016/j.cities.2024.105169},
url = {https://www.sciencedirect.com/science/article/pii/S0264275124003834},
author = {Koichi Ito and Yuhao Kang and Ye Zhang and Fan Zhang and Filip Biljecki}
}
```
