import os
import requests
import pandas as pd
import sparql_dataframe
import numpy as np
import networkx as nx
from rdflib import Graph
from rdflib.plugins.sparql import prepareQuery
from urllib.parse import quote
from io import StringIO

# SPARQL endpoint URL 
HOSTNAME_ENDPOINT = 'http://localhost:3030/sn-levels/'
QUERY_ENDPOINT = HOSTNAME_ENDPOINT + 'query'
UPDATE_ENDPOINT = HOSTNAME_ENDPOINT + 'update'

# aggregation queries to transform data to higher abstraction level

QUERY_AGGREGATE_ENTTYPECOUNTRY = """
PREFIX :   <http://example.org/onto/>
PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
INSERT {
    _:tupleA a :Tuple ;              
        a [ a rdfs:Class ;                    
            :enterpriseType ?enterpriseTypeA ;                  
            :country ?countryA ] . 
    ?enterpriseTypeA a :EnterpriseType .
    ?countryA a :Country .
    _:tupleRelation a :TupleRelation ;         
        :into _:tupleA ;                     
        :from _:tupleB ;         
        :enterpriseQuantity ?quantity .                                  
    _:tupleB a :Tuple ;              
        a [ a rdfs:Class ;                    
            :enterpriseType ?enterpriseTypeB ;                  
            :country ?countryB ] .
    ?enterpriseTypeB a :EnterpriseType .
    ?countryB a :Country .
} WHERE {
    {
        SELECT ?countryA ?countryB ?enterpriseTypeA ?enterpriseTypeB (COUNT(?enterpriseRelation) AS ?quantity)
        WHERE {
            ?enterpriseA a :Enterprise ;
                :enterpriseType ?enterpriseTypeA ;
                :jurisdiction ?countryA .
            ?enterpriseRelation a :EnterpriseRelation ;
                :into ?enterpriseA ;
                :from ?enterpriseB .
            ?enterpriseB a :Enterprise ;
                :enterpriseType ?enterpriseTypeB ;
                :jurisdiction ?countryB .
        } GROUP BY ?countryA ?countryB ?enterpriseTypeA ?enterpriseTypeB
    }
}
"""

QUERY_AGGREGATE_ENTTYPECONTINENT = """
PREFIX :   <http://example.org/onto/>
PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
INSERT {
    _:tupleA a :Tuple ;              
        a [ a rdfs:Class ;                    
            :enterpriseType ?enterpriseTypeA ;                  
            :continent ?continentA ] . 
    _:tupleRelation a :TupleRelation ;         
        :into _:tupleA ;                     
        :from _:tupleB ;         
        :enterpriseQuantity ?quantity .                                  
    _:tupleB a :Tuple ;              
        a [ a rdfs:Class ;                    
            :enterpriseType ?enterpriseTypeB ;                  
            :continent ?continentB ] .
} WHERE {
    {
        SELECT ?continentA ?continentB ?enterpriseTypeA ?enterpriseTypeB (SUM(?enterpriseQuantity) AS ?quantity)
        WHERE {
            ?tupleA a :Tuple ;              
                a [ a rdfs:Class ;                    
                    :enterpriseType ?enterpriseTypeA ;                  
                    :country ?countryA ] . 
            ?countryA :continent ?continentA .
            ?continentA a :Continent .
            ?tupleRelation a :TupleRelation ;         
                :into ?tupleA ;                     
                :from ?tupleB ;         
                :enterpriseQuantity ?enterpriseQuantity .                                  
            ?tupleB a :Tuple ;              
                a [ a rdfs:Class ;                    
                    :enterpriseType ?enterpriseTypeB ;                  
                    :country ?countryB ] . 
            ?countryB :continent ?continentB .
            ?continentB a :Continent .  
        } GROUP BY ?continentA ?continentB ?enterpriseTypeA ?enterpriseTypeB
    }
}
"""

QUERY_AGGREGATE_ENTTYPE = """
PREFIX :   <http://example.org/onto/>
PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
INSERT {
    _:enterpriseTypeRelation a :EnterpriseTypeRelation ;         
        :into ?enterpriseTypeA ;                     
        :from ?enterpriseTypeB ;         
        :enterpriseQuantity ?quantity .                                  
} WHERE {
    {
        SELECT ?enterpriseTypeA ?enterpriseTypeB (SUM(?enterpriseQuantity) AS ?quantity)
        WHERE {
            ?tupleA a :Tuple ;              
                a [ a rdfs:Class ;                    
                    :enterpriseType ?enterpriseTypeA ;                  
                    :country ?countryA ] . 
            ?enterpriseTypeA a :EnterpriseType .
            ?tupleRelation a :TupleRelation ;         
                :into ?tupleA ;                     
                :from ?tupleB ;         
                :enterpriseQuantity ?enterpriseQuantity .                                  
            ?tupleB a :Tuple ;              
                a [ a rdfs:Class ;                    
                    :enterpriseType ?enterpriseTypeB ;                  
                    :country ?countryB ] .
            ?enterpriseTypeB a :EnterpriseType .
        } GROUP BY ?enterpriseTypeA ?enterpriseTypeB
    }
}
"""

