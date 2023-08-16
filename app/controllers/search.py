from app.models.workflow import WorkflowSearchSchema

def compound_queries(query_params: WorkflowSearchSchema):
    query =  { "$match": { "$text":
                           {"$search": query_params.cube_username}

                           }
               }
    response = {
        "$project": {
            "_id": 1,
            "request.cube_user_info.username": 1
        }
    }
    return query, response

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