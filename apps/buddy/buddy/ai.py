"""LLM integration for Buddy - supports Ollama (local) and Claude (API)."""

import re
from .config import SYSTEM_PROMPT

# Try Ollama first (free, local)
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Fallback to Claude
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class BuddyAI:
    """Handles conversation with LLM (Ollama or Claude)."""

    def __init__(self, provider: str = "ollama", model: str = "mistral"):
        self.provider = provider
        self.model = model
        self.conversation_history: list[dict] = []
        self.known_person: str | None = None
        self.language: str = "en"  # Can be "en" or "ar"

        if provider == "ollama":
            if not OLLAMA_AVAILABLE:
                raise RuntimeError("Ollama not installed. Run: pip install ollama")
            print(f"Using Ollama with model: {model}")
            print("Make sure Ollama is running: ollama serve")
        elif provider == "claude":
            if not ANTHROPIC_AVAILABLE:
                raise RuntimeError("Anthropic not installed. Run: pip install anthropic")
            from .config import ANTHROPIC_API_KEY, CLAUDE_MODEL
            self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
            self.model = CLAUDE_MODEL
            print(f"Using Claude with model: {self.model}")

    def set_language(self, lang: str):
        """Set response language (en or ar)."""
        self.language = lang
        print(f"[AI] Language set to: {lang}")

    def set_context(self, person_name: str | None = None):
        """Update context about current situation."""
        self.known_person = person_name

    def chat(self, user_message: str, context: dict | None = None, lang: str = "en") -> tuple[str, list[str]]:
        """
        Send a message and get a response.

        Returns:
            Tuple of (response_text, list_of_actions)
        """
        # Set language for this request
        self.language = lang
        print(f"[BUDDY] Chat called with lang={lang}, message={user_message[:30]}...")
        print(f"[BUDDY] Current provider: {self.provider}, model: {self.model}")
        # Build context string
        context_parts = []
        if context:
            if context.get("detected_face"):
                name = context["detected_face"]
                if name == "unknown":
                    context_parts.append("You see someone you don't recognize.")
                else:
                    context_parts.append(f"You recognize {name}!")
            if context.get("no_face"):
                context_parts.append("You don't see anyone in front of you.")
            if context.get("language"):
                context_parts.append(context["language"])

        # Add context to message if present
        full_message = user_message
        if context_parts:
            full_message = f"[Instructions: {' '.join(context_parts)}]\n\nUser: {user_message}"

        # Build pending history WITHOUT committing yet — if the LLM call fails,
        # we don't want a dangling user turn that breaks subsequent calls.
        pending = self.conversation_history + [{"role": "user", "content": full_message}]
        if len(pending) > 20:
            pending = pending[-20:]
        saved_history = self.conversation_history
        self.conversation_history = pending

        try:
            if self.provider == "ollama":
                response_text = self._chat_ollama()
            else:
                response_text = self._chat_claude()
        except Exception as e:
            # Roll back history so the conversation isn't corrupted.
            self.conversation_history = saved_history
            err_type = type(e).__name__
            print(f"[AI] {self.provider} chat failed: {err_type}: {e}")
            if self.language == "ar":
                msg = f"عذراً، صار خطأ بالاتصال ({err_type}). جرب مرة لو سمحت. [ACTION:droop_antennas]"
            else:
                msg = f"Sorry — couldn't reach the {self.provider} backend ({err_type}). Try again. [ACTION:droop_antennas]"
            return self._clean_response(msg), self._parse_actions(msg)

        # Only commit on success.
        self.conversation_history.append({"role": "assistant", "content": response_text})
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

        actions = self._parse_actions(response_text)
        clean_text = self._clean_response(response_text, user_message=user_message)
        return clean_text, actions

    def _chat_ollama(self) -> str:
        """Chat using Ollama (local). Universal bilingual system prompt.
        num_predict cap prevents runaway local-LLM replies from saturating TTS."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self.conversation_history)
        response = ollama.chat(
            model=self.model,
            messages=messages,
            options={"num_predict": 250},
        )
        return response["message"]["content"]

    def _chat_claude(self) -> str:
        """Chat using Claude API. Capped at 180 tokens — Buddy is supposed to be
        snappy. Anything longer = slow reply + heavy TTS bill."""
        import time as _t
        t0 = _t.time()
        response = self.client.messages.create(
            model=self.model,
            max_tokens=180,
            system=SYSTEM_PROMPT,
            messages=self.conversation_history,
        )
        out = response.content[0].text
        print(f"[AI] Claude {_t.time()-t0:.2f}s  in={len(self.conversation_history)} turns  out={len(out)} chars")
        return out

    def _parse_actions(self, text: str) -> list[str]:
        """Extract [ACTION:name] tags from response."""
        pattern = r'\[ACTION:(\w+)\]'
        return re.findall(pattern, text)

    # Broad regex — Claude may write [see RESOURCES], [See Resources], [RESOURCES],
    # [الموارد], [انظر RESOURCES], [see resources list], etc.
    _RESOURCES_TOKEN_RE = re.compile(
        r"\[\s*(?:see|انظر|راجع|انظري)?\s*(?:RESOURCES?|resources?|الموارد|مصادر)[^\]]*\]",
        re.IGNORECASE,
    )
    # Real verified hand-off lines (numbers from RESOURCES.md — Iraq ambulance + Jiyan Erbil)
    _HANDOFF_AR = (
        "لو الموضوع كبير وتحس روحك بخطر، الرجاء اتصل بالإسعاف على ١٢٢ هسه، "
        "أو تواصل مع مؤسسة جيان في أربيل على الرقم ٠٦٦ ٢٦٤ ٧٩٧٩، يقدمون دعم مجاني."
    )
    _HANDOFF_EN = (
        "If this is bigger than us, please call ambulance 122 right now, "
        "or reach Jiyan Foundation in Erbil at 066 264 7979 — free trauma support."
    )
    # Crisis trigger phrases — if user message contains ANY of these AND Claude's reply
    # didn't include the hand-off token, we force-append it. Belt and suspenders.
    _CRISIS_PATTERNS = [
        r"\bkill myself\b", r"\bend it\b", r"\bsuicid", r"\bhurt myself\b",
        r"\bcut myself\b", r"\bwant to die\b", r"\bdon'?t want to (live|be here)",
        r"\bno reason to live\b", r"\bgive up\b",
        r"اقتل نفسي", r"انتحار", r"اريد اموت", r"أريد أن أموت", r"ما عاد اتحمل",
        r"ما عدت أتحمل", r"تعبت من الحياة", r"ما عندي رغبة", r"اذي نفسي",
        r"أذي نفسي", r"أؤذي نفسي", r"ما لي خاطر اعيش",
    ]
    _CRISIS_RE = re.compile("|".join(_CRISIS_PATTERNS), re.IGNORECASE)

    def _clean_response(self, text: str, user_message: str = "") -> str:
        """Strip meta-tags and inject real resources before TTS / display.

        Safety net: if the user's message contains crisis keywords AND Claude's reply
        doesn't already include the hand-off token, we prepend the hand-off so the
        user always sees real human resources — never just a warm reply alone.
        """
        # Strip leaked instruction tags Claude sometimes echoes from the prompt
        text = re.sub(r"\[Instructions?:[^\]]*\]\s*", "", text, flags=re.IGNORECASE)

        is_arabic = bool(re.search(r"[؀-ۿ]", text))
        handoff = self._HANDOFF_AR if is_arabic else self._HANDOFF_EN

        had_token = bool(self._RESOURCES_TOKEN_RE.search(text))
        text = self._RESOURCES_TOKEN_RE.sub(handoff, text)

        # Force-append hand-off if user was in crisis and Claude forgot the token
        if user_message and self._CRISIS_RE.search(user_message) and not had_token:
            print(f"[SAFETY] crisis phrase detected in user msg — force-appending hand-off")
            text = text.rstrip() + "\n\n" + handoff
        pattern = r'\[ACTION:\w+\]'
        return re.sub(pattern, '', text).strip()

    def reset_conversation(self):
        """Clear conversation history."""
        self.conversation_history = []
        self.known_person = None


# Singleton instance
_ai_instance: BuddyAI | None = None


def get_ai(provider: str = "ollama", model: str = "mistral") -> BuddyAI:
    """Get the AI instance."""
    global _ai_instance
    if _ai_instance is None:
        _ai_instance = BuddyAI(provider=provider, model=model)
    return _ai_instance
