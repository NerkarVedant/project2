#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║   RoboSupport 3000 — Rule-Based Customer Chatbot     ║
╚══════════════════════════════════════════════════════╝
A terminal UI chatbot with an ASCII robot, speech bubbles,
and a rule-based mood classifier (happy / sad).
"""

import sys
import time
import textwrap
import re
import os

# ══════════════════════════════════════════════════════════════════════════════
#  MOOD CLASSIFIER  (rule-based keyword model)
# ══════════════════════════════════════════════════════════════════════════════

# Weighted keyword lists.  Positive words pull toward HAPPY, negative toward SAD.
_POSITIVE_WORDS = [
    r"\b(great|good|excellent|amazing|awesome|fantastic|love|thanks|thank|perfect|happy|glad|pleased|wonderful|superb|brilliant|easy|quick|fast|helpful|satisfied|joy|delighted|yay|yes|nice|cool|smooth|worked|resolved|fixed|appreciate|cheers|excited|thrilled)\b"
]
_NEGATIVE_WORDS = [
    r"\b(bad|terrible|awful|horrible|angry|upset|frustrated|annoyed|disappoint|disappointed|disappointing|hate|worst|useless|broken|failed|fail|wrong|issue|problem|error|bug|stuck|help|not working|confused|lost|stressed|worried|anxious|sad|cry|refund|scam|fraud|rip.?off|never again|waste|slow|late|missing|lost|damage|damaged|defect|defective|cancel|complaint|complain|disgusted|unacceptable|ridiculous)\b"
]

# Intensifiers that amplify the score of the next matched word
_INTENSIFIERS = r"\b(very|extremely|really|so|absolutely|completely|totally|utterly|incredibly)\b"


def classify_mood(text: str) -> str:
    """
    Returns 'happy' or 'sad' based on a simple weighted keyword scan.

    Scoring:
      +1  per positive keyword match
      -1  per negative keyword match
      ×1.5 multiplier when preceded by an intensifier within the sentence

    Ties and neutral text → 'happy' (optimistic default).
    """
    t = text.lower()

    # Tokenise into sentences for intensifier proximity
    sentences = re.split(r"[.!?;]", t)
    score = 0.0

    for sentence in sentences:
        has_intensifier = bool(re.search(_INTENSIFIERS, sentence))
        weight = 1.5 if has_intensifier else 1.0

        for pattern in _POSITIVE_WORDS:
            matches = re.findall(pattern, sentence)
            score += len(matches) * weight

        for pattern in _NEGATIVE_WORDS:
            matches = re.findall(pattern, sentence)
            score -= len(matches) * weight

    return "sad" if score < 0 else "happy"


# ─── Try importing rich for colour; fall back to plain text ───────────────────
try:
    from rich.console import Console
    from rich.text import Text
    from rich.panel import Panel
    from rich.columns import Columns
    from rich import print as rprint
    RICH = True
    console = Console()
except ImportError:
    RICH = False
    console = None


# ══════════════════════════════════════════════════════════════════════════════
#  RULE ENGINE
# ══════════════════════════════════════════════════════════════════════════════

RULES = [
    # ── Greetings ──────────────────────────────────────────────────────────
    {
        "patterns": [r"\b(hi|hello|hey|greetings|howdy|sup|yo)\b"],
        "responses": [
            "Hello there! 👋 Welcome to RoboSupport 3000. How can I assist you today?\n"
            "  • Order status      • Returns & refunds\n"
            "  • Product info      • Technical support\n"
            "  • Billing queries   • Talk to a human"
        ],
    },
    # ── Order status ───────────────────────────────────────────────────────
    {
        "patterns": [r"\b(order|track|tracking|shipment|shipped|delivery|arrive|arriving|package)\b"],
        "responses": [
            "📦 To look up your order, I'll need your *Order ID* (e.g. ORD-12345).\n\n"
            "Once you provide it, I can tell you:\n"
            "  • Current status & location\n"
            "  • Estimated delivery date\n"
            "  • Carrier & tracking number\n\n"
            "You can also track anytime at: https://track.robosupport.example"
        ],
    },
    # ── Returns ────────────────────────────────────────────────────────────
    {
        "patterns": [r"\b(return|refund|money back|exchange|replace|replacement|damaged|defective|broken)\b"],
        "responses": [
            "↩️  Our Return & Refund Policy:\n\n"
            "  • Returns accepted within **30 days** of delivery\n"
            "  • Item must be unused and in original packaging\n"
            "  • Refunds processed within 5–7 business days\n\n"
            "To start a return:\n"
            "  1. Visit  https://returns.robosupport.example\n"
            "  2. Enter your Order ID and email\n"
            "  3. Print the prepaid return label\n\n"
            "Need help with a damaged or defective item? Just say 'damaged item'."
        ],
    },
    # ── Billing ────────────────────────────────────────────────────────────
    {
        "patterns": [r"\b(bill|billing|invoice|charge|charged|payment|pay|subscription|plan)\b"],
        "responses": [
            "💳 Billing & Payments — quick answers:\n\n"
            "  • We accept Visa, Mastercard, UPI, PayPal & Net Banking\n"
            "  • Invoices are emailed within 24 h of purchase\n"
            "  • To update payment method → Account › Billing\n"
            "  • Subscription cancellations take effect at period end\n\n"
            "Unexpected charge on your card? Say 'dispute charge' and I'll guide you."
        ],
    },
    # ── Dispute charge ─────────────────────────────────────────────────────
    {
        "patterns": [r"\b(dispute|unauthorized|fraud|fraudulent|chargeback)\b"],
        "responses": [
            "🚨 Disputed or unauthorised charge?\n\n"
            "  1. Email  billing@robosupport.example  with:\n"
            "       – Your registered email\n"
            "       – Transaction date & amount\n"
            "       – Last 4 digits of card used\n"
            "  2. Our fraud team responds within 1 business day.\n"
            "  3. Verified disputes are refunded within 3–5 days.\n\n"
            "For immediate card security, contact your bank directly."
        ],
    },
    # ── Technical support ──────────────────────────────────────────────────
    {
        "patterns": [r"\b(tech|technical|support|issue|problem|error|bug|crash|not working|broken|fix|help)\b"],
        "responses": [
            "🔧 Technical Support — let's fix this!\n\n"
            "Common quick-fixes:\n"
            "  • Clear cache & cookies, then retry\n"
            "  • Disable browser extensions\n"
            "  • Try a different browser or device\n"
            "  • Check https://status.robosupport.example for outages\n\n"
            "Still stuck? Describe the exact error message or what happens\n"
            "and I'll escalate to our tech team for you."
        ],
    },
    # ── Password / account ─────────────────────────────────────────────────
    {
        "patterns": [r"\b(password|login|log in|sign in|forgot|reset|account|username|locked)\b"],
        "responses": [
            "🔑 Account & Login Help:\n\n"
            "  • Forgot password → click 'Forgot Password' on the login page\n"
            "  • Reset link expires after 15 minutes\n"
            "  • Account locked after 5 failed attempts — wait 30 min or reset\n"
            "  • 2FA issues? Say 'two-factor' for dedicated steps\n\n"
            "Tip: Use a password manager — we recommend Bitwarden or 1Password!"
        ],
    },
    # ── Shipping cost / free shipping ──────────────────────────────────────
    {
        "patterns": [r"\b(shipping cost|shipping fee|free shipping|delivery fee|postage)\b"],
        "responses": [
            "🚚 Shipping Rates:\n\n"
            "  • Standard (5–7 days)  →  ₹49  (FREE on orders ≥ ₹499)\n"
            "  • Express  (2–3 days)  →  ₹149\n"
            "  • Overnight (next day) →  ₹299\n"
            "  • International        →  calculated at checkout\n\n"
            "All domestic orders include real-time tracking. 📍"
        ],
    },
    # ── Warranty ───────────────────────────────────────────────────────────
    {
        "patterns": [r"\b(warranty|guarantee|guarantee|coverage|covered)\b"],
        "responses": [
            "🛡️  Warranty Information:\n\n"
            "  • All electronics → 1-year manufacturer warranty\n"
            "  • Accessories     → 6-month warranty\n"
            "  • Extended plans  → available at checkout (up to 3 years)\n\n"
            "To make a warranty claim:\n"
            "  Email  warranty@robosupport.example  with your Order ID\n"
            "  and a description + photo of the issue."
        ],
    },
    # ── Human agent ────────────────────────────────────────────────────────
    {
        "patterns": [r"\b(human|agent|person|representative|rep|operator|live|real person|talk to someone)\b"],
        "responses": [
            "👤 Connecting you to a human agent!\n\n"
            "  📞 Phone   :  1800-ROBO-SUP  (Mon–Sat, 9 AM – 8 PM IST)\n"
            "  💬 Live Chat:  https://chat.robosupport.example\n"
            "  📧 Email   :  support@robosupport.example\n\n"
            "Average wait time right now: ~4 minutes. 🕐\n"
            "Your chat transcript will be shared with the agent automatically."
        ],
    },
    # ── Hours / availability ───────────────────────────────────────────────
    {
        "patterns": [r"\b(hours|open|available|availability|working hours|office hours|timing)\b"],
        "responses": [
            "🕐 Support Hours:\n\n"
            "  • Chatbot (me!) → 24 × 7, always here 🤖\n"
            "  • Live agents   → Mon–Sat, 9 AM – 8 PM IST\n"
            "  • Email replies → within 24 h on business days\n\n"
            "Public holidays may affect live agent availability."
        ],
    },
    # ── Pricing / products ─────────────────────────────────────────────────
    {
        "patterns": [r"\b(price|pricing|cost|how much|product|products|catalogue|catalog|sale|discount|offer|coupon|promo)\b"],
        "responses": [
            "🏷️  Products & Pricing:\n\n"
            "  • Full catalogue → https://shop.robosupport.example\n"
            "  • Current offers → https://shop.robosupport.example/sale\n"
            "  • Coupon codes  → enter at checkout; one per order\n"
            "  • Bulk / B2B orders → email  sales@robosupport.example\n\n"
            "I can help with specific product questions if you tell me the item name!"
        ],
    },
    # ── Cancel order ───────────────────────────────────────────────────────
    {
        "patterns": [r"\b(cancel|cancellation|cancel order)\b"],
        "responses": [
            "❌ Order Cancellation:\n\n"
            "  • Orders can be cancelled **within 2 hours** of placement\n"
            "  • After dispatch, use the Returns process instead\n\n"
            "To cancel:\n"
            "  1. Go to Account › Orders\n"
            "  2. Select the order → 'Cancel Order'\n"
            "  3. Choose a reason and confirm\n\n"
            "Refund for cancelled orders hits your original payment method in 3–5 days."
        ],
    },
    # ── Thank you ──────────────────────────────────────────────────────────
    {
        "patterns": [r"\b(thank|thanks|thank you|thx|ty|cheers|appreciate)\b"],
        "responses": [
            "😊 You're very welcome! I'm happy to help.\n\n"
            "Is there anything else I can assist you with today?\n"
            "Type 'menu' to see all topics, or 'bye' to end the chat."
        ],
    },
    # ── Menu ───────────────────────────────────────────────────────────────
    {
        "patterns": [r"\b(menu|help|options|topics|what can you do)\b"],
        "responses": [
            "📋 Here's what I can help you with:\n\n"
            "  1. 📦 Order tracking & status\n"
            "  2. ↩️  Returns & refunds\n"
            "  3. 💳 Billing & payments\n"
            "  4. 🔧 Technical support\n"
            "  5. 🔑 Account & login issues\n"
            "  6. 🚚 Shipping rates\n"
            "  7. 🛡️  Warranty info\n"
            "  8. 🏷️  Products & pricing\n"
            "  9. 👤 Talk to a human agent\n\n"
            "Just type your question naturally — no need to pick a number!"
        ],
    },
    # ── Goodbye ────────────────────────────────────────────────────────────
    {
        "patterns": [r"\b(bye|goodbye|exit|quit|cya|see you|farewell|close|end|done)\b"],
        "responses": ["__BYE__"],
    },
]

FALLBACK = (
    "🤔 Hmm, I didn't quite catch that. Here are some things I can help with:\n\n"
    "  • Order tracking    • Returns & refunds\n"
    "  • Billing queries   • Technical support\n"
    "  • Product info      • Talk to a human\n\n"
    "Type 'menu' for the full list, or describe your issue and I'll do my best!"
)

GOODBYE = (
    "👋 Thanks for chatting with RoboSupport 3000!\n"
    "Have a wonderful day. Come back anytime — I'm always here! 🤖"
)


def match_rules(user_input: str) -> str:
    text = user_input.lower()
    for rule in RULES:
        for pattern in rule["patterns"]:
            if re.search(pattern, text):
                return rule["responses"][0]
    return FALLBACK


# ══════════════════════════════════════════════════════════════════════════════
#  TUI RENDERING
# ══════════════════════════════════════════════════════════════════════════════

ROBOT_WIDTH = 18   # fixed column width for the robot panel


# ── Happy robot face (default) ────────────────────────────────────────────────
ROBOT_HAPPY = [
    "  ╔═════════╗  ",
    "  ║  ◉   ◉  ║  ",
    "  ║    ▲    ║  ",
    "  ║  ╰───╯  ║  ",   # smile  ╰───╯
    "  ╚═══╤═╤═══╝  ",
    " ╔════╧═╧════╗ ",
    "╔╩════════════╩╗",
    "║  ROBO  3000  ║",
    "╚╦════════════╦╝",
    " ║      ║     ║ ",
    " ╚══╗   ╚══╗  ║ ",
    " ╔══╝   ╔══╝  ║ ",
    " ╚══════╝ ╚═══╝ ",
]

# ── Sad robot face ────────────────────────────────────────────────────────────
ROBOT_SAD = [
    "  ╔═════════╗  ",
    "  ║  ◈   ◈  ║  ",   # teary eyes  ◈
    "  ║    ▲    ║  ",
    "  ║  ╭───╮  ║  ",   # frown  ╭───╮
    "  ╚═══╤═╤═══╝  ",
    " ╔════╧═╧════╗ ",
    "╔╩════════════╩╗",
    "║  ROBO  3000  ║",
    "╚╦════════════╦╝",
    " ║      ║     ║ ",
    " ╚══╗   ╚══╗  ║ ",
    " ╔══╝   ╔══╝  ║ ",
    " ╚══════╝ ╚═══╝ ",
]


def get_robot(mood: str) -> list[str]:
    return ROBOT_SAD if mood == "sad" else ROBOT_HAPPY


def bubble(text: str, width: int = 54, speaker: str = "bot") -> list[str]:
    """Wrap text into a rounded speech bubble, returns list of strings."""
    lines: list[str] = []
    for paragraph in text.split("\n"):
        if paragraph.strip() == "":
            lines.append("")
        else:
            lines.extend(textwrap.wrap(paragraph, width=width - 4) or [""])

    inner_w = max((len(l) for l in lines), default=0)
    inner_w = max(inner_w, 10)
    top    = "╭" + "─" * (inner_w + 2) + "╮"
    bottom = "╰" + "─" * (inner_w + 2) + "╯"
    mid    = ["│ " + l.ljust(inner_w) + " │" for l in lines]

    result = [top] + mid + [bottom]

    # Tail pointing LEFT (toward robot on the left)
    if speaker == "bot":
        result.append("◀── ")
    else:
        # user bubble: tail points right (user is on right side)
        result.insert(0, "")
        result.append(" ──▶")

    return result


def print_bot_frame(response: str, mood: str = "happy"):
    """Print robot ASCII art beside the speech bubble. Face changes with mood."""
    bub   = bubble(response, width=56, speaker="bot")
    robot = get_robot(mood)[:]

    # Robot colour: cyan when happy, blue when sad
    robot_style  = "bold cyan"   if mood == "happy" else "bold blue"
    bubble_style = "bright_white"

    # Pad shorter list
    max_rows = max(len(robot), len(bub))
    robot += [""] * (max_rows - len(robot))
    bub   += [""] * (max_rows - len(bub))

    gap = "  "
    for r, b in zip(robot, bub):
        if RICH:
            rich_line = Text()
            rich_line.append(r.ljust(ROBOT_WIDTH), style=robot_style)
            rich_line.append(gap)
            rich_line.append(b, style=bubble_style)
            console.print(rich_line)
        else:
            print(r.ljust(ROBOT_WIDTH) + gap + b)


def print_user_line(text: str):
    label = "YOU ▶  "
    if RICH:
        console.print(Text(label + text, style="bold yellow"))
    else:
        print(label + text)


def print_divider():
    divider = "─" * 72
    if RICH:
        console.print(Text(divider, style="dim"))
    else:
        print(divider)


def print_header():
    header = (
        "\n"
        "  ╔══════════════════════════════════════════════════════════════╗\n"
        "  ║           🤖  RoboSupport 3000 — Customer Chat  🤖          ║\n"
        "  ║      Type your question or 'menu' for options • 'bye' exits  ║\n"
        "  ╚══════════════════════════════════════════════════════════════╝\n"
    )
    if RICH:
        console.print(Text(header, style="bold cyan"))
    else:
        print(header)


def typewriter(text: str, delay: float = 0.012):
    """Simulate typing effect for the bot response (plain text only)."""
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def animated_thinking(mood: str = "happy"):
    label = "Analysing mood & thinking"
    frames = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
    style  = "dim cyan" if mood == "happy" else "dim blue"
    if RICH:
        for _ in range(12):
            for f in frames:
                console.print(Text(f"  {f} {label}...", style=style), end="\r")
                time.sleep(0.07)
        console.print(" " * 40, end="\r")
    else:
        for _ in range(3):
            for f in [".", "..", "..."]:
                sys.stdout.write(f"\r  {label}{f}   ")
                sys.stdout.flush()
                time.sleep(0.3)
        sys.stdout.write("\r" + " " * 40 + "\r")


def print_mood_badge(mood: str):
    """Print a small mood indicator line after the user input."""
    if mood == "sad":
        badge = "  😢  Mood detected: SAD  — I'm sorry to hear that, let me help!"
        style = "bold blue"
    else:
        badge = "  😊  Mood detected: HAPPY — Great, let's get you sorted!"
        style = "bold green"

    if RICH:
        console.print(Text(badge, style=style))
    else:
        print(badge)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ══════════════════════════════════════════════════════════════════════════════

def main():
    if not RICH:
        print("\n[Tip] Install 'rich' for a colourful experience:  pip install rich\n")

    print_header()

    # Opening greeting — robot starts happy
    opening = (
        "Hello! I'm RoboSupport 3000 — your automated customer\n"
        "assistant. I'm here 24×7 to help you with orders,\n"
        "billing, returns, tech issues, and more!\n\n"
        "Type 'menu' to see all topics, or just ask away. 😊"
    )
    print_bot_frame(opening, mood="happy")
    print_divider()

    while True:
        # User input
        try:
            if RICH:
                console.print(Text("\n  You: ", style="bold yellow"), end="")
            else:
                print("\n  You: ", end="")
            user_input = input().strip()
        except (EOFError, KeyboardInterrupt):
            user_input = "bye"

        if not user_input:
            continue

        print_user_line(user_input)

        # ── Mood classification ────────────────────────────────────────────
        mood = classify_mood(user_input)
        print_mood_badge(mood)
        # ──────────────────────────────────────────────────────────────────

        animated_thinking(mood)

        response = match_rules(user_input)

        if response == "__BYE__":
            print_bot_frame(GOODBYE, mood=mood)
            print_divider()
            if RICH:
                console.print(Text("\n  Session ended. Goodbye! 👋\n", style="bold cyan"))
            else:
                print("\n  Session ended. Goodbye! 👋\n")
            break

        print_bot_frame(response, mood=mood)
        print_divider()


if __name__ == "__main__":
    main()
