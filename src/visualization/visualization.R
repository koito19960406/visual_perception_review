pacman::p_load(tidyverse, hrbrthemes, scales, paletteer, sf, basemaps, ggalluvial,
               ggrepel, xtable, stringdist, dendextend, ggpattern)

round <- "2nd_run"

theme_custom <- function(...){
  theme_ipsum() +
    theme(axis.text.y = element_text(vjust = 0.5, hjust=1, size = 15),
          plot.background = element_rect(fill = "black", colour = "black"),
          panel.background = element_rect(fill = "black"),
          panel.grid = element_line(colour = "grey50"),
          axis.text = element_text(colour = "white"),
          axis.title = element_text(colour = "white"),
          plot.title = element_text(colour = "white"),
          plot.subtitle = element_text(colour = "white"),
          plot.caption = element_text(colour = "white"),
          legend.background = element_rect(fill = "black"),
          legend.text = element_text(colour = "white"),
          legend.title = element_text(colour = "white"),
          strip.background = element_rect(fill = "grey30", colour = "grey30"),
          strip.text = element_text(colour = "white"),
          ...)
}

dir_figure <- paste0("reports/figures/", round, "/")
if (!dir.exists(dir_figure)){
  dir.create(dir_figure)
}

# citations ---------------------------------------------------------------
citations <- read.csv(paste0("data/processed/", round, "/citation_df.csv")) %>% 
  dplyr::select(record_id, X0)

# journal -----------------------------------------------------------------
journal <- read.csv("data/external/asreview_dataset_all_visual-urban-perception-2023-07-09-2023-07-17.csv") %>% 
  group_by(Source.title) %>% 
  summarize(count=n()) %>% 
  drop_na(Source.title) %>% 
  top_n(20, count) %>% 
  arrange(count) %>% 
  mutate(rank = row_number()) %>% 
  dplyr::select(-count)

journal_year <- read.csv("data/external/asreview_dataset_all_visual-urban-perception-2023-07-09-2023-07-17.csv") %>% 
  group_by(Source.title, Year) %>% 
  summarize(count=n()) %>% 
  drop_na(Source.title) %>% 
  filter(Source.title %in% journal$Source.title) %>% 
  left_join(journal,by="Source.title")


ggplot(journal_year) +
  # geom_bar(stat = "identity", position = "stack") +
  geom_col(aes(x=reorder(Source.title,rank), y=count, fill=Year), stat = "identity", position = "stack") +
  labs(x = "",
       y = "number of papers",
       title = "Journals/conferences by the number of papers",
       caption = "Data: papers downloaded from Scopus on 2023/08/15") +
  paletteer::scale_fill_paletteer_c("viridis::magma") +
  coord_flip() +
  theme_custom(panel.grid.major = element_blank(),
               panel.grid.minor = element_blank(),
               plot.margin = margin(0, 0, 0, 0))
ggsave(paste0(dir_figure, "jounral.png"), width = 20, height = 11)

# number of papers --------------------------------------------------------
scopus_initial <- read.csv("data/external/scopus_input.csv") %>% 
  mutate(Year=case_when(
    Year < 2000 ~ 1999,
    TRUE ~ as.numeric(Year))) %>% 
  group_by(Year) %>% 
  summarize(count=n()) %>% 
  drop_na(Year)

gg <- ggplot(scopus_initial, aes(x = Year, y = count)) +
  geom_col(aes(fill = ifelse(Year == 1999, "blue-gray", "default"))) +
  scale_fill_manual(values = c("blue-gray" = "#6699CC", "default" = "gray70")) +
  scale_x_continuous(breaks = c(1999, 2005, 2010, 2015, 2020, 2023),
                     labels = c("1960 - 2000", 2005, 2010, 2015, 2020, 2023)) +
  labs(y = "number of papers",
       title = "Papers containing relevant keywords",
       caption = "Data: papers downloaded from Scopus on 2023-07-19") +
  theme_ipsum() +
  theme(plot.margin = margin(0, 0, 0, 0),
        legend.position = "none")

print(gg)

# Save the plot
ggsave(paste0(dir_figure, "num_papers.png"), width = 5, height = 5)

# aspect ------------------------------------------------------------------
aspect <- read.csv(paste0("data/processed/", round, "/recalibrated_aspect.csv")) %>% 
  distinct(X0, improved_aspect) %>% 
  left_join(citations, by = "X0") %>%
  filter(!is.na(record_id)) %>% 
  mutate(aspect = tolower(improved_aspect)) %>%
  mutate(aspect = str_trim(str_split_fixed(aspect, ",", 2)[,1])) %>% 
  group_by(aspect) %>% 
  mutate(
    count = n(),
    aspect = case_when(
    X0 == "978-3-319-95588-9_67.pdf" ~ "public space",
    str_detect(aspect, "reclassify the aspect of the study") ~ "greenery",
    str_detect(aspect, "others: study methodology") ~ "landscape",
    str_detect(aspect, "others: sensory perception") ~ "landscape",
    str_detect(aspect, "others: visual aesthetics") ~ "landscape",
    str_detect(aspect, "others: population prediction") ~ "public space",
    TRUE ~ aspect)) %>% 
  group_by(aspect) %>% 
  summarize(count=n()) %>% 
  mutate(dummy="") %>% 
  arrange(aspect != "others", count) %>%
  mutate(aspect = factor(aspect, levels = unique(aspect)))

# palette <- paletteer::paletteer_d("rcartocolor::Antique")[3:(length(unique(aspect$aspect))+2)]
palette <- paletteer::paletteer_d("palettesForR::Caramel")
num_colors <- length(unique(aspect$aspect))
indices <- round(seq(2, length(palette), length.out = num_colors))
selected_colors <- palette[indices]
# Lightened pastel color palette based on your provided colors
original_pastel_palette <- c("#B6A6D2FF", "#D2A9AFFF", "#E8B57DFF", "#EDE3A9FF", "#8AA5A0FF", 
                             "#A2C5B4FF", "#C7C48DFF", "#D7B0B2FF", "#C89A76FF", "#56B0A3FF", 
                             "#7F9FC2FF", "#D4B5C3FF", "#A2E0CEFF")
ggplot(aspect) +
  geom_col(aes(x=dummy, y=count, fill = aspect), 
           position = "fill",
           width = 1) +
  scale_y_continuous(name = "Percentage of publications", 
                     labels = scales::label_percent()) +
  scale_x_discrete(expand = expansion(add =c(0.8,0))) + # Add this line to control the space around the plot on the x-axis
  # paletteer::scale_fill_paletteer_d("rcartocolor::Antique", guide = guide_legend(reverse = TRUE)) +
  scale_fill_manual(values = original_pastel_palette, guide = guide_legend(reverse = TRUE)) +
  coord_flip() +
  labs(x="", fill = "", title = "Aspects of the built environment",
       subtitle = "studied by reviewed papers") +
  theme_ipsum() +
  theme(legend.position = "bottom",
        panel.grid.major.y = element_blank(),
        plot.margin = margin(0, 0, 0, 0))
