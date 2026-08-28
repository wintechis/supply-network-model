import hashlib
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from decimal import Decimal

import orjson

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

INPUT_DIR = Path("./USLCI_Database/processes")
# INPUT_DIR = Path("./test")
OUTPUT_FILE = Path("uslci-snapo.ttl")

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

    products = {}
    units = {}

    ttl = []

    exchanges = process.get("exchanges", [])

    inputs = []
    outputs = []
    waste = None

    for ex in exchanges:

        flow = ex["flow"]
        
        # Disposal; hazardous waste
        if flow["@id"] == "b20513f5-f6ff-4753-90e7-01e1b1e9eada":
            waste  = ex

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

        in_amount = Decimal(str(inp["amount"]))
        if in_amount == 0:
            continue
        # print(f"in_amount: {in_amount}")

        in_id = inp["flow"]["@id"]
        inp_unit_id = inp["unit"]["@id"]

        for out in outputs:

            out_amount = Decimal(str(out["amount"]))
            if out_amount == 0:
                continue
            # print(f"out_amount: {out_amount}")

            out_id = out["flow"]["@id"]
            out_unit_id = out["unit"]["@id"]

            quantity = in_amount / out_amount

            sid = supply_id(in_id, out_id, process_id)

            waste_str = ""

            if waste != None:
                waste_amount = Decimal(str(waste["amount"])) / out_amount
                waste_str = (
                    f'uslci:{out_id} uslci:waste '
                    f'"{decimal_str(waste_amount)}"^^xsd:decimal .'
                )

            ttl.append(
f"""uslci:{sid} a sn:SupplyFlow ;
    sn:abstraction :ProductTypeAbstraction ;
    :input uslci:{in_id} ;
    :output uslci:{out_id} ;
    sn:volume [
        a sn:Volume ;
        sn:unit uslci:{inp_unit_id} ;
        sn:quantity "{decimal_str(quantity)}"^^xsd:decimal
    ] .
uslci:{out_id} qudt:unit uslci:{out_unit_id} .
{waste_str}

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