import os
import sys

def main():
    if len(sys.argv) < 2:
        mode = "api"
    else:
        mode = sys.argv[1]

    py = sys.executable

    if mode == "api":
        host = os.getenv("UVICORN_HOST", "0.0.0.0")
        port = os.getenv("UVICORN_PORT", "5000")
        workers = os.getenv("UVICORN_WORKERS", "1")
        cmd = [
            py,
            "-m", "uvicorn",
            "api.main:app",
            "--log-config=/app/logging.conf",
            "--host", host,
            "--port", str(port),
            "--workers", str(workers)
        ]
        os.execvp(py, cmd)

    elif mode == "worker":
        loglevel = os.getenv("CELERY_LOGLEVEL", "info")
        concurrency = os.getenv("CELERY_CONCURRENCY", "4")
        cmd = [
            py,
            "-m", "celery",
            "-A", "worker.lookup",
            "worker",
            f"--loglevel={loglevel}",
            f"--concurrency={concurrency}"
        ]
        os.execvp(py, cmd)

    elif mode == "pytest":
        cmd = [py, "-m", "pytest"] + sys.argv[2:]
        os.execvp(py, cmd)

    elif mode == "cli":
        cmd = [py, "-m", "cli"] + sys.argv[2:]
        os.execvp(py, cmd)

    else:
        os.execvp(mode, sys.argv[1:])

if __name__ == "__main__":
    main()
