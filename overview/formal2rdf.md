# Patterns to map a formalisation to RDF/RDFS

| Formalisation | Description | RDF/RDFS Concept | RDFS Ontology | Constraints |
| - | - | - | - | - |
| $A$ | Set $A$ | Class | :A a rdfs:Class . | - |
| $A \subseteq B$ | Subset $A$ | Subclass | :A rdfs:subClassOf :B . | - |
| $A \subseteq B \times C$ | Binary relation $A$ | Property | :A rdfs:domain :B ; rdfs:range :C . | - |
| $A \subseteq B \times C \times D$ | N-ary relation $A$ | Reified class + one property per arity $B$, $C$, $D$ | :A a rdfs:Class . :b rdfs:domain :A ; rdfs:range :B . :c rdfs:domain :A ; rdfs:range :C . :d rdfs:domain :A ; rdfs:range :D . | All properties functional + unique combination of property value instances :B, :C, :D per :A instance |
| $A \subseteq B \times C$ and $D \subseteq A \times E$ | Qualified binary relation $A$ | Reified class + one property each for $B$, $C$ | :A a rdfs:Class . :b rdfs:domain :A ; rdfs:range :B . :c rdfs:domain :A ; rdfs:range :C . | All properties functional + unique combination of property value instances :B, :C per :A instance |
| $A: B \rightarrow C$ | Unary function $A$ | Property | :A rdfs:domain :B ; rdfs:range :C . | Functional property :A |
| $A: B \times C \rightarrow D$ | N-ary function $A$ | Reified class + one property per arity $B$, $C$ + one property for $D$ | :A a rdfs:Class . :b rdfs:domain :A ; rdfs:range :B . :c rdfs:domain :A ; rdfs:range :C . :d rdfs:domain :A ; rdfs:range :D . | All properties functional + unique combination of property value instances :B, :C per :A instance |
| $A \subseteq B \times C$ and $D \subseteq E \times F$ and $A \subseteq D$ | Subrelation $A$ | Subproperty | :A rdfs:subPropertyOf :D . | - |
| $A_{a \rightarrow b} \subseteq B_a \times B_b$ and $B_a, B_b \subseteq B$ | ? $A_a$ | Subproperty | ? | ? |
