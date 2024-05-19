theme_custom_dark <- function() {
    theme_ipsum() +
        theme(
            axis.text.y = element_text(vjust = 0.5, hjust = 1, size = 15),
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
            strip.text = element_text(colour = "white")
        )
}

theme_custom_light <- function() {
    theme_ipsum() +
        theme(
            legend.position = "bottom",
            panel.grid.major.y = element_blank(),
            plot.title = element_text(size = 25, margin = margin(b = 20)),
            plot.title.position = "plot",
            legend.text = element_text(size = 20),
            plot.margin = margin(20, 20, 20, 20),
            legend.title = element_blank(),
            legend.margin = margin(0, 0, 0, 0),
            # legend.spacing.x = unit(0, "mm"),
            # legend.spacing.y = unit(0, "mm") # Spacing between legend items horizontally
        )
}

plot_wordclouds <- function(path, round, dir_figure) {
    citation_df <- read.csv(paste0(path, "/data/processed/", round, "/citation_df.csv"))
    aspect <- read.csv(paste0(path, "/data/processed/", round, "/aspect.csv")) %>%
        mutate(improved_aspect = case_when(
            str_detect(improved_aspect, "greenery") | str_detect(improved_aspect, "waterscapes") ~ "greenery and water",
            str_detect(improved_aspect, "infrastructure") ~ "street design",
            TRUE ~ improved_aspect
        ))

    # Join dataframes by "X0"
    joined_df <- left_join(citation_df, aspect, by = "X0")

    # Ensure the stopwords dataset is available
    data("stop_words", package = "tidytext")

    # Loop through each unique aspect and create a word cloud
    set.seed(42) # For reproducibility
    for (i in unique(joined_df$improved_aspect)) {
        cat("Processing aspect:", i, "\n") # Print current aspect being processed

        # Filter the joined_df by the aspect and prepare data for the word cloud
        filtered_df <- joined_df %>%
            filter(improved_aspect == i) %>%
            unnest_tokens(word, Abstract) %>%
            count(word, sort = TRUE) %>%
            anti_join(stop_words) %>%
            filter(!word %in% c("study", "results")) %>%
            top_n(20, n)

        # Create word cloud plot
        plot <- ggplot(filtered_df) +
            geom_text_wordcloud(aes(label = word, size = n, color = factor(sample.int(7, nrow(filtered_df), replace = TRUE))), rm_outside = TRUE) +
            paletteer::scale_color_paletteer_d("MetBrewer::Veronese") +
            scale_size_area(max_size = 35) +
            theme_ipsum() +
            labs(title = paste("Word Cloud for", i))

        # Save the plot
        ggsave(paste0(dir_figure, "wordcloud_", gsub(" ", "_", i), ".png"), plot = plot, width = 10, height = 10)
    }
}

plot_heatmap <- function(path, round, dir_figure) {
    citation_df <- read.csv(paste0(path, "/data/processed/", round, "/citation_df.csv"))
    aspect <- read.csv(paste0(path, "/data/processed/", round, "/aspect.csv")) %>%
        mutate(improved_aspect = case_when(
            str_detect(improved_aspect, "greenery") | str_detect(improved_aspect, "waterscapes") ~ "greenery and water",
            str_detect(improved_aspect, "infrastructure") ~ "street design",
            str_detect(improved_aspect, "general urban environment") ~ "city as a whole",
            TRUE ~ improved_aspect
        ))

    # Join dataframes by "X0"
    joined_df <- left_join(citation_df, aspect, by = "X0")

    # Process data for heatmap
    grouped_df <- joined_df %>%
        mutate(Year = if_else(Year < 2000, 2000, Year)) %>%
        group_by(improved_aspect, Year) %>%
        summarize(count = n(), .groups = "drop") %>%
        drop_na(improved_aspect) %>%
        filter(improved_aspect != "others") %>%
        complete(improved_aspect, Year = 2000:2023, fill = list(count = 0)) %>%
        mutate(count = if_else(count > 20, 20, count)) %>%
        group_by(improved_aspect) %>%
        mutate(total = sum(count)) %>%
        ungroup() %>%
        mutate(improved_aspect = factor(improved_aspect, levels = unique(improved_aspect[order(total, decreasing = FALSE)]))) %>%
        arrange(improved_aspect, Year)

    # Create and save heatmap
    plot <- ggplot(grouped_df, aes(x = Year, y = improved_aspect, fill = count)) +
        geom_tile(color = "white") +
        scale_fill_viridis(
            name = "",
            option = "magma",
            limits = c(0, 20),
            breaks = c(0, 5, 10, 15, 20),
            labels = c("0", "5", "10", "15", ">=20")
        ) +
        labs(
            x = "Year",
            y = "",
            title = "Number of papers by aspect and year",
            caption = "Data: papers downloaded from Scopus on 2023/08/15"
        ) +
        theme_ipsum(base_size = 20) +
        theme(
            panel.grid.major = element_blank(),
            panel.grid.minor = element_blank(),
            legend.direction = "horizontal",
            legend.position = "bottom",
            legend.box.just = "center",
            legend.title = element_blank(),
            legend.key.width = unit(2, "cm"),
            plot.margin = margin(0, 0, 0, 0),
            axis.text.x = element_text(size = 12),
            axis.text.y = element_text(size = 12),
            plot.title.position = "panel",
            plot.title = element_text(face = "plain", vjust = -50, hjust = 0.53)
        ) +
        scale_x_continuous(
            breaks = c(2000, 2005, 2010, 2015, 2020, 2023),
            labels = c("1972-2000", "2005", "2010", "2015", "2020", "2023")
        ) +
        coord_fixed(ratio = 1) +
        labs(title = "Number of papers by year")

    ggsave(paste0(dir_figure, "heatmap.png"), plot = plot, width = 10, height = 5)
}

plot_num_papers <- function(scopus_input_path, dir_figure) {
    scopus_initial <- read.csv(scopus_input_path) %>%
        mutate(Year = case_when(
            Year < 2000 ~ 1999,
            TRUE ~ as.numeric(Year)
        )) %>%
        group_by(Year) %>%
        summarize(count = n(), .groups = "drop") %>%
        drop_na(Year)

    gg <- ggplot(scopus_initial, aes(x = Year, y = count)) +
        geom_col(aes(fill = ifelse(Year == 1999, "blue-gray", "default"))) +
        scale_fill_manual(values = c("blue-gray" = "#6699CC", "default" = "gray70")) +
        scale_x_continuous(
            breaks = c(1999, 2005, 2010, 2015, 2020, 2023),
            labels = c("1960 - 2000", "2005", "2010", "2015", "2020", "2023")
        ) +
        labs(
            y = "number of papers",
            title = "Papers containing relevant keywords",
            caption = "Data: papers downloaded from Scopus on 2023-07-19"
        ) +
        theme_ipsum() +
        theme(
            plot.margin = margin(0, 0, 0, 0),
            legend.position = "none"
        )

    # Ensure the directory exists
    if (!dir.exists(dir_figure)) {
        dir.create(dir_figure, recursive = TRUE)
    }

    # Save the plot
    ggsave(paste0(dir_figure, "num_papers.png"), plot = gg, width = 5, height = 5)
}

plot_aspects <- function(path, round, dir_figure) {
    citations <- read.csv(paste0(path, "/data/processed/", round, "/citation_df.csv")) %>%
        dplyr::select(record_id, X0)

    aspect <- read.csv(paste0(path, "/data/processed/", round, "/aspect.csv")) %>%
        distinct(X0, improved_aspect) %>%
        left_join(citations, by = "X0") %>%
        filter(!is.na(record_id)) %>%
        mutate(aspect = tolower(improved_aspect)) %>%
        mutate(aspect = str_trim(str_split_fixed(aspect, ",", 2)[, 1])) %>%
        group_by(aspect) %>%
        mutate(
            count = n(),
            aspect = case_when(
                X0 == "978-3-319-95588-9_67.pdf" ~ "public space",
                str_detect(improved_aspect, "greenery") | str_detect(improved_aspect, "waterscapes") ~ "greenery and water",
                str_detect(aspect, "reclassify the aspect of the study") ~ "greenery",
                str_detect(aspect, "others: study methodology") ~ "landscape",
                str_detect(aspect, "others: sensory perception") ~ "landscape",
                str_detect(aspect, "others: visual aesthetics") ~ "landscape",
                str_detect(aspect, "others: population prediction") ~ "public space",
                str_detect(aspect, "infrastructure") ~ "street design",
                str_detect(improved_aspect, "general urban environment") ~ "city as a whole",
                TRUE ~ aspect
            )
        ) %>%
        group_by(aspect) %>%
        summarize(count = n()) %>%
        mutate(dummy = "") %>%
        arrange(aspect != "others", count) %>%
        mutate(aspect = factor(aspect, levels = unique(aspect)))

    original_pastel_palette <- c(
        "#B6A6D2FF", "#D2A9AFFF", "#E8B57DFF", "#EDE3A9FF", "#8AA5A0FF",
        "#A2C5B4FF", "#C7C48DFF", "#D7B0B2FF", "#C89A76FF", "#56B0A3FF",
        "#7F9FC2FF", "#D4B5C3FF", "#A2E0CEFF"
    )

    aspect_plot <- ggplot(aspect) +
        geom_col(aes(x = dummy, y = count, fill = aspect),
            position = "fill",
            width = 0.7
        ) +
        scale_y_continuous(
            name = "Percentage of publications",
            labels = label_percent()
        ) +
        scale_fill_manual(values = original_pastel_palette, guide = guide_legend(nrow = 2, reverse = TRUE)) +
        coord_flip() +
        labs(x = "", fill = "", title = "Aspects of the built environment") +
        theme_custom_light()

    if (!dir.exists(dir_figure)) {
        dir.create(dir_figure, recursive = TRUE)
    }

    ggsave(paste0(dir_figure, "aspects.png"), plot = aspect_plot, width = 10, height = 4)
    return(aspect_plot)
}


