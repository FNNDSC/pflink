# pflink
A Python-FastAPI application to interact with CUBE and pfdcm.

User can Query/Retrieve/Push/Register dicoms and additionally create new feed, add new node or pipeline on the registered dicoms in CUBE using `pflink`.

## Quick Start

```bash
git clone https://github.com/FNNDSC/pflink.git
cd pflink
docker build -t local/pflink .
./pflink.sh
```

### An instance of `mongodb` & `pflink` should be up and running on `localhost` on the following ports:


app           |  URL
--------------|---------------------------
mongoDB       | http://localhost:27017
pflink        | http://localhost:8050


Go to http://localhost:8050/docs for API usage

## Unmake

```bash
cd pflink
./unmake.sh
```
