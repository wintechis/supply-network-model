# Patterns to map a formalisation to RDF/RDFS

| Formalisation | Description | RDF/RDFS | Constraints |
| - | - | - | - |
| $A$ | Set $A$ | Class | - |
| $A \subseteq B$ | Subset $A$ | Subclass | - |
| $A \subseteq B \times C$ | Binary relation $A$ | Property | - |
| $A \subseteq B \times C \times D$ | N-ary relation $A$ | Reified class + one property per arity $B$, $C$, $D$ | All properties functional + unique combination of property values $B \times C \times D$ |
| $A \subseteq B \times C$ and $D \subseteq A \times E$ | Qualified binary relation $A$ | Reified class + one property for $B$, $C$ | All properties functional + unique combination of property values $B \times C$ |
| $A: B \rightarrow C$ | Unary function $A$ | Property | Functional property |
| $A: B \times C \rightarrow D$ | N-ary function $A$ | Reified class + one property per arity $B$, $C$ + one property for $D$ | All properties functional + unique combination of property values $B \times C$ |
| $A_a \subseteq B_a \times B_a$ and $B_a \subseteq B$ and $A_a \subseteq A$ | ? $A_a$ | Subproperty | ? |
| $A_{a \rightarrow b} \subseteq B_a \times B_b$ and $B_a, B_b \subseteq B$ | ? $A_a$ | Subproperty | ? |
