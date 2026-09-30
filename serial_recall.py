import csv
import os
import queue
import threading
import tkinter as tk
from typing import Optional, Callable, Any


def display_sequence(
    sequence: Any,
    interval: Optional[float] = None,
    bg: str = "black",
    fg: str = "white",
    font_size: int = 120,
    on_finish: Optional[Callable] = None,
    tts: bool = False,
    sleep: int = 0,
    csv_name: str = "serial_recall.csv",
):
    """
    Fullscreen sequence presentation + SERIAL recall task.

    Flow:
        1. Press Enter to start
        2. Enter name
        3. Sequence is displayed
        4. Wait for `sleep` seconds
        5. Enter recalled items one at a time
        6. Results are saved to CSV

    CSV columns:
        name
        n
        n_correct

    Scoring is strictly positional: the answer typed for position k
    counts as correct only if it matches sequence item k. Wrong
    answers never cause errors; they simply aren't counted.

    During recall:
        Enter  -> submit the answer for the current position
                  (a blank Enter skips that position)
        Escape -> finish recall early and save results
                  (unanswered positions count as incorrect)
    """

    csv_path = "experiments/" + csv_name

    # Create experiments directory if it doesn't exist
    os.makedirs("experiments", exist_ok=True)

    # ------------------------------------------------------------
    # Normalize sequence
    # ------------------------------------------------------------

    if isinstance(sequence, (list, tuple)):
        seq = list(sequence)
    else:
        seq = [sequence]

    auto = isinstance(interval, (int, float))

    # Make sure sleep is valid
    wait_seconds = max(0, float(sleep))

    # ------------------------------------------------------------
    # Text-to-speech
    # ------------------------------------------------------------

    speech_queue = queue.Queue()
    speech_finished = threading.Event()

    def tts_worker():
        try:
            import win32com.client

            voice = win32com.client.Dispatch("SAPI.SpVoice")
            voice.Rate = -2

            while True:
                speech_item = speech_queue.get()

                if speech_item is None:
                    break

                text, speech_done = speech_item

                try:
                    voice.Speak(str(text))

                except Exception as error:
                    print("TTS speaking error:", repr(error))

                finally:
                    speech_done.set()

        except Exception as error:
            print("TTS initialization error:", repr(error))

        finally:
            speech_finished.set()

    if tts:
        threading.Thread(
            target=tts_worker,
            daemon=True
        ).start()

    # ------------------------------------------------------------
    # Window
    # ------------------------------------------------------------

    root = tk.Tk()

    root.configure(bg=bg)
    root.attributes("-fullscreen", True)

    label = tk.Label(
        root,
        text="Press Enter to start",
        bg=bg,
        fg=fg,
        font=("Helvetica", 100),
        justify="center",
    )

    label.pack(
        expand=True,
        fill="both",
    )

    # Text input used both for name and recall
    entry = tk.Entry(
        root,
        bg=bg,
        fg=fg,
        insertbackground=fg,
        font=("Helvetica", 80),
        justify="center",
        bd=0,
        highlightthickness=0,
    )

    # Don't show input initially
    entry.pack_forget()

    # ------------------------------------------------------------
    # State
    # ------------------------------------------------------------

    state = {
        "phase": "start",

        "name": "",

        "index": 0,

        "after_id": None,

        "speech_done": None,

        "tts_stop_sent": False,

        "recall": [],

        "saved": False,

        "closing": False,
    }

    # ------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------

    def cancel_after():
        """Cancel any scheduled Tkinter callback."""

        if state["after_id"] is not None:
            try:
                root.after_cancel(state["after_id"])
            except Exception:
                pass

            state["after_id"] = None

    def stop_tts():
        """Tell the TTS worker to stop."""

        if tts and not state["tts_stop_sent"]:
            speech_queue.put(None)
            state["tts_stop_sent"] = True

    def close_window():
        """Close the application."""

        if state["closing"]:
            return

        state["closing"] = True

        cancel_after()
        stop_tts()

        root.destroy()

    # ------------------------------------------------------------
    # Phase 1: Name
    # ------------------------------------------------------------

    def begin_name():
        state["phase"] = "name"

        label.config(
            text="Enter your name",
            font=("Helvetica", 80),
        )

        entry.pack(
            pady=(0, 200),
            padx=200,
            fill="x",
        )

        entry.delete(0, tk.END)
        entry.focus_set()

    def submit_name():
        name = entry.get().strip()

        if not name:
            label.config(
                text="Enter your name",
            )
            return

        state["name"] = name

        entry.delete(0, tk.END)
        entry.pack_forget()

        begin_sequence()

    # ------------------------------------------------------------
    # Phase 2: Sequence presentation
    # ------------------------------------------------------------

    def begin_sequence():
        state["phase"] = "sequence"
        state["index"] = 0

        show_current()

    def show_current():
        i = state["index"]

        # Sequence is over
        if i >= len(seq):
            begin_waiting()
            return

        item = seq[i]

        # Display item
        label.config(
            text=str(item),
            font=("Helvetica", font_size),
        )

        # Speak item
        if tts:
            state["speech_done"] = threading.Event()

            speech_queue.put(
                (
                    str(item),
                    state["speech_done"],
                )
            )

        else:
            state["speech_done"] = None

        # Automatic advancement
        if auto:
            ms = int(float(interval) * 1000)

            state["after_id"] = root.after(
                ms,
                wait_for_speech,
            )

    def wait_for_speech():
        """
        Wait until both:
            - interval has elapsed
            - speech has finished
        """

        speech_done = state["speech_done"]

        if (
            tts
            and speech_done is not None
            and not speech_done.is_set()
            and not speech_finished.is_set()
        ):
            state["after_id"] = root.after(
                20,
                wait_for_speech,
            )

            return

        state["after_id"] = None

        advance()

    def advance():
        cancel_after()

        state["index"] += 1

        show_current()

    # ------------------------------------------------------------
    # Phase 3: Waiting period
    # ------------------------------------------------------------

    def begin_waiting():
        """
        Show a static waiting message for the requested amount
        of time.

        Example:
            sleep=30

        Displays:

            Waiting 30 seconds

        for the full 30 seconds. It does NOT count down.
        """

        cancel_after()

        state["phase"] = "waiting"

        # Hide the text entry if it happens to be visible
        entry.pack_forget()

        # Format whole numbers without ".0"
        if wait_seconds.is_integer():
            wait_text = str(int(wait_seconds))
        else:
            wait_text = str(wait_seconds)

        label.config(
            text=f"Waiting {wait_text} seconds",
            font=("Helvetica", 80),
        )

        # After the full wait period, begin recall
        state["after_id"] = root.after(
            int(wait_seconds * 1000),
            begin_recall,
        )

    # ------------------------------------------------------------
    # Phase 4: Serial recall
    # ------------------------------------------------------------

    def begin_recall():
        cancel_after()

        state["phase"] = "recall"
        state["recall"] = []

        label.config(
            text=(
                f"Recall\n\n"
                f"Item 1 of {len(seq)}"
            ),
            font=("Helvetica", 60),
        )

        entry.pack(
            pady=(0, 150),
            padx=200,
            fill="x",
        )

        entry.delete(0, tk.END)
        entry.focus_set()

    def submit_recall():
        # A blank answer is kept as "" so it acts as a skipped
        # position and later answers stay aligned to the right slot.
        answer = entry.get().strip()

        state["recall"].append(answer)

        entry.delete(0, tk.END)

        amount_entered = len(state["recall"])

        # Finish automatically once every position has an answer.
        if amount_entered >= len(seq):
            save_results()
            return

        label.config(
            text=(
                f"Recall\n\n"
                f"Item {amount_entered + 1} of {len(seq)}"
            )
        )

    # ------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------

    def normalize(value):
        """
        Normalize values so, for example:

            sequence item: 42
            entered text:  "42"

        match correctly.

        casefold() means:
            A == a
            CAR == car
        """

        return str(value).strip().casefold()

    def calculate_n_correct():
        """
        Return the number of items recalled in the correct position.

        Example:

            seq    = [1, 2, 3]
            recall = ["1", "5", "3"]

        returns 2 (positions 1 and 3 match).

        Comparison is by position only, so wrong, blank, or
        missing answers are just not counted.
        """

        total = 0

        for sequence_item, answer in zip(seq, state["recall"]):
            if normalize(sequence_item) == normalize(answer):
                total += 1

        return total

    # ------------------------------------------------------------
    # CSV saving
    # ------------------------------------------------------------

    def save_results():
        # Prevent saving twice
        if state["saved"]:
            return

        state["saved"] = True
        state["phase"] = "finished"

        cancel_after()

        n = len(seq)
        n_correct = calculate_n_correct()

        # Check whether CSV needs a header
        needs_header = (
            not os.path.exists(csv_path)
            or os.path.getsize(csv_path) == 0
        )

        try:
            with open(
                csv_path,
                "a",
                newline="",
                encoding="utf-8",
            ) as file:

                writer = csv.writer(file)

                if needs_header:
                    writer.writerow([
                        "name",
                        "n",
                        "n_correct",
                    ])

                writer.writerow([
                    state["name"],
                    n,
                    n_correct,
                ])

        except Exception as error:
            print("CSV saving error:", repr(error))

            label.config(
                text=(
                    "Error saving results\n\n"
                    f"{error}\n\n"
                    "Press Escape to close"
                ),
                font=("Helvetica", 40),
            )

            entry.pack_forget()

            return

        # Hide input box
        entry.pack_forget()

        # Results screen
        label.config(
            text=(
                "Finished\n\n"
                f"{n_correct} / {n} correct\n\n"
                "Press Enter or Escape to close"
            ),
            font=("Helvetica", 50),
        )

        stop_tts()

        if on_finish:
            try:
                on_finish()

            except Exception as error:
                print("on_finish error:", repr(error))

    # ------------------------------------------------------------
    # Keyboard handling
    # ------------------------------------------------------------

    def handle_enter(event=None):

        phase = state["phase"]

        if phase == "start":
            begin_name()

        elif phase == "name":
            submit_name()

        elif phase == "recall":
            submit_recall()

        elif phase == "finished":
            close_window()

        return "break"

    def handle_space(event=None):
        """
        Space only advances the presentation if no automatic
        interval was supplied.

        It does NOT interfere with typing spaces into the
        name/recall Entry boxes.
        """

        if state["phase"] == "sequence" and not auto:
            advance()
            return "break"

    def handle_escape(event=None):

        # Escape during recall = submit early
        if state["phase"] == "recall":

            save_results()

            # User specifically used Escape, so close
            # immediately after saving.
            root.after(10, close_window)

        else:
            close_window()

        return "break"

    # ------------------------------------------------------------
    # Bind controls
    # ------------------------------------------------------------

    root.bind("<Return>", handle_enter)
    root.bind("<Escape>", handle_escape)
    root.bind("<space>", handle_space)

    root.mainloop()


# ------------------------------------------------------------
# Example
# ------------------------------------------------------------

if __name__ == "__main__":

    display_sequence(
        ["A", "car", "42"],
        interval=2,
        sleep=0,
        bg="black",
        fg="white",
        font_size=720,
        tts=True,
        csv_name="test.csv",
    )