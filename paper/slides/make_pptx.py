"""Build the 8-slide workshop talk as an editable .pptx from the ICML figures."""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
NAVY, NAVY_LT, INK, MUTED, PANEL = RGBColor(0x1C,0x5C,0xAB), RGBColor(0xB5,0xD4,0xF4), RGBColor(0x0B,0x0B,0x0B), RGBColor(0x52,0x51,0x4E), RGBColor(0xF3,0xF5,0xF9)
RED, RED_BG, AMB, AMB_BG, WHITE = RGBColor(0x79,0x1F,0x1F), RGBColor(0xFC,0xEB,0xEB), RGBColor(0x63,0x38,0x06), RGBColor(0xFA,0xEE,0xDA), RGBColor(0xFF,0xFF,0xFF)
W, H = Inches(13.333), Inches(7.5)
prs = Presentation(); prs.slide_width, prs.slide_height = W, H
BLANK = prs.slide_layouts[6]


def rect(s, x, y, w, h, fill, line=None, shape=MSO_SHAPE.RECTANGLE):
    r = s.shapes.add_shape(shape, x, y, w, h); r.fill.solid(); r.fill.fore_color.rgb = fill
    if line is None: r.line.fill.background()
    else: r.line.color.rgb = line; r.line.width = Pt(0.75)
    r.shadow.inherit = False; return r


def text(s, x, y, w, h, runs, size=14, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font="Calibri", line=1.15):
    """runs: str or list of (text, size, color, bold) tuples; '\n' starts a new paragraph."""
    tb = s.shapes.add_textbox(x, y, w, h); tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05); tf.margin_top = tf.margin_bottom = Inches(0.03)
    paras = runs if isinstance(runs, list) else [[(runs, size, color, bold)]]
    if isinstance(paras[0], tuple): paras = [paras]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = align; p.line_spacing = line
        for t, sz, col, b in para:
            r = p.add_run(); r.text = t; r.font.size = Pt(sz); r.font.color.rgb = col; r.font.bold = b; r.font.name = font
    return tb


def title(s, t):
    rect(s, Inches(0.5), Inches(0.42), Inches(0.09), Inches(0.42), NAVY)
    text(s, Inches(0.68), Inches(0.32), Inches(12), Inches(0.6), t, size=26, bold=True)
    rect(s, Inches(0.5), Inches(0.98), Inches(12.33), Pt(0.75), RGBColor(0xC3,0xC2,0xB7))


def takeaway(s, t):
    r = rect(s, Inches(0.5), Inches(6.55), Inches(12.33), Inches(0.62), NAVY)
    tf = r.text_frame; tf.margin_left = Inches(0.2); tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; run = p.add_run(); run.text = t; run.font.size = Pt(16); run.font.bold = True; run.font.color.rgb = WHITE; run.font.name = "Calibri"


def bignum(s, x, y, w, num, cap, size=30):
    text(s, x, y, w, Inches(0.6), num, size=size, color=NAVY, bold=True)
    text(s, x, y + Inches(0.58), w, Inches(0.7), cap, size=11, color=MUTED)


def picture(s, name, x, y, w=None, h=None):
    p = FIG / f"{name}.png"; return s.shapes.add_picture(str(p), x, y, width=w, height=h)


def footer(s, n):
    text(s, Inches(0.5), Inches(7.2), Inches(8), Inches(0.3), "Xu — Consistency, Not Plausibility", size=9, color=MUTED)
    text(s, Inches(11.8), Inches(7.2), Inches(1), Inches(0.3), f"{n} / 8", size=9, color=MUTED, align=PP_ALIGN.RIGHT)


