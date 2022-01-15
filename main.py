import os
import sys
import time
import logging
from PIL import Image, UnidentifiedImageError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


blocklist = ["horizontal.png", "vertical.png"]


class SimpleEventHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_any_event(self, event):
        if event.is_directory or any(
            [event.src_path.endswith(b) for b in blocklist]
        ):
            return
        self.callback()


def merge_files(path: str):
    start_time = time.time()

    # Delete all existing artefacts
    for entry in blocklist:
        try:
            os.remove(os.path.join(path, entry))
        except FileNotFoundError:
            pass

    # Load all existing images
    files = []
    for file in os.listdir(path):
        file = os.path.join(path, file)
        if os.path.isdir(file) or any([file.endswith(b) for b in blocklist]):
            continue
        files.append(file)

    files = sorted(files)

    images = []
    for file in files:
        try:
            images.append(Image.open(file))
        except UnidentifiedImageError:
            pass

    if images == []:
        logging.info("No images to merge. 😴")
        return

    # Create the output images
    heights = list(map(lambda i: i.height, images))
    widths = list(map(lambda i: i.width, images))

    width = sum(widths)
    height = max(heights)
    result = Image.new("RGBA", (width, height), color="#000000FF")

    x, y = 0, 0
    for img in images:
        result.paste(img, (x, y))
        x += img.width
        img.close()

    result.save(os.path.join(path, "horizontal.png"))
    result.close()
    logging.info(
        f"Merged {len(images)} images. 🙏  ({time.time() - start_time:.3f}s)"
    )


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    path = sys.argv[1] if len(sys.argv) > 1 else "."
    event_handler = SimpleEventHandler(lambda: merge_files(path))
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    try:
        logging.info(f"Started watching {path} 👀")
        merge_files(path)
        while True:
            time.sleep(0.5)
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
