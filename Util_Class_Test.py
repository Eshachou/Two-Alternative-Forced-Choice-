"""
ONE-FILE TEST VERSION .

Top to bottom: theme, logic, widgets, demo, then the window-building functions.
The window only opens at the very bottom, inside main().

Order (top to bottom ) :
    1. Imports
    2. Theme       (colours, font, shared Entry style)
    3. Logic       (parse_total, IntervalPicker: no widgets inside)
    4. Widgets     (Toggle, ActiveSurfaces, DestTemp, TrialSetup,
                    IntervalIndicator, ResponseDecisionPlot)
    5. Demo        (DemoTrialRunner: fake trials, delete when real trials exist)
"""


# 1. IMPORTS

import math
import random
import re
import tkinter as tk

import matplotlib
matplotlib.use("TkAgg")                       # must come BEFORE the matplotlib backend imports below
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg



# 2. THEME  (every colour and font in the program lives here)

Bg          = "#101827"   # window background
Card        = "#1D2A3D"   # each panel sits on this lighter card
InputBg     = "#111B2B"   # inside of the typing boxes
Text        = "#F1F5F9"   # main text (almost white)
SmallLabels = "#9CAEC4"   # small grey-blue labels
Accent      = "#54C7B7"   # teal, used for "you are typing here"
Border      = "#42546B"   # thin outlines

OnColour    = "#00AA00"   # zone active (green)
OffColour   = "#CC3030"   # zone inactive (red)

Font = "Helvetica"

MAX_TRIALS = 200      # PLACEHOLDER upper limit for Total Trials; confirm with the protocol

# Every typing box gets the same look, so we write it once.
# Use it as:  tk.Entry(parent, **EntryStyle)   ("**" unpacks the dict into keyword arguments)
EntryStyle = dict(
    justify="center",
    font=(Font, 11),
    fg=Text,
    bg=InputBg,
    insertbackground=Text,        # the blinking cursor (default is black)
    relief="flat",
    highlightthickness=1,         # reserve a 1px ring = our visible border
    highlightbackground=Border,   # ring colour when NOT selected
    highlightcolor=Accent,        # ring colour when you click inside
)



# 3. LOGIC  

def ParseTotal(text, low=1, high=MAX_TRIALS):
    """Check the Total Trials text. Returns (number, None) if fine, or (None, message) if not.

    re.fullmatch accepts only digits 0-9: no "2.5", no "1e3", no "1_0", no minus sign.
    """
    text = text.strip()
    if text == "":
        return None, "Enter a whole number"
    if not re.fullmatch(r"[0-9]+", text):
        return None, "Whole numbers only"
    value = int(text)
    if not low <= value <= high:
        return None, f"Must be {low} to {high}"
    return value, None


class IntervalPicker:
    """
    Randomly decides which interval (A or B) contains the stimulus, once per trial.

    The experimenter cannot choose: that is the point of randomising. The seed is kept
    so the exact A/B sequence of a run can be reproduced later (and saved in the log).
    """

    def __init__(self, seed=None):
        if seed is None:
            seed = random.SystemRandom().randrange(2**32)
        self.seed = seed
        self.rng = random.Random(seed)    # our own dice; same seed -> same sequence

    def next(self):
        return self.rng.choice(["A", "B"])


# 4. WIDGETS

class Toggle(tk.Canvas):
    """Zone's status indicator: active_color when on (green), deactive_color when off (red).
    Click it to flip the state.
    command = optional function called with the toggle that was clicked."""

    def __init__(self, parent, size=38, active=True,
                 active_color=OnColour, deactive_color=OffColour,
                 command=None, **kwargs):
        kwargs.setdefault("bg", parent.cget("bg"))   # match the card colour
        super().__init__(parent, width=size, height=size,
                         highlightthickness=0, cursor="hand2", **kwargs)
        self.active = active
        self.active_color = active_color
        self.deactive_color = deactive_color
        self.command = command
        self.locked = False
        pad = 4
        self.oval = self.create_oval(
            pad, pad, size - pad, size - pad,
            fill=active_color if active else deactive_color,
            outline="#050505", width=4)
        self.bind("<Button-1>", self._on_click)

    def _on_click(self, event):
        if self.locked:
            return
        self.set(not self.active)   # flip: True <-> False
        if self.command:
            self.command(self)

    def set(self, state):
        self.active = state
        self.itemconfig(self.oval,
                        fill=self.active_color if state else self.deactive_color)