ggsave(paste0(dir_figure, "aspects.png"), width = 10, height = 4)


# location ----------------------------------------------------------------
location <- read.csv(paste0("data/processed/", round, "/location.csv")) %>% 
  # Extract latitude and longitude using regex
  mutate(latitude = as.numeric(str_extract(study_area, "(?<=\\()[-]?[0-9]+\\.[0-9]+(?=,)")),
         longitude = as.numeric(str_extract(study_area, "(?<=, )[-]?[0-9]+\\.[0-9]+(?=\\))"))) %>%
  drop_na(c("longitude", "latitude")) %>% 
  # Convert to sf object
  st_as_sf(coords = c("longitude", "latitude"), crs = 4326)  %>% # EPSG:4326 refers to WGS 84, common latitude-longitude CRS
  st_transform(3857)
bbox <- st_bbox(c(xmin = -180, xmax = 180, ymin = -60, ymax =80), crs = st_crs(4326))
basemap_ggplot(bbox, map_service = "carto", map_type = "light_no_labels", force = T) +
  geom_sf(data = location, color = "red", size = 0.5, alpha = 0.4, linewidth = 0) +
  labs(x="", y="", fill = "", title = "Locations of study areas",
       subtitle="used by the reviewed papers",
       caption="Basemap: carto") +
  theme_ipsum() +
  theme(axis.text.x = element_blank(),
        axis.text.y = element_blank(),
        axis.ticks = element_blank(),
        panel.grid.major = element_blank(),
        plot.margin = margin(t = 0,  # Top margin
                             r = 0,  # Right margin
                             b = 0,  # Bottom margin
                             l = 0)) # Left margin)
ggsave(paste0(dir_figure, "location.png"), width = 5, height =5)


# extent ------------------------------------------------------------------
extent <- read.csv(paste0("data/processed/", round, "/extent.csv")) %>%
  left_join(citations, by = "X0") %>%
  filter(!is.na(record_id)) %>% 
  mutate(extent = case_when(
    extent == "XXX-level" ~ "not applicable",
    extent == "Not applicable" ~ "not applicable",
    extent == "individual image-level" ~ "not applicable",
    extent == "campus-level" ~ "building-level",
    extent == "school-level" ~ "building-level",
    extent == "state-level" ~ "district-level",
    extent == "town-level" ~ "city-level",
    T ~ extent
  )) %>% 
  group_by(extent) %>% 
  summarize(count=n()) %>% 
  mutate(dummy="") 
happy_pastel_palette_adjusted <- c("#8A89B3FF", "#9FC3C1FF", "darkgray", "#D6A3A5FF", "#EED9B3FF", "#B2C2A9FF")
ggplot(extent) +
  geom_col(aes(x=dummy, y=count, fill = reorder(extent, count)), 
           position = "fill",
           width = 0.8) +
  scale_y_continuous(name = "Percentage of publications", 
                     labels = scales::label_percent()) +
  scale_x_discrete(expand = expansion(add =c(0.8,0))) + # Add this line to control the space around the plot on the x-axis
  scale_fill_manual(values = happy_pastel_palette_adjusted, guide = guide_legend(reverse = TRUE)) +
  coord_flip() +
  labs(x="", fill = "", title = "Extent of study areas",
       subtitle = "among reviewed papers") +
  theme_ipsum() +
  theme(legend.position = "bottom",
        panel.grid.major.y = element_blank(),
        plot.margin = margin(0, 0, 0, 0))
ggsave(paste0(dir_figure, "extent.png"), width = 10, height = 4)



# image data type ------------------------------------------------------
image_data_type <- read.csv(paste0("data/processed/", round, "/recalibrated_image_data_type.csv")) %>%
  left_join(citations, by = "X0") %>%
  filter(!is.na(record_id)) %>% 
  rename("file_name" = "X0", 
         "image_data_type" = "improved_image_data_type") %>% 
  distinct(file_name,image_data_type) %>% 
  filter(image_data_type != "") %>% 
  group_by(image_data_type) %>% 
  summarize(count=n()) %>% 
  mutate(image_data_type = case_when(
    count < 3 ~ "others",
    TRUE ~ image_data_type)) %>% 
  group_by(image_data_type) %>% 
  summarize(count=sum(count)) %>% 
  mutate(dummy="") %>% 
  arrange(count)

palette <- paletteer::paletteer_d("MetBrewer::Signac")
color_palette <- c("aerial image" = palette[1], 
                   "geo-tagged photos" = palette[2], 
                   "virtual reality" = palette[3], 
                   "others" = palette[4], 
                   "street view image" = palette[5],
                   "non-geo-tagged photos" = palette[6],
                   "video" = palette[7]
                   )
# Darker color palette
# Even darker color palette harmonized with your provided colors
lighter_pastel_palette <- c("#9FCBB2", "#9FAFCC", "#A098C2", "#D69BA3", "#F5B89F", "#D5C5A8", "#DFA7B9")
ggplot(image_data_type) +
  geom_col(aes(x=dummy, y=count, fill = reorder(image_data_type, count)), 
           position = "fill",
           width = 0.8) +
  scale_y_continuous(name = "Percentage of publications", 
                     labels = scales::label_percent()) +
  scale_x_discrete(expand = expansion(add =c(0.8,0))) + # Add this line to control the space around the plot on the x-axis
  # paletteer::scale_fill_paletteer_d("nord::aurora", guide = guide_legend(reverse = TRUE)) +
  scale_fill_manual(values = lighter_pastel_palette, guide = guide_legend(reverse = TRUE)) + # Add custom color palette
  coord_flip() +
  labs(x="", fill = "", title = "Image data types",
       subtitle = "used by reviewed papers") +
  theme_ipsum() +
  theme(legend.position = "bottom",
        panel.grid.major.y = element_blank(),
        plot.margin = margin(0, 0, 0, 0))
ggsave(paste0(dir_figure, "image_data_type.png"), width = 10, height =4)


# subjective data type ----------------------------------------------------
subjective_data_type <- read.csv(paste0("data/processed/", round, "/perception_data_type.csv")) %>%
  left_join(citations, by = "X0") %>%
  filter(!is.na(record_id)) %>% 
  mutate(
    X0.1 = tolower(X0.1),
    subjective_data_type=case_when(
    str_detect(X0.1, "public") ~ "publicly available data",
    str_detect(X0.1, "subjective") ~ "their own collection",
    str_detect(X0.1, "survey") ~ "their own collection",
    str_detect(X0.1, "collection") ~ "their own collection",
    str_detect(X0.1, "questionnaire") ~ "their own collection",
    str_detect(X0.1, "pulse") ~ "publicly available data",
    str_detect(X0.1, "existing") ~ "publicly available data",
    TRUE ~ X0.1
  )) %>% 
  filter(subjective_data_type=="publicly available data" | subjective_data_type=="their own collection") %>%
  distinct(X0,subjective_data_type) %>% 
  group_by(subjective_data_type) %>% 
  summarize(count=n()) %>% 
  mutate(subjective_data_type = case_when(
    count < 3 ~ "others",
    TRUE ~ subjective_data_type)) %>% 
  group_by(subjective_data_type) %>% 
  summarize(count=sum(count)) %>% 
  mutate(dummy="") 
