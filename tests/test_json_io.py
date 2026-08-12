import json
import tempfile
import unittest
from pathlib import Path

from scripts.json_io import atomic_write_json, read_json


class JsonIoTests(unittest.TestCase):
    def test_atomic_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.json"
            atomic_write_json(path, {"patient": "Lung_Patient_3", "history": [1, 2]})
            self.assertEqual(read_json(path)["history"], [1, 2])
            self.assertEqual(json.loads(path.read_text())["patient"], "Lung_Patient_3")

    def test_incomplete_json_returns_none(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.json"
            path.write_text('{"patient":')
            self.assertIsNone(read_json(path))


if __name__ == "__main__":
    unittest.main()
