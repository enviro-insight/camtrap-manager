#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(googledrive)
  library(httr)
})

DOWNLOAD_DIR <- "20260421"   # use the download date as these files are updated regularly
NAME_REGEX <- "camera.*_"
CASE_SENSITIVE <- FALSE

sanitize_filename <- function(name) {
  name <- gsub('[<>:"/\\\\|?*]', "_", name)
  name <- sub("[ .]+$", "", name)
  if (nchar(name) == 0) "unnamed_file" else name
}

name_matches <- function(filename) {
  grepl(NAME_REGEX, filename, ignore.case = !CASE_SENSITIVE, perl = TRUE)
}

get_drive_auth <- function() {
  cache_dir <- ".secrets"

  dir.create(cache_dir, showWarnings = FALSE)

  options(gargle_oauth_cache = cache_dir)

  drive_auth(
    scopes = "https://www.googleapis.com/auth/drive.readonly",
    path = "credentials.json",
    cache = cache_dir
  )
}

list_root_google_sheets <- function() {
  q <- paste(
    "'root' in parents",
    "and trashed = false",
    "and mimeType = 'application/vnd.google-apps.spreadsheet'"
  )

  drive_find(
    pattern = NULL,
    q = q,
    n_max = Inf,
    fields = "files(id, name, mimeType)"
  )
}

export_sheet_as_csv <- function(file_id, destination) {
  url <- sprintf(
    "https://www.googleapis.com/drive/v3/files/%s/export?mimeType=text/csv",
    URLencode(as.character(file_id), reserved = TRUE)
  )

  token <- drive_token()

  resp <- GET(
    url,
    config = add_headers(Authorization = paste("Bearer", token$credentials$access_token)),
    write_disk(destination, overwrite = TRUE)
  )

  stop_for_status(resp)
}

main <- function() {
  dir.create(DOWNLOAD_DIR, recursive = TRUE, showWarnings = FALSE)

  get_drive_auth()

  files <- list_root_google_sheets()

  found_any <- nrow(files) > 0
  downloaded_any <- FALSE

  if (found_any) {
    for (i in seq_len(nrow(files))) {
      file_name <- files$name[[i]]

      if (!name_matches(file_name)) {
        next
      }

      downloaded_any <- TRUE

      safe_name <- sanitize_filename(file_name)
      destination <- file.path(DOWNLOAD_DIR, paste0(safe_name, ".csv"))

      cat(sprintf("Exporting: %s\n", file_name))
      cat(sprintf("  Saving as: %s\n", basename(destination)))

      export_sheet_as_csv(files$id[[i]], destination)

      cat("  Done.\n\n")
    }
  }

  if (!found_any) {
    cat("No Google Sheets found directly in My Drive root.\n")
  } else if (!downloaded_any) {
    cat("Google Sheets were found in root, but none matched the name filter.\n")
  } else {
    cat(sprintf("Finished. Files saved to: %s\n", normalizePath(DOWNLOAD_DIR)))
  }
}

# this makes it run when source()ed, but not when loaded as a library
if (sys.nframe() == 0) {
  main()
}