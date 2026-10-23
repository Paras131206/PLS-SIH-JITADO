"""engine/apaar_engine/server.py

Embedded Localhost Web Server & Interactive Dashboard for APAAR-SDMS Validation Engine.
Provides an interactive GUI at http://localhost:8000 and http://localhost:5173 for testing
Phase 0-Phase 3 rules (V001-V020), deduplication, and anomaly detection.
"""

from __future__ import annotations

import json
import logging
import socket
import threading
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

import pandas as pd

from apaar_engine.anomaly.metrics import BatchMetricState
from apaar_engine.models import BatchReport
from apaar_engine.registry import MockApaarRegistry
from apaar_engine.reports.dq_report import export_dq_report_xlsx
from apaar_engine.validate import validate_batch

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("apaar_server")

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_DIR = REPO_ROOT / "data" / "synthetic"
STATIC_DIR = Path(__file__).resolve().parent / "static"

_intake_df: Optional[pd.DataFrame] = None
_registry: Optional[MockApaarRegistry] = None
_central_df: Optional[pd.DataFrame] = None
_history_states: Optional[list] = None
_latest_report: Optional[BatchReport] = None


def load_reference_data() -> None:
    global _intake_df, _registry, _central_df, _history_states
    intake_csv = SYNTHETIC_DIR / "intake.csv"
    if intake_csv.exists():
        _intake_df = pd.read_csv(intake_csv)

    reg_csv = SYNTHETIC_DIR / "registry.csv"
    if reg_csv.exists():
        _registry = MockApaarRegistry.from_csv(reg_csv)

    central_csv = SYNTHETIC_DIR / "central_snapshot.csv"
    if central_csv.exists():
        _central_df = pd.read_csv(central_csv)

    hist_json = SYNTHETIC_DIR / "history_states.json"
    if hist_json.exists():
        with open(hist_json, mode="r", encoding="utf-8") as f:
            _history_states = [BatchMetricState.from_json(item) for item in json.load(f)]


class ApaarServerHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            html_file = STATIC_DIR / "index.html"
            html_content = (
                html_file.read_bytes() if html_file.exists() else b"<h1>APAAR Engine</h1>"
            )
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_content)
            return

        if path == "/api/health":
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            health_json = json.dumps({"status": "ok", "engine": "apaar_engine", "version": "0.3.0"})
            self.wfile.write(health_json.encode("utf-8"))
            return

        if path == "/api/sample/clean":
            clean_csv = SYNTHETIC_DIR / "students.csv"
            global _latest_report
            _latest_report = validate_batch(
                clean_csv,
                intake_df=_intake_df,
                registry=_registry,
                central_df=_central_df,
            )
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(_latest_report.model_dump_json().encode("utf-8"))
            return

        if path == "/api/sample/defects":
            defects_csv = SYNTHETIC_DIR / "students_with_defects.csv"
            _latest_report = validate_batch(
                defects_csv,
                intake_df=_intake_df,
                registry=_registry,
                central_df=_central_df,
                history=_history_states,
            )
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(_latest_report.model_dump_json().encode("utf-8"))
            return

        if path == "/api/export-xlsx":
            if _latest_report is None:
                self.send_error(HTTPStatus.BAD_REQUEST, "No batch has been validated yet.")
                return
            xlsx_bytes = export_dq_report_xlsx(_latest_report)
            self.send_response(HTTPStatus.OK)
            xlsx_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            self.send_header("Content-Type", xlsx_type)
            self.send_header("Content-Disposition", 'attachment; filename="BatchReport_DQ.xlsx"')
            self.end_headers()
            self.wfile.write(xlsx_bytes)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/validate":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            content_type = self.headers.get("Content-Type", "")
            global _latest_report

            if "multipart/form-data" in content_type:
                boundary = content_type.split("boundary=")[1].strip().encode("utf-8")
                parts = body.split(boundary)
                file_bytes = b""
                for part in parts:
                    if b'filename="' in part:
                        headers_body = part.split(b"\r\n\r\n", 1)
                        if len(headers_body) > 1:
                            file_bytes = headers_body[1].rstrip(b"\r\n--")
                            break
                if not file_bytes:
                    file_bytes = body
            else:
                file_bytes = body

            try:
                _latest_report = validate_batch(
                    file_bytes,
                    intake_df=_intake_df,
                    registry=_registry,
                    central_df=_central_df,
                    history=_history_states,
                )
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(_latest_report.model_dump_json().encode("utf-8"))
            except Exception as e:
                logger.exception("Validation failed: %s", e)
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Validation error: {e}")
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")


class DualStackServer(ThreadingHTTPServer):
    address_family = socket.AF_INET6

    def server_bind(self) -> None:
        try:
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except Exception:
            pass
        super().server_bind()


def start_server_on_port(port: int) -> None:
    try:
        server = DualStackServer(("::", port), ApaarServerHandler)
        logger.info("Serving APAAR Engine Web App (dual-stack) on http://localhost:%d", port)
        server.serve_forever()
    except Exception as exc:
        logger.info("Could not bind dual-stack on port %d (%s), falling back to IPv4...", port, exc)
        try:
            server_v4 = ThreadingHTTPServer(("0.0.0.0", port), ApaarServerHandler)
            logger.info("Serving APAAR Engine Web App (IPv4) on http://localhost:%d", port)
            server_v4.serve_forever()
        except Exception as exc4:
            logger.warning("Could not bind port %d: %s", port, exc4)


def main() -> None:
    load_reference_data()
    # Launch servers on standard ports: 8000, 5173, and 3000
    ports = [8000, 5173, 3000]
    threads = []
    for port in ports:
        t = threading.Thread(target=start_server_on_port, args=(port,), daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
