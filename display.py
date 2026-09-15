import csv
import json
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
    csv_name: str = "free_recall.csv",
):
    """
    Fullscreen sequence presentation + free recall task.

    Flow:
        1. Press Enter to start
        2. Enter name
        3. Sequence is displayed
        4. Enter recalled items one at a time
        5. Results are saved to free_recall.csv

    CSV columns:
        name
        n
        n_correct
        id_correct

    id_correct contains the original 1-based positions of correctly
    recalled items.

    During recall:
        Enter  -> submit current answer
        Escape -> finish recall early and save results
    """

    csv_path = "experiments/" + csv_name

    # ------------------------------------------------------------
    # Normalize sequence
    # ------------------------------------------------------------

    if isinstance(sequence, (list, tuple)):
        seq = list(sequence)
    else:
        seq = [sequence]

    auto = isinstance(interval, (int, float))

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

    # Don't show it initially
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
        """Cancel any scheduled sequence advancement."""

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
            begin_recall()
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
    # Phase 3: Free recall
    # ------------------------------------------------------------

    def begin_recall():
        cancel_after()

        state["phase"] = "recall"
        state["recall"] = []

        label.config(
            text=(
                f"Recall\n\n"
                f"0 / {len(seq)} entered"
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
        answer = entry.get().strip()

        # Ignore blank entries
        if not answer:
            return

        state["recall"].append(answer)

        entry.delete(0, tk.END)

        amount_entered = len(state["recall"])

        label.config(
            text=(
                f"Recall\n\n"
                f"{amount_entered} / {len(seq)} entered"
            )
        )

        # Finish automatically once they have entered
        # the same number of responses as there were items.
        if amount_entered >= len(seq):
            save_results()

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

    def calculate_correct_ids():
        """
        Return the 1-based indices of correctly recalled items.

        Example:

            seq = [15, 82, 34, 91]

            recall = ["34", "15"]

        returns:

            [1, 3]

        A sequence item can only be matched once.
        """

        matched_indices = set()

        for answer in state["recall"]:

            normalized_answer = normalize(answer)

            for i, sequence_item in enumerate(seq):

                # Already counted this sequence item
                if i in matched_indices:
                    continue

                if normalize(sequence_item) == normalized_answer:
                    matched_indices.add(i)
                    break

        # Convert 0-based Python indices to 1-based IDs
        correct_ids = [
            i + 1
            for i in sorted(matched_indices)
        ]

        return correct_ids

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

        correct_ids = calculate_correct_ids()

        n = len(seq)
        n_correct = len(correct_ids)

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
                        "id_correct",
                    ])

                writer.writerow([
                    state["name"],
                    n,
                    n_correct,
                    json.dumps(correct_ids),
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
                f"Correct item positions:\n"
                f"{correct_ids}\n\n"
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
        bg="black",
        fg="white",
        font_size=720,
        tts=True,
        csv_path="free_recall.csv",
    )