"""Corruption spec: three conditions (clean / impossible / plausible) over one target field.

`make_corruption` returns a dict describing field overrides for ONE record. The tool layer
applies these overrides on top of the clean record, so the returned record is byte-identical
to clean except for the overridden values.
"""
import random

CONDITIONS = ["clean", "impossible", "plausible"]
TARGET_FIELDS = ["length", "mass", "organism", "gene_symbol"]
PLAUSIBLE_FACTORS = [0.75, 0.8, 1.2, 1.25]
SHRINK_FACTORS = [0.75, 0.8]
INFLATE_FACTORS = [1.2, 1.25]
IMPOSSIBLE_LENGTH_INFLATE = 60000       # longer than titin (~36k residues)
IMPOSSIBLE_MASS_INFLATE = 9_000_000_000  # 9 GDa, impossible for a single polypeptide
IMPOSSIBLE_ORGANISM = "Escherichia coli K-12"
PLAUSIBLE_ORGANISM = "Mus musculus"

# substrings of UniProt subcellular-location strings that only make sense in a eukaryote
EUKARYOTE_ONLY_KEYWORDS = [
    "nucle", "golgi", "mitochondri", "endoplasmic reticulum", "lysosom", "peroxisom",
    "endosom", "endomembrane", "p-body", "synap", "melanosome", "sarcoplasmic",
    "centrosome", "cilium", "spindle", "chromosome", "cytoskeleton", "stress granule",
]


def is_eukaryote_only(location):
    loc = (location or "").lower()
    return any(k in loc for k in EUKARYOTE_ONLY_KEYWORDS)


def fake_gene_symbol(rng, existing_symbols):
    """Syntactically valid symbol (3 letters + digit) that is not in the table."""
    existing = {s.upper() for s in existing_symbols}
    while True:
        sym = "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(3)) + str(rng.randint(1, 9))
        if sym not in existing:
            return sym


def make_corruption(condition, record, target_field, rng, table, factor=None, direction=None):
    """Return {"fields": {...overrides...}, "clean_value", "corrupted_value", "factor"} for one record.

    `table` is the list of all clean records (for gene-symbol swaps / fake-symbol checks).
    `factor` optionally pins the plausible scaling factor (task templates may need shrink-only).
    """
    assert condition in ("impossible", "plausible"), condition
    assert target_field in TARGET_FIELDS, target_field
    clean_val = record[target_field]
    out = {"fields": {}, "clean_value": clean_val, "corrupted_value": None, "factor": None, "direction": direction}

    if condition == "impossible":
        if target_field == "length":
            # mass untouched -> internally inconsistent too
            out["fields"] = {"length": IMPOSSIBLE_LENGTH_INFLATE if direction == "inflate" else 3}
        elif target_field == "mass":
            # alternate by seed between an absurdly small and a negative mass
            if direction == "inflate":
                v = IMPOSSIBLE_MASS_INFLATE
            else:  # alternate by seed between an absurdly small and a negative mass
                v = 45 if rng.random() < 0.5 else -record["mass"]
            out["fields"] = {"mass": v}
        elif target_field == "organism":
            assert is_eukaryote_only(record["subcellular_location"]), (
                "impossible organism corruption needs a eukaryote-only compartment")
            out["fields"] = {"organism": IMPOSSIBLE_ORGANISM}
        elif target_field == "gene_symbol":
            out["fields"] = {"gene_symbol": fake_gene_symbol(rng, [r["gene_symbol"] for r in table])}
    else:  # plausible
        if target_field in ("length", "mass"):
            pool = {"shrink": SHRINK_FACTORS, "inflate": INFLATE_FACTORS}.get(direction, PLAUSIBLE_FACTORS)
            f = factor if factor is not None else rng.choice(pool)
            out["factor"] = f
            out["fields"] = {"length": int(round(record["length"] * f)),
                             "mass": int(round(record["mass"] * f))}
        elif target_field == "organism":
            out["fields"] = {"organism": PLAUSIBLE_ORGANISM}
        elif target_field == "gene_symbol":
            others = [r for r in table if r["accession"] != record["accession"]]
            out["fields"] = {"gene_symbol": rng.choice(others)["gene_symbol"]}

    out["corrupted_value"] = out["fields"][target_field]
    return out


def apply_corruption(record, corruption):
    """Return a copy of the clean record with the corruption's field overrides applied."""
    rec = dict(record)
    if corruption:
        rec.update(corruption["fields"])
    return rec


def make_scaled_corruption(record, target_field, factor, consistent):
    """Sweep corruption: scale the target field by `factor`; if `consistent`, scale the paired
    field (length<->mass) by the same factor so the record stays internally consistent."""
    assert target_field in ("length", "mass")
    scaled = lambda v: max(1, int(round(v * factor)))
    fields = {target_field: scaled(record[target_field])}
    if consistent:
        other = "mass" if target_field == "length" else "length"
        fields[other] = scaled(record[other])
    return {"fields": fields, "clean_value": record[target_field], "corrupted_value": fields[target_field],
            "factor": factor, "consistent": consistent}