plot_study_area <- function(path, round, dir_figure) {
    location_path <- paste0(path, "/data/processed/", round, "/study_area.csv")
    location <- read.csv(location_path) %>%
        mutate(
            latitude = as.numeric(lat),
            longitude = as.numeric(lon)
        ) %>%
        drop_na(c("longitude", "latitude")) %>%
        st_as_sf(coords = c("longitude", "latitude"), crs = 4326) %>%
        st_transform(crs = 3857) # Transform coordinates to Web Mercator

    bbox <- st_bbox(c(xmin = -180, xmax = 180, ymin = -60, ymax = 80), crs = st_crs(4326))
    plot <- basemap_ggplot(bbox, map_service = "carto", map_type = "light_no_labels", force = T) +
        geom_sf(data = location, color = "red", size = 0.5, alpha = 0.4, linewidth = 0) +
        labs(
            x = "", y = "", fill = "", title = "Locations of study areas",
            subtitle = "used by the reviewed papers",
            caption = "Basemap: carto"
        ) +
        theme_ipsum() +
        theme(
            axis.text.x = element_blank(),
            axis.text.y = element_blank(),
            axis.ticks = element_blank(),
            panel.grid.major = element_blank(),
            plot.margin = margin(
                t = 0, # Top margin
                r = 0, # Right margin
                b = 0, # Bottom margin
                l = 0
            )
        ) # Left margin)
    if (!dir.exists(dir_figure)) {
        dir.create(dir_figure, recursive = TRUE)
    }

    ggsave(paste0(dir_figure, "study_area.png"), plot = plot, width = 5, height = 5)
}

plot_researcher_location <- function(path, round, dir_figure) {
    location_path <- paste0(path, "/data/processed/", round, "/researcher_location.csv")
    location <- read.csv(location_path) %>%
        mutate(
            latitude = as.numeric(lat),
            longitude = as.numeric(lon)
        ) %>%
        drop_na(c("longitude", "latitude")) %>%
        st_as_sf(coords = c("longitude", "latitude"), crs = 4326) %>%
        st_transform(crs = 3857) # Transform coordinates to Web Mercator

    bbox <- st_bbox(c(xmin = -180, xmax = 180, ymin = -60, ymax = 80), crs = st_crs(4326))
    plot <- basemap_ggplot(bbox, map_service = "carto", map_type = "light_no_labels", force = T) +
        geom_sf(data = location, color = "red", size = 0.5, alpha = 0.4, linewidth = 0) +
        labs(
            x = "", y = "", fill = "", title = "Locations of researchers",
            subtitle = "who authored the reviewed papers",
            caption = "Basemap: carto"
        ) +
        theme_ipsum() +
        theme(
            axis.text.x = element_blank(),
            axis.text.y = element_blank(),
            axis.ticks = element_blank(),
            panel.grid.major = element_blank(),
            plot.margin = margin(
                t = 0, # Top margin
                r = 0, # Right margin
                b = 0, # Bottom margin
                l = 0
            )
        ) # Left margin)
    if (!dir.exists(dir_figure)) {
        dir.create(dir_figure, recursive = TRUE)
    }

    ggsave(paste0(dir_figure, "researcher_location.png"), plot = plot, width = 5, height = 5)
}


plot_study_area_researcher_location <- function(path, round, dir_figure) {
    # Read the CSV files
    origin_sf <- read.csv(paste0(path, "/data/processed/", round, "/study_area.csv")) %>%
        drop_na(lon, lat) %>%
        mutate(id = filename) %>%
        st_as_sf(coords = c("lon", "lat"), crs = 4326) %>%
        st_transform(crs = 3857) %>%
        select(id)
    destination_sf <- read.csv(paste0(path, "/data/processed/", round, "/researcher_location.csv")) %>%
        drop_na(lon, lat) %>%
        mutate(id = X0) %>%
        st_as_sf(coords = c("lon", "lat"), crs = 4326) %>%
        st_transform(crs = 3857) %>%
        select(id)

    # Identify matching IDs in both origin and destination datasets
    matching_ids <- intersect(origin_sf$id, destination_sf$id)

    # Filter both sf objects to keep only matching IDs
    origin_sf <- origin_sf %>% filter(id %in% matching_ids)
    destination_sf <- destination_sf %>% filter(id %in% matching_ids)

    # Create lines for matching IDs
    line_geometries <- vector("list", length(matching_ids))
    names(line_geometries) <- matching_ids

    for (id in matching_ids) {
        origin_point <- origin_sf[origin_sf$id == id, ]
        destination_point <- destination_sf[destination_sf$id == id, ]

        line <- st_sfc(st_linestring(rbind(st_coordinates(origin_point), st_coordinates(destination_point))), crs = st_crs(origin_sf))
        line_geometries[[as.character(id)]] <- line
    }

    lines_sf <- st_sf(id = names(line_geometries), geometry = do.call(c, line_geometries), crs = st_crs(origin_sf))

    bbox <- st_bbox(c(xmin = -180, xmax = 180, ymin = -60, ymax = 80), crs = st_crs(4326))
    # Plot
    plot <- basemap_ggplot(bbox, map_service = "carto", map_type = "light_no_labels", force = T) +
        geom_sf(data = origin_sf, aes(color = "Origin"), size = 1, alpha = 0.3, linewidth = 0) +
        geom_sf(data = destination_sf, aes(color = "Destination"), size = 1, alpha = 0.3, linewidth = 0) +
        geom_sf(data = lines_sf, color = "black", linewidth = 0.1, alpha = 0.4, linetype = "dashed") +
        scale_color_manual(values = c("Origin" = "blue", "Destination" = "red"), labels = c("Study areas", "First authors")) +
        labs(
            x = "", y = "", fill = "", color = "", title = "Locations of first authors and study areas",
            subtitle = "in the reviewed papers",
            caption = "Basemap: carto"
        ) +
        theme_ipsum() +
        theme(
            axis.text.x = element_blank(),
            axis.text.y = element_blank(),
            axis.ticks = element_blank(),
            panel.grid.major = element_blank(),
            plot.margin = margin(
                t = 0, # Top margin
                r = 0, # Right margin
                b = 0, # Bottom margin
                l = 0
            )
        ) # Left margin)

    # Save the plot
    ggsave(paste0(dir_figure, "/researcher_study_areas.png"), plot = plot, width = 5, height = 5)
}

