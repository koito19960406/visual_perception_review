pacman::p_load(tidyverse, hrbrthemes, scales, paletteer, sf, basemaps, ggalluvial,
               ggrepel, xtable)


# journal -----------------------------------------------------------------
journal <- read.csv("data/external/scopus_with_journal.csv") %>% 
  group_by(Source.title) %>% 
  summarize(count=n()) %>% 
  drop_na(Source.title) %>% 
  filter(count>10)

ggplot(journal) +
  geom_col(aes(x=reorder(Source.title,count), y=count)) +
  labs(x = "Journals",
       y = "number of papers",
       title = "Journal names by number of papers",
       caption = "Data: papers downloaded from Scopus on 2023/03/23") +
  coord_flip() +
  theme_ipsum() +
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1, size = 6),
        plot.title = element_text(hjust=1))
ggsave("reports/figures/jounral.png", width = 10, height = 10)

# number of papers --------------------------------------------------------
scopus_initial <- read.csv("data/external/scopus_20230323.csv") %>% 
  mutate(Year=case_when(
    Year < 2000 ~ 1999,
    TRUE ~ as.numeric(Year))) %>% 
  group_by(Year) %>% 
  summarize(count=n()) %>% 
  drop_na(Year)
ggplot(scopus_initial) +
  geom_col(aes(x=Year, y=count)) +
  scale_x_continuous(breaks = c(1999, 2005, 2010, 2015, 2020),
                     labels = c("1960 - 2000",2005,2010,2015,2020)) +
  labs(y = "number of papers",
       title = "Papers containing relevant keywords",
       caption = "Data: papers downloaded from Scopus on 2023/03/23") +
  theme_ipsum()
ggsave("reports/figures/num_papers.png", width = 5, height =5)


# aspect ------------------------------------------------------------------
aspect <- read.csv("data/processed/aspect.csv") %>% 
  group_by(aspect) %>% 
  summarize(count=n()) %>% 
  mutate(aspect = case_when(
    count < 2 ~ "others",
    TRUE ~ aspect)) %>% 
  group_by(aspect) %>% 
  summarize(count=sum(count)) %>% 
  mutate(dummy="") 
palette <- paletteer::paletteer_d("rcartocolor::Antique")[3:(length(unique(aspect$aspect))+2)]
ggplot(aspect) +
  geom_col(aes(x=dummy, y=count, fill = reorder(aspect, count)), 
           position = "fill",
           width = 1) +
  scale_y_continuous(name = "Percentage of publications", 
                     labels = scales::label_percent()) +
  scale_x_discrete(expand = expansion(add =c(0.8,0))) + # Add this line to control the space around the plot on the x-axis
  # paletteer::scale_fill_paletteer_d("rcartocolor::Antique", guide = guide_legend(reverse = TRUE)) +
  scale_fill_manual(values = palette, guide = guide_legend(reverse = TRUE)) +
  coord_flip() +
  labs(x="", fill = "", title = "Aspects of the built environment",
       subtitle = "studied by reviewed papers") +
  theme_ipsum() +
  theme(legend.position = "bottom",
        panel.grid.major.y = element_blank())
ggsave("reports/figures/aspects.png", width = 10, height = 4)


# location ----------------------------------------------------------------
location <- read.csv("data/processed/location.csv") %>% 
  st_as_sf(coords = c("latitude","longitude"), crs = 4326) %>% 
  st_transform(3857)
bbox <- st_bbox(c(xmin = -180, xmax = 180, ymin = -60, ymax =80), crs = st_crs(4326))
basemap_ggplot(bbox, map_service = "carto", map_type = "light", force = T) +
  geom_sf(data = location, color = "red", size = 0.5) +
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
ggsave("reports/figures/location.png", width = 5, height =5)


# extent ------------------------------------------------------------------
extent <- read.csv("data/processed/extent.csv") %>%
  filter(extent != "None") %>% 
  group_by(extent) %>% 
  summarize(count=n()) %>% 
  mutate(dummy="") 

ggplot(extent) +
  geom_col(aes(x=dummy, y=count, fill = reorder(extent, count)), 
           position = "fill",
           width = 0.8) +
  scale_y_continuous(name = "Percentage of publications", 
                     labels = scales::label_percent()) +
  scale_x_discrete(expand = expansion(add =c(0.8,0))) + # Add this line to control the space around the plot on the x-axis
  paletteer::scale_fill_paletteer_d("ggthemes::excel_Feathered", guide = guide_legend(reverse = TRUE)) +
  coord_flip() +
  labs(x="", fill = "", title = "Extent of study areas",
       subtitle = "among reviewed papers") +
  theme_ipsum() +
  theme(legend.position = "bottom",
        panel.grid.major.y = element_blank())
