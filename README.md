# securecomputing

Working with AI on framing secure computing environments: HIPAA and (lower priority) CUI.

## Quick Start

See `PROJECT_OVERVIEW.md` for the master document, glossary, and project structure.

## Generating the PDF Book

All markdown files can be consolidated into a single PDF using Pandoc. The Mermaid diagrams
(in `PROJECT_OVERVIEW.md`) are rendered to images automatically via the `mermaid-filter` pandoc
filter, and a Lua filter (`strip-emoji.lua`) replaces emoji characters that XeLaTeX cannot render.

### Prerequisites (WSL/Ubuntu)

**1. Pandoc and LaTeX**

```bash
sudo apt update
sudo apt install -y pandoc texlive-latex-recommended texlive-fonts-recommended \
  texlive-latex-extra texlive-xetex
```

This is ~500MB on first install. `texlive-xetex` provides the `xelatex` PDF engine which
supports Unicode fonts.

**2. Unicode fonts**

DejaVu Sans provides broad Unicode coverage (checkmarks, box-drawing, arrows, etc.):

```bash
sudo apt install -y fonts-dejavu
```

**3. Node.js, mermaid-cli, and mermaid-filter**

The `mermaid-filter` pandoc filter renders Mermaid diagram code blocks to images during PDF
generation. It depends on `mmdc` (from `@mermaid-js/mermaid-cli`) which uses a headless
Chromium browser under the hood.

```bash
npm install --global @mermaid-js/mermaid-cli mermaid-filter
```

**4. Chromium dependencies for headless rendering**

WSL/Ubuntu minimal installs are missing shared libraries that Chromium (Puppeteer) needs:

```bash
sudo apt install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
  libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
  libpango-1.0-0 libcairo2 libasound2
```

**5. Lua filter for emoji**

The file `strip-emoji.lua` (in this repo) replaces emoji characters ([i], [x], [ ], [~], [!])
with text equivalents before XeLaTeX processes them. No emoji font installation is needed.
The source markdown is unchanged — emoji still render on GitHub.

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

This produces a ~100-page PDF with auto-generated table of contents.

### Alternative: HTML output (no LaTeX needed)

Only pandoc, Node.js, and the mermaid packages are required (skip steps 1–2 and 4 above):

```bash
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