color_palette <- c("publicly available data" = "#eec643", "their own collection" = "darkgray")
ggplot(subjective_data_type) +
  geom_col(aes(x=dummy, y=count, fill = reorder(subjective_data_type, count)), 
           position = "fill",
           width = 0.8) +
  scale_y_continuous(name = "Percentage of publications", 
                     labels = scales::label_percent()) +
  scale_x_discrete(expand = expansion(add =c(0.8,0))) + # Add this line to control the space around the plot on the x-axis
  # paletteer::scale_fill_paletteer_d("nord::algoma_forest", guide = guide_legend(reverse = TRUE)) +
  scale_fill_manual(values = color_palette, guide = guide_legend(reverse = TRUE)) + # Add custom color palette
  coord_flip() +
  labs(x="", fill = "", title = "Subjective data types",
       subtitle = "used by reviewed papers") +
  theme_ipsum() +
  theme(legend.position = "bottom",
        panel.grid.major.y = element_blank(),
        plot.margin = margin(0, 0, 0, 0))
ggsave(paste0(dir_figure, "subjective_data_type.png"), width = 10, height = 4)


# subjective data source ----------------------------------------------------
subjective_data_source <- read.csv(paste0("data/processed/", round, "/subjective_data_source.csv")) %>%
  distinct(DOI,subjective_data_source) %>% 
  filter(subjective_data_source != "") %>% 
  group_by(subjective_data_source) %>% 
  summarize(count=n()) %>% 
  mutate(subjective_data_source = case_when(
    count < 3 ~ "others",
    TRUE ~ subjective_data_source)) %>% 
  group_by(subjective_data_source) %>% 
  summarize(count=sum(count)) %>% 
  mutate(dummy="") 
palette <- paletteer::paletteer_d("ggthemes::excel_Main_Event")[2:(length(unique(subjective_data_source$subjective_data_source))+1)]
ggplot(subjective_data_source) +
  geom_col(aes(x=dummy, y=count, fill = reorder(subjective_data_source, count)), 
           position = "fill",
           width = 0.8) +
  scale_y_continuous(name = "Percentage of publications", 
                     labels = scales::label_percent()) +
  scale_x_discrete(expand = expansion(add =c(0.8,0))) + # Add this line to control the space around the plot on the x-axis
  # paletteer::scale_fill_paletteer_d("ggthemes::excel_Main_Event", guide = guide_legend(reverse = TRUE)) +
  scale_fill_manual(values = palette, guide = guide_legend(reverse = TRUE)) +
  coord_flip() +
  labs(x="", fill = "", title = "Subjective data sources",
       subtitle = "used by reviewed papers") +
  theme_ipsum() +
  theme(legend.position = "bottom",
        panel.grid.major.y = element_blank(),
        plot.margin = margin(0, 0, 0, 0))
ggsave(paste0(dir_figure, "subjective_data_source.png"), width = 10, height = 4)


# subjective data size ----------------------------------------------------
subjective_data_size <- read.csv(paste0("data/processed/", round, "/perception_data_type.csv")) %>%
  left_join(citations, by = "X0") %>%
  filter(!is.na(record_id)) %>% 
  rename("subjective_data_size"="X2") %>% 
  filter(subjective_data_size != "None") %>% 
  mutate(subjective_data_size=as.numeric(subjective_data_size),
         subjective_data_size=case_when(
           subjective_data_size>2000 ~ 2000,
           T ~ subjective_data_size
         ))

ggplot(subjective_data_size) +
  geom_histogram(aes(x=subjective_data_size),bins=20, color = "white") +
  scale_x_continuous(labels = c(0,500,1000,1500,"> 2000")) +
  labs(x = "Number of participants",
       y = "Number of papers",
       title = "Number of participants",
       subtitle = "analyzed by reviewed papers",
       caption = "") +
  theme_ipsum() +
  theme(plot.margin = margin(0, 0, 0, 0))
ggsave(paste0(dir_figure, "subjective_data_size.png"), width = 10, height = 4)


# other_sensory_data ----------------------------------------------------
other_sensory_data <- read.csv(paste0("data/processed/", round, "/other_sensory_data.csv")) %>%
  left_join(citations, by = "X0") %>%
  filter(!is.na(record_id)) %>% 
  rename("filename" = "X0", "other_sensory_data" = "label_dict") %>% 
  group_by(filename) %>%
  mutate(flag = ifelse(any(other_sensory_data != "None"), 1, 0)) %>% 
  ungroup() %>% 
  filter(!(other_sensory_data=="None"&flag==1)) %>% 
  distinct(filename,other_sensory_data) %>% 
  group_by(other_sensory_data) %>% 
  summarize(count=n()) %>% 
  mutate(dummy="")
palette <- rev(paletteer::paletteer_d("ggthemes::excel_View"))[3:(length(unique(aspect$aspect))+1)]
ggplot(other_sensory_data) +
  geom_col(aes(x=dummy, y=count, fill = reorder(other_sensory_data, count)), 
           position = "fill",
           width = 0.8) +
  scale_y_continuous(name = "Percentage of publications", 
                     labels = scales::label_percent()) +
  scale_x_discrete(expand = expansion(add =c(0.8,0))) + # Add this line to control the space around the plot on the x-axis
  # paletteer::scale_fill_paletteer_d("ggthemes::excel_View", guide = guide_legend(reverse = TRUE)) +
  scale_fill_manual(values = palette, guide = guide_legend(reverse = TRUE)) +
  coord_flip() +
  labs(x="", fill = "", title = "Non-visual sensory data",
       subtitle = "used by reviewed papers") +
  theme_ipsum() +
  theme(legend.position = "bottom",
        panel.grid.major.y = element_blank())
ggsave(paste0(dir_figure, "other_sensory_data.png"), width = 10, height = 4)


# type_of_research ----------------------------------------------------
type_of_research <- read.csv(paste0("data/processed/", round, "/type_of_research.csv")) %>%
  left_join(citations, by = "X0") %>%
  filter(!is.na(record_id)) %>% 
  mutate(research_type = tolower(research_type),
         research_type = case_when(
           str_detect(research_type, "mixed") ~ "mixed",
           T ~ research_type
         )) %>% 
  group_by(research_type) %>% 
  summarize(count=n()) %>% 
  mutate(dummy="") %>% 
  filter(research_type %in% c("qualitative", "quantitative", "mixed"))
