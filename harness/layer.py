"""Tool-layer wrapper: verify every returned record harness-side against the full database entry and
either annotate the summary with a verification block (agent decides) or replace mismatched values (ceiling)."""
import json


class HarnessLayer:
    def __init__(self, inner, dom, table_s, table_f, mode, check):
        self.inner, self.dom, self.ts, self.tf, self.mode, self.check = inner, dom, table_s, table_f, mode, check

    @property
    def calls(self): return self.inner.calls

    def call(self, tool, args):
        out, err = self.inner.call(tool, args)
        if err: return out, err
        rec = json.loads(out); acc = rec.get("accession") or str(rec.get("cid"))
        corr = self.inner.corruption if acc == self.inner.target_acc else None
        full = json.loads(self.dom.render(self.tf, self.ts.by_acc[acc], corr))
        v = self.check(rec, self.ts, full=full)
        bad = {f: r for f, r in v.items() if r.get("status") in ("mismatch", "not_found")}
        entry = self.inner.calls[-1]; entry["harness"] = {"mode": self.mode, "flagged": sorted(bad), "verdicts": v}
        if bad and self.mode == "replace":
            for f, r in bad.items():
                if "derived" in r and f not in ("gene_symbol", "name"): rec[f] = r["derived"]
        rec["_verification"] = ({f: {k: r[k] for k in ("status", "observed", "derived", "route") if k in r} for f, r in bad.items()}
                                if bad else "all fields consistent with the full database record")
        new = json.dumps(rec); entry["annotated_output"] = new
        return new, False
