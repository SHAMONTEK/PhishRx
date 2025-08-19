import customtkinter as ctk
import random

PHISHING_FACTS = [
    "Phishing is the most reported cybercrime according to the FBI.",
    "Emails with 'urgent' or 'act now' are often phishing traps.",
    "Real companies will never ask for passwords via email.",
    "Hover over links before clicking — check where they really lead.",
    "Phishing costs businesses billions annually in fraud and breaches."
]

QUIZ_QUESTIONS = [
    {
        "q": "What’s a sign of a phishing email?",
        "a": ["Misspellings", "Generic greetings", "Too-good offers", "All of the above"],
        "c": 3
    },
    {
        "q": "Which protocol is secure for browsing?",
        "a": ["http", "ftp", "https", "smtp"],
        "c": 2
    }
]

def launch_learn_mode(parent):
    frame = ctk.CTkFrame(parent)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    ctk.CTkLabel(frame, text="🎓 Learn Mode", font=("Helvetica", 18, "bold"), text_color="#0099ff").pack(pady=8)
    fact_box = ctk.CTkTextbox(frame, height=100, wrap="word")
    fact_box.pack(pady=4)
    fact = random.choice(PHISHING_FACTS)
    fact_box.insert("end", "📘 Did you know?\n")
    fact_box.insert("end", f"{fact}\n\n")
    fact_box.configure(state="disabled")

    def load_quiz():
        question = random.choice(QUIZ_QUESTIONS)
        quiz_frame = ctk.CTkFrame(frame)
        quiz_frame.pack(pady=10)

        ctk.CTkLabel(quiz_frame, text=question["q"], font=("Helvetica", 14)).pack()
        for idx, option in enumerate(question["a"]):
            ctk.CTkButton(
                quiz_frame,
                text=option,
                command=lambda i=idx: ctk.CTkLabel(
                    quiz_frame,
                    text="✅ Correct!" if i == question["c"] else "❌ Try again.",
                    text_color="#00ffcc" if i == question["c"] else "#ff3333"
                ).pack()
            ).pack(pady=2)

    ctk.CTkButton(frame, text="🧠 Take Quiz", command=load_quiz).pack(pady=5)
    return frame
