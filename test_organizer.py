import tempfile
import unittest
from pathlib import Path

from organizer import classify_file, execute_cleanup, scan_folder, summarize, undo_cleanup


class OrganizerTests(unittest.TestCase):
    def test_classification_is_case_insensitive(self):
        self.assertEqual(classify_file(Path("PHOTO.JPG")), "Images")
        self.assertEqual(classify_file(Path("installer.MSI")), "Installers")
        self.assertEqual(classify_file(Path("mystery")), "Other")

    def test_scan_ignores_subfolders_and_dotfiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "photo.jpg").write_text("x")
            (root / ".secret.txt").write_text("x")
            (root / "AlreadyThere").mkdir()
            (root / "AlreadyThere" / "nested.pdf").write_text("x")
            plans = scan_folder(root)
            self.assertEqual([Path(p.source).name for p in plans], ["photo.jpg"])

    def test_collision_is_skipped_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "report.pdf").write_text("new")
            (root / "Documents").mkdir()
            target = root / "Documents" / "report.pdf"
            target.write_text("existing")
            plans = scan_folder(root)
            self.assertEqual(plans[0].status, "skip")
            log = root / "log.json"
            result = execute_cleanup(plans, log)
            self.assertEqual(target.read_text(), "existing")
            self.assertEqual((root / "report.pdf").read_text(), "new")
            self.assertEqual(len(result["moves"]), 0)

    def test_cleanup_and_undo_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            originals = {
                "résumé.pdf": "doc",
                "photo.JPG": "image",
                "setup.exe": "installer",
                "archive.zip": "archive",
                "README": "other",
            }
            for name, content in originals.items():
                (root / name).write_text(content, encoding="utf-8")
            plans = scan_folder(root)
            self.assertEqual(summarize(plans)["Total"], 5)
            log = root / "transaction.json"
            result = execute_cleanup(plans, log)
            self.assertEqual(len(result["moves"]), 5)
            for name in originals:
                self.assertFalse((root / name).exists())
            undo = undo_cleanup(log)
            self.assertEqual(len(undo["restored"]), 5)
            self.assertFalse(log.exists())
            for name, content in originals.items():
                self.assertEqual((root / name).read_text(encoding="utf-8"), content)

    def test_undo_refuses_to_overwrite_new_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = root / "photo.jpg"
            original.write_text("old")
            log = root / "transaction.json"
            execute_cleanup(scan_folder(root), log)
            original.write_text("new file occupying original path")
            result = undo_cleanup(log)
            self.assertEqual(len(result["restored"]), 0)
            self.assertEqual(len(result["skipped"]), 1)
            self.assertEqual(original.read_text(), "new file occupying original path")
            self.assertTrue((root / "Images" / "photo.jpg").exists())


if __name__ == "__main__":
    unittest.main()