happy_pastel_palette <- c("#A5A5A5FF", "#FFDE8DFF", "#9E7AB4FF")
ggplot(type_of_research) +
  geom_col(aes(x=dummy, y=count, fill = reorder(research_type, count)), 
           position = "fill",
           width = 0.8) +
  scale_y_continuous(name = "Percentage of publications", 
                     labels = scales::label_percent()) +
  scale_x_discrete(expand = expansion(add =c(0.8,0))) + # Add this line to control the space around the plot on the x-axis
  scale_fill_manual(values = happy_pastel_palette, guide = guide_legend(reverse = TRUE)) +
  coord_flip() +
  labs(x="", fill = "", title = "Type of research among reviewed papers",
       subtitle = "") +
  theme_ipsum() +
  theme(legend.position = "bottom",
        panel.grid.major.y = element_blank(),
        plot.margin = margin(0, 0, 0, 0))
ggsave(paste0(dir_figure, "type_of_research.png"), width = 10, height = 4)

# type_of_research_detail ----------------------------------------------------
type_of_research_detail <- read.csv(paste0("data/processed/", round, "/type_of_research_detail.csv")) %>%
  left_join(citations, by = "X0") %>%
  filter(!is.na(record_id)) %>% 
  rename("filename" = "X0", "type_of_research_detail" = "research_types") %>% 
  distinct(filename,type_of_research_detail) %>% 
  mutate(type_of_research_detail = tolower(type_of_research_detail),
    type_of_research_detail = case_when(
    str_detect(type_of_research_detail, "qualitative") ~ "exploratory analysis",
    str_detect(type_of_research_detail, "regression") ~ "regression",
    str_detect(type_of_research_detail, "correlation") ~ "regression",
    str_detect(type_of_research_detail, "descript") ~ "exploratory analysis",
    str_detect(type_of_research_detail, "experimental") ~ "exploratory analysis",
    str_detect(type_of_research_detail, "chi-square") ~ "regression",
    str_detect(type_of_research_detail, "cluster") ~ "model development",
    str_detect(type_of_research_detail, "index") ~ "index construction",
    str_detect(type_of_research_detail, "exploratory") ~ "exploratory analysis",
    str_detect(type_of_research_detail, "model development") ~ "model development",
    str_detect(type_of_research_detail, "questionnaire") ~ "exploratory analysis",
    str_detect(type_of_research_detail, "pilot") ~ "exploratory analysis",
    T ~ "others"
  )) %>% 
  group_by(type_of_research_detail) %>% 
  summarize(count=n()) %>% 
  mutate(dummy="")
palette <- c("#8FA587FF", "#F7B374FF", "#E49E7DFF", "#A9887CFF", "#BFAE8DFF")
ggplot(type_of_research_detail) +
  geom_col(aes(x=dummy, y=count, fill = reorder(type_of_research_detail, count)), 
           position = "fill",
           width = 0.8) +
  scale_y_continuous(name = "Percentage of publications", 
                     labels = scales::label_percent()) +
  scale_x_discrete(expand = expansion(add =c(0.8,0))) + # Add this line to control the space around the plot on the x-axis
  # paletteer::scale_fill_paletteer_d("ggthemes::stata_s2color", guide = guide_legend(reverse = TRUE)) +
  scale_fill_manual(values = palette, guide = guide_legend(reverse = TRUE)) +
  coord_flip() +
  labs(x="", fill = "", title = "Type of research among reviewed papers",
       subtitle = "") +
  theme_ipsum() +
  theme(legend.position = "bottom",
        panel.grid.major.y = element_blank(),
        plot.margin = margin(0, 0, 0, 0))
ggsave(paste0(dir_figure, "type_of_research_detail.png"), width = 10, height = 4)

# cv_model_purpose ----------------------------------------------------
cv_model_purpose <- read.csv(paste0("data/processed/", round, "/cv_model.csv")) %>%
  left_join(citations, by = "X0") %>%
  filter(!is.na(record_id)) %>% 
  rename("cv_model_purpose" = "X1", "filename" = "X0") %>% 
  filter(cv_model_purpose != "") %>% 
  mutate(cv_model_purpose = tolower(cv_model_purpose),
    cv_model_purpose = case_when(
    str_detect(cv_model_purpose, "classification") ~ "image classification",
    str_detect(cv_model_purpose, "detection") | str_detect(cv_model_purpose, "object")  ~ "object detection",
    str_detect(cv_model_purpose, "segmentation") ~ "semantic/instance segmentation",
    str_detect(cv_model_purpose, "extraction") ~ "feature extraction",
    TRUE ~ "others"
  )) %>% 
  distinct(filename,cv_model_purpose) %>% 
  group_by(cv_model_purpose) %>% 
  summarize(count=n()) %>% 
  mutate(dummy="")
palette <- c("#B7A4D4FF", "#E2ADC1FF", "#F5D379FF", "#F7BF8DFF", "#C0CEB0FF", "#7A8D5EFF", "#FEFDE4FF")
ggplot(cv_model_purpose) +
  geom_col(aes(x=dummy, y=count, fill = reorder(cv_model_purpose, count)), 
           position = "fill",
           width = 0.8) +
  scale_y_continuous(name = "Percentage of publications", 
                     labels = scales::label_percent()) +
  scale_x_discrete(expand = expansion(add =c(0.8,0))) + # Add this line to control the space around the plot on the x-axis
  # paletteer::scale_fill_paletteer_d("nord::mountain_forms", guide = guide_legend(reverse = TRUE)) +
  scale_fill_manual(values = palette, guide = guide_legend(reverse = TRUE)) +
  coord_flip() +
  labs(x="", fill = "", title = "Purposes of computer vision models",
       subtitle = "used by the reviewed papers") +
  theme_ipsum() +
  theme(legend.position = "bottom",
        panel.grid.major.y = element_blank(),
        plot.margin = margin(0, 0, 0, 0))
ggsave(paste0(dir_figure, "cv_model_purpose.png"), width = 10, height = 4)

# cv_model_training ----------------------------------------------------
cv_model_training <- read.csv(paste0("data/processed/", round, "/cv_model.csv")) %>%
  left_join(citations, by = "X0") %>%
  filter(!is.na(record_id)) %>% 
  rename("cv_model_training" = "X2", "filename" = "X0") %>% 
  filter(cv_model_training != "") %>% 
  mutate(cv_model_training = tolower(cv_model_training),
         cv_model_training = case_when(
           str_detect(cv_model_training, "pre-trained with fine-tuning") ~ "pre-trained with fine-tuning",
           str_detect(cv_model_training, "pre-trained without fine-tuning") | str_detect(cv_model_training, "retrain") ~ "pre-trained without fine-tuning",
           str_detect(cv_model_training, "trained") | str_detect(cv_model_training, "trained with")  ~ "trained from scratch",
           TRUE ~  "not applicable"
         )) %>% 
  group_by(cv_model_training) %>% 
  summarize(count=n()) %>% 
  mutate(dummy="")
