#!/usr/bin/env python3
"""Download real, freely available papers into sample_library/demo_semiconductors/.

    python get_demo_papers.py

The PDFs come straight from where their authors made them free to read (arXiv and
OSTI.gov). They are author versions, so the layout and page numbers differ from the
journal versions. They are downloaded to your computer only: the repository stores
the links, never the papers, because a journal's PDF cannot be shared publicly.

Two more papers in the same set have no free copy that a script can download. If your
institution has access, download them from the DOI links printed at the end and drop
them into the same folder.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import httpx

FOLDER = Path(__file__).resolve().parent / "sample_library" / "demo_semiconductors"
HEADERS = {"User-Agent": "research-mcp-workshop/1.0 (AgentForge workshop)"}

FREE = [
    {"file": "Wong et al. - 2021 - Ultrawide-bandgap semiconductors An overview.pdf",
     "journal": "Journal of Materials Research", "doi": "10.1557/s43578-021-00458-1",
     "url": "https://www.osti.gov/servlets/purl/1883171", "source": "OSTI.gov"},
    {"file": "Woods-Robinson et al. - 2020 - Wide Band Gap Chalcogenide Semiconductors.pdf",
     "journal": "Chemical Reviews", "doi": "10.1021/acs.chemrev.9b00600",
     "url": "https://arxiv.org/pdf/1910.08153", "source": "arXiv"},
    {"file": "Yue et al. - 2020 - Spin‐Gapless Semiconductors.pdf",
     "journal": "Small", "doi": "10.1002/smll.201905155",
     "url": "https://arxiv.org/pdf/2006.06883", "source": "arXiv"},
]

NO_FREE_COPY = [
    ("Hao et al. 2021, Oxygen Vacant Semiconductor Photocatalysts, Advanced Functional Materials",
     "10.1002/adfm.202100919"),
    ("Wang et al. 2020, Flexoelectronics of centrosymmetric semiconductors, Nature Nanotechnology",
     "10.1038/s41565-020-0700-y"),
]


def download(paper: dict, folder: Path) -> str:
    """Download one paper. Returns a short status line."""
    target = folder / paper["file"]
    if target.exists():
        return f"already here   {paper['file']}"
    response = httpx.get(paper["url"], headers=HEADERS, timeout=60, follow_redirects=True)
    response.raise_for_status()
    if not response.content.startswith(b"%PDF"):
        raise ValueError("the server did not send a PDF")
    target.write_bytes(response.content)
    return f"downloaded     {paper['file']}  ({len(response.content) // 1024} KB, {paper['source']})"


def main(folder: Path = FOLDER) -> int:
    folder.mkdir(parents=True, exist_ok=True)
    print(f"Downloading free versions into {folder}\n")
    failures = 0
    for i, paper in enumerate(FREE):
        if i and paper["source"] == "arXiv":
            time.sleep(3)                      # arXiv asks automated clients to pause between requests
        try:
            print("  " + download(paper, folder))
        except (httpx.HTTPError, ValueError) as err:
            failures += 1
            print(f"  FAILED         {paper['file']}: {err}\n"
                  f"                 Download it by hand from {paper['url']}")
    print("\nNot downloadable by script (no free copy). If your institution has access:")
    for title, doi in NO_FREE_COPY:
        print(f"  - {title}\n    https://doi.org/{doi}")
    print("\nThese papers are now part of sample_library, so search finds them alongside the practice papers.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