ggsave("reports/figures/extent.png", width = 10, height = 4)



# image data type ------------------------------------------------------
image_data_type <- read.csv("data/processed/image_data_type.csv") %>%
  distinct(DOI,image_data_type) %>% 
  filter(image_data_type != "") %>% 
  group_by(image_data_type) %>% 
  summarize(count=n()) %>% 
  mutate(image_data_type = case_when(
    count < 3 ~ "others",
    TRUE ~ image_data_type)) %>% 
  group_by(image_data_type) %>% 
  summarize(count=sum(count)) %>% 
  mutate(dummy="") 
palette <- paletteer::paletteer_d("nord::aurora")
color_palette <- c("aerial image" = palette[1], 
                   "geo-tagged photos" = palette[2], 
                   "virtual reality" = palette[3], 
                   "others" = palette[4], 
                   "street view image" = palette[5]
                   )
ggplot(image_data_type) +
  geom_col(aes(x=dummy, y=count, fill = reorder(image_data_type, count)), 
           position = "fill",
           width = 0.8) +
  scale_y_continuous(name = "Percentage of publications", 
                     labels = scales::label_percent()) +
  scale_x_discrete(expand = expansion(add =c(0.8,0))) + # Add this line to control the space around the plot on the x-axis
  # paletteer::scale_fill_paletteer_d("nord::aurora", guide = guide_legend(reverse = TRUE)) +
  scale_fill_manual(values = color_palette, guide = guide_legend(reverse = TRUE)) + # Add custom color palette
  coord_flip() +
  labs(x="", fill = "", title = "Image data types",
       subtitle = "used by reviewed papers") +
  theme_ipsum() +
  theme(legend.position = "bottom",
        panel.grid.major.y = element_blank())
ggsave("reports/figures/image_data_type.png", width = 10, height =4)


# subjective data type ----------------------------------------------------
subjective_data_type <- read.csv("data/processed/subjective_data_type.csv") %>%
  mutate(subjective_data_type=case_when(
    str_detect(subjective_data_type, "public") ~ "publicly available data",
    str_detect(subjective_data_type, "subjective") ~ "their own collection",
    str_detect(subjective_data_type, "survey") ~ "their own collection",
    TRUE ~ subjective_data_type
  )) %>% 
  filter(subjective_data_type=="publicly available data" | subjective_data_type=="their own collection") %>%
  distinct(DOI,subjective_data_type) %>% 
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
        panel.grid.major.y = element_blank())
ggsave("reports/figures/subjective_data_type.png", width = 10, height = 4)


# subjective data source ----------------------------------------------------
subjective_data_source <- read.csv("data/processed/subjective_data_source.csv") %>%
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
        panel.grid.major.y = element_blank())
ggsave("reports/figures/subjective_data_source.png", width = 10, height = 4)


# subjective data size ----------------------------------------------------
subjective_data_size <- read.csv("data/processed/subjective_data_size.csv") %>%
  filter(subjective_data_size != "None") %>% 
  mutate(subjective_data_size=as.numeric(subjective_data_size),
         subjective_data_size=case_when(
           subjective_data_size>2000 ~ 2000,
           T ~ subjective_data_size
         ))

ggplot(subjective_data_size) +
  geom_histogram(aes(x=subjective_data_size),bins=20) +
  scale_x_continuous(labels = c(0,500,1000,1500,"> 2000")) +
  labs(x = "Number of participants",
       y = "Number of papers",
       title = "Number of participants",
       subtitle = "analyzed by reviewed papers",
       caption = "") +
  theme_ipsum()
ggsave("reports/figures/subjective_data_size.png", width = 10, height = 4)


# other_sensory_data ----------------------------------------------------
other_sensory_data <- read.csv("data/processed/other_sensory_data.csv") %>%
  group_by(DOI) %>%
  mutate(flag = ifelse(any(other_sensory_data != "None"), 1, 0)) %>% 
  ungroup() %>% 
  filter(!(other_sensory_data=="None"&flag==1)) %>% 
  distinct(DOI,other_sensory_data) %>% 
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
ggsave("reports/figures/other_sensory_data.png", width = 10, height = 4)


