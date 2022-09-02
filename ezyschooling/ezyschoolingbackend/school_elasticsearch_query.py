body = {  
    "query": {  
        "bool": { 
            "must": [
                {
                    "nested" : {
                        "path" : "feestructure_set",
                        "query" : {
                            "bool" : {
                                "must" : [
                                    {
                                        "match" : { 
                                            "feestructure_set.class_relation.slug" : "7"
                                        },
                                    },
                                    {
                                        "range" : {
                                            "feestructure_set.fee_price" : {
                                                "gte" : 100,
                                                "lte" : 1000
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    }
                },
                # {
                #     "simple_query_string": {
                #         "query": "school",
                #         "fields": ["name^3"],
                #     }
                # },
                {
                    "match": { 
                        "school_type.slug" : "primary" 
                    }
                },
                # {
                #     "match": { 
                #         "region.slug" : "east-delhi-z8o32fe2" 
                #     }
                # },
                # {
                #     "match": { 
                #         "state.slug" : "delhi" 
                #     }
                # },
                # {
                #     "match": {  
                #         "school_board.slug" : "cbse"
                #     } 
                # },
                # {
                #     "match": {  
                #         "school_category" : "Boys"
                #     } 
                # }
            ],
            "filter": {
                "geo_distance": {
                    "distance": "15km",
                    "geocoords" : {
                            "lat" : 28.6894,
                            "lon" : 77.2919
                    }
                }
            }
        } 
    }  
}


body = {  
    "query": {  
        "bool": { 
            "must": {
                "match": { 
                    "school_type.slug" : { 
                        "query" : "primary" 
                    } 
                }, 
                "match": {  
                    "school_board.slug" : {  
                         "query" : "cbse"  
                    }  
                } 
            }
        } 
    }  
}

res = es.search(  
    index="local-ezyschooling-school-profile",  
    body=body,  
)

body = {
    "query": {
        "nested" : {
            "path" : "feestructure_set",
            "query" : { 
                "match" : { 
                    "feestructure_set.active" : True 
                },
            }
        }
    }
}