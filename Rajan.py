# Telegramimport os, json, random
from telegram import Update, Poll
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    PollAnswerHandler,
    ContextTypes
)
from questions import QUESTIONS

BOT_TOKEN = os.environ.get("BOT_TOKEN")
STATE_FILE = "state.json"

# ---------- STATE ----------
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {
        "index": 0,
        "scores": {},
        "chat_id": None,
        "current_correct": None
    }

def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

state = load_state()

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state["chat_id"] = update.effective_chat.id
    save_state()
    await send_question(context)

# ---------- SEND QUESTION ----------
async def send_question(context: ContextTypes.DEFAULT_TYPE):
    idx = state["index"]

    if idx >= len(QUESTIONS):
        text = "🏆 Final Score 🏆\n\n"
        for u, s in state["scores"].items():
            text += f"{u} : {s}\n"

        await context.bot.send_message(state["chat_id"], text)

        state["index"] = 0
        state["scores"] = {}
        state["current_correct"] = None
        save_state()
        return

    q = QUESTIONS[idx]

    options = list(q["options"])
    correct_text = q["options"][q["correct"]]
    random.shuffle(options)
    correct_index = options.index(correct_text)

    state["current_correct"] = correct_index
    save_state()

    await context.bot.send_poll(
        chat_id=state["chat_id"],
        question=q["q"],
        options=options,
        type=Poll.QUIZ,
        correct_option_id=correct_index,
        is_anonymous=False,
        open_period=20
    )

    context.job_queue.run_once(next_question, 20)

# ---------- NEXT QUESTION ----------
async def next_question(context: ContextTypes.DEFAULT_TYPE):
    state["index"] += 1
    save_state()
    await send_question(context)

# ---------- ANSWER ----------
async def poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ans = update.poll_answer
    user = ans.user.first_name
    selected = ans.option_ids[0]

    if user not in state["scores"]:
        state["scores"][user] = 0

    if selected == state["current_correct"]:
        state["scores"][user] += 1

    save_state()

# ---------- MAIN ----------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(PollAnswerHandler(poll_answer))

    print("🤖 Quiz Bot Running on Cloud")
    app.run_polling()

if __name__ == "__main__":
    main()