# type_of_research ----------------------------------------------------
type_of_research <- read.csv("data/processed/type_of_research.csv") %>%
  group_by(type_of_research) %>% 
  summarize(count=n()) %>% 
  mutate(dummy="")

ggplot(type_of_research) +
  geom_col(aes(x=dummy, y=count, fill = reorder(type_of_research, count)), 
           position = "fill",
           width = 0.8) +
  scale_y_continuous(name = "Percentage of publications", 
                     labels = scales::label_percent()) +
  scale_x_discrete(expand = expansion(add =c(0.8,0))) + # Add this line to control the space around the plot on the x-axis
  paletteer::scale_fill_paletteer_d("yarrr::ipod", guide = guide_legend(reverse = TRUE)) +
  coord_flip() +
  labs(x="", fill = "", title = "Type of research among reviewed papers",
       subtitle = "") +
  theme_ipsum() +
  theme(legend.position = "bottom",
        panel.grid.major.y = element_blank())
ggsave("reports/figures/type_of_research.png", width = 10, height = 4)

# type_of_research_detail ----------------------------------------------------
type_of_research_detail <- read.csv("data/processed/type_of_research_detail.csv") %>%
  distinct(DOI,type_of_research_detail) %>% 
  group_by(type_of_research_detail) %>% 
  summarize(count=n()) %>% 
  mutate(dummy="")
palette <- paletteer::paletteer_d("Redmonder::qMSOOr")[2:(length(unique(type_of_research_detail$type_of_research_detail))+1)]
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
        panel.grid.major.y = element_blank())
ggsave("reports/figures/type_of_research_detail.png", width = 10, height = 4)

# cv_model_purpose ----------------------------------------------------
cv_model_purpose <- read.csv("data/processed/cv_model_purpose.csv") %>%
  filter(cv_model_purpose != "") %>% 
  mutate(cv_model_purpose = tolower(cv_model_purpose),
    cv_model_purpose = case_when(
    str_detect(cv_model_purpose, "classification") ~ "image classification",
    str_detect(cv_model_purpose, "detection") | str_detect(cv_model_purpose, "object")  ~ "object detection",
    str_detect(cv_model_purpose, "segmentation") ~ "sementic/instance segmentation",
    str_detect(cv_model_purpose, "extraction") ~ "feature extraction",
    TRUE ~ "others"
  )) %>% 
  distinct(DOI,cv_model_purpose) %>% 
  group_by(cv_model_purpose) %>% 
  summarize(count=n()) %>% 
  mutate(dummy="")
palette <- rev(paletteer::paletteer_d("Redmonder::qMSOPap")[1:(length(unique(cv_model_purpose$cv_model_purpose))+2)])
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
        panel.grid.major.y = element_blank())
ggsave("reports/figures/cv_model_purpose.png", width = 10, height = 4)

# cv_model_training ----------------------------------------------------
cv_model_training <- read.csv("data/processed/cv_model_training.csv") %>%
  filter(cv_model_training != "") %>% 
  mutate(cv_model_training = tolower(cv_model_training),
         cv_model_training = case_when(
           str_detect(cv_model_training, "pre-trained with fine-tuning") ~ "pre-trained with fine-tuning",
           str_detect(cv_model_training, "pre-trained without fine-tuning") ~ "pre-trained without fine-tuning",
           str_detect(cv_model_training, "trained") | str_detect(cv_model_training, "trained with")  ~ "trained from scratch",
           TRUE ~ "others"
         )) %>% 
  filter(cv_model_training!="others") %>% 
  group_by(cv_model_training) %>% 
  summarize(count=n()) %>% 
  mutate(dummy="")

ggplot(cv_model_training) +
  geom_col(aes(x=dummy, y=count, fill = reorder(cv_model_training, count)), 
           position = "fill",
           width = 0.8) +
  scale_y_continuous(name = "Percentage of publications", 
                     labels = scales::label_percent()) +
  scale_x_discrete(expand = expansion(add =c(0.8,0))) + # Add this line to control the space around the plot on the x-axis
  paletteer::scale_fill_paletteer_d("ggthemes::excel_Badge", guide = guide_legend(reverse = TRUE)) +
  coord_flip() +
  labs(x="", fill = "", title = "Training processes for computer vision models",
       subtitle = "used by the reviewed papers") +
  theme_ipsum() +
  theme(legend.position = "bottom",
        panel.grid.major.y = element_blank())
