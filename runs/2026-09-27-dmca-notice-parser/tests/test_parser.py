import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLES = REPO_ROOT / "samples"
SCRIPT = REPO_ROOT / "dmca_notice_parser.py"

sys.path.insert(0, str(REPO_ROOT))

from dmca_notice_parser import parse_notice  # noqa: E402


def read_sample(name):
    return (SAMPLES / name).read_text(encoding="utf-8")


EXPECTED = {
    "notice1.txt": {
        "claimant_name": "Marguerite Delacroix-Ferris",
        "claimant_email": "mdelacroix@example.org",
        "infringing_urls": [
            "http://cdn.example.net/uploads/2026/atlas-chapter-one.pdf",
            "http://cdn.example.net/uploads/2026/atlas-chapter-two.pdf",
            "http://mirror.example.net/files/atlas-chapter-one.pdf",
        ],
        "original_work_urls": [
            "https://www.example.org/catalog/atlas-of-forgotten-rivers",
            "https://www.example.org/catalog/atlas-of-forgotten-rivers/preview",
        ],
        "date": "2026-03-05",
    },
    "notice2.txt": {
        "claimant_name": "Desmond Achterberg",
        "claimant_email": "desmond.achterberg@example.com",
        "infringing_urls": [
            "https://files.example.net/share/nightjar-sessions.zip",
            "https://files.example.net/share/nightjar-sessions-part2.zip",
        ],
        "original_work_urls": [
            "https://achterberg-sound.example.com/releases/nightjar-sessions",
        ],
        "date": "2026-03-05",
    },
    "notice3.txt": {
        "claimant_name": "Yolanda Pritchett-Osei",
        "claimant_email": "legal@pritchett-osei.example.org",
        "infringing_urls": [
            "https://gallery.example.net/albums/kepler-bay/lanterns-01.jpg",
            "https://gallery.example.net/albums/kepler-bay/lanterns-02.jpg",
            "http://blog.example.net/2026/02/kepler-bay-photo-dump/",
        ],
        "original_work_urls": [
            "https://pritchett-osei.example.org/portfolio/kepler-bay",
            "https://pritchett-osei.example.org/shop/prints/lanterns-01",
        ],
        "date": "2026-11-14",
    },
}


def test_notice1_all_fields():
    assert parse_notice(read_sample("notice1.txt")) == EXPECTED["notice1.txt"]


def test_notice2_all_fields():
    assert parse_notice(read_sample("notice2.txt")) == EXPECTED["notice2.txt"]


def test_notice3_all_fields():
    assert parse_notice(read_sample("notice3.txt")) == EXPECTED["notice3.txt"]


def test_urls_are_classified_per_url_not_per_line():
    text = (
        "I am the owner of the copyrighted work being infringed at "
        "https://bad.example/x\n"
    )
    result = parse_notice(text)
    assert result["infringing_urls"] == ["https://bad.example/x"]
    assert result["original_work_urls"] == []


def test_infringement_stem_switches_back_to_infringing():
    text = (
        "Original work: https://good.example/o\n"
        "Infringement: https://bad.example/x\n"
    )
    result = parse_notice(text)
    assert result["infringing_urls"] == ["https://bad.example/x"]
    assert result["original_work_urls"] == ["https://good.example/o"]


def test_url_before_any_cue_follows_the_nearest_cue_to_its_right():
    text = "https://x.example is an infringing copy of my copyrighted work\n"
    result = parse_notice(text)
    assert result["infringing_urls"] == ["https://x.example"]
    assert result["original_work_urls"] == []


def test_original_url_label_switches_to_original_bucket():
    assert parse_notice("Original URL: https://example.org/mine")["original_work_urls"] == [
        "https://example.org/mine"
    ]


def test_signoff_block_supplies_name_when_unlabelled():
    text = (
        "To whom it may concern,\n"
        "\n"
        "Please remove the infringing upload described below.\n"
        "\n"
        "Regards,\n"
        "Hortense Vaillancourt\n"
    )
    assert parse_notice(text)["claimant_name"] == "Hortense Vaillancourt"


def test_signoff_followed_by_slash_s_strips_the_marker():
    text = (
        "Please remove the infringing upload described below.\n"
        "\n"
        "Sincerely,\n"
        "/s/ Jane Doe\n"
    )
    assert parse_notice(text)["claimant_name"] == "Jane Doe"


def test_empty_text():
    assert parse_notice("") == {
        "claimant_name": None,
        "claimant_email": None,
        "infringing_urls": [],
        "original_work_urls": [],
        "date": None,
    }


def test_garbage_text_does_not_crash():
    garbage = "\x00\x01 !!! ???\n<<<>>> \n\t\t 42 %%% åß∂\n/////\n"
    assert parse_notice(garbage) == {
        "claimant_name": None,
        "claimant_email": None,
        "infringing_urls": [],
        "original_work_urls": [],
        "date": None,
    }


def test_unlabelled_text_with_urls_but_no_sections_defaults_to_infringing():
    result = parse_notice("please look at https://example.com/a and https://example.com/b")
    assert result["infringing_urls"] == [
        "https://example.com/a",
        "https://example.com/b",
    ]
    assert result["original_work_urls"] == []


def test_alternate_date_formats():
    assert parse_notice("Date: 5 March 2026")["date"] == "2026-03-05"
    assert parse_notice("Date: March 5, 2026")["date"] == "2026-03-05"
    assert parse_notice("Date: 2026-03-05")["date"] == "2026-03-05"
    assert parse_notice("Date: 03/05/2026")["date"] == "2026-03-05"
    assert parse_notice("Date: 2026-03-05T09:12:00Z")["date"] == "2026-03-05"


def test_invalid_date_is_null():
    assert parse_notice("Date: sometime next week")["date"] is None
    assert parse_notice("Date: 2026-13-45")["date"] is None


def test_cli_outputs_json_for_each_sample():
    for name, expected in EXPECTED.items():
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), str(SAMPLES / name)],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stderr
        assert json.loads(proc.stdout) == expected


def test_cli_strips_utf8_bom_from_first_line(tmp_path):
    notice = tmp_path / "bom-notice.txt"
    notice.write_text(
        "Claimant: Jane Doe\nEmail: jane@example.org\n",
        encoding="utf-8-sig",
    )
    assert notice.read_bytes().startswith(b"\xef\xbb\xbf")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(notice)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result["claimant_name"] == "Jane Doe"
    assert result["claimant_email"] == "jane@example.org"


def test_cli_missing_file_exits_1(tmp_path):
    missing = tmp_path / "does-not-exist.txt"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(missing)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    assert proc.stdout == ""
    assert proc.stderr.strip()


def test_cli_without_arguments_exits_1():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    assert "usage" in proc.stderr.lower()