plot_study_area_researcher_location_alluvial <- function(path, round, dir_figure) {
    # Read the CSV files
    origin_sf <- read.csv(paste0(path, "/data/processed/", round, "/study_area_country_clean.csv")) %>%
        drop_na(Country_clean) %>%
        mutate(
            id = filename,
            study_areas = Country_clean
        ) %>%
        select(id, study_areas)
    destination_sf <- read.csv(paste0(path, "/data/processed/", round, "/researcher_location_country_clean.csv")) %>%
        drop_na(Country_clean) %>%
        mutate(
            id = X0,
            first_authors = Country_clean
        ) %>%
        select(id, first_authors)

    # get top 10 first authors
    top_10_first_authors <- destination_sf %>%
        group_by(first_authors) %>%
        summarize(freq = n(), .groups = "drop") %>%
        arrange(desc(freq)) %>%
        head(10) %>%
        pull(first_authors)

    # for origin_sf and destination_sf, filter only top 10 first authors mutate other countries to "other"
    origin_sf <- origin_sf %>%
        mutate(study_areas = ifelse(study_areas %in% top_10_first_authors, study_areas, "other"))
    destination_sf <- destination_sf %>%
        mutate(first_authors = ifelse(first_authors %in% top_10_first_authors, first_authors, "other"))

    # inner join
    alluvial_df <- inner_join(origin_sf, destination_sf, by = "id") %>%
        group_by(study_areas, first_authors) %>%
        summarize(freq = n(), .groups = "drop") %>%
        filter(freq > 1) %>%
        # sort by top_10_first_authors
        mutate(
            study_areas = factor(study_areas, levels = c(top_10_first_authors, "other")),
            first_authors = factor(first_authors, levels = c(top_10_first_authors, "other"))
        )

    ggplot(
        data = alluvial_df,
        aes(axis1 = first_authors, axis2 = study_areas, y = freq)
    ) +
        geom_alluvium(aes(fill = first_authors), show.legend = F, alpha = 0.8) +
        geom_stratum(alpha = 0, size = 0.2) +
        geom_text(
            stat = "stratum",
            aes(label = after_stat(stratum))
        ) +
        scale_x_discrete(
            limits = c("First authors", "Study areas"),
            expand = c(0.15, 0.05)
        ) +
        scale_fill_manual(
            values = paletteer_d("DresdenColor::paired"),
            guide = "none"
        ) +
        labs(
            title = "Countries of first authors and study areas",
            subtitle = "in the reviewed papers",
            caption = "Data: papers downloaded from Scopus on 2023-07-19",
            fill = "Country",
            x = "",
            y = "Number of papers"
        ) +
        theme_ipsum() +
        theme(
            # axis.text.x = element_blank(),
            axis.text.y = element_blank(),
            axis.ticks = element_blank(),
            panel.grid.major = element_blank(),
            plot.margin = margin(
                t = 0, # Top margin
                r = 0, # Right margin
                b = 0, # Bottom margin
                l = 0
            )
        ) # Left margin)
    ggsave(paste0(dir_figure, "/researcher_study_areas_alluvial.png"), width = 5, height = 10)
}


plot_extent <- function(path, round, dir_figure) {
    # Ensure citations dataframe is available or loaded within this function or globally
    citations <- read.csv(paste0(path, "/data/processed/", round, "/citation_df.csv")) %>%
        dplyr::select(record_id, X0)

    # Build the path dynamically based on input arguments
    file_path <- paste0(path, "/data/processed/", round, "/extent_scale.csv")

    # Read the data and perform operations
    extent <- read.csv(file_path) %>%
        left_join(citations, by = c("filename" = "X0")) %>%
        filter(!is.na(record_id)) %>%
        mutate(extent = case_when(
            extent_scale == "XXX-level" ~ "not applicable",
            extent_scale == "Not applicable" ~ "not applicable",
            str_detect(extent_scale, "NA") | is.na(extent_scale) ~ "not applicable",
            extent_scale == "individual image-level" ~ "not applicable",
            extent_scale == "university-level" ~ "building-level",
            extent_scale == "school-level" ~ "building-level",
            extent_scale == "state-level" ~ "district-level",
            extent_scale == "country-level" ~ "district-level",
            extent_scale == "town-level" ~ "city-level",
            extent_scale == "neighbourhood-level" ~ "neighborhood-level",
            TRUE ~ extent_scale
        )) %>%
        group_by(extent) %>%
        summarize(count = n()) %>%
        mutate(dummy = "")

    happy_pastel_palette_adjusted <- c("#8A89B3FF", "#9FC3C1FF", "#D6A3A5FF", "darkgray", "#EED9B3FF", "#B2C2A9FF")

    extent_plot <- ggplot(extent) +
        geom_col(aes(x = dummy, y = count, fill = reorder(extent, count)),
            position = "fill",
            width = 0.7
        ) +
        scale_y_continuous(
            name = "Percentage of publications",
            labels = scales::label_percent()
        ) +
        scale_x_discrete(expand = expansion(add = c(0.8, 0))) +
        scale_fill_manual(values = happy_pastel_palette_adjusted, guide = guide_legend(nrow = 2, reverse = TRUE)) +
        coord_flip() +
        labs(
            x = "", fill = "", title = "Extent of study areas",
            subtitle = NULL
        ) +
        theme_custom_light()

    # Save the plot to the specified directory
    ggsave(paste0(dir_figure, "extent.png"), plot = extent_plot, width = 10, height = 4)
    return(extent_plot)
}

plot_image_data_type <- function(path, round, dir_figure) {
    # Ensure citations dataframe is available or loaded within this function or globally
    citations <- read.csv(paste0(path, "/data/processed/", round, "/citation_df.csv")) %>%
        dplyr::select(record_id, X0)
    # Construct the file path dynamically
    file_path <- paste0(path, "/data/processed/", round, "/image_data.csv")

    # Read the data, perform manipulations, and create the plot
    image_data_type <- read.csv(file_path) %>%
        left_join(citations, by = c("filename" = "X0")) %>%
        filter(!is.na(record_id)) %>%
        rename(
            image_data_type = "Type_of_image_data"
        ) %>%
        distinct(filename, image_data_type) %>%
        filter(image_data_type != "") %>%
        group_by(image_data_type) %>%
        summarize(count = n()) %>%
        mutate(image_data_type = case_when(
            image_data_type == "other geo-tagged photos" ~ "geo-tagged photos",
            image_data_type == "non-geotagged photos" ~ "non-geo-tagged-photos",
            str_detect(image_data_type, "virtual") ~ "virtual reality",
            str_detect(image_data_type, "video") ~ "video",
            str_detect(image_data_type, "simulated") ~ "non-geotagged-photos",
            count < 3 | image_data_type == "not applicable" ~ "others",
            TRUE ~ image_data_type
        )) %>%
        filter(image_data_type != "others") %>%
        group_by(image_data_type) %>%
        summarize(count = sum(count)) %>%
        mutate(dummy = "") %>%
        arrange(count)

    # Define the color palette
    lighter_pastel_palette <- c("#DFA7B9", "#D5C5A8", "#F5B89F", "#D69BA3", "#A098C2", "#9FCBB2")

    image_data_type_plot <- ggplot(image_data_type) +
        geom_col(aes(x = dummy, y = count, fill = reorder(image_data_type, count)),
            position = "fill",
            width = 0.7
        ) +
        scale_y_continuous(
            name = "Percentage of publications",
            labels = scales::label_percent()
        ) +
        scale_x_discrete(expand = expansion(add = c(0.8, 0))) +
        scale_fill_manual(values = lighter_pastel_palette, guide = guide_legend(nrow = 2, reverse = TRUE)) +
        coord_flip() +
        labs(
            x = "", fill = "", title = "Visual data types",
            subtitle = NULL
        ) +
        theme_custom_light()

    # Save the plot to the specified directory
    ggsave(paste0(dir_figure, "image_data_type.png"), plot = image_data_type_plot, width = 10, height = 4)
    return(image_data_type_plot)
}

plot_subjective_data_type <- function(path, round, dir_figure) {
    # Assuming 'citations' dataframe is loaded or accessible within this function
    citations <- read.csv(paste0(path, "/data/processed/", round, "/citation_df.csv")) %>%
        dplyr::select(record_id, X0)
    file_path <- paste0(path, "/data/processed/", round, "/subjective_perception_data.csv")

    subjective_data_type <- read.csv(file_path) %>%
        left_join(citations, by = c("filename" = "X0")) %>%
        filter(!is.na(record_id)) %>%
        mutate(
            Subjective_data_source = tolower(Subjective_data_source),
            subjective_data_type = case_when(
                str_detect(Subjective_data_source, "public") ~ "publicly available data",
                str_detect(Subjective_data_source, "subjective") ~ "their own collection",
                str_detect(Subjective_data_source, "survey") ~ "their own collection",
                str_detect(Subjective_data_source, "collection") ~ "their own collection",
                str_detect(Subjective_data_source, "questionnaire") ~ "their own collection",
                str_detect(Subjective_data_source, "pulse") ~ "publicly available data",
                str_detect(Subjective_data_source, "existing") ~ "publicly available data",
                TRUE ~ Subjective_data_source
            )
        ) %>%
        filter(subjective_data_type == "publicly available data" | subjective_data_type == "their own collection") %>%
        distinct(filename, subjective_data_type) %>%
        group_by(subjective_data_type) %>%
        summarize(count = n()) %>%
        mutate(subjective_data_type = case_when(
            count < 3 ~ "others",
            TRUE ~ subjective_data_type
        )) %>%
        group_by(subjective_data_type) %>%
        summarize(count = sum(count)) %>%
        mutate(dummy = "")

    color_palette <- c("publicly available data" = "#eec643", "their own collection" = "darkgray")

    subjective_data_type_plot <- ggplot(subjective_data_type) +
        geom_col(aes(x = dummy, y = count, fill = reorder(subjective_data_type, count)),
            position = "fill",
            width = 0.7
        ) +
        scale_y_continuous(
            name = "Percentage of publications",
            labels = scales::label_percent()
        ) +
        scale_x_discrete(expand = expansion(add = c(0.8, 0))) +
        scale_fill_manual(values = color_palette, guide = guide_legend(nrow = 2, reverse = TRUE)) +
        coord_flip() +
        labs(
            x = "", fill = "", title = "Subjective data types",
            subtitle = NULL
        ) +
        theme_custom_light()

    ggsave(paste0(dir_figure, "subjective_data_type.png"), plot = subjective_data_type_plot, width = 10, height = 4)
    return(subjective_data_type_plot)
}

