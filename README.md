### Python functions for managing camera trap data

Originally built for managing camera trap data from Liberia SP2. Camera locations are recorded in Memento, synced to Google Drive, then pulled together here. 

`download.py` fetches all the Memento database data from Google Drive*

`merge.py` merges those datasets and extract just the fields we need for mapping/analysis

`metadata.py` extracts metadata from a set of camera trap videos into a CSV file for adding identifications, joining to the relevant deployments from `merge.py`.

*Requires authentication via the EI phones account - remember a phone when doing this...