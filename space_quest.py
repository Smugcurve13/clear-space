import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from space_core import Chunk, build_ai_prompt, format_bytes, scan_storage, trash_command

MINIMUM_ITEM_SIZE = 100 * 1024 * 1024


class SpaceCleaner(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Clear Space")
        self.geometry("980x700")
        self.minsize(760, 560)
        self.configure(bg="#f7f8fa")
        self.root_path = Path("/")
        self.result = None
        self.configure_styles()
        self.show_welcome()

    def configure_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f7f8fa")
        style.configure("Hero.TLabel", background="#f7f8fa", foreground="#15171a", font=("Helvetica", 30, "bold"))
        style.configure("Heading.TLabel", background="#f7f8fa", foreground="#15171a", font=("Helvetica", 20, "bold"))
        style.configure("Body.TLabel", background="#f7f8fa", foreground="#5e6673", font=("Helvetica", 12))
        style.configure("Muted.TLabel", background="#f7f8fa", foreground="#8b929d", font=("Helvetica", 10))
        style.configure("Primary.TButton", background="#15171a", foreground="#ffffff", font=("Helvetica", 12, "bold"), padding=(16, 11))
        style.map("Primary.TButton", background=[("active", "#30343a")])
        style.configure("Secondary.TButton", font=("Helvetica", 11, "bold"), padding=(12, 8))
        style.configure("TButton", font=("Helvetica", 11), padding=(10, 7))

    def clear(self):
        for child in self.winfo_children():
            child.destroy()

    def show_welcome(self):
        self.clear()
        page = ttk.Frame(self, padding=44)
        page.pack(fill="both", expand=True)
        ttk.Label(page, text="CLEAR SPACE", style="Muted.TLabel").pack(anchor="w", pady=(20, 10))
        ttk.Label(page, text="Find room without\nguessing.", style="Hero.TLabel").pack(anchor="w")
        ttk.Label(
            page,
            text="We will scan every part of this Mac that macOS lets this app read, then turn the results into understandable groups instead of a maze of folders.",
            style="Body.TLabel",
            wraplength=600,
            justify="left",
        ).pack(anchor="w", pady=(18, 28))
        steps = ttk.Frame(page)
        steps.pack(anchor="w", pady=(0, 32))
        for number, text in (("01", "Scan your storage"), ("02", "Start with the biggest category"), ("03", "Review before anything goes to Trash")):
            row = ttk.Frame(steps)
            row.pack(anchor="w", pady=5)
            ttk.Label(row, text=number, style="Muted.TLabel", width=5).pack(side="left")
            ttk.Label(row, text=text, style="Body.TLabel").pack(side="left")
        ttk.Button(page, text="Scan this Mac", style="Primary.TButton", command=self.start_scan).pack(anchor="w")
        ttk.Button(page, text="Choose a folder instead", style="Secondary.TButton", command=self.choose_root).pack(anchor="w", pady=(10, 0))
        ttk.Label(page, text="No files are changed during a scan. You decide whether to reveal, keep, or move any item to Trash.", style="Muted.TLabel").pack(anchor="w", pady=(20, 0))

    def choose_root(self):
        chosen = filedialog.askdirectory(initialdir=self.root_path)
        if chosen:
            self.root_path = Path(chosen)
            self.start_scan()

    def start_scan(self):
        self.clear()
        page = ttk.Frame(self, padding=44)
        page.pack(fill="both", expand=True)
        ttk.Label(page, text="Scanning storage", style="Hero.TLabel").pack(anchor="w", pady=(90, 12))
        self.scan_status = ttk.Label(page, text=f"Looking through {self.root_path}. Inaccessible locations are skipped.", style="Body.TLabel", wraplength=650)
        self.scan_status.pack(anchor="w")
        self.progress = ttk.Progressbar(page, mode="indeterminate", length=440)
        self.progress.pack(anchor="w", pady=(28, 10))
        self.progress.start(12)
        ttk.Label(page, text="This can take a while on a full drive. Keep the app open.", style="Muted.TLabel").pack(anchor="w")
        threading.Thread(target=self.scan_worker, daemon=True).start()

    def scan_worker(self):
        try:
            result = scan_storage(self.root_path, MINIMUM_ITEM_SIZE, 100)
            free = shutil.disk_usage(self.root_path).free
            self.after(0, lambda: self.show_overview(result, free))
        except OSError as error:
            self.after(0, lambda: self.show_error(error))

    def show_error(self, error):
        self.clear()
        messagebox.showerror("Clear Space", f"This location could not be scanned.\n\n{error}")
        self.show_welcome()

    def show_overview(self, result, free):
        self.result = result
        self.clear()
        page = ttk.Frame(self, padding=(36, 28))
        page.pack(fill="both", expand=True)
        header = ttk.Frame(page)
        header.pack(fill="x")
        ttk.Label(header, text="Clear Space", style="Heading.TLabel").pack(side="left")
        ttk.Button(header, text="Scan another location", style="Secondary.TButton", command=self.choose_root).pack(side="right")
        ttk.Label(page, text=f"{format_bytes(free)} free on {self.root_path}", style="Body.TLabel").pack(anchor="w", pady=(5, 28))

        ordered = sorted(result.category_sizes.items(), key=lambda item: item[1], reverse=True)
        if not ordered:
            ttk.Label(page, text="Nothing readable was found here.", style="Hero.TLabel").pack(anchor="w", pady=(60, 10))
            ttk.Label(page, text="Choose another folder or grant the app permission to the storage you want to inspect.", style="Body.TLabel").pack(anchor="w")
            return

        largest_name, largest_size = ordered[0]
        focus = ttk.Frame(page, padding=22)
        focus.pack(fill="x", pady=(0, 24))
        ttk.Label(focus, text="START HERE", style="Muted.TLabel").pack(anchor="w")
        ttk.Label(focus, text=f"{largest_name} is using {format_bytes(largest_size)}", style="Heading.TLabel").pack(anchor="w", pady=(5, 3))
        ttk.Label(focus, text="We will show the largest readable chunks first, clearly marked as files or folders.", style="Body.TLabel").pack(anchor="w", pady=(0, 14))
        ttk.Button(focus, text=f"Review {largest_name}", style="Primary.TButton", command=lambda: self.show_category(largest_name)).pack(anchor="w")

        ttk.Label(page, text="Storage groups", style="Heading.TLabel").pack(anchor="w", pady=(0, 10))
        grid = ttk.Frame(page)
        grid.pack(fill="both", expand=True)
        for index, (category, size) in enumerate(ordered):
            card = tk.Frame(grid, bg="#ffffff", highlightbackground="#e3e6eb", highlightthickness=1, padx=18, pady=16)
            card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=(0, 10) if index % 2 == 0 else (10, 0), pady=7)
            tk.Label(card, text=category, bg="#ffffff", fg="#15171a", font=("Helvetica", 14, "bold"), anchor="w").pack(fill="x")
            tk.Label(card, text=format_bytes(size), bg="#ffffff", fg="#5e6673", font=("Helvetica", 11), anchor="w").pack(fill="x", pady=(4, 12))
            ttk.Button(card, text="Review", command=lambda name=category: self.show_category(name)).pack(anchor="w")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

    def show_category(self, category):
        assert self.result is not None
        self.clear()
        page = ttk.Frame(self, padding=(36, 28))
        page.pack(fill="both", expand=True)
        header = ttk.Frame(page)
        header.pack(fill="x")
        ttk.Button(header, text="← All storage", style="Secondary.TButton", command=lambda: self.show_overview(self.result, shutil.disk_usage(self.root_path).free)).pack(side="left")
        ttk.Label(header, text=category, style="Heading.TLabel").pack(side="left", padx=14)
        size = self.result.category_sizes[category]
        ttk.Label(page, text=f"{format_bytes(size)} total. Largest readable chunks are first.", style="Body.TLabel").pack(anchor="w", pady=(14, 18))

        holder = ttk.Frame(page)
        holder.pack(fill="both", expand=True)
        canvas = tk.Canvas(holder, bg="#f7f8fa", highlightthickness=0)
        scrollbar = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview)
        content = ttk.Frame(canvas)
        content.bind("<Configure>", lambda _: canvas.configure(scrollregion=canvas.bbox("all")))
        window = canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window, width=event.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        chunks = [chunk for chunk in self.result.chunks if chunk.category == category]
        if not chunks:
            ttk.Label(content, text="This category is spread across smaller items. No individual file or folder exceeded 100 MB.", style="Body.TLabel", padding=(0, 24)).pack(anchor="w")
            return
        for chunk in chunks:
            self.add_chunk(content, chunk)

    def add_chunk(self, parent, chunk: Chunk):
        card = tk.Frame(parent, bg="#ffffff", highlightbackground="#e3e6eb", highlightthickness=1, padx=18, pady=15)
        card.pack(fill="x", pady=6)
        top = tk.Frame(card, bg="#ffffff")
        top.pack(fill="x")
        tk.Label(top, text=chunk.kind.upper(), bg="#ffffff", fg="#77808c", font=("Helvetica", 9, "bold")).pack(side="left")
        tk.Label(top, text=format_bytes(chunk.size), bg="#ffffff", fg="#15171a", font=("Helvetica", 12, "bold")).pack(side="right")
        tk.Label(card, text=chunk.path.name, bg="#ffffff", fg="#15171a", font=("Helvetica", 14, "bold"), anchor="w", wraplength=750).pack(fill="x", pady=(5, 1))
        tk.Label(card, text=chunk.guidance, bg="#ffffff", fg="#5e6673", font=("Helvetica", 10), anchor="w", wraplength=750, justify="left").pack(fill="x", pady=(0, 4))
        tk.Label(card, text=str(chunk.path.parent), bg="#ffffff", fg="#8b929d", font=("Helvetica", 9), anchor="w", wraplength=750).pack(fill="x", pady=(0, 12))
        actions = tk.Frame(card, bg="#ffffff")
        actions.pack(fill="x")
        ttk.Button(actions, text="Reveal", command=lambda: self.reveal(chunk.path)).pack(side="left")
        ttk.Button(actions, text="Ask any AI", command=lambda: self.show_prompt(chunk)).pack(side="left", padx=8)
        ttk.Button(actions, text="Move to Trash…", command=lambda: self.confirm_trash(chunk)).pack(side="left")

    def reveal(self, path):
        try:
            command = ["open", "-R", str(path)] if sys.platform == "darwin" else ["xdg-open", str(path.parent)]
            subprocess.run(command, check=False)
        except OSError as error:
            messagebox.showerror("Clear Space", f"Could not reveal this item.\n\n{error}")

    def show_prompt(self, chunk):
        popup = tk.Toplevel(self)
        popup.title("Ask any AI")
        popup.geometry("720x520")
        popup.configure(bg="#f7f8fa")
        frame = ttk.Frame(popup, padding=22)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Ask any AI", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(frame, text="This prompt contains only metadata. Paste it into ChatGPT, Claude, or another assistant.", style="Body.TLabel", wraplength=620).pack(anchor="w", pady=(5, 12))
        text = tk.Text(frame, wrap="word", bg="#ffffff", fg="#15171a", relief="solid", borderwidth=1, padx=12, pady=12)
        text.insert("1.0", build_ai_prompt(chunk))
        text.configure(state="disabled")
        text.pack(fill="both", expand=True)
        ttk.Button(frame, text="Copy prompt", style="Primary.TButton", command=lambda: self.copy_prompt(popup, text)).pack(anchor="e", pady=(12, 0))

    def copy_prompt(self, popup, text):
        prompt = text.get("1.0", "end-1c")
        popup.clipboard_clear()
        popup.clipboard_append(prompt)
        popup.update()
        messagebox.showinfo("Ask any AI", "Prompt copied. No file content was included.", parent=popup)

    def confirm_trash(self, chunk):
        answer = messagebox.askyesno(
            "Move to Trash?",
            f"You are about to move this {chunk.kind.lower()} to Trash:\n\n{chunk.path.name}\n{format_bytes(chunk.size)}\n\nCheck it first if you are unsure. This app will not permanently delete it.",
            icon="warning",
        )
        if not answer:
            return
        try:
            subprocess.run(trash_command(sys.platform, chunk.path), check=True)
        except (OSError, subprocess.CalledProcessError) as error:
            messagebox.showerror("Clear Space", f"Could not move this item to Trash.\n\n{error}")
            return
        messagebox.showinfo("Moved to Trash", f"{chunk.path.name} was moved to Trash. The storage view will now refresh.")
        self.start_scan()


if __name__ == "__main__":
    SpaceCleaner().mainloop()