class ActiveSurfaces:
    """Card with five Zone toggles. Read the result with get_active_zones()."""

    def __init__(self, parent, command=None):
        self.frame = tk.Frame(parent, bg=Card, padx=18, pady=9,
                              highlightbackground=Border, highlightthickness=1)

        tk.Label(self.frame, text="Active Surfaces", font=(Font, 13, "bold"),
                 fg=Text, bg=Card).pack(anchor="w", pady=(0, 8))

        row = tk.Frame(self.frame, bg=Card)
        row.pack(fill="x")

        self.toggles = []
        for i in range(5):
            col = tk.Frame(row, bg=Card)
            col.grid(row=0, column=i, padx=7)
            row.grid_columnconfigure(i, weight=1, uniform="zone")

            tk.Label(col, text=f"Zone {i + 1}", font=(Font, 10),
                     fg=SmallLabels, bg=Card).pack(pady=(0, 6))

            toggle = Toggle(col, command=command)
            toggle.pack()
            self.toggles.append(toggle)

    def get_active_zones(self):
        
        return [i + 1 for i, t in enumerate(self.toggles) if t.active]


class DestTemp:
    """
    window       = the parent widget this card is placed in
    title        = name of the protocol phase, e.g. "Stimulus Duration (s)"
    showDuration = True shows the duration box, False leaves it out

    Builds one card: a top line (title + optional duration) and five zone boxes.
    """

    def __init__(self, window, title, showDuration=True):
        # on self because the main file needs to pack it
        self.baseFrame = tk.Frame(
            window, bg=Card,
            padx=18, pady=9,
            highlightbackground=Border,
            highlightthickness=1,
        )

        frame1 = tk.Frame(self.baseFrame, bg=Card)   # top line
        frame2 = tk.Frame(self.baseFrame, bg=Card)   # zone boxes
        frame1.pack(fill="x", pady=(0, 12))
        frame2.pack(fill="x")

        tk.Label(frame1, text=title, font=(Font, 13, "bold"),
                 fg=Text, bg=Card).pack(side="left")

        # Duration: only if this panel wants one
        self.duration = None            
        self.durationInput = None
        if showDuration:
            self.duration = tk.StringVar(value="2.0")  
            tk.Label(frame1, text="Duration (s)", font=(Font, 10),
                     fg=SmallLabels, bg=Card).pack(side="left", padx=(25, 8))
            self.durationInput = tk.Entry(frame1, textvariable=self.duration,
                                          width=7, **EntryStyle)
            self.durationInput.pack(side="left")

        # Five zone values: a list, so we can loop over them
        self.zones = [tk.StringVar(value="") for _ in range(5)]
        self.z1, self.z2, self.z3, self.z4, self.z5 = self.zones

        self.zoneInputs = []            # kept so we can lock/disable them later
        for i, zone_var in enumerate(self.zones):
            zone_frame = tk.Frame(frame2, bg=Card)
            zone_frame.grid(row=0, column=i, padx=7, sticky="ew")

            tk.Label(zone_frame, text=f"ZONE {i + 1}",
                     font=(Font, 9, "bold"), fg=SmallLabels, bg=Card).pack(pady=(0, 6))

            entry = tk.Entry(zone_frame, textvariable=zone_var,
                             width=8, **EntryStyle)
            entry.pack(ipady=4)
            self.zoneInputs.append(entry)

            frame2.grid_columnconfigure(i, weight=1, uniform="zone")