plot_subjective_data_size <- function(path, round, dir_figure) {
    # Ensure citations dataframe is available or loaded within this function or globally
    citations <- read.csv(paste0(path, "/data/processed/", round, "/citation_df.csv")) %>%
        dplyr::select(record_id, X0)
    # Load the data
    subjective_data_size <- read.csv(paste0(path, "/data/processed/", round, "/subjective_perception_data.csv")) %>%
        left_join(citations, by = c("filename" = "X0")) %>% # Assuming 'citations' is accessible here
        filter(!is.na(record_id)) %>%
        rename("subjective_data_size" = "Number_of_participants") %>%
        filter(subjective_data_size != "None") %>%
        mutate(
            subjective_data_size = as.numeric(subjective_data_size),
            subjective_data_size = case_when(
                subjective_data_size > 2000 ~ 2000,
                TRUE ~ subjective_data_size
            )
        )

    # Plot
    plot <- ggplot(subjective_data_size) +
        geom_histogram(aes(x = subjective_data_size), bins = 20, color = "white") +
        scale_x_continuous(breaks = c(0, 500, 1000, 1500, 2000), labels = c("0", "500", "1000", "1500", "> 2000")) +
        labs(
            x = "Number of participants",
            y = "Number of papers",
            title = "Number of participants",
            subtitle = "analyzed by reviewed papers",
            caption = ""
        ) +
        theme_ipsum() +
        theme(plot.margin = margin(20, 20, 20, 20))

    # Save the plot
    ggsave(paste0(dir_figure, "subjective_data_size.png"), plot = plot, width = 10, height = 4)
}

plot_type_of_research <- function(path, round, dir_figure) {
    # Ensure citations dataframe is available or loaded within this function or globally
    citations <- read.csv(paste0(path, "/data/processed/", round, "/citation_df.csv")) %>%
        dplyr::select(record_id, X0)
    # Load the data
    type_of_research <- read.csv(paste0(path, "/data/processed/", round, "/research_type_and_method.csv")) %>%
        left_join(citations, by = c("filename" = "X0")) %>% # Assuming 'citations' is accessible here
        filter(!is.na(record_id)) %>%
        mutate(
            research_type = tolower(Type_of_research),
            research_type = case_when(
                str_detect(research_type, "mixed") | research_type == "qualitative and quantitative" ~ "mixed",
                TRUE ~ research_type
            )
        ) %>%
        group_by(research_type) %>%
        summarize(count = n()) %>%
        mutate(dummy = "") %>%
        filter(research_type %in% c("qualitative", "quantitative", "mixed"))

    happy_pastel_palette <- c("#A5A5A5FF", "#FFDE8DFF", "#9E7AB4FF")

    # Plot
    type_of_research_plot <- ggplot(type_of_research) +
        geom_col(aes(x = dummy, y = count, fill = reorder(research_type, count)),
            position = "fill",
            width = 0.7
        ) +
        scale_y_continuous(
            name = "Percentage of publications",
            labels = scales::label_percent()
        ) +
        scale_x_discrete(expand = expansion(add = c(0.8, 0))) +
        scale_fill_manual(values = happy_pastel_palette, guide = guide_legend(nrow = 2, reverse = TRUE)) +
        coord_flip() +
        labs(
            x = "", fill = "", title = "Overall types of research",
            subtitle = NULL
        ) +
        theme_custom_light()

    # Save the plot
    ggsave(paste0(dir_figure, "type_of_research.png"), plot = type_of_research_plot, width = 10, height = 4)
    return(type_of_research_plot)
}

plot_type_of_research_detail <- function(path, round, dir_figure) {
    # Ensure citations dataframe is available or loaded within this function or globally
    citations <- read.csv(paste0(path, "/data/processed/", round, "/citation_df.csv")) %>%
        dplyr::select(record_id, X0)
    # Load the data
    type_of_research_detail <- read.csv(paste0(path, "/data/processed/", round, "/analysis_type.csv")) %>%
        left_join(citations, by = c("filename" = "X0")) %>% # Assuming 'citations' is accessible here
        filter(!is.na(record_id)) %>%
        rename("type_of_research_detail" = "Type_of_analysis") %>%
        distinct(filename, type_of_research_detail) %>%
        mutate(
            type_of_research_detail = tolower(type_of_research_detail),
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
                TRUE ~ "others"
            )
        ) %>%
        group_by(type_of_research_detail) %>%
        summarize(count = n()) %>%
        mutate(dummy = "")

    palette <- c("#8FA587FF", "#F7B374FF", "#E49E7DFF", "#A9887CFF", "#BFAE8DFF")

    # Plot
    type_of_research_detail_plot <- ggplot(type_of_research_detail) +
        geom_col(aes(x = dummy, y = count, fill = reorder(type_of_research_detail, count)),
            position = "fill",
            width = 0.7
        ) +
        scale_y_continuous(
            name = "Percentage of publications",
            labels = scales::label_percent()
        ) +
        scale_x_discrete(expand = expansion(add = c(0.8, 0))) +
        scale_fill_manual(values = palette, guide = guide_legend(nrow = 2, reverse = TRUE)) +
        coord_flip() +
        labs(
            x = "", fill = "", title = "Detailed types of research",
            subtitle = NULL
        ) +
        theme_custom_light()

    # Save the plot
    ggsave(paste0(dir_figure, "type_of_research_detail.png"), plot = type_of_research_detail_plot, width = 10, height = 4)
    return(type_of_research_detail_plot)
}

plot_cv_model_purpose <- function(path, round, dir_figure) {
    # Ensure citations dataframe is available or loaded within this function or globally
    citations <- read.csv(paste0(path, "/data/processed/", round, "/citation_df.csv")) %>%
        dplyr::select(record_id, X0)
    # Load the data
    cv_model_purpose <- read.csv(paste0(path, "/data/processed/", round, "/computer_vision_models.csv")) %>%
        left_join(citations, by = c("filename" = "X0")) %>% # Assuming 'citations' is accessible here
        filter(!is.na(record_id)) %>%
        rename("cv_model_purpose" = "Purpose") %>%
        filter(cv_model_purpose != "") %>%
        mutate(
            cv_model_purpose = tolower(cv_model_purpose),
            cv_model_purpose = case_when(
                str_detect(cv_model_purpose, "classification") ~ "image classification",
                str_detect(cv_model_purpose, "detection") | str_detect(cv_model_purpose, "object") ~ "object detection",
                str_detect(cv_model_purpose, "segmentation") ~ "segmentation",
                str_detect(cv_model_purpose, "extraction") ~ "feature extraction",
                str_detect(cv_model_purpose, "not applicable") ~ "not applicable",
                TRUE ~ "others"
            )
        ) %>%
        distinct(filename, cv_model_purpose) %>%
        group_by(cv_model_purpose) %>%
        summarize(count = n()) %>%
        mutate(dummy = "")

    palette <- c("#B7A4D4FF", "#E2ADC1FF", "#F5D379FF", "#F7BF8DFF", "#C0CEB0FF", "darkgray", "#7A8D5EFF", "#FEFDE4FF")

    # Plot
    cv_model_purpose_plot <- ggplot(cv_model_purpose) +
        geom_col(aes(x = dummy, y = count, fill = reorder(cv_model_purpose, count)),
            position = "fill",
            width = 0.7
        ) +
        scale_y_continuous(
            name = "Percentage of publications",
            labels = scales::label_percent()
        ) +
        scale_x_discrete(expand = expansion(add = c(0.8, 0))) +
        scale_fill_manual(values = palette, guide = guide_legend(nrow = 2, reverse = TRUE)) +
        coord_flip() +
        labs(
            x = "", fill = "", title = "Purposes of computer vision models",
            subtitle = NULL
        ) +
        theme_custom_light()

    # Save the plot
    ggsave(paste0(dir_figure, "cv_model_purpose.png"), plot = cv_model_purpose_plot, width = 10, height = 4)
    return(cv_model_purpose_plot)
}

