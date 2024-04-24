from app.models.workflow import WorkflowSearchSchema
from datetime import date
import datetime


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

def date_search(start_date: datetime.date, end_date: datetime.date):
    """
    Search for specific DB record between date ranges
    """
    # end date by default has zero-hour timestamp which means any records created after that
    # will not show up in the results. To include the end date, we must add the day after in the range
    end_date = end_date + datetime.timedelta(days=1)
    query = { "creation_time": { "$gte": str(start_date) , "$lte": str(end_date)} }
    return query
