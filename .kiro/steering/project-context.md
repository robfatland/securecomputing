---
inclusion: auto
---

# SPEACR Project Context

## What This Is

SPEACR (Synthetic PHI Environment on AWS for Clinical Research) is a demonstrator/template for building HIPAA-compliant research computing infrastructure on AWS. It combines organizational controls (policies, roles, training, risk assessment) with technical controls (CDK infrastructure, encryption, monitoring, AI gatekeeper) and includes a working synthetic data pipeline.

## Repository Structure

Two repositories + one data folder:

- `~/securecomputing` — Main repo: documentation (~120 pages), CDK infrastructure code, analysis notebooks
- `~/securecomputing-datagen` — Data generation code: Synthea-based pipeline producing PD0–PD3
- `~/securecomputing-data` — Generated output (not in git): 896 MB synthetic data; also in `s3://securecomputing-persistent-data/`

## Key Documents

- `PROJECT_OVERVIEW.md` — Master document: glossary, phases, gates, scenario, to-do list
- `ARCHITECTURE.md` — Technical design: VPC, IAM, KMS, compute, monitoring, cost, Blank Slate Rule
- `infrastructure/README.md` — CDK deploy/destroy procedures, build guide, IDE access
- `COMPLETION.md` — What's built vs. what a real project must add
- `securecomputing-datagen/BUILD.md` — Data generation pipeline (Steps 1–12)

## Conventions

- Template markers: `[!] **TEMPLATE:**` and `[i] **GENERIC:**` flag sections needing customization
- Development tracks: Track A (datagen), Track B (CDK infrastructure), Track C (analysis code)
- Three lifecycle modes: HIBERNATE (pause), DECOMMISSION (HIPAA end-of-life), DESTROY (blank slate)
- `destroy_mode=True` in CDK — development default; no retention, cheap instances
- PI name: Dr. D.R. Smith; institutions: UW (university), FH (collaborator healthcare facility)

## Current Status (as of June 2026)

- Documentation: ~95% complete
- Data generation (Track A): Complete — all generators working, 25,932 files produced
- Infrastructure (Track B): CDK code written, deployed and verified, DESTROY tested (blank slate confirmed May 2026)
- Analysis (Track C): ~5% — one example notebook exists; no Docker pipeline or gatekeeper Lambda yet
- AWS infrastructure is currently DESTROYED (not running)

## Synthetic Data (PD0–PD3)

- PD0: OMOP CDM EHR (11,272 patients, 7.3M rows)
- PD1: Kidney stone PXRD+FTIR (14,638 CIF files)
- PD2: Genomics VCF (11,272 files, 10 stone-associated genes)
- PD3: Lab results (1.47M rows, correlated with stone type)
- All linked by synthetic MRN; clinically coherent (stone type drives genomics + labs)

## Working from Multiple Machines

Pull repos from GitHub + data from S3:
```
git clone https://github.com/robfatland/securecomputing.git ~/securecomputing
git clone https://github.com/robfatland/securecomputing-datagen.git ~/securecomputing-datagen
aws s3 sync s3://securecomputing-persistent-data/ ~/securecomputing-data/
```

No Synthea, Java, or Athena vocabularies needed on additional machines.
