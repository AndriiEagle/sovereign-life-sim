import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from revenue_lab.__main__ import main, load, MAX_INPUT_BYTES

class CliTests(unittest.TestCase):
    def test_demo_labeled_simulated(self):
        output=io.StringIO()
        with contextlib.redirect_stdout(output): rc=main(["demo"])
        self.assertEqual(rc,0)
        self.assertEqual(json.loads(output.getvalue())["status"],"SIMULATED_NO_CUSTOMERS_NO_PAYMENTS")
    def test_nonexistent_file_returns_two(self):
        with tempfile.TemporaryDirectory() as d:
            with contextlib.redirect_stderr(io.StringIO()): rc=main(["quote",str(Path(d)/"missing.json")])
        self.assertEqual(rc,2)
    def test_json_array_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"input.json";p.write_text("[]")
            with self.assertRaises(ValueError): load(str(p))
    def test_oversized_input_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"input.json";p.write_bytes(b" "*(MAX_INPUT_BYTES+1))
            with self.assertRaises(ValueError): load(str(p))
    def test_utf8_bom_supported(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"input.json";p.write_text('{"action":"validate_fixture"}',encoding="utf-8-sig")
            self.assertEqual(load(str(p))["action"],"validate_fixture")
    def test_bad_date_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"input.json";p.write_text('{}')
            with contextlib.redirect_stderr(io.StringIO()): rc=main(["freshness",str(p),"--as-of","bad"])
            self.assertEqual(rc,2)
    def test_gate_outputs_no_execution(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"input.json";p.write_text('{"action":"send_email","approved":true}')
            out=io.StringIO()
            with contextlib.redirect_stdout(out): rc=main(["gate",str(p)])
            self.assertEqual(rc,0);self.assertFalse(json.loads(out.getvalue())["executed"])

if __name__=="__main__": unittest.main()
