# NMI outline: Consistency, not plausibility: why tool-using science agents relay database errors

## Abstract (~150 words)
Agents notice wrong database values but relay them anyway. What decides relay is agreement among record fields, not plausibility
or the availability of a derivation route. Real corrected UniProt errors pass 90-100% of the time. A second source fixes most of it,
except where agents defer to a primary record that is longer than the second source.

## Results
1. A deployed agent relays corrupted live database values (Biomni; OSF vq5cp). Impossible 2%, plausible 24-28% (DeepSeek, Flash);
   derivation routes are used when the workflow passes through them (H2 reversed). Fig. 1: proxy setup and rates.
2. Noticed yet answered (benchmark; 10 models, 5 vendors, 2 domains). Impossible values flagged in 75-100% of runs and relayed in
   32-93%; plausible values relayed in 93-100%, direction-blind. Cue taxonomy (needs validation-set agreement). Fig. 2.
3. What makes an agent override.
   3a. Internal contradiction: the full record corrects only when it contradicts the value (benchmark full-record experiment).
   3b. Boundaries: override curves exist but are task-set-specific (Phase 1; Phase 4b E1).
   3c. Coherence defeats the full record (Phase 3): coherent plausible 70-98% relayed; visible artifacts are a cue some models use (v1/v2).
   3d. Agreement decides (Phase 4b): one more agreeing field raises relay (Opus 52 -> 87%); in-record disagreement lowers it.
   3e. A route enables detection, not override (Phase 4): models compute the true mass, say so, and answer from the record;
       placeholders (0 Da) are replaced, data are reported. Figs. 3-4.
4. Real errors (Phase 5, UniSave): 79 historically corrected sequences relayed in 90-100% of runs, with no size gradient. Fig. 5.
5. Mitigation (Phases 2, 3, 5). Derivation checks: proteins 0-1%, chemistry residual is names. Second source: catches covered
   entities, but flag-and-defer persists where the record is longer (Phase 3 and Phase 5 R3; DeepSeek 31% on real errors).
   A false all-clear does not certify errors (P4 null). Annotate ~ replace (Phase 2, rerun on independent runs). Fig. 6.

## Discussion
Verification must live outside the model and be enforced (replace, not annotate, where a derived value exists); agents treat the
primary record as authoritative even against their own computation; implications for agent and database design.
Limits: one sample per cell; two domains; constructed corruptions except Phase 5; historical annotations unavailable; model
snapshots dated; three cache-key collisions found and corrected (leak check caught one).

## Methods
Tasks and templates; corruption designs (single-field, coherent, scaled, real); record formats; models and providers; harness
(derivation checks, second sources with coverage and false-alarm floors); pre-registrations (OSF links for Biomni, Phase 4 + 4b
addendum, Phase 5) and dated in-repo predictions (Phase 3); analysis and exclusions; cache keys and leak check; costs.

## Still needed before drafting
- Validation labelling (200 protein + 100 chemistry concerns) and second annotator: Results 2 cue claims depend on it.
- OSF links for the Phase 4 registration, 4b addendum and Phase 5 registration into the repo.
