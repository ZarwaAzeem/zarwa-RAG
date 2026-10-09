"""Turns retrieved resume chunks into an answer.

With Anthropic credentials the answer is written by Claude, grounded in the
retrieved chunks. Without them (or if the call fails) the service falls back to
an extractive answer built directly from the best-matching chunks, so the chat
always works.
"""
import logging
import re

import anthropic

from . import config
from .acquisition import Chunk

log = logging.getLogger("rag.generator")

FIRST_NAME = config.PERSON_NAME.split()[0]

SYSTEM_PROMPT = f"""You are the assistant on {config.PERSON_NAME}'s personal site. Recruiters, \
collaborators and other visitors chat with you to learn about {FIRST_NAME}.

Each visitor message arrives with excerpts retrieved from {FIRST_NAME}'s resume. Those excerpts \
are your only source of facts about {FIRST_NAME}: visitors may act on what you say, so anything \
you state has to be traceable to them. When the excerpts don't cover a question, say the resume \
doesn't mention it and point the visitor to the contact details if they are in the excerpts.

Speak about {FIRST_NAME} in the third person, by name rather than with gendered pronouns, in a \
warm and professional voice. Visitors read on a phone-sized chat screen, so answer in a few \
sentences, using short "- " bullets only for lists such as skills or projects. Plain text only, \
apart from **bold** for names of projects, roles or organisations."""

GREETING = re.compile(r"^\s*(hi|hello|hey|salam|assalam\w*|good (morning|afternoon|evening))\b[\s!.,]*$", re.I)
THANKS = re.compile(r"^\s*(thanks|thank you|thx|great|ok|okay|cool|nice)\b[\s!.,]*$", re.I)

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def small_talk(message: str) -> str | None:
    if GREETING.match(message):
        return (
            f"Hi! I'm {FIRST_NAME}'s assistant. Ask me about {FIRST_NAME}'s skills, projects, "
            "experience, education or how to get in touch."
        )
    if THANKS.match(message):
        return f"Happy to help! Anything else you'd like to know about {FIRST_NAME}?"
    return None


def _body(chunk: Chunk) -> str:
    """The chunk without its section line; entries with bullets get a bold title."""
    title, _, rest = chunk.text.split("\n", 1)[-1].partition("\n")
    if "•" in rest:
        return f"**{title}**\n{rest}"
    return f"{title}\n{rest}".strip()


def extractive_answer(hits: list[tuple[Chunk, float]]) -> str:
    relevant = [(chunk, score) for chunk, score in hits if score >= config.MIN_SCORE]
    if not relevant:
        return (
            f"I couldn't find that in {FIRST_NAME}'s resume. Try asking about skills, projects, "
            "experience, education or contact details."
        )
    # Keep the chunks that are close to the best match, grouped by section.
    best = relevant[0][1]
    kept = [chunk for chunk, score in relevant if score >= best * 0.75][:3]
    sections: dict[str, list[str]] = {}
    for chunk in kept:
        sections.setdefault(chunk.section, []).append(_body(chunk))
    parts = [f"Here's what {FIRST_NAME}'s resume says:"]
    for section, bodies in sections.items():
        # A section with titled entries (projects, jobs) doesn't need its own heading.
        heading = "" if all(body.startswith("**") for body in bodies) else f"**{section}**\n"
        parts.append(heading + "\n\n".join(bodies))
    return "\n\n".join(parts)


def _llm_answer(message: str, history: list[dict], hits: list[tuple[Chunk, float]]) -> str:
    excerpts = "\n\n".join(
        f'<excerpt section="{chunk.section}" source="{chunk.source}">\n{chunk.text}\n</excerpt>'
        for chunk, _ in hits
    )
    # Earlier turns go in as plain conversation; the API needs a user turn first.
    turns = [{"role": turn["role"], "content": turn["content"]} for turn in history]
    while turns and turns[0]["role"] != "user":
        turns.pop(0)
    turns.append(
        {
            "role": "user",
            "content": f"<resume_excerpts>\n{excerpts}\n</resume_excerpts>\n\nVisitor: {message}",
        }
    )
    response = _get_client().beta.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        output_config={"effort": "low"},
        # If the model declines a request, let the API retry it on a fallback model.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=turns,
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("model declined the request")
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    if not text:
        raise RuntimeError("model returned no text")
    return text


def answer(message: str, history: list[dict], hits: list[tuple[Chunk, float]]) -> tuple[str, str]:
    """Return (answer, mode) where mode is "llm" or "extractive"."""
    if config.LLM_ENABLED:
        try:
            return _llm_answer(message, history, hits), "llm"
        except anthropic.AuthenticationError:
            log.error("Anthropic credentials were rejected - using extractive answers")
        except anthropic.RateLimitError:
            log.warning("Anthropic rate limit hit - using an extractive answer")
        except anthropic.APIStatusError as error:
            log.error("Anthropic API error %s: %s", error.status_code, error.message)
        except anthropic.APIConnectionError:
            log.error("Could not reach the Anthropic API - using an extractive answer")
        except RuntimeError as error:
            log.warning("LLM answer unavailable (%s) - using an extractive answer", error)
    return small_talk(message) or extractive_answer(hits), "extractive"
