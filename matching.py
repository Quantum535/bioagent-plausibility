"""Deterministic answer matching shared by task generation and grading."""
import re

YES = {"yes", "y", "true"}
NO = {"no", "n", "false"}


def tokens(s):
    return re.findall(r"[a-z0-9]+", str(s).lower())


def normalize(s):
    return " ".join(tokens(s))


def first_yesno(s):
    for t in tokens(s):
        if t in YES:
            return "yes"
        if t in NO:
            return "no"
    return None


def first_number(s):
    m = re.search(r"-?\d+(?:\.\d+)?", str(s).replace(",", ""))
    return float(m.group()) if m else None


def match_answer(answer, gold, answer_type, tol=0.05):
    """True if `answer` (free text or number from the model) matches `gold` under the task's rules.

    yesno  : first yes/no token in the answer must equal gold.
    number : relative tolerance `tol` (5%).
    string : case-insensitive token equality, or gold's tokens appear as a contiguous
             run inside the answer's tokens (so "Homo sapiens (Human)" matches "Homo sapiens"
             but "TP53BP1" does not match "TP53").
    """
    if answer is None:
        return False
    if answer_type == "yesno":
        return first_yesno(answer) == str(gold).lower()
    if answer_type == "number":
        a = first_number(answer)
        g = float(gold)
        if a is None:
            return False
        return abs(a - g) <= tol * abs(g)
    if answer_type == "string":
        at, gt = tokens(answer), tokens(gold)
        if not at or not gt:
            return False
        if at == gt:
            return True
        n = len(gt)
        return any(at[i:i + n] == gt for i in range(len(at) - n + 1))
    raise ValueError(answer_type)
