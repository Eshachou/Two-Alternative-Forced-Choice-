"""
participant_screen.py  --  what the PARTICIPANT sees (display only).

This file draws things. It never decides anything: no thermode, no staircase,
no answers. The experiment calls its five commands at the right moments:

    show_cross()          fixation cross  (waiting, and between trials)
    show_ready()          "Get ready"
    show_interval("A")    the big letter A  (or "B")
    show_prompt()         the question with A and B
    clear()               blank screen

It must NEVER show a temperature, or which interval holds the stimulus.

Test it alone (no hardware needed):   python participant_screen.py
Then drag the window to the second monitor and press  F  for fullscreen
(Esc leaves fullscreen).
"""

import tkinter as tk


# --- Colours and wording (this screen has its own plain look on purpose) ------
BG = "black"
FG = "white"
FONT = "Helvetica"

READY_TEXT = "Get ready!"
PROMPT_TEXT = "Which interval had the stimulus?"    # PLACEHOLDER wording: confirm with PI

CROSS_SIZE = 0.10        # half the length of one arm, as a fraction of the window's smaller side
CROSS_THICKNESS = 10     # line thickness in pixels


class ParticipantScreen:
    """A second window that shows one thing at a time.

    How it works: we remember WHAT to show (self.mode) and redraw the whole canvas
    from that every time. Resizing or going fullscreen therefore just works, because
    everything is placed relative to the window's current size.
    """

    def __init__(self, root):
        # Toplevel = an extra window that belongs to the same program as root
        self.window = tk.Toplevel(root)
        self.window.title("Participant screen")
        self.window.configure(bg=BG)
        self.window.geometry("800x500+100+100")      # width x height + x + y position

        self.canvas = tk.Canvas(self.window, bg=BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.mode = "cross"       # what is on screen right now
        self.letter = ""          # used only when mode == "interval"
        self.fullscreen = False

        # <Configure> fires whenever the window changes size -> redraw to fit
        self.canvas.bind("<Configure>", lambda event: self._redraw())
        self.window.bind("<f>", lambda event: self._set_fullscreen(not self.fullscreen))
        self.window.bind("<Escape>", lambda event: self._set_fullscreen(False))

    # ---- the five commands the experiment uses ---------------------------------
    def show_cross(self):
        self.mode = "cross"
        self._redraw()

    def show_ready(self):
        self.mode = "ready"
        self._redraw()

    def show_interval(self, name):
        """name = "A" or "B"."""
        self.mode = "interval"
        self.letter = name
        self._redraw()

    def show_prompt(self):
        self.mode = "prompt"
        self._redraw()

    def clear(self):
        self.mode = "blank"
        self._redraw()

    # ---- fullscreen ---------------------------------------------------------------
    def _set_fullscreen(self, on):
        self.fullscreen = on
        self.window.attributes("-fullscreen", on)
        self.window.config(cursor="none" if on else "")   # hide the mouse arrow
        self.window.focus_force()                          # keep keyboard focus here

    # ---- drawing ------------------------------------------------------------------
    def _redraw(self):
        c = self.canvas
        c.delete("all")                                    # wipe, then draw again
        w, h = c.winfo_width(), c.winfo_height()
        cx, cy = w / 2, h / 2                              # centre of the screen

        if self.mode == "cross":
            arm = min(w, h) * CROSS_SIZE                   # half the length of one arm
            c.create_line(cx - arm, cy, cx + arm, cy, fill=FG, width=CROSS_THICKNESS)
            c.create_line(cx, cy - arm, cx, cy + arm, fill=FG, width=CROSS_THICKNESS)

        elif self.mode == "ready":
            c.create_text(cx, cy, text=READY_TEXT, fill=FG,
                          font=(FONT, -int(h * 0.10)))     # negative size = pixels

        elif self.mode == "interval":
            c.create_text(cx, cy, text=self.letter, fill=FG,
                          font=(FONT, -int(h * 0.40), "bold"))

        elif self.mode == "prompt":
            c.create_text(cx, h * 0.28, text=PROMPT_TEXT, fill=FG,
                          font=(FONT, -int(h * 0.075)), width=w * 0.9)   # width = wrap long text
            c.create_text(w * 0.30, h * 0.62, text="A", fill=FG,
                          font=(FONT, -int(h * 0.20), "bold"))
            c.create_text(w * 0.70, h * 0.62, text="B", fill=FG,
                          font=(FONT, -int(h * 0.20), "bold"))
        # mode == "blank": draw nothing


# =============================== DEMO =============================================
# Runs only when you start THIS file directly, never when another file imports it.
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Demo controls")
    root.geometry("260x330+950+100")

    screen = ParticipantScreen(root)
    screen.window.protocol("WM_DELETE_WINDOW", root.destroy)   # closing it ends the demo

    def demo_trial():
        """Cross -> Get ready -> A -> B -> question -> cross.
        Delays ADD UP: each number is the wait after the previous step.
        root.after(ms, function) schedules a call without freezing the window.
        """
        steps = [
            (0,    screen.show_cross),
            (1500, screen.show_ready),
            (1500, lambda: screen.show_interval("A")),
            (2000, screen.clear),
            (500,  lambda: screen.show_interval("B")),
            (2000, screen.clear),
            (500,  screen.show_prompt),
            (3000, screen.show_cross),
        ]
        t = 0
        for delay, action in steps:
            t += delay
            root.after(t, action)

    tk.Label(root, text="Participant screen demo", font=(("Helvetica"), 12, "bold")).pack(pady=8)
    for text, action in [
        ("Cross",          screen.show_cross),
        ("Get ready",      screen.show_ready),
        ("Interval A",     lambda: screen.show_interval("A")),
        ("Interval B",     lambda: screen.show_interval("B")),
        ("Question",       screen.show_prompt),
        ("Blank",          screen.clear),
        ("Run demo trial", demo_trial),
    ]:
        tk.Button(root, text=text, command=action).pack(fill="x", padx=14, pady=2)

    tk.Label(root, text="Drag the black window to the\nsecond monitor, click it, press F.",
             font=("Helvetica", 9)).pack(pady=8)

    root.mainloop()