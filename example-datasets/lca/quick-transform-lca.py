import hashlib
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import orjson

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

INPUT_DIR = Path("./USLCI_Database/processes")
# INPUT_DIR = Path("./test")
OUTPUT_FILE = Path("uslci.ttl")

USLCI = "https://www.lcacommons.gov/lca-collaboration/National_Renewable_Energy_Laboratory/USLCI_Database_Public/datasets/"
EX = "https://purl.org/supply-network/examples/"
QUDT = "http://qudt.org/schema/qudt/"
SN = "https://purl.org/supply-network/onto#"

HEADER = f"""@prefix uslci: <{USLCI}> .
@prefix : <{EX}> .
@prefix qudt: <{QUDT}> .
@prefix sn: <{SN}> .
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


# -----------------------------------------------------------------------------
# Worker
# -----------------------------------------------------------------------------

def process_file(json_file):
    with open(json_file, "rb") as f:
        process = orjson.loads(f.read())

    process_id = process.get("@id", json_file.stem)

    products = {}
    units = {}

    ttl = []

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

        if ex["isInput"]:
            inputs.append(ex)
        else:
            outputs.append(ex)

    for inp in inputs:

        in_amount = float(inp["amount"])
        if in_amount == 0:
            continue

        in_id = inp["flow"]["@id"]

        for out in outputs:

            out_amount = float(out["amount"])
            if out_amount == 0:
                continue

            out_id = out["flow"]["@id"]
            unit_id = out["unit"]["@id"]

            quantity = out_amount / in_amount

            sid = supply_id(in_id, out_id, process_id)

            ttl.append(
f"""uslci:{sid} a sn:SupplyFlow ;
    sn:abstraction :ProductTypeLevel ;
    :input uslci:{in_id} ;
    :output uslci:{out_id} ;
    sn:volume [
        a sn:Volume ;
        sn:unit uslci:{unit_id} ;
        sn:quantity "{quantity}"^^xsd:decimal
    ] .

"""
            )

    return products, units, "".join(ttl)


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
f"""uslci:{pid} a :ProductType ;
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