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
):
    """Display items (characters or list) fullscreen.

    Behavior:
    - If 'interval' is a number (int or float), the sequence auto-advances every `interval` seconds.
    - Otherwise, advances when the user presses Space.
    - If 'tts' is enabled, Windows SAPI text-to-speech will read aloud each item.

    'sequence' may be a single item (e.g. 'A') or a list/tuple of items.

    Press 'Escape' to close.
    """

    # Normalize sequence into a list
    if isinstance(sequence, (list, tuple)):
        seq = list(sequence)
    else:
        seq = [sequence]

    auto = isinstance(interval, (int, float))

    # TTS runs in one background worker so speech does not block the GUI.
    speech_queue = queue.Queue()
    speech_finished = threading.Event()

    def tts_worker():
        try:
            import win32com.client

            voice = win32com.client.Dispatch("SAPI.SpVoice")
            # SAPI's normal rate is 0. A small negative value is slower.
            voice.Rate = -2

            while True:
                speech_item = speech_queue.get()

                if speech_item is None:
                    break

                text, speech_done = speech_item

                try:
                    # Speak is synchronous, so this event is set only after
                    # the current item has finished being spoken.
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
        threading.Thread(target=tts_worker, daemon=True).start()

    root = tk.Tk()
    root.configure(bg=bg)
    root.attributes("-fullscreen", True)
    label = tk.Label(root, text="Press Space to begin", bg=bg, fg=fg, font=("Helvetica", 160))
    label.pack(expand=True)

    state = {
        "started": False,
        "index": 0,
        "after_id": None,
        "tts_enabled": bool(tts),
        "tts_stop_sent": False,
        "finished": False,
        "speech_done": None,
    }

    def finish(wait_for_tts=False):
        if state["finished"]:
            return

        if tts and wait_for_tts and not speech_finished.is_set():
            # Let the worker finish queued speech before closing normally.
            if not state["tts_stop_sent"]:
                speech_queue.put(None)
                state["tts_stop_sent"] = True
            root.after(50, lambda: finish(wait_for_tts=True))
            return

        state["finished"] = True

        if tts and not state["tts_stop_sent"]:
            speech_queue.put(None)
            state["tts_stop_sent"] = True

        if on_finish:
            try:
                on_finish()
            except Exception as error:
                print("on_finish error:", repr(error))

        root.destroy()

    def show_current():
        i = state["index"]
        if i >= len(seq):
            finish(wait_for_tts=True)
            return
        item = seq[i]

        # Display item
        label.config(text=str(item), font=("Helvetica", font_size))

        # Speak the item and keep its completion event for synchronized timing.
        if tts:
            state["speech_done"] = threading.Event()
            speech_queue.put((str(item), state["speech_done"]))
        else:
            state["speech_done"] = None

        if auto:
            # Advance after the interval and after TTS has finished, if enabled.
            ms = int(float(interval) * 1000)
            state["after_id"] = root.after(ms, wait_for_speech)

    def wait_for_speech():
        """Wait until the current item has finished speaking before advancing."""
        speech_done = state["speech_done"]
        if (
            tts
            and speech_done is not None
            and not speech_done.is_set()
            and not speech_finished.is_set()
        ):
            state["after_id"] = root.after(20, wait_for_speech)
            return

        state["after_id"] = None
        advance()

    def advance(event=None):
        # cancel any scheduled callback
        if state.get("after_id"):
            try:
                root.after_cancel(state["after_id"])
            except Exception:
                pass
            state["after_id"] = None
        state["index"] += 1
        show_current()

    def start_or_advance(event=None):
        if not state["started"]:
            state["started"] = True
            state["index"] = 0
            show_current()
        else:
            # manual advance
            if not auto:
                advance()

    # Bind keys
    root.bind("<space>", start_or_advance)
    root.bind("<Escape>", lambda e: finish())

    root.mainloop()


if __name__ == "__main__":
    display_sequence(["A", "car", "42"], interval=2, bg="black", fg="white", font_size=720, tts=True)
    # display_sequence_fullscreen(["1", "2", "3"], interval=0.5, bg="white", fg="black", font_size=200)