plot_cv_model_training <- function(path, round, dir_figure) {
    # Ensure citations dataframe is available or loaded within this function or globally
    citations <- read.csv(paste0(path, "/data/processed/", round, "/citation_df.csv")) %>%
        dplyr::select(record_id, X0)
    # Load the data
    cv_model_training <- read.csv(paste0(path, "/data/processed/", round, "/computer_vision_models.csv")) %>%
        left_join(citations, by = c("filename" = "X0")) %>% # Assuming 'citations' is accessible here
        filter(!is.na(record_id)) %>%
        rename("cv_model_training" = "Training_procedure") %>%
        filter(cv_model_training != "") %>%
        mutate(
            cv_model_training = tolower(cv_model_training),
            cv_model_training = case_when(
                str_detect(cv_model_training, "pre-trained with fine-tuning") ~ "pre-trained with fine-tuning",
                str_detect(cv_model_training, "pre-trained without fine-tuning") | str_detect(cv_model_training, "retrain") ~ "pre-trained without fine-tuning",
                str_detect(cv_model_training, "trained") | str_detect(cv_model_training, "trained with") ~ "trained from scratch",
                TRUE ~ "not applicable"
            )
        ) %>%
        group_by(cv_model_training) %>%
        summarize(count = n()) %>%
        mutate(dummy = "")

    palette <- c("#FBCB74FF", "#78D3D7FF", "#AED8A1FF", "darkgray", "#E8A3A0FF", "#A899A0FF")

    # Plot
    cv_model_training_plot <- ggplot(cv_model_training) +
        geom_col(aes(x = dummy, y = count, fill = reorder(cv_model_training, count)),
            position = "fill",
            width = 0.7
        ) +
        scale_y_continuous(
            name = "Percentage of publications",
            labels = scales::label_percent()
        ) +
        scale_x_discrete(expand = expansion(add = c(0.8, 0))) +
        scale_fill_manual(values = palette, guide = guide_legend(nrow = 2, reverse = TRUE)) +
        coord_flip() +
        labs(
            x = "", fill = "", title = "Training processes for computer vision models",
            subtitle = NULL
        ) +
        theme_custom_light()

    # Save the plot
    ggsave(paste0(dir_figure, "cv_model_training.png"), plot = cv_model_training_plot, width = 10, height = 4)
    return(cv_model_training_plot)
}

plot_data_availability <- function(path, round, dir_figure) {
    # Ensure citations dataframe is available or loaded within this function or globally
    citations <- read.csv(paste0(path, "/data/processed/", round, "/citation_df.csv")) %>%
        dplyr::select(record_id, X0)
    # Load the data
    data_availability <- read.csv(paste0(path, "/data/processed/", round, "/data_availability.csv")) %>%
        left_join(citations, by = c("filename" = "X0")) %>% # Assuming 'citations' is accessible here
        filter(!is.na(record_id)) %>%
        filter(Data_availability != "") %>%
        mutate(
            data_availability = tolower(Data_availability),
            data_availability = case_when(
                str_detect(data_availability, "not mentioned") ~ "data not available",
                str_detect(data_availability, "via") ~ "data available via URL",
                str_detect(data_availability, "url") ~ "data available via URL",
                str_detect(data_availability, "online") ~ "data available via URL",
                str_detect(data_availability, "github") ~ "data available via URL",
                str_detect(data_availability, "request") ~ "data available upon request",
                str_detect(data_availability, "not available") ~ "data not available",
                str_detect(data_availability, "do not have permission") ~ "data not available",
                str_detect(data_availability, "data available") & str_detect(data_availability, "restrictions") ~ "data available upon request",
                str_detect(data_availability, "the low-level visual") ~ "data available via URL",
                TRUE ~ data_availability
            )
        ) %>%
        group_by(data_availability) %>%
        summarize(count = n()) %>%
        mutate(dummy = "")

    palette <- c("#F2D48DFF", "#A8C7A7FF", "#A9A08AFF", "darkgray")

    # Plot
    data_availability_plot <- ggplot(data_availability) +
        geom_col(aes(x = dummy, y = count, fill = reorder(data_availability, count)),
            position = "fill",
            width = 0.7
        ) +
        scale_y_continuous(
            name = "Percentage of publications",
            labels = scales::label_percent()
        ) +
        scale_x_discrete(expand = expansion(add = c(0.8, 0))) +
        scale_fill_manual(values = palette, guide = guide_legend(nrow = 2, reverse = TRUE)) +
        coord_flip() +
        labs(
            x = "", fill = "", title = "Availability of data",
            subtitle = NULL
        ) +
        theme_custom_light()

    # Save the plot
    ggsave(paste0(dir_figure, "data_availability.png"), plot = data_availability_plot, width = 10, height = 4)
    return(data_availability_plot)
}


plot_irb_approval <- function(path, round, dir_figure) {
    # Ensure citations dataframe is available or loaded within this function or globally
    citations <- read.csv(paste0(path, "/data/processed/", round, "/citation_df.csv")) %>%
        dplyr::select(record_id, X0)
    # Load the data
    irb <- read.csv(paste0(path, "/data/processed/", round, "/ethical_approval.csv")) %>%
        left_join(citations, by = c("filename" = "X0")) %>% # Assuming 'citations' is accessible here
        filter(!is.na(record_id)) %>%
        rename("irb" = "Ethical_approval") %>%
        filter(irb != "") %>%
        mutate(
            irb = tolower(irb),
            irb = case_when(
                str_detect(irb, "yes") ~ "mentioned",
                TRUE ~ "not mentioned"
            )
        ) %>%
        group_by(irb) %>%
        summarize(count = n()) %>%
        mutate(dummy = "")

    palette <- c("#E8A5D4FF", "darkgray")

    # Plot
    irb_plot <- ggplot(irb) +
        geom_col(aes(x = dummy, y = count, fill = reorder(irb, count)),
            position = "fill",
            width = 0.7
        ) +
        scale_y_continuous(
            name = "Percentage of publications",
            labels = scales::label_percent()
        ) +
        scale_x_discrete(expand = expansion(add = c(0.8, 0))) +
        scale_fill_manual(values = palette, guide = guide_legend(nrow = 2, reverse = TRUE)) +
        coord_flip() +
        labs(
            x = "", fill = "", title = "Approval from institutional review boards",
            subtitle = NULL
        ) +
        theme_custom_light()

    # Save the plot
    ggsave(paste0(dir_figure, "irb.png"), plot = irb_plot, width = 10, height = 4)
    return(irb_plot)
}

plot_combined <- function(path, round, dir_figure) {
    # Generate each plot
    aspect_plot <- plot_aspects(path, round, dir_figure)
    extent_plot <- plot_extent(path, round, dir_figure)
    image_data_type_plot <- plot_image_data_type(path, round, dir_figure)
    cv_model_purpose_plot <- plot_cv_model_purpose(path, round, dir_figure)
    cv_model_training_plot <- plot_cv_model_training(path, round, dir_figure)
    subjective_data_type_plot <- plot_subjective_data_type(path, round, dir_figure)
    type_of_research_plot <- plot_type_of_research(path, round, dir_figure)
    type_of_research_detail_plot <- plot_type_of_research_detail(path, round, dir_figure)
    data_availability_plot <- plot_data_availability(path, round, dir_figure)
    irb_plot <- plot_irb_approval(path, round, dir_figure)

    # Combine all plots
    combined_plot <- cowplot::plot_grid(
        aspect_plot, extent_plot, image_data_type_plot,
        cv_model_purpose_plot, cv_model_training_plot,
        subjective_data_type_plot, type_of_research_plot, type_of_research_detail_plot,
        data_availability_plot, irb_plot,
        ncol = 2
    ) +
        theme_custom_light()

    # Save the combined plot
    ggsave(paste0(dir_figure, "combined_plot.png"), combined_plot, width = 20, height = 15)
}