class TrialSetup:
    """Small one-line card: "Total Trials [ 20 ]" where the experimenter types the run length.

    The box starts EMPTY. While typing, the border turns red and a short message appears
    to the right if the text is not a valid whole number (nothing shows when it is fine).
    Each time the text becomes valid, `command(total)` is called, so the graph can resize
    itself without this class knowing the graph exists (decoupling).
    """

    def __init__(self, parent, command=None):
        self.command = command

        self.frame = tk.Frame(parent, bg=Card, padx=12, pady=8,
                              highlightbackground=Border, highlightthickness=1)
        tk.Label(self.frame, text="Total Trials", font=(Font, 11, "bold"),
                 fg=Text, bg=Card).pack(side="left")

        # StringVar on self: if it were a plain local variable Python would delete it
        # when __init__ ends, and the box would go blank.
        self.total = tk.StringVar(value="")
        self.entry = tk.Entry(self.frame, textvariable=self.total, width=6,
                              disabledbackground=InputBg, disabledforeground=SmallLabels,
                              **EntryStyle)
        self.entry.pack(side="left", padx=(10, 0), ipady=3)

        self.error_label = tk.Label(self.frame, text="", font=(Font, 9),
                                    fg=OffColour, bg=Card)
        self.error_label.pack(side="left", padx=(8, 0))

    
        self.total.trace_add("write", self._on_change)

    def _on_change(self, *args):               
        text = self.total.get()
        value, error = ParseTotal(text)
        bad = error is not None and text.strip() != ""   

        ring = OffColour if bad else Border
        focus_ring = OffColour if bad else Accent
        self.entry.config(highlightbackground=ring, highlightcolor=focus_ring)
        self.error_label.config(text=error if bad else "")

        if value is not None and self.command:
            self.command(value)

    def get_total(self):
        """The valid number of trials, or None if the box is empty or invalid."""
        return ParseTotal(self.total.get())[0]

    def set_error(self, message):
        """Let other code show a message here (e.g. 'Enter total trials first')."""
        self.error_label.config(text=message)

    def lock(self, locked=True):
        # A run in progress must not change its own length.
        self.entry.config(state="disabled" if locked else "normal")


class IntervalIndicator:
    """Which interval (A or B) holds the stimulus, and how strong.

    One compact row:  This Trial | [Interval A] [Interval B]
    The interval with the stimulus gets a teal border, its temperature.
    """

    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg=Card, padx=12, pady=8,
                              highlightbackground=Border, highlightthickness=1)
        tk.Label(self.frame, text="This Trial", font=(Font, 11, "bold"),
                 fg=Text, bg=Card).pack(side="left", padx=(0, 10))

        row = tk.Frame(self.frame, bg=Card)
        row.pack(side="left", fill="x", expand=True)
        row.grid_rowconfigure(0, weight=1)

        self.boxes = {}                       
        for i, name in enumerate(("A", "B")):
            box = tk.Frame(row, bg=InputBg, highlightthickness=2, highlightbackground=Border)
            box.grid(row=0, column=i, padx=4, sticky="nsew")      # nsew = fill the cell fully
            row.grid_columnconfigure(i, weight=1, uniform="interval")   # equal widths
            title = tk.Label(box, text=f"Interval {name}", font=(Font, 10, "bold"),
                             fg=SmallLabels, bg=InputBg)
            title.pack(pady=(4, 0))
            detail = tk.Label(box, text="-", font=(Font, 9), fg=SmallLabels, bg=InputBg)
            detail.pack(pady=(0, 4))
            self.boxes[name] = (box, title, detail)

    def show(self, interval, temp, baseline=None):
        """interval = "A" or "B" (the one with the stimulus); temp = stimulus temperature;
        baseline = optional, to show how far the stimulus is from it."""
        for name, (box, title, detail) in self.boxes.items():
            if name == interval:
                box.config(highlightbackground=Accent)
                title.config(fg=Text)
                text = f"STIMULUS {temp:.1f} \u00b0C"
                if baseline is not None:
                    text += f" ({temp - baseline:+.1f})"
                detail.config(text=text, fg=Accent)
            else:
                box.config(highlightbackground=Border)
                title.config(fg=SmallLabels)
                detail.config(text="baseline" if baseline is None else f"{baseline:.1f} \u00b0C",
                              fg=SmallLabels)

    def clear(self):
        for box, title, detail in self.boxes.values():
            box.config(highlightbackground=Border)
            title.config(fg=SmallLabels)
            detail.config(text="-", fg=SmallLabels)


