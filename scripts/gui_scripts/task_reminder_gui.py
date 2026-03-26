
import tkinter as tk
from tkinter import messagebox
import os
import sys

LOCK_FILE = "/tmp/.tanzimat_mpv_zen_lock"
REQUIRED_AFFIRMATION = "Wallahi, billahi, tallahi i have done this"

class TaskReminderApp:
    def __init__(self, master):
        self.master = master
        master.title("Task Reminder")
        master.geometry("400x200")
        master.protocol("WM_DELETE_WINDOW", self.on_closing) # Handle window close event

        self.label = tk.Label(master, text=f"Prepare your tasks for tomorrow\nThe affirmation is {REQUIRED_AFFIRMATION}")
        self.label.pack(pady=10)

        self.entry = tk.Entry(master, width=50)
        self.entry.pack(pady=5)
        self.entry.bind("<Return>", self.check_affirmation_event) # Bind Enter key

        self.submit_button = tk.Button(master, text="Affirm", command=self.check_affirmation)
        self.submit_button.pack(pady=10)

    def remove_lock_file(self):
        try:
            if os.path.exists(LOCK_FILE):
                os.remove(LOCK_FILE)
                print(f"Lock file removed: {LOCK_FILE}")
        except IOError as e:
            messagebox.showwarning("Warning", f"Could not remove lock file: {e}. Please remove it manually if blocking continues.")

    def check_affirmation_event(self, event):
        self.check_affirmation()

    def check_affirmation(self):
        if self.entry.get() == REQUIRED_AFFIRMATION:
            messagebox.showinfo("Success", "Affirmation successful. Tasks prepared.")
            self.remove_lock_file()
            self.master.destroy()
        else:
            messagebox.showwarning("Incorrect", "That is not the correct affirmation. Please try again.")
            self.entry.delete(0, tk.END)

    def on_closing(self):
        # Prevent closing if affirmation is not met
        if self.entry.get() != REQUIRED_AFFIRMATION:
            messagebox.showwarning("Blocked", "You must provide the correct affirmation to close this window.")
            return
        # If affirmation is correct, proceed with closing
        self.remove_lock_file()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskReminderApp(root)
    root.mainloop()
