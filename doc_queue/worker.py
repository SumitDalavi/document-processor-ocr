"""
Async document processing worker using a simple queue abstraction.
In production: swap _QueueBackend for Celery+Redis or AWS SQS.
"""
from __future__ import annotations
import json, os, time, threading, uuid
from dataclasses import dataclass, field
from typing import Callable, List, Optional
from queue import Queue, Empty


@dataclass
class Job:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_path: str = ""
    output_format: str = "json"       # json | markdown
    status: str = "queued"            # queued | processing | done | failed
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


class DocumentQueue:
    """In-process queue for document processing jobs (drop-in for Celery/SQS)."""

    def __init__(self, num_workers: int = 2):
        self._queue: Queue = Queue()
        self._jobs: dict[str, Job] = {}
        self._workers: List[threading.Thread] = []
        self._processor: Optional[Callable] = None
        self._running = False
        self._num_workers = num_workers

    def set_processor(self, fn: Callable):
        """Set the function that processes each job."""
        self._processor = fn

    def start(self):
        """Start background worker threads."""
        self._running = True
        for _ in range(self._num_workers):
            t = threading.Thread(target=self._worker_loop, daemon=True)
            t.start()
            self._workers.append(t)

    def stop(self):
        self._running = False

    def enqueue(self, document_path: str, output_format: str = "json") -> Job:
        """Add a document processing job to the queue. Returns the Job (with ID)."""
        job = Job(document_path=document_path, output_format=output_format)
        self._jobs[job.id] = job
        self._queue.put(job.id)
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def _worker_loop(self):
        while self._running:
            try:
                job_id = self._queue.get(timeout=1.0)
                job = self._jobs.get(job_id)
                if job is None:
                    continue
                job.status = "processing"
                try:
                    result = self._processor(job.document_path, job.output_format)
                    job.result = result
                    job.status = "done"
                except Exception as e:
                    job.error = str(e)
                    job.status = "failed"
                finally:
                    job.completed_at = time.time()
                    self._queue.task_done()
            except Empty:
                continue


# Global queue instance
queue = DocumentQueue(num_workers=int(os.getenv("WORKER_THREADS", "2")))
