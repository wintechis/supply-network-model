import hashlib
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from decimal import Decimal

import orjson

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

INPUT_DIR = Path("./USLCI_Database/processes-formatted")
# INPUT_DIR = Path("./test")
OUTPUT_FILE = Path("uslci-provo.ttl")

USLCI = "https://www.lcacommons.gov/lca-collaboration/National_Renewable_Energy_Laboratory/USLCI_Database_Public/datasets/"
EX = "https://purl.org/supply-network/examples/"
QUDT = "http://qudt.org/schema/qudt/"

HEADER = f"""@prefix uslci: <{USLCI}> .
@prefix : <{EX}> .
@prefix qudt: <{QUDT}> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

"""


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def esc(text: str) -> str:
    """Escape Turtle strings."""
    return (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )


def supply_id(input_id, output_id, process_id):
    h = hashlib.blake2b(
        f"{process_id}:{input_id}:{output_id}".encode(),
        digest_size=8,
    ).hexdigest()
    return f"sf_{h}"


def decimal_str(value):
    """Return a valid xsd:decimal lexical form (no scientific notation)."""
    return format(Decimal(str(value)), "f")


# -----------------------------------------------------------------------------
# Worker
# -----------------------------------------------------------------------------

def process_file(json_file):
    with open(json_file, "rb") as f:
        process = orjson.loads(f.read())

    process_id = process.get("@id", json_file.stem)
    process_name = process.get("name", json_file.stem)

    products = {}
    units = {}

    ttl_activity = f"""
uslci:{process_id} a prov:Activity ;
    rdfs:label "{esc(process_name)}" """

    ttl_entities = ""

    exchanges = process.get("exchanges", [])

    inputs = []
    outputs = []

    for ex in exchanges:

        flow = ex["flow"]

        if flow["flowType"] != "PRODUCT_FLOW":
            continue

        unit = ex["unit"]

        products.setdefault(flow["@id"], flow["name"])
        units.setdefault(unit["@id"], unit["name"])

        flow_id = ex["flow"]["@id"]
        ex_amount = Decimal(str(ex["amount"]))
        ex_unit_id = ex["unit"]["@id"]

        if ex["isInput"]:
            ttl_activity = ttl_activity + f""";
    prov:qualifiedUsage [ a prov:Usage ;
            prov:entity uslci:{flow_id} ;
            :quantity {ex_amount} ;
            :unit uslci:{ex_unit_id} ] """
        else:
            ttl_entities = ttl_entities + f"""

uslci:{flow_id} a prov:Entity ;
    prov:qualifiedGeneration [ a prov:Generation ;
            prov:activity uslci:{process_id} ;
            :quantity {ex_amount} ;
            :unit uslci:{ex_unit_id} ] .
"""

    ttl = ttl_activity + "." + ttl_entities

    return products, units, ttl


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():

    files = list(INPUT_DIR.glob("*.json"))

    all_products = {}
    all_units = {}

    ttl_chunks = []

    with ProcessPoolExecutor() as executor:

        for products, units, ttl in executor.map(process_file, files):

            all_products.update(products)
            all_units.update(units)
            ttl_chunks.append(ttl)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:

        out.write(HEADER)

        # Products

        for pid, name in all_products.items():
            out.write(
f"""uslci:{pid} a prov:Entity ;
    rdfs:label "{esc(name)}" .

"""
            )

        # Units

        for uid, name in all_units.items():
            out.write(
f"""uslci:{uid} a qudt:Unit ;
    rdfs:label "{esc(name)}" .

"""
            )

        # Supply flows

        for chunk in ttl_chunks:
            out.write(chunk)

    print(f"Processed {len(files)} files.")
    print(f"Products : {len(all_products)}")
    print(f"Units    : {len(all_units)}")
    print(f"Output   : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()