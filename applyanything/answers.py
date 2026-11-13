"""Route free-text form prompts and pick from applicant-approved wording."""
import hashlib
import re
import tomllib


_AI = r"(?:not )?(?:an? )?(?:llm|large language model|ai (?:agent|assistant|bot|model|system)|chatbot|bot|robot)\b"
_SCREENING = re.compile(
    rf"\b(?:if you(?: are|'re)|are you) {_AI}"
    r"|\b(?:if you(?: are|'re)|are you) (?:an? )?ai(?=\s*(?:[,.:;?]|or (?:a )?human\b|$))"
    r"|\b(?:if you(?: are|'re)|are you|(?:confirm|prove|verify|certify) (?:that )?you(?: are|'re)) "
    r"(?:(?:a )?(?:real )?human|not (?:a )?(?:robot|bot))\b"
    r"|\b(?:did|have) you (?:use|used) (?:generative )?ai\b[^.!?]*\b"
    r"(?:this (?:job )?(?:application|answer|response|form)|to (?:help )?(?:fill|write|complete|answer|draft|submit))\b"
    r"|\b(?:(?:do not|don't|may not|must not) use|without (?:using|the use of)) (?:generative )?ai\b"
)


def normalize(text):
    return " ".join(text.casefold().replace("’", "'").split()).rstrip(" *")


def route(path, application_id, question, instructions="", max_chars=None):
    """Return a draft, a manual handoff, or a request to use the regular packet."""
    prompt = normalize(question)
    if _SCREENING.search(f"{prompt}\n{normalize(instructions)}"):
        return {"action": "manual", "reason": "Human verification or AI-use instructions"}

    try:
        with path.open("rb") as f:
            entries = tomllib.load(f).get("question", [])
    except FileNotFoundError:
        entries = []

    if not isinstance(entries, list):
        raise ValueError("Use one [[question]] table for each approved prompt")
    approved = {}
    for entry in entries:
        label = entry.get("prompt") if isinstance(entry, dict) else None
        if not isinstance(label, str) or not normalize(label):
            raise ValueError("Each [[question]] needs a nonempty prompt")
        key = normalize(label)
        if key in approved:
            raise ValueError(f"Duplicate approved prompt: {label}")
        variants = entry.get("variants")
        if not isinstance(variants, list) or not variants or any(
            not isinstance(answer, str) or not answer.strip() for answer in variants
        ):
            raise ValueError(f"Expected one or more nonempty variants for: {label}")
        approved[key] = sorted({answer.strip() for answer in variants})

    if prompt not in approved:
        return {"action": "use_packet"}

    variants = approved[prompt]
    if max_chars is not None:
        # Browser maxlength counts UTF-16 code units, including two for astral characters.
        variants = [answer for answer in variants if len(answer.encode("utf-16-le")) // 2 <= max_chars]
    if not variants:
        return {"action": "manual", "reason": "No approved wording fits the character limit"}

    key = f"{application_id}\0{prompt}".encode("utf-8")
    index = int.from_bytes(hashlib.sha256(key).digest(), "big") % len(variants)
    return {"action": "fill", "answer": variants[index]}
