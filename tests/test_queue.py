"""Tests for the async document processing queue."""
import time, pytest
from queue.worker import DocumentQueue, Job


def make_queue(processor=None):
    q = DocumentQueue(num_workers=1)
    q.set_processor(processor or (lambda path, fmt: {"text": f"Extracted from {path}", "format": fmt}))
    q.start()
    return q


def test_enqueue_returns_job():
    q = make_queue()
    job = q.enqueue("test.pdf")
    assert job.id is not None
    assert job.status == "queued"
    q.stop()


def test_job_processes_successfully():
    q = make_queue()
    job = q.enqueue("report.pdf")
    # Wait for processing
    for _ in range(20):
        time.sleep(0.1)
        j = q.get_job(job.id)
        if j and j.status in ("done", "failed"):
            break
    assert j.status == "done"
    assert j.result is not None
    q.stop()


def test_failed_job_records_error():
    def bad_processor(path, fmt):
        raise ValueError("Unsupported format")

    q = make_queue(processor=bad_processor)
    job = q.enqueue("broken.pdf")
    for _ in range(20):
        time.sleep(0.1)
        j = q.get_job(job.id)
        if j and j.status in ("done", "failed"):
            break
    assert j.status == "failed"
    assert j.error is not None
    assert "Unsupported" in j.error
    q.stop()


def test_multiple_jobs():
    q = make_queue()
    jobs = [q.enqueue(f"doc{i}.pdf") for i in range(5)]
    time.sleep(1.5)
    done = sum(1 for j in jobs if q.get_job(j.id).status == "done")
    assert done == 5
    q.stop()


def test_get_nonexistent_job():
    q = make_queue()
    assert q.get_job("nonexistent-id") is None
    q.stop()
