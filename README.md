### Python functions for managing camera trap data

Originally built for managing camera trap data from Liberia SP2. Camera locations are recorded in Memento, synced to Google Drive, then pulled together here. 

`download.py` fetches all the Memento database data from Google Drive*

`merge.py` merges those datasets and extracts just the fields we need for mapping/analysis

`metadata.py` extracts metadata from a set of camera trap videos into a CSV file for adding identifications, joining to the relevant deployments from `merge.py`.

*Requires authentication via the EI phones account - remember a phone when doing this...

Built with `uv` for managing dependencies and running scripts, ala `uv run download.py`.

Note the credentials.json file comes from the EI phones account General project (Google Cloud Console).

### R script equivalents

Equivalent R scripts (translated with LLMs) are also here, with the same names above. 

Run these with Rscript (make sure it's on the system path), e.g. `Rscript metadata.R [params] `, or just `source()` them in RStudio.

Install the relevant packages with `Rscript -e "install.packages(c('googledrive','httr'))"`