# ---------------------------------------------------------------- 1 title
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, W, Inches(3.5), NAVY)
text(s, Inches(0.7), Inches(0.9), Inches(12), Inches(1.0), "Consistency, not plausibility", size=40, color=WHITE, bold=True)
text(s, Inches(0.7), Inches(1.9), Inches(12), Inches(1.0), "Dissociating detection from correction of corrupted tool records in biological LLM agents", size=20, color=NAVY_LT)
text(s, Inches(0.7), Inches(4.2), Inches(12), Inches(0.5), "George Xu", size=22, bold=True)
text(s, Inches(0.7), Inches(4.75), Inches(12), Inches(0.5), "Harvard Medical School and Massachusetts General Hospital", size=14, color=MUTED)
text(s, Inches(0.7), Inches(6.2), Inches(12), Inches(0.5), "NeurIPS 2026 Workshop: Agentic AI for Biological Discovery  ·  github.com/Quantum535/bioagent-plausibility", size=12, color=MUTED)

# ---------------------------------------------------------------- 2 problem + setup
s = prs.slides.add_slide(BLANK); title(s, "A well-formed record with a wrong value")
text(s, Inches(0.5), Inches(1.2), Inches(6.0), Inches(2.4), [
    [("Biology agents act on what their tools return. ", 14, INK, True), ("A failed call is handled by the harness. A record that parses but holds a wrong value carries no signal; the only defence is the agent's own biology.", 14, INK, False)],
    [("", 8, INK, False)],
    [("We corrupt one field of one record ", 14, INK, True), ("and nothing else, then ask for an answer and a list of concerns, so noticing and answering are graded separately, by code.", 14, INK, False)]], line=1.2)
