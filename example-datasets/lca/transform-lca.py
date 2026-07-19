import json
import uuid
from pathlib import Path
from decimal import Decimal

from rdflib import (
    Graph,
    Namespace,
    Literal,
    RDF,
    RDFS,
    BNode,
    XSD,
)

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

INPUT_DIR = Path("./USLCI_Database/processes")
# INPUT_DIR = Path("./test")
OUTPUT_FILE = "uslci.ttl"

# Namespaces
USLCI = Namespace("https://www.lcacommons.gov/lca-collaboration/National_Renewable_Energy_Laboratory/USLCI_Database_Public/datasets/")
EX = Namespace("https://purl.org/supply-network/examples/")
QUDT = Namespace("http://qudt.org/schema/qudt/")
SN = Namespace("https://purl.org/supply-network/onto#")


# -----------------------------------------------------------------------------
# RDF graph
# -----------------------------------------------------------------------------

g = Graph()

g.bind("uslci", USLCI)
g.bind("", EX)
g.bind("qudt", QUDT)
g.bind("sn", SN)
g.bind("rdfs", RDFS)
g.bind("xsd", XSD)

created_products = set()
created_units = set()


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def add_product(flow):
    """Create ProductType resource only once."""
    fid = flow["@id"]

    if fid in created_products:
        return

    created_products.add(fid)

    uri = USLCI[fid]

    g.add((uri, RDF.type, EX.ProductType))
    g.add((uri, RDFS.label, Literal(flow["name"])))


def add_unit(unit):
    """Create Unit resource only once."""
    uid = unit["@id"]

    if uid in created_units:
        return

    created_units.add(uid)

    uri = USLCI[uid]

    g.add((uri, RDF.type, QUDT.Unit))
    g.add((uri, RDFS.label, Literal(unit["name"])))


def create_supply_flow(input_ex, output_ex):
    """Create one SupplyFlow from an input/output pair."""

    # Create deterministic random identifier
    supply_uri = USLCI["sf_" + uuid.uuid4().hex]

    input_amount = Decimal(str(input_ex["amount"]))
    output_amount = Decimal(str(output_ex["amount"]))

    if input_amount == 0:
        return
    if output_amount == 0:
        return

    g.add((supply_uri, RDF.type, SN.SupplyFlow))
    g.add((supply_uri, SN.level, EX.ProductTypeLevel))

    g.add(
        (
            supply_uri,
            EX.input,
            USLCI[input_ex["flow"]["@id"]],
        )
    )

    g.add(
        (
            supply_uri,
            EX.output,
            USLCI[output_ex["flow"]["@id"]],
        )
    )

    volume = BNode()

    g.add((supply_uri, SN.volume, volume))
    g.add((volume, RDF.type, SN.Volume))

    g.add(
        (
            volume,
            SN.unit,
            USLCI[output_ex["unit"]["@id"]],
        )
    )

    quantity = output_amount / input_amount

    g.add(
        (
            volume,
            SN.quantity,
            Literal(quantity, datatype=XSD.decimal),
        )
    )


# -----------------------------------------------------------------------------
# Process files
# -----------------------------------------------------------------------------

for json_file in INPUT_DIR.glob("*.json"):

    with open(json_file, encoding="utf-8") as f:
        process = json.load(f)
        print(f"Processing {json_file} ...")

    exchanges = process.get("exchanges", [])

    inputs = []
    outputs = []

    for ex in exchanges:

        add_product(ex["flow"])
        add_unit(ex["unit"])

        if ex["isInput"]:
            inputs.append(ex)
        else:
            outputs.append(ex)

    # Cartesian product:
    # every input with every output
    for inp in inputs:
        for out in outputs:
            create_supply_flow(inp, out)


# -----------------------------------------------------------------------------
# Save graph
# -----------------------------------------------------------------------------

g.serialize(destination=OUTPUT_FILE, format="turtle")

print(f"Written {len(g)} triples to {OUTPUT_FILE}")