palette <- c("#FBCB74FF", "darkgray", "#78D3D7FF", "#AED8A1FF", "#E8A3A0FF", "#A899A0FF")
ggplot(cv_model_training) +
  geom_col(aes(x=dummy, y=count, fill = reorder(cv_model_training, count)), 
           position = "fill",
           width = 0.8) +
  scale_y_continuous(name = "Percentage of publications", 
                     labels = scales::label_percent()) +
  scale_x_discrete(expand = expansion(add =c(0.8,0))) + # Add this line to control the space around the plot on the x-axis
  scale_fill_manual(values = palette, guide = guide_legend(reverse = TRUE)) +
  coord_flip() +
  labs(x="", fill = "", title = "Training processes for computer vision models",
       subtitle = "used by the reviewed papers") +
  theme_ipsum() +
  theme(legend.position = "bottom",
        panel.grid.major.y = element_blank(),
        plot.margin = margin(0, 0, 0, 0))
ggsave(paste0(dir_figure, "cv_model_training.png"), width = 10, height = 4)


# code_availability ----------------------------------------------------
code_availability <- read.csv(paste0("data/processed/", round, "/code_availability.csv")) %>%
  left_join(citations, by = "X0") %>%
  filter(!is.na(record_id)) %>% 
  filter(code_availability != "") %>% 
  mutate(code_availability = tolower(code_availability),
         code_availability = case_when(
           str_detect(code_availability, "not mentioned") ~ "not mentioned",
           str_detect(code_availability, "via") ~ "code available via URL",
           str_detect(code_availability, "request")  ~ "code available upon request",
           str_detect(code_availability, "not available")  ~ "code not available",
           str_detect(code_availability, "code available")  ~ "code available upon request",
           TRUE ~  code_availability
         )) %>% 
  group_by(code_availability) %>% 
  summarize(count=n()) %>% 
  mutate(dummy="")
palette <- happy_pastel_palette_adjusted_6 <- c("#E7D38DFF", "darkgray", "#E89B8DFF", "#8DB0C5FF")
ggplot(code_availability) +
  geom_col(aes(x=dummy, y=count, fill = reorder(code_availability, count)), 
           position = "fill",
           width = 0.5) +
  scale_y_continuous(name = "Percentage of publications", 
                     labels = scales::label_percent()) +
  scale_x_discrete(expand = expansion(add =c(0.8,0))) + # Add this line to control the space around the plot on the x-axis
  # paletteer::scale_fill_paletteer_d("ggthemes::wsj_rgby", guide = guide_legend(reverse = TRUE)) +
  scale_fill_manual(values = palette, guide = guide_legend(reverse = TRUE)) +
  coord_flip() +
  labs(x="", fill = "", title = "Availability of code",
       subtitle = "among the reviewed papers") +
  theme_ipsum() +
  theme(legend.position = "bottom",
        panel.grid.major.y = element_blank(),
        plot.margin = margin(0, 0, 0, 0))
ggsave(paste0(dir_figure, "code_availability.png"), width = 10, height = 4)


# data_availability ----------------------------------------------------
data_availability <- read.csv(paste0("data/processed/", round, "/data_availability.csv")) %>%
  left_join(citations, by = "X0") %>%
  filter(!is.na(record_id)) %>% 
  filter(data_availability != "") %>% 
  mutate(data_availability = tolower(data_availability),
         data_availability = case_when(
           str_detect(data_availability, "not mentioned") ~ "not mentioned",
           str_detect(data_availability, "via") ~ "data available via URL",
           str_detect(data_availability, "url") ~ "data available via URL",
           str_detect(data_availability, "online") ~ "data available via URL",
           str_detect(data_availability, "github") ~ "data available via URL",
           str_detect(data_availability, "request")  ~ "data available upon request",
           str_detect(data_availability, "not available")  ~ "data not available",
           str_detect(data_availability, "data available") & str_detect(data_availability, "restrictions") ~ "data available upon request",
           TRUE ~ data_availability
         )) %>% 
  group_by(data_availability) %>% 
  summarize(count=n()) %>% 
  mutate(dummy="")
palette <- c("darkgray","#F2D48DFF", "#A8C7A7FF", "#A9A08AFF")
ggplot(data_availability) +
  geom_col(aes(x=dummy, y=count, fill = reorder(data_availability, count)), 
           position = "fill",
           width = 0.8) +
  scale_y_continuous(name = "Percentage of publications", 
                     labels = scales::label_percent()) +
  scale_x_discrete(expand = expansion(add =c(0.8,0))) + # Add this line to control the space around the plot on the x-axis
  # paletteer::scale_fill_paletteer_d("ggthemes::excel_Crop", guide = guide_legend(reverse = TRUE)) +
  scale_fill_manual(values = palette, guide = guide_legend(reverse = TRUE)) +
  coord_flip() +
  labs(x="", fill = "", title = "Availability of data",
       subtitle = "among the reviewed papers") +
  theme_ipsum() +
  theme(legend.position = "bottom",
        panel.grid.major.y = element_blank(),
        plot.margin = margin(0, 0, 0, 0))
ggsave(paste0(dir_figure, "data_availability.png"), width = 10, height = 4)

# irb ----------------------------------------------------
irb <- read.csv(paste0("data/processed/", round, "/irb.csv")) %>%
  left_join(citations, by = "X0") %>%
  filter(!is.na(record_id)) %>% 
  rename("irb" = "irb_approval") %>% 
  filter(irb != "") %>% 
  mutate(irb = tolower(irb),
         irb = case_when(
           str_detect(irb, "yes") ~ "Mentioned",
           TRUE ~ "Not mentioned"
         )) %>% 
  group_by(irb) %>% 
  summarize(count=n()) %>% 
  mutate(dummy="")
palette <- c("darkgray", "#E8A5D4FF")
ggplot(irb) +
  geom_col(aes(x=dummy, y=count, fill = reorder(irb, count)), 
           position = "fill",
           width = 0.8) +
  scale_y_continuous(name = "Percentage of publications", 
                     labels = scales::label_percent()) +
  scale_x_discrete(expand = expansion(add =c(0.8,0))) + # Add this line to control the space around the plot on the x-axis
  # paletteer::scale_fill_paletteer_d("ggthemes::excel_Crop", guide = guide_legend(reverse = TRUE)) +
  scale_fill_manual(values = palette, guide = guide_legend(reverse = TRUE)) +
  coord_flip() +
  labs(x="", fill = "", title = "Approval from institutional review boards",
       subtitle = "among the reviewed papers") +
  theme_ipsum() +
  theme(legend.position = "bottom",
        panel.grid.major.y = element_blank(),
        plot.margin = margin(0, 0, 0, 0))