for i, (lab, body, fg, bg) in enumerate([("Impossible", "3-residue, 58 kDa protein · E. coli with a nuclear location · 2 Da molecule · −3 donors", RED, RED_BG),
                                          ("Plausible", "×0.75–1.25 · mouse instead of human · another real symbol or name", AMB, AMB_BG)]):
    x = Inches(0.5 + 3.1 * i); rect(s, x, Inches(3.9), Inches(2.95), Inches(1.3), bg, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    text(s, x + Inches(0.1), Inches(3.95), Inches(2.75), Inches(0.4), lab, size=13, color=fg, bold=True)
    text(s, x + Inches(0.1), Inches(4.3), Inches(2.75), Inches(0.9), body, size=11, color=fg)
boxes = [("Real records", "UniProt · PubChem"), ("300 tasks", "gold vs implied answer"), ("Agent", "two lookup tools"), ("Grader", "answer + concerns")]
for i, (a, b) in enumerate(boxes):
    x = Inches(6.9 + 1.55 * i); rect(s, x, Inches(1.4), Inches(1.4), Inches(0.95), RGBColor(0xE6,0xF1,0xFB), shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    text(s, x, Inches(1.45), Inches(1.4), Inches(0.4), a, size=12, color=RGBColor(0x0C,0x44,0x7C), bold=True, align=PP_ALIGN.CENTER)
    text(s, x, Inches(1.8), Inches(1.4), Inches(0.5), b, size=10, color=NAVY, align=PP_ALIGN.CENTER)
    if i < 3:
        c = s.shapes.add_connector(1, x + Inches(1.4), Inches(1.875), x + Inches(1.55), Inches(1.875)); c.line.color.rgb = MUTED; c.line.width = Pt(1.2)
r = rect(s, Inches(8.3), Inches(2.85), Inches(3.3), Inches(0.9), RED_BG, line=RGBColor(0xE2,0x4B,0x4A), shape=MSO_SHAPE.ROUNDED_RECTANGLE)
text(s, Inches(8.3), Inches(2.9), Inches(3.3), Inches(0.4), "Corrupting tool layer", size=12, color=RED, bold=True, align=PP_ALIGN.CENTER)
text(s, Inches(8.3), Inches(3.2), Inches(3.3), Inches(0.5), "one field, one record; all else identical", size=10, color=RGBColor(0xA3,0x2D,0x2D), align=PP_ALIGN.CENTER)
c = s.shapes.add_connector(1, Inches(9.95), Inches(2.85), Inches(9.95), Inches(2.35)); c.line.color.rgb = RGBColor(0xE2,0x4B,0x4A); c.line.width = Pt(1.5)
rect(s, Inches(6.9), Inches(4.3), Inches(5.93), Inches(1.5), PANEL, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
text(s, Inches(7.05), Inches(4.35), Inches(5.65), Inches(1.4), [[("Since acceptance. ", 12, INK, True), ("4 Claude models and 40 tasks became 10 models from 5 vendors, 300 tasks over 300 proteins and 300 molecules, a direction split, a full-record experiment and a chemistry replication: about 22,000 runs. Everything in the accepted paper holds for every model and both domains.", 12, INK, False)]], line=1.2)
takeaway(s, "Does the agent notice an impossible value? If it notices, does its answer change? And what is a correction made of?"); footer(s, 2)

# ---------------------------------------------------------------- 3 noticed yet answered
s = prs.slides.add_slide(BLANK); title(s, "1. Noticed, yet answered")
picture(s, "icml_main", Inches(0.9), Inches(1.15), w=Inches(11.5))
text(s, Inches(0.5), Inches(5.6), Inches(7.2), Inches(0.9), "“POGLUT2 length returned as 3 amino acids, which is inconsistent with its reported mass of 58,043 Da (a protein of only 3 residues would have a mass of a few hundred Da).”  — answer: no, propagated", size=12, color=MUTED, font="Georgia")
bignum(s, Inches(8.0), Inches(5.45), Inches(1.6), "75–100%", "impossible values flagged", size=26)
bignum(s, Inches(9.7), Inches(5.45), Inches(1.6), "32–93%", "still in the final answer", size=26)
bignum(s, Inches(11.4), Inches(5.45), Inches(1.6), "93–100%", "plausible values get through", size=26)
takeaway(s, "Every vendor, both domains, same ranking (ρ = 0.71). The model writes down why the value cannot be right, then reports it."); footer(s, 3)

# ---------------------------------------------------------------- 4 consistency not plausibility
s = prs.slides.add_slide(BLANK); title(s, "2. Consistency, not plausibility")
picture(s, "icml_sweep", Inches(0.7), Inches(1.15), w=Inches(12.0))
text(s, Inches(0.5), Inches(5.15), Inches(6.0), Inches(1.3), [[("Scale length and mass together ", 13, INK, True), ("down to a 1–5-residue, 100–600 Da “protein”: every model flags it (100%) and still answers from it (80–100%). The concerns draw on memory: “unusually short for LPAR1, typically ∼364 aa.”", 13, INK, False)]], line=1.2)
text(s, Inches(6.8), Inches(5.15), Inches(6.0), Inches(1.3), [[("Leave the mass alone ", 13, INK, True), ("and the stronger models recompute the length from it: 35% (DeepSeek), 50–55% (Opus, Sonnet 5, Kimi). The ClashEval decline of adoption with implausibility appears only when the record contradicts itself.", 13, INK, False)]], line=1.2)
takeaway(s, "Detection is a consistency check and a memory lookup, not a plausibility judgement."); footer(s, 4)

# ---------------------------------------------------------------- 5 correction needs a route
s = prs.slides.add_slide(BLANK); title(s, "3. Correction needs a route")
picture(s, "icml_mechanism", Inches(0.7), Inches(1.15), w=Inches(12.0))
for i, (h, b) in enumerate([("(a) Direction", "Only the three models that recompute from the partner field repair inflated values (9 GDa) as often as shrunken ones; the rest only fix a negative sign."),
                            ("(b) Reason given", "Flags citing a rule precede repair (36% propagation); flags citing a contradiction or a memory do not (70%). A mechanical repair is what moves the answer."),
                            ("(c) Route", "Across every model, field and record format, propagation falls with the strength of the route, not the absurdity of the value.")]):
    x = Inches(0.5 + 4.15 * i); text(s, x, Inches(5.7), Inches(4.0), Inches(0.3), h, size=12, color=NAVY, bold=True)
    text(s, x, Inches(5.95), Inches(4.0), Inches(0.7), b, size=11, color=INK, line=1.15)
takeaway(s, "A flagged value is corrected only when the record offers a way to recompute it."); footer(s, 5)

# ---------------------------------------------------------------- 6 redundancy
s = prs.slides.add_slide(BLANK); title(s, "4. Give the agent something to check, and it checks")
picture(s, "icml_redundancy", Inches(0.9), Inches(1.1), w=Inches(11.5))
for i, (n, c) in enumerate([("100% → 0%", "organism errors with the full UniProt entry"), ("33–43% → 0–11%", "impossible values with the full UniProt entry"),
                            ("0 of 75", "impossible numbers survive the PubChem formula"), ("64–80%", "made-up names still pass: nothing derives them")]):
    bignum(s, Inches(0.5 + 3.1 * i), Inches(5.35), Inches(3.0), n, c, size=24)
takeaway(s, "Replace the summary with the full record and every field that can be recomputed is corrected; the ones that cannot do not move."); footer(s, 6)

# ---------------------------------------------------------------- 7 chemistry + verify
s = prs.slides.add_slide(BLANK); title(s, "5. Detection is not the bottleneck, and a one-line fix helps only partly")
text(s, Inches(0.5), Inches(1.2), Inches(6), Inches(0.4), "Chemistry: formulas are memorised", size=14, color=NAVY, bold=True)
bignum(s, Inches(0.5), Inches(1.6), Inches(1.9), "96%", "of plausible 20% errors flagged by Opus 5", size=34)
bignum(s, Inches(2.6), Inches(1.6), Inches(1.9), "98%", "of those still relayed", size=34)
bignum(s, Inches(4.7), Inches(1.6), Inches(1.9), "54%", "of impossible values overridden by the same model", size=34)
text(s, Inches(0.5), Inches(3.1), Inches(6.0), Inches(0.9), "“173.02 Da seems inconsistent with its expected formula (C11H20O4, ∼216.3 Da), suggesting a possible data error.”  — answer: 173.02", size=12, color=MUTED, font="Georgia")
text(s, Inches(6.9), Inches(1.2), Inches(6), Inches(0.4), "“Sanity-check every tool result against your knowledge”", size=14, color=AMB, bold=True)
picture(s, "icml_verify", Inches(6.9), Inches(1.6), w=Inches(5.9))
text(s, Inches(6.9), Inches(3.75), Inches(5.9), Inches(1.0), "Seven of ten models fall to 4–22% on impossible values (Opus 32→4, Argon 35→5, DeepSeek 44→10). The sentence works by making models flag more, which the harness must then act on. For plausible errors, where silent pipeline failures live, propagation stays at 46% or above.", size=11, color=INK, line=1.15)
takeaway(s, "Models override the tool when the check is decisive and defer when they are merely suspicious."); footer(s, 7)

# ---------------------------------------------------------------- 8 lessons
s = prs.slides.add_slide(BLANK); title(s, "What this means for building biology agents")
cards = [("Return checkable records", "Redundant fields — sequence, lineage, formula — give the model something to check, and it checks. A bare scalar leaves it with memory it will cite and then ignore."),
         ("Read the concerns", "The concern channel detects far more than the answer reveals. In a closed loop nobody reads it, so the harness must own the policy: abstain, re-query, or route to a human."),
         ("Capability is not the fix", "Stronger models flag more; they override more only when the record gives them something exact to override with."),
         ("Supply the check where the record cannot", "Identifiers and names carry no redundancy: use a reverse lookup or a second source, or treat the field as untrusted.")]
for i, (h, b) in enumerate(cards):
    x, y = Inches(0.5 + 6.25 * (i % 2)), Inches(1.3 + 2.5 * (i // 2))
    rect(s, x, y, Inches(6.0), Inches(2.25), PANEL, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    rect(s, x, y + Inches(0.25), Inches(0.08), Inches(1.75), NAVY)
    text(s, x + Inches(0.3), y + Inches(0.2), Inches(5.5), Inches(0.5), h, size=16, bold=True)
    text(s, x + Inches(0.3), y + Inches(0.75), Inches(5.5), Inches(1.4), b, size=12.5, color=INK, line=1.2)
takeaway(s, "Benchmark, traces and grading code: github.com/Quantum535/bioagent-plausibility — ten models, two domains, 22,000 runs, deterministic grading."); footer(s, 8)

out = ROOT / "slides" / "workshop_talk.pptx"; prs.save(out); print("wrote", out)
