# reservoir_buffer.py
import random, threading, time, json
from pathlib import Path
from config import get

BUF_FILE = Path(__file__).resolve().parent / "data" / "ml_buffer.jsonl"
BUF_FILE.parent.mkdir(exist_ok=True, parents=True)

class ReservoirBuffer:
    def __init__(self, max_size=None):
        self.max_size = max_size or get("MAX_BUFFER")
        self.lock = threading.Lock()
        self.buffer = []  # list of (token_hash, vector, timestamp)
        self.count_seen = 0

    def add(self, token_hash, vector, timestamp=None):
        timestamp = timestamp or time.time()
        with self.lock:
            self.count_seen += 1
            if len(self.buffer) < self.max_size:
                self.buffer.append((token_hash, vector, timestamp))
            else:
                # reservoir sampling
                i = random.randint(0, self.count_seen - 1)
                if i < self.max_size:
                    self.buffer[i] = (token_hash, vector, timestamp)
        # append to disk for forensics too (append-only)
        with open(BUF_FILE, "a") as f:
            f.write(json.dumps({"token": token_hash, "vector": vector, "ts": timestamp}) + "\n")

    def get_all(self):
        with self.lock:
            return list(self.buffer)

    def size(self):
        with self.lock:
            return len(self.buffer)

    def clear(self):
        with self.lock:
            self.buffer = []
            self.count_seen = 0
