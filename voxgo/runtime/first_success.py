"""Evidence for a live setup check; no endpoint probe can complete this check."""
from dataclasses import dataclass, field
import time


@dataclass
class LiveCheck:
    revision: int
    started_at: float = field(default_factory=time.time)
    models: bool = False
    audio: bool = False
    transcripts: set = field(default_factory=set)
    translations: set = field(default_factory=set)
    presented: set = field(default_factory=set)
    error: str = ""

    def transcript(self, item_id, revision, detected_at):
        if revision != self.revision or detected_at < self.started_at:
            return False
        if self.complete or len(self.transcripts) >= 128:
            return False
        # A speech segment from the formal capture pipeline is also audio evidence.
        self.audio = True
        self.transcripts.add(item_id)
        return True

    def translation(self, item_id, revision, error=""):
        if revision != self.revision or item_id not in self.transcripts:
            return False
        self.error = error
        if not error:
            self.translations.add(item_id)
        return not error

    def present(self, item_id):
        if item_id in self.translations:
            self.presented.add(item_id)
            return True
        return False

    @property
    def stages(self):
        return (self.models, self.audio, bool(self.transcripts), bool(self.translations), bool(self.presented))

    @property
    def complete(self):
        return all(self.stages)
