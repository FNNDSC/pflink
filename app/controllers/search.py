from app.models.workflow import WorkflowSearchSchema


def compound_queries(query_params: WorkflowSearchSchema):
    query = {"$match": {"$text":
                            {"$search": query_params.keywords}

                        }}

    rank = {
        "$sort": {"score": {"$meta": "textScore"}}
    }

    response = {
        "$project": {
            "_id": 1
        }
    }

    return query, rank, response


def index_search(query_params: dict):
    query = {
        "$match": {
            "index": "some_index",
            "text": {
                "query": "chris",
                "path": "request.cube_user_info.username"
            }
        }
    }
    return query

def date_search(start_date: str, end_date: str):
    """
    Search for specific DB record between date ranges
    """
    query = { "creation_time": { "$gte": start_date , "$lte": end_date} }
    return query