ggsave(paste0(dir_figure, "irb.png"), width = 10, height = 4)


# sankey diagram of all the attributes ------------------------------------
aspect_sankey <- read.csv(paste0("data/processed/", round, "/aspect.csv")) %>% 
  distinct(DOI, .keep_all = T) %>% 
  group_by(aspect) %>% 
  mutate(
    count=n(),
    aspect = case_when(
    count < 2 ~ "others",
    TRUE ~ aspect))
  
extent_sankey <- read.csv(paste0("data/processed/", round, "/extent.csv")) %>% 
  distinct(DOI, .keep_all = T) 

image_data_type_sankey <- read.csv(paste0("data/processed/", round, "/image_data_type.csv")) %>% 
  filter(image_data_type != "") %>% 
  group_by(image_data_type) %>% 
  mutate(
    count=n(),
    image_data_type = case_when(
      count < 3 ~ "others",
      TRUE ~ image_data_type)) %>% 
  group_by(DOI) %>% 
  mutate(count=n(),
         image_data_type=case_when(
           count > 1 ~ "mixed",
           T ~ image_data_type
         )) %>% 
  distinct(DOI, .keep_all = T) %>% 
  mutate(image_data_type=case_when(
    image_data_type == "" ~ "None",
    T ~ image_data_type
  ))

subjective_data_type_sankey <- read.csv(paste0("data/processed/", round, "/subjective_data_type.csv")) %>% 
  mutate(subjective_data_type=case_when(
    str_detect(subjective_data_type, "public") ~ "publicly available data",
    str_detect(subjective_data_type, "subjective") ~ "their own collection",
    str_detect(subjective_data_type, "survey") ~ "their own collection",
    TRUE ~ subjective_data_type
  )) %>% 
  filter(subjective_data_type=="publicly available data" | subjective_data_type=="their own collection") %>% 
  group_by(DOI) %>% 
  mutate(count=n(),
         subjective_data_type=case_when(
           count > 1 ~ "mixed with publicly available data",
           T ~ subjective_data_type
         )) %>% 
  distinct(DOI, .keep_all = T) %>% 
  mutate(subjective_data_type=case_when(
    subjective_data_type == "" ~ "None",
    T ~ subjective_data_type
  ))

other_sensory_data_sankey <- read.csv(paste0("data/processed/", round, "/other_sensory_data.csv")) %>%
  distinct(DOI,other_sensory_data) %>% 
  group_by(DOI) %>%
  mutate(flag = ifelse(any(other_sensory_data != "None"), 1, 0)) %>% 
  ungroup() %>% 
  filter(!(other_sensory_data=="None"&flag==1)) %>% 
  distinct(DOI,other_sensory_data) %>% 
  group_by(DOI) %>% 
  mutate(count=n(),
         other_sensory_data=case_when(
           count > 1 ~ "mixed",
           T ~ other_sensory_data
         )) %>% 
  distinct(DOI, .keep_all = T) %>% 
  mutate(other_sensory_data=case_when(
    other_sensory_data == "" ~ "None",
    T ~ other_sensory_data
  ))

type_of_research_sankey <- read.csv(paste0("data/processed/", round, "/type_of_research.csv")) %>%
  distinct(DOI,type_of_research) %>% 
  group_by(DOI) %>% 
  mutate(count=n(),
         type_of_research=case_when(
           count > 1 ~ "mixed",
           T ~ type_of_research
         )) %>% 
  distinct(DOI, .keep_all = T) %>% 
  mutate(type_of_research=case_when(
    type_of_research == "" ~ "None",
    T ~ type_of_research
  ))

type_of_research_detail_sankey <- read.csv(paste0("data/processed/", round, "/type_of_research_detail.csv")) %>% 
  distinct(DOI,type_of_research_detail) %>% 
  group_by(DOI) %>% 
  mutate(count=n(),
         type_of_research_detail=case_when(
           count > 1 ~ "mixed",
           T ~ type_of_research_detail
         )) %>% 
  distinct(DOI, .keep_all = T) %>% 
  mutate(type_of_research_detail=case_when(
    type_of_research_detail == "" ~ "None",
    T ~ type_of_research_detail
  ))

cv_model_purpose_sankey <- read.csv(paste0("data/processed/", round, "/cv_model_purpose.csv")) %>% 
  filter(cv_model_purpose != "") %>% 
  mutate(cv_model_purpose = tolower(cv_model_purpose),
         cv_model_purpose = case_when(
           str_detect(cv_model_purpose, "classification") ~ "image classification",
           str_detect(cv_model_purpose, "detection") | str_detect(cv_model_purpose, "object")  ~ "object detection",
           str_detect(cv_model_purpose, "segmentation") ~ "semantic/instance segmentation",
           str_detect(cv_model_purpose, "extraction") ~ "feature extraction",
           TRUE ~ "others"
         )) %>% 
  distinct(DOI,cv_model_purpose) %>% 
  group_by(DOI) %>% 
  mutate(count=n(),
         cv_model_purpose=case_when(
           count > 1 ~ "mixed",
           T ~ cv_model_purpose
         )) %>% 
  distinct(DOI, .keep_all = T) %>% 
  mutate(cv_model_purpose=case_when(
    cv_model_purpose == "" ~ "None",
    T ~ cv_model_purpose
  ))

cv_model_training_sankey <- read.csv(paste0("data/processed/", round, "/cv_model_training.csv")) %>%
  filter(cv_model_training != "") %>% 
  mutate(cv_model_training = tolower(cv_model_training),
         cv_model_training = case_when(
           str_detect(cv_model_training, "pre-trained with fine-tuning") ~ "pre-trained with fine-tuning",
           str_detect(cv_model_training, "pre-trained without fine-tuning") ~ "pre-trained without fine-tuning",
           str_detect(cv_model_training, "trained") | str_detect(cv_model_training, "trained with")  ~ "trained from scratch",
           TRUE ~ "others"
         )) %>% 
  filter(cv_model_training!="others") %>% 
  distinct(DOI,cv_model_training) %>% 
  group_by(DOI) %>% 
  mutate(count=n(),
         cv_model_training=case_when(
           count > 1 ~ "mixed",
           T ~ cv_model_training
         )) %>% 
  distinct(DOI, .keep_all = T) %>% 
  mutate(cv_model_training=case_when(
    cv_model_training == "" ~ "None",
    T ~ cv_model_training
  ))