plot_image_data_type_by_study_area <- function(path, round, dir_figure) {
    # set the palette
    color_palette <- c("#DFA7B9", "#D5C5A8", "#F5B89F", "#D69BA3", "#A098C2", "#9FCBB2")
    # set names
    names(color_palette) <- c("aerial image", "geo-tagged photos", "virtual reality", "video", "street view image", "non-geo-tagged-photos")

    # Ensure citations dataframe is available or loaded within this function or globally
    citations <- read.csv(paste0(path, "/data/processed/", round, "/citation_df.csv")) %>%
        dplyr::select(record_id, X0)
    # Construct the file path dynamically
    file_path <- paste0(path, "/data/processed/", round, "/image_data.csv")
    location_df <- read.csv(paste0(path, "/data/processed/", round, "/study_area_country_clean.csv"))
    # get top 10 study areas
    top_10_study_areas <- location_df %>%
        group_by(Country_clean) %>%
        summarize(freq = n(), .groups = "drop") %>%
        arrange(desc(freq)) %>%
        head(10) %>%
        pull(Country_clean)
    # Read the data, perform manipulations, and create the plot
    image_data_type <- read.csv(file_path) %>%
        left_join(citations, by = c("filename" = "X0")) %>%
        filter(!is.na(record_id)) %>%
        rename(
            image_data_type = "Type_of_image_data"
        ) %>%
        distinct(filename, image_data_type) %>%
        filter(image_data_type != "") %>%
        left_join(
            read.csv(paste0(path, "/data/processed/", round, "/study_area_country_clean.csv")),
            by = "filename"
        ) %>%
        filter(!is.na(Country_clean)) %>%
        filter(image_data_type != "") %>%
        group_by(image_data_type) %>%
        mutate(
            count = n(),
            image_data_type = case_when(
                image_data_type == "other geo-tagged photos" ~ "geo-tagged photos",
                image_data_type == "non-geotagged photos" ~ "non-geo-tagged-photos",
                str_detect(image_data_type, "virtual") ~ "virtual reality",
                str_detect(image_data_type, "video") ~ "video",
                str_detect(image_data_type, "simulated") ~ "non-geotagged-photos",
                count < 3 | image_data_type == "not applicable" ~ "others",
                TRUE ~ image_data_type
            ),
            Country_clean = case_when(
                Country_clean %in% top_10_study_areas ~ Country_clean,
                TRUE ~ "other"
            ),
            Country_clean = factor(Country_clean, levels = rev(c(top_10_study_areas, "other")))
        ) %>%
        filter(image_data_type != "others") %>%
        group_by(Country_clean, image_data_type) %>%
        # Calculate the ratio of visual data types for each aspect
        summarize(count = n()) %>%
        mutate(image_data_type = factor(image_data_type, levels = rev(names(color_palette)))) %>%
        ungroup()

    ggplot(
        data = image_data_type,
        aes(x = Country_clean, y = count, fill = image_data_type)
    ) +
        geom_col(stat = "identity", position = "fill") +
        scale_y_continuous(labels = scales::percent_format()) +
        scale_fill_manual(
            values = color_palette,
            guide = guide_legend(reverse = TRUE),
            limits = names(color_palette)
        ) + # Add custom color palette
        labs(
            x = "Country",
            y = "Share of papers",
            title = "Visual data types by study area",
            subtitle = NULL
        ) +
        coord_flip() +
        theme_custom_light() +
        theme(
            axis.text.x = element_text(angle = 45, hjust = 1, size = 20),
            axis.text.y = element_text(size = 20),
            # legend text
            legend.text = element_text(size = 20)
        )
    # Save the plot to the specified directory
    ggsave(paste0(dir_figure, "image_data_type_by_study_area.png"), width = 9, height = 9)
}

plot_image_data_type_by_extent <- function(path, round, dir_figure) {
    # set the palette
    color_palette <- c("#DFA7B9", "#D5C5A8", "#F5B89F", "#D69BA3", "#A098C2", "#9FCBB2")
    # set names
    names(color_palette) <- c("aerial image", "geo-tagged photos", "virtual reality", "video", "street view image", "non-geo-tagged-photos")

    # Ensure citations dataframe is available or loaded within this function or globally
    citations <- read.csv(paste0(path, "/data/processed/", round, "/citation_df.csv")) %>%
        dplyr::select(record_id, X0)
    # Construct the file path dynamically
    file_path <- paste0(path, "/data/processed/", round, "/image_data.csv")
    extent_df <- read.csv(paste0(path, "/data/processed/", round, "/extent_scale.csv"))
    # Read the data, perform manipulations, and create the plot
    image_data_type <- read.csv(file_path) %>%
        left_join(citations, by = c("filename" = "X0")) %>%
        filter(!is.na(record_id)) %>%
        rename(
            image_data_type = "Type_of_image_data"
        ) %>%
        distinct(filename, image_data_type) %>%
        filter(image_data_type != "") %>%
        left_join(
            extent_df,
            by = "filename"
        ) %>%
        filter(!is.na(extent_scale)) %>%
        filter(image_data_type != "") %>%
        group_by(image_data_type) %>%
        mutate(
            count = n(),
            image_data_type = case_when(
                image_data_type == "other geo-tagged photos" ~ "geo-tagged photos",
                image_data_type == "non-geotagged photos" ~ "non-geo-tagged-photos",
                str_detect(image_data_type, "virtual") ~ "virtual reality",
                str_detect(image_data_type, "video") ~ "video",
                str_detect(image_data_type, "simulated") ~ "non-geotagged-photos",
                count < 3 | image_data_type == "not applicable" ~ "others",
                TRUE ~ image_data_type
            ),
            extent_scale = case_when(
                extent_scale == "XXX-level" ~ "not applicable",
                extent_scale == "Not applicable" ~ "not applicable",
                str_detect(extent_scale, "NA") | is.na(extent_scale) ~ "not applicable",
                extent_scale == "individual image-level" ~ "not applicable",
                extent_scale == "university-level" ~ "building-level",
                extent_scale == "school-level" ~ "building-level",
                extent_scale == "state-level" ~ "district-level",
                extent_scale == "country-level" ~ "district-level",
                extent_scale == "town-level" ~ "city-level",
                extent_scale == "neighbourhood-level" ~ "neighborhood-level",
                TRUE ~ extent_scale
            )
        ) %>%
        filter(image_data_type != "others") %>%
        group_by(extent_scale, image_data_type) %>%
        # Calculate the ratio of visual data types for each aspect
        summarize(count = n()) %>%
        mutate(image_data_type = factor(image_data_type, levels = rev(names(color_palette)))) %>%
        ungroup()
    ggplot(
        data = image_data_type,
        aes(x = extent_scale, y = count, fill = image_data_type)
    ) +
        geom_col(stat = "identity", position = "fill") +
        scale_y_continuous(labels = scales::percent_format()) +
        scale_fill_manual(
            values = color_palette,
            guide = guide_legend(reverse = TRUE),
            limits = names(color_palette)
        ) + # Add custom color palette
        labs(
            x = "Extent",
            y = "Share of papers",
            title = "Visual data types by extent",
            subtitle = NULL
        ) +
        coord_flip() +
        theme_custom_light() +
        theme(
            axis.text.x = element_text(angle = 45, hjust = 1, size = 20),
            axis.text.y = element_text(size = 20),
            # legend text
            legend.text = element_text(size = 20)
        )
    # Save the plot to the specified directory
    ggsave(paste0(dir_figure, "image_data_type_by_extent.png"), width = 9, height = 9)
}

plot_image_data_type_by_year <- function(path, round, dir_figure) {
    # set the palette
    color_palette <- c("#DFA7B9", "#D5C5A8", "#F5B89F", "#D69BA3", "#A098C2", "#9FCBB2")
    # set names
    names(color_palette) <- c("aerial image", "geo-tagged photos", "virtual reality", "video", "street view image", "non-geo-tagged-photos")

    # Ensure citations dataframe is available or loaded within this function or globally
    citations <- read.csv(paste0(path, "/data/processed/", round, "/citation_df.csv")) %>%
        dplyr::select(record_id, X0, Year)
    # Construct the file path dynamically
    file_path <- paste0(path, "/data/processed/", round, "/image_data.csv")
    # Read the data, perform manipulations, and create the plot
    image_data_type <- read.csv(file_path) %>%
        left_join(citations, by = c("filename" = "X0")) %>%
        filter(!is.na(record_id)) %>%
        rename(
            image_data_type = "Type_of_image_data"
        ) %>%
        distinct(filename, image_data_type, Year) %>%
        filter(image_data_type != "") %>%
        group_by(image_data_type) %>%
        mutate(
            count = n(),
            image_data_type = case_when(
                image_data_type == "other geo-tagged photos" ~ "geo-tagged photos",
                image_data_type == "non-geotagged photos" ~ "non-geo-tagged-photos",
                str_detect(image_data_type, "virtual") ~ "virtual reality",
                str_detect(image_data_type, "video") ~ "video",
                str_detect(image_data_type, "simulated") ~ "non-geotagged-photos",
                count < 3 | image_data_type == "not applicable" ~ "others",
                TRUE ~ image_data_type
            ),
            image_data_type = factor(image_data_type, levels = rev(names(color_palette))),
            # sort year like 1990, 1991, 1992, ...
            year = case_when(
                Year < 2000 ~ 1999,
                TRUE ~ as.numeric(Year)
            )
        ) %>%
        filter(image_data_type != "others") %>% 
        group_by(year, image_data_type) %>%
        # Calculate the ratio of visual data types for each aspect
        summarize(count = n()) %>%
        mutate(image_data = factor(image_data_type, levels = rev(names(color_palette)))) %>%
        ungroup()
    ggplot(
        data = image_data_type,
        aes(x = year, y = count, fill = image_data_type)
    ) +
        geom_col(stat = "identity", position = "stack") +
        # scale_y_continuous(labels = scales::percent_format()) +
        scale_fill_manual(
            values = color_palette,
            guide = guide_legend(reverse = TRUE),
            limits = names(color_palette)
        ) + # Add custom color palette
        scale_x_continuous(
            breaks = c(1999, 2005, 2010, 2015, 2020, 2023),
            labels = c("1960 - 2000", "2005", "2010", "2015", "2020", "2023")
        ) +
        labs(
            x = "Year",
            y = "Number of papers",
            title = "Visual data types by year",
            subtitle = NULL
        ) +
        # coord_flip() +
        theme_custom_light() +
        theme(
            axis.text.x = element_text(angle = 45, hjust = 1, size = 20),
            axis.text.y = element_text(size = 20),
            # legend text
            legend.text = element_text(size = 20)
        )
    # Save the plot to the specified directory
    ggsave(paste0(dir_figure, "image_data_type_by_year.png"), width = 9, height = 9)
}

