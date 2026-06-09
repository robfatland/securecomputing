# Appendices

---

## Appendix A: PDF Generation

### Prerequisites (WSL/Ubuntu, one-time)

**1. Pandoc and LaTeX**

```bash
sudo apt update
sudo apt install -y pandoc texlive-latex-recommended texlive-fonts-recommended \
  texlive-latex-extra texlive-xetex
```

**2. Unicode fonts**

```bash
sudo apt install -y fonts-dejavu
```

**3. Node.js, mermaid-cli, and mermaid-filter**

```bash
npm install --global @mermaid-js/mermaid-cli mermaid-filter
```

**4. Chromium dependencies (for headless Mermaid rendering)**

```bash
sudo apt install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
  libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
  libpango-1.0-0 libcairo2 libasound2
```

**5. Puppeteer Chrome path**

The `mermaid-filter` uses Puppeteer which needs to find the Chromium binary. If you get
"Could not find Chromium" errors, set the executable path:

```bash
export PUPPETEER_EXECUTABLE_PATH=$(find ~/.cache/puppeteer -name chrome -type f | head -1)
```

Add to `~/.bashrc` for persistence:

```bash
echo 'export PUPPETEER_EXECUTABLE_PATH=$(find ~/.cache/puppeteer -name chrome -type f | head -1)' >> ~/.bashrc
```

**6. Lua filter for emoji**

The file `strip-emoji.lua` (in this repo) replaces emoji characters with text equivalents
before XeLaTeX processes them. No emoji font installation required.

### Generate PDF Book

```bash
cd ~/securecomputing
pandoc -V geometry:margin=1in \
  -V mainfont="DejaVu Sans" \
  -V sansfont="DejaVu Sans" \
  -V monofont="DejaVu Sans Mono" \
  --pdf-engine=xelatex \
  -H pandoc-header.tex \
  --lua-filter=strip-emoji.lua \
  --lua-filter=table-widths.lua \
  -F mermaid-filter \
  TITLE.md \
  PROJECT_OVERVIEW.md \
  ARCHITECTURE.md \
  GATES.md \
  PHASE0_CHARTER.md \
  RISK_ASSESSMENT.md \
  POLICY_AI_ACCEPTABLE_USE.md \
  POLICY_SUITE.md \
  SYNTHETIC_DATA.md \
  ANALYSIS.md \
  DIAGRAMS.md \
  COST.md \
  COMPLETION.md \
  NISTDocs.md \
  ORGANIZATIONAL_STRUCTURE.md \
  KNOWLEDGE_CHECKS.md \
  APPENDICES.md \
  -o SecureComputing_Book.pdf
```

`TITLE.md` provides the cover page via raw LaTeX (title, preparation credit). The TOC is generated inline within `TITLE.md` rather than via pandoc's `--toc` flag, ensuring correct page ordering.

### Generate HTML (alternative, no LaTeX needed)

Only pandoc, Node.js, and the mermaid packages are required (skip LaTeX and font steps above):

```bash
pandoc --toc --toc-depth=2 --standalone \
  --lua-filter=strip-emoji.lua \
  --lua-filter=table-widths.lua \
  -F mermaid-filter \
  TITLE.md PROJECT_OVERVIEW.md ARCHITECTURE.md GATES.md \
  PHASE0_CHARTER.md RISK_ASSESSMENT.md \
  POLICY_AI_ACCEPTABLE_USE.md POLICY_SUITE.md \
  SYNTHETIC_DATA.md ANALYSIS.md DIAGRAMS.md COST.md COMPLETION.md \
  NISTDocs.md ORGANIZATIONAL_STRUCTURE.md KNOWLEDGE_CHECKS.md \
  APPENDICES.md \
  -o SecureComputing_Book.html
```

---

## Appendix B: Related Repositories and Directories

| Repository / Directory | Purpose |
|------------------------|---------|
| [`securecomputing`](https://github.com/robfatland/securecomputing) | System documentation, CDK infrastructure, analysis code |
| [`securecomputing-datagen`](https://github.com/robfatland/securecomputing-datagen) | Synthetic PHI data generation pipeline (Synthea + custom generators) |
| `~/securecomputing-data/` | Generated synthetic data (not in git); persisted in `s3://securecomputing-persistent-data/` |

### Contents of `securecomputing-data/`

| Subdirectory | Contents | Volume |
|--------------|----------|--------|
| `pd0/` | OMOP CDM v5.4 tables (8 CSVs) + PHI mapping + patient stone assignments | 11,272 patients, ~7.3M rows, ~595 MB |
| `pd1/` | Kidney stone composition CIF files (PXRD + FTIR per specimen) | 14,638 files, ~58 MB |
| `pd2/` | Genomics VCF files (one per patient, stone-correlated variants) | 11,272 files, ~143 MB |
| `pd3/` | Longitudinal lab results CSV (correlated with stone type) | 1 file, 1.47M rows, ~99 MB |

All datasets are linked by synthetic MRN. Total: ~25,900 files, ~896 MB. See `SYNTHETIC_DATA.md` for clinical context and `securecomputing-datagen/BUILD.md` for the generation pipeline.

---

## Appendix C: Document Revision History

| Date | Change |
|------|--------|
| May 2026 | Initial build: Phases 0–2 documented, CDK deployed and verified, synthetic data generated (PD0–PD3), DESTROY/rebuild tested |
| June 2026 | Documentation polish: PDF generation with Mermaid diagrams, emoji handling, page breaks between documents, COMPLETION.md expanded with SP→OS adaptation process |
