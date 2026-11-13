"""Create local private grading archive; never upload or publish."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from .prepare import ROOT

def main():
    output = ROOT / "submission_2A202603688_PRIVATE.zip"
    files = []
    for p in ROOT.iterdir():
        if p.is_file() and (p.suffix in {".md",".txt",".ps1"} or p.name==".gitignore"):
            files.append(p)
    for folder in ("starter","data","benchmark","configs","results","artifacts","report","docs","tests","assets"):
        for p in (ROOT/folder).rglob("*"):
            if not p.is_file() or "__pycache__" in p.parts or ".venv" in p.parts:
                continue
            if p.name.startswith(".env") and p.name!=".env.example":
                continue
            if p.name=="submission_package.json" or p.suffix==".pyc":
                continue
            if p.name.startswith("~$") or p.suffix in {".tmp", ".bak"}:
                continue
            if p.parent == ROOT / "artifacts/presentation" and (
                p.suffix.lower() in {".png", ".jpg"} or p.name.endswith("_Demo.pptx")
            ):
                continue
            if p.relative_to(ROOT).as_posix() in {
                "starter/preview_ingestion.py", "starter/preview_normalization.py",
                "starter/scripts/inspect_pdf.py", "starter/scripts/create_slide.py",
            }:
                continue
            files.append(p)
    notice = ("PRIVATE EDUCATIONAL SUBMISSION — local archive, not uploaded.\n"
              "Contains student-supplied PDF and derived text for grading.\n"
              "Public redistribution rights and original URL are not verified.\n"
              "AI-assisted qualitative labels require student confirmation.\n")
    with ZipFile(output,"w",compression=ZIP_DEFLATED) as archive:
        archive.writestr("PRIVATE_SUBMISSION.txt",notice)
        for path in sorted(set(files)):
            archive.write(path,path.relative_to(ROOT))
    with ZipFile(output) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert "data/raw/tai_lieu.pdf" in names
        assert "results/traces.jsonl" in names
        assert not any("/.venv/" in n or "/.cache/" in n or n.endswith("/.env") for n in names)
    info = {"filename":output.name,"bytes":output.stat().st_size,
            "sha256":hashlib.sha256(output.read_bytes()).hexdigest(),"files":len(names),
            "uploaded":False,"git_commit_created":False}
    (ROOT/"artifacts/submission_package.json").write_text(json.dumps(info,indent=2),encoding="utf-8")
    print(json.dumps(info,indent=2))

if __name__ == "__main__":
    main()