plot_cv_model_purpose_by_year <- function(path, round, dir_figure) {
    # set the palette
    color_palette <- c("#B7A4D4FF", "#E2ADC1FF", "#F5D379FF", "#F7BF8DFF", "#C0CEB0FF", "darkgray")
    # set names
    names(color_palette) <- c("feature extraction", "others", "object detection", "image classification", "segmentation", "not applicable")

    # Ensure citations dataframe is available or loaded within this function or globally
    citations <- read.csv(paste0(path, "/data/processed/", round, "/citation_df.csv")) %>%
        dplyr::select(record_id, X0, Year)
    # Construct the file path dynamically
    file_path <- paste0(path, "/data/processed/", round, "/computer_vision_models.csv")
    # Read the data, perform manipulations, and create the plot
    cv_model_purpose <- read.csv(file_path) %>%
        left_join(citations, by = c("filename" = "X0")) %>%
        filter(!is.na(record_id)) %>%
        rename("cv_model_purpose" = "Purpose") %>%
        filter(cv_model_purpose != "") %>%
        mutate(
            cv_model_purpose = tolower(cv_model_purpose),
            cv_model_purpose = case_when(
                str_detect(cv_model_purpose, "classification") ~ "image classification",
                str_detect(cv_model_purpose, "detection") | str_detect(cv_model_purpose, "object") ~ "object detection",
                str_detect(cv_model_purpose, "segmentation") ~ "segmentation",
                str_detect(cv_model_purpose, "extraction") ~ "feature extraction",
                str_detect(cv_model_purpose, "not applicable") ~ "not applicable",
                TRUE ~ "others"
            ),
            year = case_when(
                Year < 2000 ~ 1999,
                TRUE ~ as.numeric(Year)
            )
        ) %>%
        group_by(year, cv_model_purpose) %>%
        # Calculate the ratio of visual data types for each aspect
        summarize(count = n()) %>%
        mutate(cv_model_purpose = factor(cv_model_purpose, levels = rev(names(color_palette)))) %>%
        ungroup()
    ggplot(
        data = cv_model_purpose,
        aes(x = year, y =   count, fill = cv_model_purpose)
    ) +
        geom_col(stat = "identity", position = "stack") +
        # scale_y_continuous(labels = scales::percent_format()) +
        scale_fill_manual(
            values = color_palette,
            guide = guide_legend(reverse = TRUE),
            limits = names(color_palette)
        ) + # Add custom color palette
        scale_x_continuous(
            breaks = c(1999, 2005, 2010, 2015, 2020, 2023),
            labels = c("1960 - 2000", "2005", "2010", "2015", "2020", "2023")
        ) +
        labs(
            x = "Year",
            y = "Number of papers",
            title = "Computer vision model purposes by year",
            subtitle = NULL
        ) +
        # coord_flip() +
        theme_custom_light() +
        theme(
            axis.text.x = element_text(angle = 45, hjust = 1, size = 20),
            axis.text.y = element_text(size = 20),
            # legend text
            legend.text = element_text(size = 20)
        )
    # Save the plot to the specified directory
    ggsave(paste0(dir_figure, "cv_model_purpose_by_year.png"), width = 9, height = 9)
}

plot_cv_model_training_by_year <- function(path, round, dir_figure) {
    # set the palette
    color_palette <- c("#FBCB74FF", "#78D3D7FF", "#AED8A1FF", "darkgray")
    # set names
    names(color_palette) <- c("pre-trained without fine-tuning", "trained from scratch", "pre-trained with fine-tuning", "not applicable")

    # Ensure citations dataframe is available or loaded within this function or globally
    citations <- read.csv(paste0(path, "/data/processed/", round, "/citation_df.csv")) %>%
        dplyr::select(record_id, X0, Year)
    # Construct the file path dynamically
    file_path <- paste0(path, "/data/processed/", round, "/computer_vision_models.csv")
    # Read the data, perform manipulations, and create the plot
    cv_model_training <- read.csv(file_path) %>%
        left_join(citations, by = c("filename" = "X0")) %>%
        filter(!is.na(record_id)) %>%
        rename("cv_model_training" = "Training_procedure") %>%
        filter(cv_model_training != "") %>%
        mutate(
            cv_model_training = tolower(cv_model_training),
            cv_model_training = case_when(
                str_detect(cv_model_training, "pre-trained with fine-tuning") ~ "pre-trained with fine-tuning",
                str_detect(cv_model_training, "pre-trained without fine-tuning") | str_detect(cv_model_training, "retrain") ~ "pre-trained without fine-tuning",
                str_detect(cv_model_training, "trained") | str_detect(cv_model_training, "trained with") ~ "trained from scratch",
                TRUE ~ "not applicable"
            ),
            year = case_when(
                Year < 2000 ~ 1999,
                TRUE ~ as.numeric(Year)
            )
        ) %>%
        group_by(year, cv_model_training) %>%
        # Calculate the ratio of visual data types for each aspect
        summarize(count = n()) %>%
        mutate(cv_model_training = factor(cv_model_training, levels = rev(names(color_palette)))) %>%
        ungroup()
    ggplot(
        data = cv_model_training,
        aes(x = year, y = count, fill = cv_model_training)
    ) +
        geom_col(stat = "identity", position = "stack") +
        # scale_y_continuous(labels = scales::percent_format()) +
        scale_fill_manual(
            values = color_palette,
            guide = guide_legend(reverse = TRUE),
            limits = names(color_palette)
        ) + # Add custom color palette
        scale_x_continuous(
            breaks = c(1999, 2005, 2010, 2015, 2020, 2023),
            labels = c("1960 - 2000", "2005", "2010", "2015", "2020", "2023")
        ) +
        labs(
            x = "Year",
            y = "Number of papers",
            title = "Computer vision model training processes by year",
            subtitle = NULL
        ) +
        # coord_flip() +
        guides(fill = guide_legend(nrow = 2)) +
        theme_custom_light() +
        theme(
            axis.text.x = element_text(angle = 45, hjust = 1, size = 20),
            axis.text.y = element_text(size = 20),
            # legend text
            legend.text = element_text(size = 20)
        )
    # Save the plot to the specified directory
    ggsave(paste0(dir_figure, "cv_model_training_by_year.png"), width = 9, height = 9)
}