ggsave("reports/figures/cv_model_training.png", width = 10, height = 4)


# code_availability ----------------------------------------------------
code_availability <- read.csv("data/processed/code_availability.csv") %>%
  filter(code_availability != "") %>% 
  mutate(code_availability = tolower(code_availability),
         code_availability = case_when(
           str_detect(code_availability, "not mentioned") ~ "not mentioned",
           str_detect(code_availability, "via") ~ "code available via URL",
           str_detect(code_availability, "request")  ~ "code available upon request",
           str_detect(code_availability, "not available")  ~ "code not available",
           TRUE ~ "others"
         )) %>% 
  group_by(code_availability) %>% 
  summarize(count=n()) %>% 
  mutate(dummy="")
palette <- rev(c("darkgray", paletteer::paletteer_d("ggthemes::wsj_rgby")[1:(length(unique(code_availability$code_availability))-1)]))
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
        panel.grid.major.y = element_blank())
ggsave("reports/figures/code_availability.png", width = 10, height = 4)


# data_availability ----------------------------------------------------
data_availability <- read.csv("data/processed/data_availability.csv") %>%
  filter(data_availability != "") %>% 
  mutate(data_availability = tolower(data_availability),
         data_availability = case_when(
           str_detect(data_availability, "not mentioned") ~ "not mentioned",
           str_detect(data_availability, "via") ~ "data available via URL",
           str_detect(data_availability, "request")  ~ "data available upon request",
           str_detect(data_availability, "not available")  ~ "data not available",
           TRUE ~ "others"
         )) %>% 
  group_by(data_availability) %>% 
  summarize(count=n()) %>% 
  mutate(dummy="")
palette <- rev(c("darkgray", paletteer::paletteer_d("ggthemes::excel_Crop")[2:(length(unique(data_availability$data_availability)))]))
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
        panel.grid.major.y = element_blank())
ggsave("reports/figures/data_availability.png", width = 10, height = 4)

# irb ----------------------------------------------------
irb <- read.csv("data/processed/irb.csv") %>%
  filter(irb != "") %>% 
  mutate(irb = tolower(irb),
         irb = case_when(
           str_detect(irb, "yes") ~ "Mentioned",
           TRUE ~ "Not mentioned"
         )) %>% 
  group_by(irb) %>% 
  summarize(count=n()) %>% 
  mutate(dummy="")
palette <- c("#CE69BEFF","darkgray")
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
  labs(x="", fill = "", title = "Approval from institurional review boards",
       subtitle = "among the reviewed papers") +
  theme_ipsum() +
  theme(legend.position = "bottom",
        panel.grid.major.y = element_blank())
ggsave("reports/figures/irb.png", width = 10, height = 4)


# sankey diagram of all the attributes ------------------------------------
aspect_sankey <- read.csv("data/processed/aspect.csv") %>% 
  distinct(DOI, .keep_all = T) %>% 
  group_by(aspect) %>% 
  mutate(
    count=n(),
    aspect = case_when(
    count < 2 ~ "others",
    TRUE ~ aspect))
  
extent_sankey <- read.csv("data/processed/extent.csv") %>% 
  distinct(DOI, .keep_all = T) 

image_data_type_sankey <- read.csv("data/processed/image_data_type.csv") %>% 
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

subjective_data_type_sankey <- read.csv("data/processed/subjective_data_type.csv") %>% 
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

other_sensory_data_sankey <- read.csv("data/processed/other_sensory_data.csv") %>%
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

type_of_research_sankey <- read.csv("data/processed/type_of_research.csv") %>%
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

type_of_research_detail_sankey <- read.csv("data/processed/type_of_research_detail.csv") %>% 
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

