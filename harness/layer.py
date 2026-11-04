"""Tool-layer wrapper: verify every returned record harness-side against the full database entry and
either annotate the summary with a verification block (agent decides) or replace mismatched values (ceiling)."""
import json
import os


UNI = {"length": ("sequence", "length"), "mass": ("sequence", "molWeight"), "organism": ("organism", "scientificName"),
       "gene_symbol": ("genes", 0, "geneName", "value")}  # where a full UniProt record keeps the summary fields
def _get(d, path):
    for k in path: d = d[k]
    return d
def _pop(d, path):
    for k in path[:-1]: d = d[k]
    if isinstance(d, dict): d.pop(path[-1], None)


class HarnessLayer:
    def __init__(self, inner, dom, table_s, table_f, mode, check):
        self.inner, self.dom, self.ts, self.tf, self.mode, self.check = inner, dom, table_s, table_f, mode, check

    @property
    def calls(self): return self.inner.calls

    def call(self, tool, args):
        out, err = self.inner.call(tool, args)
        if err: return out, err
        rec = json.loads(out); full_prot = "primaryAccession" in rec
        acc = rec.get("accession") or rec.get("primaryAccession") or str(rec.get("cid"))
        view = rec
        if full_prot:  # summary view of a full protein record for the derivation check
            view = {"accession": acc}
            for f, path in UNI.items():
                try: view[f] = _get(rec, path)
                except (KeyError, IndexError, TypeError): pass
        corr = self.inner.corruption if acc == self.inner.target_acc else None
        full = json.loads(self.dom.render(self.tf, self.ts.by_acc[acc], corr))
        v = self.check(view, self.ts, full=full)
        bad = {f: r for f, r in v.items() if r.get("status") in ("mismatch", "not_found")}
        if os.environ.get("HARNESS_SECOND_SOURCE") == "1":  # Phase 3: independent database
            from harness import second_source as ss
            if "length" in rec or "mass" in rec:
                sv, route = ss.check_protein_ss(acc, rec), "second source: AlphaFold DB sequence for this accession"
            else:
                sv, route = ss.check_compound_ss(self.ts.by_acc[acc].get("cid", acc), rec), "second source: NCI CACTUS structure for this compound name"
            for f, r in sv.items():
                v[f + "_second_source"] = r
                if r["status"] == "mismatch" and f not in bad:
                    ref = r["second_source"]
                    try: ref = round(float(ref), 2) if f in ("mass", "molecular_weight") else int(ref)
                    except (TypeError, ValueError): pass
                    bad[f] = {"status": "mismatch", "observed": r["record"], "derived": ref, "route": route}
        entry = self.inner.calls[-1]; entry["harness"] = {"mode": self.mode, "flagged": sorted(bad), "verdicts": v}
        if bad and self.mode == "replace":
            for f, r in bad.items():
                if "derived" in r and f not in ("gene_symbol", "name"): rec[f] = r["derived"]
        rec["_verification"] = ({f: {k: r[k] for k in ("status", "observed", "derived", "route") if k in r} for f, r in bad.items()}
                                if bad else "all fields consistent with the full database record")
        if bad and self.mode == "blank":  # withhold mismatched derivable fields, no note; identifiers untouched
            for f in list(bad):
                if f in ("gene_symbol", "name"): continue
                if full_prot: _pop(rec, UNI.get(f, (f,)))
                else: rec.pop(f, None)
            rec.pop("_verification", None)
        style = os.environ.get("HARNESS_REPLACE_STYLE")  # robustness Part 3: how a replacement is presented
        if self.mode == "replace" and style == "silent":
            rec.pop("_verification", None)
        elif self.mode == "replace" and style == "labeled" and bad:
            rec["_verification"] = {f: ({"status": "replaced", "value_now_shown_in_this_record": r["derived"],
                                         "source_of_value_shown": r.get("route"), "original_database_value_replaced": r.get("observed")}
                                        if ("derived" in r and f not in ("gene_symbol", "name"))
                                        else {k: r[k] for k in ("status", "observed", "derived", "route") if k in r}) for f, r in bad.items()}
        new = json.dumps(rec); entry["annotated_output"] = new
        return new, False