class ResponseDecisionPlot:
    """Live staircase graph: trial number vs delivered stimulus temperature.
    Green dot = correct, red dot = incorrect. Builds the graph inside the window."""

    def __init__(self, parent, total_trials=50):
        self.total = total_trials                       # how many trials the x-axis shows
        self.trials, self.temps, self.correct = [], [], []

        self.frame = tk.Frame(parent, bg=Card, padx=18, pady=15,
                              highlightbackground=Border, highlightthickness=1)
        tk.Label(self.frame, text="Progress", font=(Font, 13, "bold"),
                 fg=Text, bg=Card).pack(anchor="w", pady=(0, 12))

        self.fig = Figure(figsize=(6, 4.2), dpi=100, facecolor=Card)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self._redraw()

    def set_total(self, total_trials):
        """Change how many trials the x-axis shows."""
        self.total = total_trials
        self._redraw()

    def add_point(self, trial, temp, correct):
        """Call once after every trial: records the result and redraws."""
        self.trials.append(trial)
        self.temps.append(temp)
        self.correct.append(correct)
        self._redraw()

    def clear(self):
        """Forget all points (start a fresh run)."""
        self.trials, self.temps, self.correct = [], [], []
        self._redraw()

    def _redraw(self):
        ax = self.ax
        ax.clear()                                      # wipe, then draw everything again
        ax.set_facecolor(InputBg)
        for spine in ax.spines.values():
            spine.set_color(Border)
        ax.tick_params(colors=SmallLabels)
        ax.set_xlabel("Trial number", color=SmallLabels)
        ax.set_ylabel("degC", color=SmallLabels)
        ax.grid(True, color=Border, alpha=0.4, linewidth=0.5)
        ax.set_xlim(0.5, self.total + 0.5)

       
        step = math.ceil(self.total / 10)
        ticks = sorted(set([1] + list(range(step, self.total + 1, step)) + [self.total]))
        ax.set_xticks(ticks)

        if self.temps:
            ax.plot(self.trials, self.temps, color=SmallLabels, lw=1.2, zorder=1)
            dots = [OnColour if c else OffColour for c in self.correct]
            ax.scatter(self.trials, self.temps, c=dots, s=60, zorder=2,
                       edgecolors="#050505")
        lo = min([34] + [t - 0.5 for t in self.temps])   
        hi = max([40] + [t + 0.5 for t in self.temps])
        ax.set_ylim(lo, hi)
        self.fig.tight_layout()
        self.canvas.draw_idle()                         


# 5. DEMO  (fake trials; delete this section when the real experiment is wired in)

class DemoTrialRunner:
    """Runs invented trials so every new panel can be tested before real trials exist.
    """
    DEMO_BASELINE = 34.0       # invented

    def __init__(self, plot, picker, setup, indicator, p_correct=0.7):
        self.plot = plot
        self.picker = picker
        self.setup = setup
        self.indicator = indicator
        self.p_correct = p_correct

    def simulate_trial(self):
        total = self.setup.get_total()
        if total is None:                          # guard clause: stop early if not ready
            self.setup.set_error("Enter total trials first")
            return

        n = len(self.plot.trials) + 1
        if n > total:                              # run finished
            return

        self.setup.lock()                          # the run's length is now fixed

        interval = self.picker.next()      # the "dice throw"
        ok = random.random() < self.p_correct
        prev = self.plot.temps[-1] if self.plot.temps else 38.0
        temp = prev - 0.3 if ok else prev + 0.6                    # invented numbers

        self.indicator.show(interval, temp, baseline=self.DEMO_BASELINE)
        self.plot.add_point(n, temp, ok)

    def reset(self):
        """Start a fresh run: wipe the graph and indicator, unlock the setup boxes."""
        self.plot.clear()
        self.indicator.clear()
        self.setup.lock(False)



