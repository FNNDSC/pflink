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

# Addition support scripts
## `setup.sh`
After starting new instances of `pflink` & `mongo` locally, we can a `setup` script available in the repo.
The setup script provides the following support:
1) Authentication (authenticate into any running instance of ``pflink``)
2) Add a new `PFDCM` service to `MongoDB`

### to use:
```commandline
cd pflink
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
cd pflink
./resetWorkflow.sh --help
```