code_availability_sankey <- read.csv(paste0("data/processed/", round, "/code_availability.csv")) %>% 
  filter(code_availability != "") %>% 
  mutate(code_availability = tolower(code_availability),
         code_availability = case_when(
           str_detect(code_availability, "not mentioned") ~ "not mentioned",
           str_detect(code_availability, "via") ~ "code available via URL",
           str_detect(code_availability, "request")  ~ "code available upon request",
           str_detect(code_availability, "not available")  ~ "code not available",
           TRUE ~ "others"
         )) %>% 
  distinct(DOI,code_availability) %>% 
  group_by(DOI) %>% 
  mutate(count=n(),
         code_availability=case_when(
           count > 1 ~ "mixed",
           T ~ code_availability
         )) %>% 
  distinct(DOI, .keep_all = T) %>% 
  mutate(code_availability=case_when(
    code_availability == "" ~ "None",
    T ~ code_availability
  ))

data_availability_sankey <- read.csv(paste0("data/processed/", round, "/data_availability.csv")) %>%
  filter(data_availability != "") %>% 
  mutate(data_availability = tolower(data_availability),
         data_availability = case_when(
           str_detect(data_availability, "not mentioned") ~ "not mentioned",
           str_detect(data_availability, "via") ~ "data available via URL",
           str_detect(data_availability, "request")  ~ "data available upon request",
           str_detect(data_availability, "not available")  ~ "data not available",
           TRUE ~ "others"
         )) %>% 
  distinct(DOI,data_availability) %>% 
  group_by(DOI) %>% 
  mutate(count=n(),
         data_availability=case_when(
           count > 1 ~ "mixed",
           T ~ data_availability
         )) %>% 
  distinct(DOI, .keep_all = T) %>% 
  mutate(data_availability=case_when(
    data_availability == "" ~ "None",
    T ~ data_availability
  ))

df_list <- list(
            aspect_sankey, 
            extent_sankey,
            image_data_type_sankey,
            subjective_data_type_sankey,
            other_sensory_data_sankey,
            type_of_research_sankey,
            type_of_research_detail_sankey,
            cv_model_purpose_sankey,
            cv_model_training_sankey,
            code_availability_sankey,
            data_availability_sankey
            )

joined_sankey <- reduce(df_list, left_join, by = "DOI") %>% 
  select(-contains("count")) %>% 
  mutate_all(~replace_na(.,"None")) %>% 
  mutate_all(~str_replace_all(.,"None", "NA")) %>% 
  mutate(percentage=1/nrow(.)*100)
# check the data
is_alluvia_form(as.data.frame(joined_sankey), axes = 1:3, silent = TRUE)

# plot
ggplot(as.data.frame(joined_sankey),
       aes(y = percentage,
           axis1 = aspect, 
           axis2 = extent, 
           axis3 = image_data_type,
           axis4 = subjective_data_type,
           axis5 = other_sensory_data,
           axis6 = type_of_research,
           axis7 = type_of_research_detail,
           axis8 = cv_model_purpose,
           axis9 = cv_model_training,
           axis10 = code_availability,
           axis11 = data_availability)) +
  geom_flow(aes(fill = aspect)) +
  paletteer::scale_fill_paletteer_d("rcartocolor::Antique", guide = guide_legend(reverse = TRUE)) +
  geom_stratum(alpha = .75, reverse = FALSE) +
  geom_label_repel(stat = "stratum", aes(label = after_stat(stratum)),
            reverse = FALSE, size = 5, fill = alpha(c("white"),0.5), 
            box.padding = 0.5, max.overlaps = Inf) +
  scale_x_continuous(breaks = 1:length(df_list), labels = c("Aspect", 
                                              "Study area extent", 
                                              "Visual data type", 
                                              "Subjective data type",
                                              "Other sensory data",
                                              "Type of research",
                                              "Type of research in detail",
                                              "Purpose of computer models",
                                              "Training processes for computer vision models",
                                              "Availability of code",
                                              "Availability of data"
                                              )) +
  coord_flip() +
  labs(title = "Reviewed studies by their characteristics") +
  theme_ipsum() +
  theme(legend.position = "bottom",
        axis.text = element_text(size = 20))
ggsave(paste0(dir_figure, "sankey.png"), width = 20, height = 10)

# table: citation, aspect, image data type, subjective data type ----------
# load data
aspect_table <- read.csv(paste0("data/processed/", round, "/recalibrated_aspect.csv")) %>% 
  distinct(X0, improved_aspect) %>% 
  left_join(citations, by = "X0") %>%
  filter(!is.na(record_id)) %>% 
  mutate(aspect = tolower(improved_aspect)) %>%
  mutate(aspect = str_trim(str_split_fixed(aspect, ",", 2)[,1])) %>% 
  group_by(aspect) %>% 
  mutate(
    count = n(),
    aspect = case_when(
      X0 == "978-3-319-95588-9_67.pdf" ~ "public space",
      str_detect(aspect, "reclassify the aspect of the study") ~ "greenery",
      str_detect(aspect, "others: study methodology") ~ "landscape",
      str_detect(aspect, "others: sensory perception") ~ "landscape",
      str_detect(aspect, "others: visual aesthetics") ~ "landscape",
      str_detect(aspect, "others: population prediction") ~ "public space",
      TRUE ~ aspect)) %>% 
  rename("file_name" = "X0")

citations_table <- read.csv(paste0("data/processed/", round, "/citations_by_aspect.csv")) %>% 
  rename("count"="aspect.1") %>% 
  mutate(aspect = case_when(
    aspect == "the summary provided does not contain enough information to reclassify the aspect. please provide a more detailed summary." ~ "public space",
    str_detect(aspect, "reclassify the aspect of the study") ~ "greenery",
    str_detect(aspect, "others: study methodology") ~ "landscape",
    str_detect(aspect, "others: sensory perception") ~ "landscape",
    str_detect(aspect, "others: visual aesthetics") ~ "landscape",
    str_detect(aspect, "others: population prediction") ~ "public space",
    TRUE ~ aspect)) %>% 
  group_by(aspect) %>%
  summarise(citations = paste(citations, collapse = ", "),
            count = sum(count)) %>% 
  arrange(desc(count))

subjective_data_type_table <-read.csv(paste0("data/processed/", round, "/perception_data_type.csv")) %>%
  left_join(citations, by = "X0") %>%
  filter(!is.na(record_id)) %>% 
  rename("file_name" = "X0") %>% 
  mutate(
    X0.1 = tolower(X0.1),
    subjective_data_type=case_when(
      str_detect(X0.1, "public") ~ "publicly available data",
      str_detect(X0.1, "subjective") ~ "their own collection",
      str_detect(X0.1, "survey") ~ "their own collection",
      str_detect(X0.1, "collection") ~ "their own collection",
      str_detect(X0.1, "questionnaire") ~ "their own collection",
      str_detect(X0.1, "pulse") ~ "publicly available data",
      str_detect(X0.1, "existing") ~ "publicly available data",
      TRUE ~ X0.1
    )) %>% 
  filter(subjective_data_type=="publicly available data" | subjective_data_type=="their own collection") %>%
  distinct(file_name,subjective_data_type)

