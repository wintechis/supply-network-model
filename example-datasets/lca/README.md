# Life Cicle Assessment Dataset

`olca-schema.ttl` downloaded from [greendelta.github.io](http://greendelta.github.io/olca-schema/schema.ttl); fixed two ttl syntax errors.

`context.jsonld` downloaded from [greendelta.github.io](http://greendelta.github.io/olca-schema/context.jsonld).

`USLCI_Database` downloaded from [lcacommons.gov](https://www.lcacommons.gov/lca-collaboration/National_Renewable_Energy_Laboratory/USLCI_Database_Public/datasets).

`quick-transform-lca.py` creates a proper RDF graph from the dataset. Even though the `USLCI_Database` is available as JSON-LD, the data only uses `@type` and `@id` annotations, resulting in only `rdf:type` triples.

Example of a resulting supply flow modelled with SNAPO:

```[ttl]
uslci:1a34bf95-f897-4af9-b70c-368fce9e41d6 a :ProductType ;
    rdfs:label "Natural gas; production mixture; to energy use" .
uslci:43aed9d7-5a9b-3f3e-8d51-cc8bebd9a9a1 a :ProductType ;
    rdfs:label "Acenaphthene" .
uslci:xx a sn:SupplyFlow ;
    sn:abstraction :ProductTypeLevel ;
    :input uslci:1a34bf95-f897-4af9-b70c-368fce9e41d6 ;
    :output uslci:43aed9d7-5a9b-3f3e-8d51-cc8bebd9a9a1 ;
    sn:volume [ a sn:Volume ;
        sn:unit uslci:20aadc24-a391-41cf-b340-3e4529f44bde" ;
        sn:quantity "4.2393504057720465E-11"^^xsd:decimal .]
```
