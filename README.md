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
```bash
cd pflink
./setup.sh --help
```

## `resetWorkflow.sh`