QUERY_AGGREGATE_COUNTRY = """
PREFIX :   <http://example.org/onto/>
PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
INSERT {
    _:countryRelation a :CountryRelation ;         
        :into ?countryA ;                     
        :from ?countryB ;         
        :enterpriseQuantity ?quantity .                                  
} WHERE {
    {
        SELECT ?countryA ?countryB (SUM(?enterpriseQuantity) AS ?quantity)
        WHERE {
            ?tupleA a :Tuple ;              
                a [ a rdfs:Class ;                    
                    :enterpriseType ?enterpriseTypeA ;                  
                    :country ?countryA ] . 
            ?countryA a :Country .
            ?tupleRelation a :TupleRelation ;         
                :into ?tupleA ;                     
                :from ?tupleB ;         
                :enterpriseQuantity ?enterpriseQuantity .                                  
            ?tupleB a :Tuple ;              
                a [ a rdfs:Class ;                    
                    :enterpriseType ?enterpriseTypeB ;                  
                    :country ?countryB ] .
            ?countryB a :Country .
        } GROUP BY ?countryA ?countryB
    }
}
"""

QUERY_AGGREGATE_CONTINENT = """
PREFIX :   <http://example.org/onto/>
PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
INSERT {
    _:continentRelation a :ContinentRelation ;         
        :into ?continentA ;                     
        :from ?continentB ;         
        :enterpriseQuantity ?quantity .                                  
} WHERE {
    {
        SELECT ?continentA ?continentB (SUM(?enterpriseQuantity) AS ?quantity)
        WHERE {
            ?tupleA a :Tuple ;              
                a [ a rdfs:Class ;                    
                    :enterpriseType ?enterpriseTypeA ;                  
                    :continent ?continentA ] . 
            ?continentA a :Continent .
            ?tupleRelation a :TupleRelation ;         
                :into ?tupleA ;                     
                :from ?tupleB ;         
                :enterpriseQuantity ?enterpriseQuantity .                                  
            ?tupleB a :Tuple ;              
                a [ a rdfs:Class ;                    
                    :enterpriseType ?enterpriseTypeB ;                  
                    :continent ?continentB ] .
            ?continentB a :Continent .
        } GROUP BY ?continentA ?continentB
    }
}
"""


# Function to run aggregation queries
def run_aggregation_queries():
    try:
        print("Running query to aggregate (enterprise type, country) tuples from enterprises")
        sparql_response = requests.post(UPDATE_ENDPOINT, headers={'Content-Type': 'application/sparql-update'}, data=QUERY_AGGREGATE_ENTTYPECOUNTRY)
        sparql_response.raise_for_status()  # Raise an exception for HTTP errors
        print("HTTP status: " + str(sparql_response.status_code))

        print("Running query to aggregate (enterprise type, continent) tuples from (enterprise type, country) tuples")
        sparql_response = requests.post(UPDATE_ENDPOINT, headers={'Content-Type': 'application/sparql-update'}, data=QUERY_AGGREGATE_ENTTYPECONTINENT)
        sparql_response.raise_for_status()  # Raise an exception for HTTP errors
        print("HTTP status: " + str(sparql_response.status_code))

        print("Running query to aggregate enterprise types from (enterprise type, country) tuples")
        sparql_response = requests.post(UPDATE_ENDPOINT, headers={'Content-Type': 'application/sparql-update'}, data=QUERY_AGGREGATE_ENTTYPE)
        sparql_response.raise_for_status()  # Raise an exception for HTTP errors
        print("HTTP status: " + str(sparql_response.status_code))

        print("Running query to aggregate countries from (enterprise type, country) tuples")
        sparql_response = requests.post(UPDATE_ENDPOINT, headers={'Content-Type': 'application/sparql-update'}, data=QUERY_AGGREGATE_COUNTRY)
        sparql_response.raise_for_status()  # Raise an exception for HTTP errors
        print("HTTP status: " + str(sparql_response.status_code))

        print("Running query to aggregate continents from (enterprise type, continent) tuples")
        sparql_response = requests.post(UPDATE_ENDPOINT, headers={'Content-Type': 'application/sparql-update'}, data=QUERY_AGGREGATE_CONTINENT)
        sparql_response.raise_for_status()  # Raise an exception for HTTP errors
        print("HTTP status: " + str(sparql_response.status_code))

        print("Aggregation queries succesfull.")
    except Exception as e:
        print(f"Error processing query: {e}")



# run code
print("Running infer-supplynetworks.py")
run_aggregation_queries()
