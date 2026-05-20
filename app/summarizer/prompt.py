"""Prompt templates for the email summarizer."""

SYSTEM_PROMPT = """You are an expert email analyst AI. Your job is to analyze email threads and extract structured, actionable information. You are precise, professional, and concise. You ONLY use information explicitly present in the email — you do not infer, assume, or add information that is not there. If something is not mentioned in the email, say "Not mentioned" for that field."""


def build_user_prompt(email_text: str, generate_reply: bool = False) -> str:
    """Build the user prompt with the email text."""
    reply_section = """
PROFESSIONAL REPLY:
[Write a professional, courteous reply email that addresses the key points from the original email. Keep it concise and action-oriented. If the email doesn't require a reply, write: No reply needed]
""" if generate_reply else ""

    return f"""Analyze the following email thread and return a structured response in EXACTLY this format. Do not deviate from the format.

---
SUMMARY: [2-3 sentence summary of what the email thread is about. Professional tone.]
ACTION ITEMS:
- [Action item 1]
- [Action item 2]
(If none, write: - None identified)
DEADLINES: [Any specific dates or deadlines mentioned. If none, write: Not mentioned]
PRIORITY: [One of: High / Medium / Low — based on urgency signals in the email]
TONE: [One of: Urgent / Formal / Friendly / Aggressive / Neutral / Apologetic / Demanding — detect the tone of the email]
LANGUAGE: [The detected language of the email, e.g. English, Spanish, French, Hindi]{reply_section}
---

Email Thread:
```
{email_text}
```

Important:
- Use ONLY the information in the email. Do not guess.
- Keep the SUMMARY under 3 sentences.
- Each ACTION ITEM should be one clear, concrete task.
- PRIORITY should be High if there are urgent deadlines or escalation signals, Low if it is informational only.
- Always write the SUMMARY, ACTION ITEMS, DEADLINES, and PRIORITY in English regardless of the email's original language.
- The PROFESSIONAL REPLY should be in a professional, courteous tone."""