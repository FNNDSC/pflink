# pflink
[![Build](https://github.com/FNNDSC/pflink/actions/workflows/build.yml/badge.svg)](https://github.com/FNNDSC/pflink/actions/workflows/build.yml)

A Python-FastAPI application to create and manage workflows using `PFDCM` & `CUBE` .

User can register DICOMs to `CUBE`and additionally create new feed, add new plugin or pipeline  in CUBE .

## Quick Start

```bash
git clone https://github.com/FNNDSC/pflink.git
cd pflink
./pflink.sh
```

### An instance of `mongodb` & `pflink` should be up and running on `localhost` on the following ports:


| app     | URL                    |
|---------|------------------------|
| mongoDB | http://localhost:27017 |
| pflink  | http://localhost:8050  |

Go to http://localhost:8050/docs for API usage


## Testing

```bash
cd pflink
./test.sh
```

## Unmake

```bash
cd pflink
./unmake.sh
```

# Examples
The `POST` API endpoint to create a new workflow or to get the status of an existing workflow is (`/api/v1/workflow/`)
### sample workflow request
```commandline
{
  "ignore_duplicate": true,
  "pfdcm_info": {
    "pfdcm_service": "PFDCM",
    "PACS_service": "orthanc"
  },
  "PACS_directive": {
    "StudyInstanceUID": "12365548",
    "SeriesInstanceUID": "66498598"
  },
  "workflow_info": {
    "feed_name": "test-%SeriesInstanceUID",
    "plugin_name": "pl-simpledsapp",
    "plugin_version": "2.1.0",
    "plugin_params": "--args ARGS"
  },
  "cube_user_info": {
    "username": "chris",
    "password": "chris1234"
  }
}
```

### sample workflow response
```commandline
{
  "status": true,
  "workflow_state": "initializing workflow",
  "state_progress": "0%",
  "feed_id": "",
  "feed_name": "",
  "message": "",
  "duplicates": null,
  "error": "",
  "workflow_progress_perc": 0
}
```

# Additional support scripts
## `setup.sh`
After starting new instances of `pflink` & `mongo` locally, we can a `setup` script available in the repo.
The setup script provides the following support:
1) Authentication (authenticate into any running instance of ``pflink``)
2) Add a new `PFDCM` service to `MongoDB`

### to use:
```commandline
cd pflink/scripts
./setup.sh --help
```

## `resetWorkflow.sh`
Sometimes, we need to find a specific workflow request and restart using `pflink`. This repo 
contains a script ``resetWorkflow`` to do so. The script does the following tasks:
1) Authenticate to a ``pflink`` instance
2) Find a list of "keys" pointing to workflow records that match the user search values
3) Display each workflow record and provide the following options:
   1) delete the record and re-submit
   2) continue to the next record
   3) exit

### to use:
```commandline
cd pflink/scripts
./resetWorkflow.sh --help
```

## `dateSearch.sh`
This is one of the most important script to use. We can use this script for find the total number of studies present
for a given study name in a give date range, and verify if any series in those studies are processed by `pflink` and 
pushed to `SYNAPSERESEARCH`.

We can also use this script to analyze all the studies matching a study name in a given date range. The parameters we 
need to provide to run this script is  a start date, an end date, a keyword for study name and the mode we want to run
this script on:
1) search
2) analyze

### to search:
```commandline
cd pflink/scripts
./dateSearch.sh -S 2024-07-03 -E 2024-07-08 -K "XR HIPS TO ANKLES LEG MEASUREMENTS" -D search

```

### to analyze:
```commandline
cd pflink/scripts
./dateSearch.sh -S 2024-07-03 -E 2024-07-08 -K "XR HIPS TO ANKLES LEG MEASUREMENTS" -D analyze

```