# This script was created to render the documentation for the testStatus repo.
# This repository contains autogenerated reports for key DataSHIELD R packages
# (e.g., dsBase).
#
# Roberto Villegas-Diaz <r.villegas-diaz@liverpool.ac.uk>
# July 2025
# SETUP ----
args <- commandArgs(trailingOnly = TRUE) # read CL arguments
# 1st argument: INPUT_DIR 
if (length(args) >= 1) {
  INPUT_DIR <- args[1]
} else {
  INPUT_DIR <- getwd()
}
# 2nd argument: OUTPUT_DIR
if (length(args) >= 2) {
  OUTPUT_DIR <- args[2]
} else {
  OUTPUT_DIR <- INPUT_DIR
}
# 3rd argument: CLEAR_DOCS
if (length(args) >= 3) {
  CLEAR_DOCS <- as.logical(args[3])
} else {
  CLEAR_DOCS <- FALSE
}

message("Using the following configuration:",
        "\n  INPUT_DIR: ", INPUT_DIR,
        "\n  OUTPUT_DIR: ", OUTPUT_DIR,
        "\n  CLEAR_DOCS: ", CLEAR_DOCS)

# create directory in case an empty directory is received
dir.create(INPUT_DIR, recursive = TRUE)
dir.create(OUTPUT_DIR, recursive = TRUE)

# HELPER FUNCTIONS ----
clean_url <- function(url, input_dir) {
  url |>
    stringr::str_replace_all("\\/\\/", "\\/") |>
    stringr::str_remove_all(stringr::str_escape(input_dir)) |>
    stringr::str_remove_all("^[\\/]*")
}
 
# GENERATE HTML ----
header_html <- glue::glue(
  "---
layout: default
title: DataSHIELD: Latest Test Status
---
<a href='https://datashield.org'><img src='https://i0.wp.com/datashield.org/wp-content/uploads/2024/07/DS-logo-A4.png' alt='DataSHIELD logo' align='right' height=100px/></a>
<h1>DataSHIELD: Test suite status</h1>
<p>DataSHIELD is an infrastructure and series of R packages that enables the remote and non-disclosive analysis of sensitive research data. DataSHIELD has been used with real world and consented research data for over 10 years.</p>
<p>The following are auto-generated reports for testing key DataSHIELD R packages.</p>
<p><bf>Last updated:</bf> {Sys.Date()} @ {format(Sys.time(), '%H:%M:%S')}
\n")

# list directories inside INPUT_DIR
dirs_lst <- INPUT_DIR |>
  list.dirs(full.names = TRUE, recursive = FALSE)
# filter out subdirectories that don't start with a letter or number
idx <- dirs_lst |>
  basename() |>
  stringr::str_detect(pattern = "^[a-zA-Z0-9]+")

body_html <- dirs_lst[idx] |>
  purrr::map(function(d) {
    new_section <- paste0("<h2>", basename(d), "</h2>\n<ul>\n")
    # clear the documents directory and only keep latest snapshot
    if (CLEAR_DOCS) {
      # list directories at level 1
      list_all_dirs_level_1 <- d |>
        list.dirs(full.names = TRUE, recursive = FALSE)
      # list directories at level 2
      list_all_dirs_level_2 <- list_all_dirs_level_1 |>
        list.dirs(full.names = TRUE, recursive = FALSE)
      # detect directories that are not the latest version, avoid cluttering repo
      idx <- stringr::str_detect(list_all_dirs_level_2, "latest", negate = TRUE)
      message("Deleting unwanted directories: \n", 
              paste0("- ", list_all_dirs_level_2[idx], collapse = "\n"))
      # delete unwanted directories
      unlink(list_all_dirs_level_2[idx], force = TRUE, recursive = TRUE)
    }
    
    aux <- d |>
      list.dirs(full.names = TRUE, recursive = FALSE) |>
      purrr::map(\(sd) paste0("\t<li><a href='", clean_url(sd, INPUT_DIR), "/latest'>", basename(sd) ,"</a></li>")) |>
      paste0(collapse = "\n")
    new_section <- paste0(new_section, aux, "\n</ul>\n\n")
  }) |>
  purrr::list_c() |>
  paste0(collapse = "")

body_html <- paste0(body_html, "\n")

# SAVE HTML ----
paste0(header_html, body_html, collapse = "") |>
  readr::write_lines(file.path(OUTPUT_DIR, "index.html"))

# list files in the current directory
message("\nFiles that will be deployed:\n",
        paste0("- ", list.files(INPUT_DIR, recursive = TRUE), collapse = "\n"))