plot_image_data_type_subjective_data_by_aspect <- function(path, round, dir_figure) {
    # Ensure citations dataframe is available or loaded within this function or globally
    citations <- read.csv(paste0(path, "/data/processed/", round, "/citation_df.csv")) %>%
        dplyr::select(record_id, X0)

    # Load and process the aspect table
    aspect_table <- read.csv(paste0(path, "/data/processed/", round, "/aspect.csv")) %>%
        distinct(X0, improved_aspect) %>%
        left_join(citations, by = "X0") %>%
        filter(!is.na(record_id)) %>%
        mutate(aspect = tolower(improved_aspect)) %>%
        mutate(aspect = str_trim(str_split_fixed(aspect, ",", 2)[, 1])) %>%
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
                str_detect(aspect, "greenery") | str_detect(aspect, "waterscapes") ~ "greenery and water",
                str_detect(aspect, "infrastructure") ~ "street design",
                TRUE ~ aspect
            ),
            filename = X0
        ) %>%
        distinct(filename, aspect)


    citations_table <- read.csv(paste0(path, "/data/processed/", round, "/citations_by_aspect.csv")) %>%
        mutate(citations_list = strsplit(citations, ",\\s*")) %>%
        unnest(citations_list) %>%
        distinct(citations_list, .keep_all = TRUE) %>%
        # group by aspect and create a new column to store citations_list as a combined string
        mutate(
            aspect = case_when(
                aspect == "the summary provided does not contain enough information to reclassify the aspect. please provide a more detailed summary." ~ "public space",
                str_detect(aspect, "reclassify the aspect of the study") ~ "greenery and water",
                str_detect(aspect, "others: study methodology") ~ "landscape",
                str_detect(aspect, "others: sensory perception") ~ "landscape",
                str_detect(aspect, "others: visual aesthetics") ~ "landscape",
                str_detect(aspect, "others: population prediction") ~ "public space",
                str_detect(aspect, "greenery") | str_detect(aspect, "waterscapes") ~ "greenery and water",
                str_detect(aspect, "infrastructure") ~ "street design",
                TRUE ~ aspect
            )
        ) %>%
        distinct(aspect, citations_list) %>%
        group_by(aspect) %>%
        summarize(
            citations = paste(citations, collapse = ", "),
            count = n()
        ) %>%
        arrange(desc(count))

    subjective_data_type_table <- read.csv(paste0(path, "/data/processed/", round, "/subjective_perception_data.csv")) %>%
        left_join(citations, by = c("filename" = "X0")) %>%
        filter(!is.na(record_id)) %>%
        mutate(
            Subjective_data_source = tolower(Subjective_data_source),
            subjective_data_type = case_when(
                str_detect(Subjective_data_source, "public") ~ "publicly available data",
                str_detect(Subjective_data_source, "subjective") ~ "their own collection",
                str_detect(Subjective_data_source, "survey") ~ "their own collection",
                str_detect(Subjective_data_source, "collection") ~ "their own collection",
                str_detect(Subjective_data_source, "questionnaire") ~ "their own collection",
                str_detect(Subjective_data_source, "pulse") ~ "publicly available data",
                str_detect(Subjective_data_source, "existing") ~ "publicly available data",
                TRUE ~ Subjective_data_source
            )
        ) %>%
        filter(subjective_data_type == "publicly available data" | subjective_data_type == "their own collection") %>%
        distinct(filename, subjective_data_type)

    image_data_type_table <- read.csv(paste0(path, "/data/processed/", round, "/image_data.csv")) %>%
        left_join(citations, by = c("filename" = "X0")) %>%
        filter(!is.na(record_id)) %>%
        rename(
            "image_data_type" = "Type_of_image_data"
        ) %>%
        distinct(filename, image_data_type) %>%
        filter(image_data_type != "") %>%
        group_by(image_data_type) %>%
        mutate(
            count = n(),
            image_data_type = case_when(
                image_data_type == "other geo-tagged photos" ~ "geo-tagged photos",
                image_data_type == "non-geotagged photos" ~ "non-geo-tagged-photos",
                str_detect(image_data_type, "virtual") ~ "virtual reality",
                str_detect(image_data_type, "video") ~ "video",
                str_detect(image_data_type, "simulated") ~ "non-geotagged-photos",
                count < 3 | image_data_type == "not applicable" ~ "others",
                TRUE ~ image_data_type
            )
        ) %>%
        filter(image_data_type != "others") %>%
        group_by(image_data_type) %>%
        mutate(
            count = n()
        )


    # merge subjective and image data type
    aspect_subjective_image <- left_join(subjective_data_type_table, aspect_table, by = "filename") %>%
        left_join(., image_data_type_table, by = "filename") %>%
        select(aspect, subjective_data_type, image_data_type)

    # !SUBJECTIVE DATA TYPE!
    color_palette <- c("publicly available data" = "#eec643", "their own collection" = "darkgray")
    # Calculate the ratio of subjective data types for each aspect
    percentages_subjective <- aspect_subjective_image %>%
        group_by(aspect, subjective_data_type) %>%
        summarize(count = n()) %>%
        mutate(
            percentage = count / sum(count),
            subjective_data_type = factor(subjective_data_type, levels = rev(names(color_palette)))
        ) %>%
        ungroup()

    # Create a stacked bar plot for each aspect and save them as images
    unique_aspects_subjective <- unique(percentages_subjective$aspect)
    for (aspect_subjective in unique_aspects_subjective) {
        plot_data <- filter(percentages_subjective, aspect == !!aspect_subjective)

        # Create the plot
        p <- ggplot(plot_data, aes(x = aspect, y = percentage, fill = subjective_data_type)) +
            geom_bar(stat = "identity", width = 0.8) +
            scale_y_continuous(labels = scales::percent_format()) +
            scale_x_discrete(expand = expansion(add = c(0.8, 0))) + # Add this line to control the space around the plot on the x-axis
            scale_fill_manual(
                values = color_palette,
                guide = guide_legend(reverse = TRUE),
                limits = names(color_palette)
            ) + # Add custom color palette
            labs(x = "", y = "", fill = "") +
            theme_minimal() +
            theme(
                axis.ticks.x = element_blank(),
                axis.text.x = element_blank(),
                panel.grid.major.x = element_blank(),
                panel.grid.minor = element_blank(),
                plot.margin = margin(0, 0, 0, 0)
            )

        # Save the plot as an image
        ggsave(paste0(dir_figure, "subjective_bar_plot_", aspect_subjective, ".png"), plot = p, width = 3, height = 3, dpi = 1000)
    }

    # Add a new column with the image file name for each aspect
    aspect_subjective_unique <- aspect_subjective_image %>%
        distinct(aspect, .keep_all = T) %>%
        mutate(image_file = paste0("fig/subjective_bar_plot_", aspect, ".png")) %>%
        select(aspect, `Subjective data types` = image_file)

    # !IMAGE DATA TYPE!
    # set the palette
    color_palette <- c("#DFA7B9", "#D5C5A8", "#F5B89F", "#D69BA3", "#A098C2", "#9FCBB2")
    # set names
    names(color_palette) <- c("aerial image", "geo-tagged photos", "virtual reality", "video", "street view image", "non-geo-tagged-photos")
    # Calculate the ratio of visual data types for each aspect
    percentages_image <- aspect_subjective_image %>%
        filter(!is.na(image_data_type)) %>%
        group_by(aspect, image_data_type) %>%
        summarize(count = n()) %>%
        mutate(
            percentage = count / sum(count),
            image_data_type = factor(image_data_type, levels = rev(names(color_palette)))
        ) %>%
        ungroup()

    # Create a stacked bar plot for each aspect and save them as images
    unique_aspects_image <- unique(percentages_image$aspect)
    for (aspect_image in unique_aspects_image) {
        plot_data <- filter(percentages_image, aspect == !!aspect_image)

        # Create the plot
        p <- ggplot(plot_data, aes(x = aspect, y = percentage, fill = image_data_type)) +
            geom_bar(stat = "identity", width = 0.8) +
            scale_y_continuous(labels = scales::percent_format()) +
            scale_x_discrete(expand = expansion(add = c(0.8, 0))) + # Add this line to control the space around the plot on the x-axis
            scale_fill_manual(
                values = color_palette,
                guide = guide_legend(reverse = TRUE),
                limits = names(color_palette)
            ) + # Add custom color palette
            labs(x = "", y = "", fill = "") +
            theme_minimal() +
            theme(
                axis.ticks = element_blank(),
                axis.text.x = element_blank(),
                panel.grid.major.x = element_blank(),
                panel.grid.minor = element_blank(),
                plot.margin = margin(0, 0, 0, 0)
            )

        # Save the plot as an image
        ggsave(paste0(dir_figure, "image_bar_plot_", aspect_image, ".png"), plot = p, width = 3.1, height = 3, dpi = 1000)
    }

    # Add a new column with the image file name for each aspect
    aspect_image_unique <- aspect_subjective_image %>%
        distinct(aspect, .keep_all = T) %>%
        mutate(image_file = paste0("fig/image_bar_plot_", aspect, ".png")) %>%
        select(aspect, `Visual data types` = image_file)

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

    sink(paste0(path, "/data/processed/", round, "/overview_aspect.tex"))
    # Print the LaTeX table
    print(latex_table,
        sanitize.text.function = include_image,
        include.rownames = FALSE,
        caption = "Overview of the papers by aspect",
        caption.placement = "top",
        table.placement = "tbp"
    )
    sink()
}