cv_model_purpose_sankey <- read.csv("data/processed/cv_model_purpose.csv") %>% 
  filter(cv_model_purpose != "") %>% 
  mutate(cv_model_purpose = tolower(cv_model_purpose),
         cv_model_purpose = case_when(
           str_detect(cv_model_purpose, "classification") ~ "image classification",
           str_detect(cv_model_purpose, "detection") | str_detect(cv_model_purpose, "object")  ~ "object detection",
           str_detect(cv_model_purpose, "segmentation") ~ "sementic/instance segmentation",
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

cv_model_training_sankey <- read.csv("data/processed/cv_model_training.csv") %>%
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

code_availability_sankey <- read.csv("data/processed/code_availability.csv") %>% 
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

data_availability_sankey <- read.csv("data/processed/data_availability.csv") %>%
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
ggsave("reports/figures/sankey.png", width = 20, height = 10)

# table: citation, aspect, image data type, subjective data type ----------
# load data
aspect_table <- read.csv("data/processed/aspect.csv") %>% 
  distinct(DOI, .keep_all = T) %>% 
  group_by(aspect) %>% 
  mutate(
    count=n(),
    aspect = case_when(
      count < 2 ~ "others",
      TRUE ~ aspect))

citations_table <- read.csv("data/processed/citations_by_aspect.csv") %>% 
  mutate(aspect = case_when(
    count < 2 ~ "others",
    TRUE ~ aspect)) %>% 
  group_by(aspect) %>%
  summarise(citations = paste(citations, collapse = ", "),
            count = sum(count)) %>% 
  arrange(desc(count))

subjective_data_type_table <- read.csv("data/processed/subjective_data_type.csv") %>%
  mutate(subjective_data_type=case_when(
    str_detect(subjective_data_type, "public") ~ "publicly available data",
    str_detect(subjective_data_type, "subjective") ~ "their own collection",
    str_detect(subjective_data_type, "survey") ~ "their own collection",
    str_detect(subjective_data_type, "perception") ~ "their own collection",
    TRUE ~ subjective_data_type
  )) %>% 
  filter(subjective_data_type=="publicly available data" | subjective_data_type=="their own collection") %>%
  distinct(DOI,subjective_data_type)

image_data_type_table <- read.csv("data/processed/image_data_type.csv") %>%
  distinct(DOI,image_data_type) %>% 
  filter(image_data_type != "") %>% 
  group_by(image_data_type) %>% 
  mutate(
    count=n(),
    image_data_type = case_when(
      count < 3 ~ "others",
      TRUE ~ image_data_type)) %>% 
  select(-count)

# merge subjective and image data type
aspect_subjective_image <- merge(subjective_data_type_table, aspect_table, by = "DOI") %>% 
  merge(., image_data_type_table, by = "DOI") %>% 
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
    scale_fill_manual(values = color_palette, guide = guide_legend(reverse = TRUE)) + # Add custom color palette
    labs(x="", y="", fill = "")+
    theme_minimal() +
    theme(axis.ticks.x = element_blank(),
          axis.text.x = element_blank(),
          panel.grid.major.x = element_blank(),
          panel.grid.minor = element_blank())
  
  # Save the plot as an image
  ggsave(paste0("reports/figures/subjective_bar_plot_", aspect_subjective, ".png"), plot = p, width = 3, height = 3, dpi = 1000)
}

# Add a new column with the image file name for each aspect
aspect_subjective_unique <- aspect_subjective_image %>% 
  distinct(aspect, .keep_all = T) %>% 
  mutate(image_file = paste0("fig/subjective_bar_plot_", aspect, ".png")) %>% 
  select(aspect, `Subjective data types` = image_file)

# !IMAGE DATA TYPE!
palette <- paletteer::paletteer_d("nord::aurora")
color_palette <- c("aerial image" = palette[1], 
                   "geo-tagged photos" = palette[2], 
                   "virtual reality" = palette[3], 
                   "others" = palette[4], 
                   "street view image" = palette[5]
)
# Calculate the ratio of image data types for each aspect
percentages_image <- aspect_subjective_image %>%
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
    scale_fill_manual(values = color_palette, guide = guide_legend(reverse = TRUE)) + # Add custom color palette
    labs(x="", y="", fill = "")+
    theme_minimal() +
    theme(axis.ticks = element_blank(),
          axis.text.x = element_blank(),
          panel.grid.major.x = element_blank(),
          panel.grid.minor = element_blank())
  
  # Save the plot as an image
  ggsave(paste0("reports/figures/image_bar_plot_", aspect_image, ".png"), plot = p, width = 2.8, height = 3, dpi = 1000)
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
citations$citations <- sapply(citations$citations, split_citations)

# !COMBINE!
table_joined <- citations %>% 
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

# Print the LaTeX table
print(latex_table,
      sanitize.text.function = include_image,
      include.rownames = FALSE,
      caption = "Overview of the papers by aspect",
      caption.placement = "top",
      table.placement = "tbp")

