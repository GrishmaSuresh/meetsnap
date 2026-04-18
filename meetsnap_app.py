import tkinter as tk
import subprocess
import threading
import os
import sys
import time
from tkinter import filedialog, messagebox
from step9_chat.chat_with_meeting import MeetingChatBot



PYTHON_PATH = r"D:\meetsnap\.venv\Scripts\python.exe"
LIVE_CAPTIONS_SCRIPT = r"D:\meetsnap\step3_live_feed\live_captions.py"
SUMMARY_SCRIPT = r"D:\meetsnap\step5_summary\summarize_transcript.py"
SUMMARY_FILE = r"D:\meetsnap\step5_summary\final_summary.txt"

ACTIONS_SCRIPT = r"D:\meetsnap\step6_actions\extract_actions.py"
ACTIONS_FILE = r"D:\meetsnap\step6_actions\actions.txt"

CALENDAR_SCRIPT = r"D:\meetsnap\step7_calendar\extract_calendar_event.py"
CALENDAR_FILE = r"D:\meetsnap\step7_calendar\meeting_event.ics"

EMAIL_SCRIPT = r"D:\meetsnap\step8_email\generate_email.py"
EMAIL_FILE = r"D:\meetsnap\step8_email\email_draft.txt"

CHAT_SCRIPT = r"D:\meetsnap\step9_chat\chat_with_meeting.py"


class MeetSnapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MeetSnap")
        self.root.geometry("520x420")
        self.root.resizable(False, False)

        tk.Label(
            root,
            text="MeetSnap",
            font=("Segoe UI", 22, "bold")
        ).pack(pady=2)

        tk.Label(
            root,
            text="Live captions & smart meeting summaries",
            font=("Segoe UI", 11)
        ).pack(pady=5)

        self.status = tk.Label(
            root,
            text="Status: Ready",
            font=("Segoe UI", 11),
            fg="green"
        )
        self.status.pack(pady=5)

        self.create_buttons()

    def create_buttons(self):

        tk.Button(
            self.root,
            text="▶ Start Meeting",
            font=("Segoe UI", 13, "bold"),
            width=30,
            command=self.start_meeting
        ).pack(pady=2)

        tk.Button(
            self.root,
            text="⏹ End Meeting",
            font=("Segoe UI", 13, "bold"),
            width=30,
            command=self.end_meeting
        ).pack(pady=2)

        tk.Button(
            self.root,
            text="📄 View Summary",
            font=("Segoe UI", 12),
            width=30,
            command=self.view_summary
        ).pack(pady=2)

        tk.Button(
            self.root,
            text="📋 View Action Items",
            font=("Segoe UI", 12),
            width=30,
            command=self.view_actions
        ).pack(pady=2)

        tk.Button(
            self.root,
            text="📅 Export Calendar",
            font=("Segoe UI", 12),
            width=30,
            command=self.export_calendar
        ).pack(pady=2)

        tk.Button(
            self.root,
            text="📧 Generate Email",
            font=("Segoe UI", 12),
            width=30,
            command=self.generate_email
        ).pack(pady=2)

        tk.Button(
            self.root,
            text="💬 Chat With Meeting",
            font=("Segoe UI", 12),
            width=30,
            command=self.open_chat
        ).pack(pady=6)

        tk.Button(
            self.root,
            text="❌ Exit",
            font=("Segoe UI", 11),
            width=30,
            command=self.root.quit
        ).pack(pady=20)

    def start_meeting(self):
        self.status.config(text="Status: Meeting in progress...", fg="blue")

        subprocess.Popen([
            PYTHON_PATH,
            LIVE_CAPTIONS_SCRIPT
        ])

    def end_meeting(self):
        self.status.config(text="Status: Processing meeting...", fg="orange")

        def process():
            try:
                subprocess.run([PYTHON_PATH, SUMMARY_SCRIPT], check=True)
                subprocess.run([PYTHON_PATH, ACTIONS_SCRIPT], check=True)

                self.status.config(
                    text="Status: Summary & actions ready",
                    fg="green"
                )
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Processing failed:\n{e}")
                self.status.config(text="Status: Failed", fg="red")

        threading.Thread(target=process, daemon=True).start()

    def start_live_captions(self):
        self.status.config(text="Status: Live captions running...", fg="blue")

        subprocess.Popen([
            PYTHON_PATH,
            LIVE_CAPTIONS_SCRIPT
        ])

    def generate_summary(self):
        def run():
            self.status.config(text="Status: Summarizing...", fg="orange")

            subprocess.run([
                PYTHON_PATH,
                SUMMARY_SCRIPT
            ])

            self.status.config(text="Status: Summary ready", fg="green")

        threading.Thread(target=run, daemon=True).start()

    def generate_actions(self):
        def run():
            self.status.config(text="Status: Extracting actions...", fg="orange")

            subprocess.run([
                PYTHON_PATH,
                ACTIONS_SCRIPT
            ])

            self.status.config(text="Status: Action items ready", fg="green")

        threading.Thread(target=run, daemon=True).start()

    def view_actions(self):
        self.status.config(text="Status: Viewing action items", fg="blue")

        if not os.path.exists(ACTIONS_FILE):
            messagebox.showerror("Error", "No action items found")
            return

        with open(ACTIONS_FILE, "r", encoding="utf-8") as f:
            text = f.read()

        win = tk.Toplevel(self.root)
        win.title("Action Items & Decisions")
        win.geometry("750x550")

        box = tk.Text(win, wrap="word", font=("Segoe UI", 11))
        box.insert("1.0", text)
        box.config(state="disabled")
        box.pack(expand=True, fill="both", padx=10, pady=10)

        def download_actions():
            save_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt")],
                title="Save Action Items",
                initialfile="meeting_action_items.txt"
            )

            if save_path:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(text)

                messagebox.showinfo("Download Complete", "Action items saved successfully!")

        btn = tk.Button(
            win,
            text="⬇ Download Action Items",
            font=("Segoe UI", 11),
            width=25,
            command=download_actions
        )
        btn.pack(pady=10)

    def view_summary(self):
        if not os.path.exists(SUMMARY_FILE):
            self.status.config(text="Status: No summary found", fg="red")
            return

        with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
            text = f.read()

        win = tk.Toplevel(self.root)
        win.title("Meeting Summary")
        win.geometry("750x550")

        # ---- Text Box ----
        box = tk.Text(
            win,
            wrap="word",
            font=("Segoe UI", 11)
        )
        box.insert("1.0", text)
        box.config(state="disabled")
        box.pack(expand=True, fill="both", padx=10, pady=10)

        # ---- Download Button ----
        def download_summary():
            save_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt")],
                title="Save Meeting Summary",
                initialfile="meeting_summary.txt"
            )

            if save_path:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(text)

                messagebox.showinfo(
                    "Download Complete",
                    "Summary saved successfully!"
                )

        btn = tk.Button(
            win,
            text="⬇️ Download Summary",
            font=("Segoe UI", 11),
            width=25,
            command=download_summary
        )
        btn.pack(pady=10)

    def export_calendar(self):
        self.status.config(text="Status: Exporting calendar...", fg="orange")

        def run():
            try:
                result = subprocess.run(
                    [PYTHON_PATH, CALENDAR_SCRIPT],
                    capture_output=True,
                    text=True
                )

                # 🔴 Show Python errors if any
                if result.returncode != 0:
                    messagebox.showerror(
                        "Calendar Error",
                        f"Script failed:\n{result.stderr}"
                    )
                    self.status.config(text="Status: Calendar failed", fg="red")
                    return

                if not os.path.exists(CALENDAR_FILE):
                    messagebox.showerror(
                        "Error",
                        "Calendar file was not created."
                    )
                    self.status.config(text="Status: Calendar failed", fg="red")
                    return

                # ✅ Validate ICS content (important)
                with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
                    content = f.read()

                if "BEGIN:VEVENT" not in content or "DTSTART" not in content:
                    messagebox.showerror(
                        "Invalid Calendar File",
                        "Generated .ics file is invalid.\nCheck event extraction."
                    )
                    self.status.config(text="Status: Invalid calendar", fg="red")
                    return

                self.status.config(
                    text="Status: Calendar ready (opening file)",
                    fg="green"
                )

                # ✅ Open automatically
                try:
                    os.startfile(CALENDAR_FILE)
                except Exception as e:
                    print("Open error:", e)

                messagebox.showinfo(
                    "Calendar Exported",
                    "Calendar file created and opened.\nIf Outlook fails, send me the .ics file."
                )

            except Exception as e:
                messagebox.showerror("Error", str(e))
                self.status.config(text="Status: Error occurred", fg="red")

        threading.Thread(target=run, daemon=True).start()
    def generate_email(self):
        self.status.config(text="Status: Generating email...", fg="orange")

        def run():
            subprocess.run([PYTHON_PATH, EMAIL_SCRIPT])
            self.status.config(
                text="Status: Email draft opened",
                fg="green"
            )

        threading.Thread(target=run, daemon=True).start()

    def open_chat(self):

        try:
            bot = MeetingChatBot()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        win = tk.Toplevel(self.root)
        win.title("Chat With Meeting")
        win.geometry("750x550")

        chat_box = tk.Text(win, wrap="word", font=("Segoe UI", 11))
        chat_box.pack(expand=True, fill="both", padx=10, pady=10)
        chat_box.config(state="disabled")


        entry = tk.Entry(win, font=("Segoe UI", 11), fg="gray")
        entry.pack(fill="x", padx=10, pady=5)

        PLACEHOLDER = "Ask your question..."

        entry.insert(0, PLACEHOLDER)

        def clear_placeholder(event):
            if entry.get() == PLACEHOLDER:
                entry.delete(0, "end")
                entry.config(fg="black")

        def add_placeholder(event):
            if not entry.get():
                entry.insert(0, PLACEHOLDER)
                entry.config(fg="gray")

        entry.bind("<FocusIn>", clear_placeholder)
        entry.bind("<FocusOut>", add_placeholder)

        def add_message(sender, text):
            chat_box.config(state="normal")

            chat_box.insert("end", f"\n{sender}: {text}\n")

            chat_box.config(state="disabled")
            chat_box.see("end")

        def update_ai_message(answer):
            chat_box.config(state="normal")

            # remove last "Thinking..." line
            chat_box.delete("end-3l", "end-1l")

            chat_box.insert("end", f"🤖 AI: {answer}\n")

            chat_box.config(state="disabled")
            chat_box.see("end")

        def send():
            question = entry.get().strip()

            if not question or question == PLACEHOLDER:
                return

            add_message("🧑 You", question)

            entry.delete(0, "end")

            # show typing indicator
            add_message("🤖 AI", "Thinking...")

            def run_ai():
                answer = bot.ask(question)

                # update UI safely from main thread
                win.after(0, lambda: update_ai_message(answer))

            threading.Thread(target=run_ai, daemon=True).start()

        send_btn = tk.Button(
            win,
            text="Send",
            font=("Segoe UI", 11),
            command=send
        )

        send_btn.pack(pady=5)

        entry.bind("<Return>", lambda e: send())


if __name__ == "__main__":
    root = tk.Tk()
    app = MeetSnapApp(root)
    root.mainloop()
