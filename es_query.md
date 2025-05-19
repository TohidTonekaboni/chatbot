GET _cat/indices?v


PUT /mana_products
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1
  }
}


DELETE /mana_products


GET mana_products/_search
{
  "query": {
    "match_all": {}
  },
  "size": 100
}


POST mana_products/_delete_by_query
{
  "query": {
    "match_all": {}
  }
}


GET mana_products/_count
{
  "query": {
    "match_all": {}
  }
}