# securecomputing

Working with AI on framing secure computing environments: HIPAA and (lower priority) CUI.

## Quick Start

See `PROJECT_OVERVIEW.md` for the master document, glossary, and project structure.

## Generating the PDF Book

All markdown files can be consolidated into a single PDF using Pandoc:

### Install (WSL/Ubuntu)

```bash
sudo apt update
sudo apt install pandoc texlive-latex-recommended texlive-fonts-recommended texlive-latex-extra texlive-xetex
npm install --global @mermaid-js/mermaid-cli mermaid-filter
```

### Generate PDF

```bash
pandoc --toc --toc-depth=2 -V geometry:margin=1in \
  -V mainfont="DejaVu Sans" -V monofont="DejaVu Sans Mono" \
  --pdf-engine=xelatex \
  --lua-filter=strip-emoji.lua \
  -F mermaid-filter \
  PROJECT_OVERVIEW.md \
  ARCHITECTURE.md \
  GATES.md \
  PHASE0_CHARTER.md \
  RISK_ASSESSMENT.md \
  COST.md \
  POLICY_AI_ACCEPTABLE_USE.md \
  POLICY_SUITE.md \
  SYNTHETIC_DATA.md \
  NISTDocs.md \
  ORGANIZATIONAL_STRUCTURE.md \
  KNOWLEDGE_CHECKS.md \
  COMPLETION.md \
  -o SecureComputing_Book.pdf
```

This produces a ~100-page PDF with auto-generated table of contents. Requires ~500MB disk for the LaTeX packages on first install.

### Alternative: HTML output (no LaTeX needed)

```bash
sudo apt install pandoc
pandoc --toc --toc-depth=2 --standalone \
  --lua-filter=strip-emoji.lua \
  -F mermaid-filter \
  PROJECT_OVERVIEW.md ARCHITECTURE.md GATES.md \
  PHASE0_CHARTER.md RISK_ASSESSMENT.md COST.md \
  POLICY_AI_ACCEPTABLE_USE.md POLICY_SUITE.md \
  SYNTHETIC_DATA.md NISTDocs.md \
  ORGANIZATIONAL_STRUCTURE.md KNOWLEDGE_CHECKS.md \
  COMPLETION.md \
  -o SecureComputing_Book.html
```

## Repository Structure

See the Project Documents table at the top of `PROJECT_OVERVIEW.md` for a full listing of documents and their purposes.

## Related Repositories

- [`securecomputing-datagen`](https://github.com/robfatland/securecomputing-datagen) — Synthetic PHI data generation tooling