# 6. BUILD THE WINDOW  

# The protocol phases: (title, does it show a duration box?)
PHASES = [
    ("Baseline (degC)",         True),
    ("Rate of Change (degC/s)", False),
    ("Stimulus Duration (s)",   True),
    ("Initial Step",            True),
    ("Baseline 3",              True),
]


def build_window():
    root = tk.Tk()
    root.title("2AFC | Experiment Control")
    root.configure(bg=Bg)
    root.minsize(900, 600)
    return root


def build_header(parent):
    tk.Label(parent, text="Two-Alternative Forced Choice",
             font=(Font, 18, "bold"), fg=Text, bg=Bg).pack(anchor="w")
    tk.Label(parent, text="Configuration Panel",
             font=(Font, 10), fg=SmallLabels, bg=Bg).pack(anchor="w", pady=(2, 10))


def build_left_column(parent):
    """Active Surfaces card + one DestTemp card per phase. Returns what other code needs."""
    active_surfaces = ActiveSurfaces(parent)
    active_surfaces.frame.pack(fill="x", pady=(0, 8))

    panels = []
    for title, show_duration in PHASES:
        panel = DestTemp(parent, title, show_duration)
        panel.baseFrame.pack(fill="x", pady=(0, 6))
        panels.append(panel)
    return active_surfaces, panels


def build_right_column(parent):
    """Right column, top to bottom: [Total Trials | This Trial] bar, graph, demo buttons.

    pack() gives space in the order you call it, and the last widgets packed are the
    first to be squeezed. So the demo row (must never vanish) is packed FIRST with
    side="bottom", then the top bar, then the graph, which takes all the space left.
    """
    demo_row = tk.Frame(parent, bg=Bg)
    demo_row.pack(side="bottom", anchor="w", pady=(6, 0))

    top_bar = tk.Frame(parent, bg=Bg)
    top_bar.pack(side="top", fill="x", pady=(0, 8))

    plot = ResponseDecisionPlot(parent, total_trials=50)

    # The setup box tells the graph when the total changes. 
    setup = TrialSetup(top_bar, command=plot.set_total)
    setup.frame.pack(side="left", fill="y")
    indicator = IntervalIndicator(top_bar)
    indicator.frame.pack(side="left", fill="both", expand=True, padx=(8, 0))

    plot.frame.pack(side="top", fill="both", expand=True)

    # --- DEMO ONLY: created after every widget it needs exists ---
    demo = DemoTrialRunner(plot, IntervalPicker(), setup, indicator)
    tk.Button(demo_row, text="Simulate trial (demo)",
              command=demo.simulate_trial).pack(side="left")
    tk.Button(demo_row, text="Reset (demo)",
              command=demo.reset).pack(side="left", padx=(8, 0))
    return plot, setup, indicator


def main():
    root = build_window()

    main_frame = tk.Frame(root, bg=Bg, padx=20, pady=12)
    main_frame.pack(fill="both", expand=True)
    build_header(main_frame)

    left = tk.Frame(main_frame, bg=Bg)
    left.pack(side="left", fill="y", anchor="n")
    right = tk.Frame(main_frame, bg=Bg)
    right.pack(side="left", fill="both", expand=True, padx=(20, 0))

    active_surfaces, panels = build_left_column(left)
    plot, setup, indicator = build_right_column(right)

    root.mainloop()       # runs until the window closes; nothing after it executes until then


if __name__ == "__main__":    # True only when you run this file, not when another file imports it
    main()