image_data_type_table <- read.csv(paste0("data/processed/", round, "/recalibrated_image_data_type.csv")) %>%
  left_join(citations, by = "X0") %>%
  filter(!is.na(record_id)) %>% 
  rename("file_name" = "X0", 
         "image_data_type" = "improved_image_data_type") %>% 
  distinct(file_name,image_data_type) %>% 
  filter(image_data_type != "") %>% 
  group_by(image_data_type) %>% 
  mutate(
    count = n(),
    image_data_type = case_when(
    count < 3 ~ "others",
    TRUE ~ image_data_type)) %>% 
  group_by(image_data_type) %>% 
  mutate(
    count = n())


# merge subjective and image data type
aspect_subjective_image <- left_join(subjective_data_type_table, aspect_table, by = "file_name") %>% 
  left_join(., image_data_type_table, by = "file_name") %>% 
  select(aspect, subjective_data_type, image_data_type)

# !SUBJECTIVE DATA TYPE!
color_palette <- c("publicly available data" = "#eec643", "their own collection" = "darkgray")
# Calculate the ratio of subjective data types for each aspect
percentages_subjective <- aspect_subjective_image %>%
  group_by(aspect, subjective_data_type) %>%
  summarize(count = n()) %>%
  mutate(percentage = count / sum(count),
         subjective_data_type = factor(subjective_data_type, levels = rev(names(color_palette)))) %>%
  ungroup()

# Create a stacked bar plot for each aspect and save them as images
unique_aspects_subjective <- unique(percentages_subjective$aspect)
for (aspect_subjective in unique_aspects_subjective) {
  plot_data <- filter(percentages_subjective, aspect == !!aspect_subjective)
  
  # Create the plot
  p <- ggplot(plot_data, aes(x = aspect, y = percentage, fill = subjective_data_type)) +
    geom_bar(stat = "identity", width = 0.8) +
    scale_y_continuous(labels = scales::percent_format()) +
    scale_x_discrete(expand = expansion(add =c(0.8,0))) + # Add this line to control the space around the plot on the x-axis
    scale_fill_manual(values = color_palette, 
                      guide = guide_legend(reverse = TRUE),
                      limits = names(color_palette)) + # Add custom color palette
    labs(x="", y="", fill = "")+
    theme_minimal() +
    theme(axis.ticks.x = element_blank(),
          axis.text.x = element_blank(),
          panel.grid.major.x = element_blank(),
          panel.grid.minor = element_blank(),
          plot.margin = margin(0, 0, 0, 0))
  
  # Save the plot as an image
  ggsave(paste0(dir_figure, "subjective_bar_plot_", aspect_subjective, ".png"), plot = p, width = 3, height = 3, dpi = 1000)
}

# Add a new column with the image file name for each aspect
aspect_subjective_unique <- aspect_subjective_image %>% 
  distinct(aspect, .keep_all = T) %>% 
  mutate(image_file = paste0("fig/subjective_bar_plot_", aspect, ".png")) %>% 
  select(aspect, `Subjective data types` = image_file)

# !IMAGE DATA TYPE!
palette <- c("#9FCBB2", "#9FAFCC", "#A098C2", "#D69BA3", "#F5B89F", "#D5C5A8", "#DFA7B9")
color_palette <- setNames(palette, image_data_type$image_data_type)
# Calculate the ratio of image data types for each aspect
percentages_image <- aspect_subjective_image %>%
  filter(!is.na(image_data_type)) %>% 
  group_by(aspect, image_data_type) %>%
  summarize(count = n()) %>%
  mutate(percentage = count / sum(count),
         image_data_type = factor(image_data_type, levels = rev(names(color_palette)))) %>%
  ungroup()

# Create a stacked bar plot for each aspect and save them as images
unique_aspects_image <- unique(percentages_image$aspect)
for (aspect_image in unique_aspects_image) {
  plot_data <- filter(percentages_image, aspect == !!aspect_image)
  
  # Create the plot
  p <- ggplot(plot_data, aes(x = aspect, y = percentage, fill = image_data_type)) +
    geom_bar(stat = "identity", width = 0.8) +
    scale_y_continuous(labels = scales::percent_format()) +
    scale_x_discrete(expand = expansion(add =c(0.8,0))) + # Add this line to control the space around the plot on the x-axis
    scale_fill_manual(values = color_palette, 
                      guide = guide_legend(reverse = TRUE),
                      limits = names(color_palette)) + # Add custom color palette
    labs(x="", y="", fill = "")+
    theme_minimal() +
    theme(axis.ticks = element_blank(),
          axis.text.x = element_blank(),
          panel.grid.major.x = element_blank(),
          panel.grid.minor = element_blank(),
          plot.margin = margin(0, 0, 0, 0))
  
  # Save the plot as an image
  ggsave(paste0(dir_figure, "image_bar_plot_", aspect_image, ".png"), plot = p, width = 3.1, height = 3, dpi = 1000)
}

# Add a new column with the image file name for each aspect
aspect_image_unique <- aspect_subjective_image %>% 
  distinct(aspect, .keep_all = T) %>% 
  mutate(image_file = paste0("fig/image_bar_plot_", aspect, ".png")) %>% 
  select(aspect, `Image data types` = image_file)

# !CITATIONS!
# Helper function to split the citation string into groups of 3 citations and wrap them in a nested tabular environment
split_citations <- function(citations) {
  citation_list <- strsplit(citations, ", ")[[1]]
  citation_groups <- split(citation_list, ceiling(seq_along(citation_list)/2))
  citation_lines <- sapply(citation_groups, paste, collapse = ", ")
  paste0("\\begin{tabular}[t]{@{}l@{}}", paste(citation_lines, collapse = " \\\\ "), "\\end{tabular}")
}

# Apply the helper function to the 'citations' column
citations_table$citations <- sapply(citations_table$citations, split_citations)

# !COMBINE!
table_joined <- citations_table %>% 
  left_join(., aspect_subjective_unique, by = "aspect") %>% 
  left_join(., aspect_image_unique, by = "aspect") %>% 
  select(Aspect = aspect, `# of papers` = count, contains("data types"))

# Custom sanitize function for including images
include_image <- function(text) {
  if (any(grepl("bar_plot_", text))) {
    sprintf("\\raisebox{-0.9cm}{\\includegraphics[width=3cm,height=3cm]{%s}}", text)
  } else {
    text
  }
}

# Convert the dataframe to a LaTeX table using the xtable function
latex_table <- xtable(table_joined)

sink(paste0("data/processed/", round, "/overview_aspect.tex"))
# Print the LaTeX table
print(latex_table,
      sanitize.text.function = include_image,
      include.rownames = FALSE,
      caption = "Overview of the papers by aspect",
      caption.placement = "top",
      table.placement = "tbp")
sink()

