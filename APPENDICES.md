# Appendices

---

## Appendix A: PDF Generation

### Install (WSL/Ubuntu, one-time)

```bash
sudo apt update
sudo apt install pandoc texlive-xetex texlive-latex-recommended texlive-fonts-recommended texlive-latex-extra
```

### Generate PDF Book

```bash
cd ~/securecomputing
pandoc --toc --toc-depth=2 -V geometry:margin=1in --pdf-engine=xelatex \
  TITLE.md \
  PROJECT_OVERVIEW.md \
  ARCHITECTURE.md \
  GATES.md \
  PHASE0_CHARTER.md \
  RISK_ASSESSMENT.md \
  POLICY_AI_ACCEPTABLE_USE.md \
  POLICY_SUITE.md \
  SYNTHETIC_DATA.md \
  DIAGRAMS.md \
  COST.md \
  COMPLETION.md \
  NISTDocs.md \
  ORGANIZATIONAL_STRUCTURE.md \
  KNOWLEDGE_CHECKS.md \
  APPENDICES.md \
  -o SecureComputing_Book.pdf
```

`TITLE.md` provides the cover page (title, subtitle "SPEACR", author, date). Pandoc uses its YAML front matter to generate a formatted title page.

### Generate HTML (alternative, no LaTeX needed)

```bash
pandoc --toc --toc-depth=2 --standalone \
  TITLE.md PROJECT_OVERVIEW.md ARCHITECTURE.md GATES.md \
  PHASE0_CHARTER.md RISK_ASSESSMENT.md \
  POLICY_AI_ACCEPTABLE_USE.md POLICY_SUITE.md \
  SYNTHETIC_DATA.md DIAGRAMS.md COST.md COMPLETION.md \
  NISTDocs.md ORGANIZATIONAL_STRUCTURE.md KNOWLEDGE_CHECKS.md \
  APPENDICES.md \
  -o SecureComputing_Book.html
```

---

## Appendix B: Related Repositories

| Repository | Purpose |
|------------|---------|
| `securecomputing` | System documentation, CDK infrastructure, analysis code |
| `securecomputing-datagen` | Synthetic PHI data generation pipeline (~15 pages documentation) |

---

## Appendix C: Document Revision History

| Date | Change |
|------|--------|
| May 2026 | Initial build: Phases 0–2 documented, CDK deployed and verified, synthetic data generated (PD0–PD3), DESTROY/rebuild tested |
