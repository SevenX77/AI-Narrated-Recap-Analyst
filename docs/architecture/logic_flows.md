# System Architecture & Logic Flows

## Overview
This document serves as the single source of truth for the system's logic and data flow.

## Core Components

### 1. Project Management
- **Project Index**: `data/project_index.json` maps source folders to unique IDs (e.g., `PROJ_001`).
- **Source Data**: Located in `分析资料/` (Analysis Data), organized by Novel Name.
- **Project Data**: Located in `data/projects/PROJ_XXX/`. Stores all persistent artifacts including raw text, alignment maps, analysis results, and generated scripts.
- **System Output**: Located in `output/`. Stores system logs (`app.log`) and operation history (`operation_history.jsonl`).

### 2. Agent Responsibilities
- **Analyst (`src.agents.deepseek_analyst`)**: 
  - **Role**: Understanding & Extraction.
  - **Input**: Raw Text (Novel or Script).
  - **Output**: Structured Events (SVO), Characters, Scenes.
  - **Note**: Does NOT know about alignment or script generation logic.
  - **Prompts**: Managed in `src/prompts/analyst.yaml`.
- **Writer (`src.agents.deepseek_writer`)**: 
  - **Role**: Creative Writing.
  - **Input**: Novel Context (Chapter-level), Analysis Data.
  - **Output**: Recap Script (JSON/Markdown).
- **Alignment Engine (`src.modules.alignment.deepseek_alignment_engine`)**: 
  - **Role**: Mapping & Correlation.
  - **Input**: Novel Events, Script Events.
  - **Output**: Alignment Map (Script Segment -> Novel Chapters).
  - **Feature**: `aggregate_context` converts map to full text context.
  - **Prompts**: Managed in `src/prompts/alignment.yaml`.
- **Feedback Agent (`src.agents.feedback_agent`)**:
  - **Role**: Evaluation & Methodology Extraction.
  - **Input**: Alignment Results.
  - **Output**: Feedback Report & Methodology Update.
  - **Prompts**: Managed in `src/prompts/feedback.yaml`.

### 3. Data Versioning Strategy
- **Principle**: "Latest Pointer + Timestamped Versions".
- **Implementation**: `src.core.artifact_manager.ArtifactManager`.
- **Structure**:
  ```text
  data/projects/PROJ_001/alignment/
  ├── alignment_v20260203_1000.json  # Historical Version
  ├── alignment_v20260203_1200.json  # Latest Version
  └── alignment_latest.json          # Pointer (Copy of latest)
  ```
- **Usage**: Downstream modules (Writer) read `*_latest.json` by default, ensuring stability while preserving history.

## Workflows

### Workflow 1: Ingestion & Alignment (One-Time Setup)
*Executed when a new project is added.*

1.  **Project Registration**:
    - Scan `分析资料/`.
    - Assign `PROJ_XXX` ID.
    - Create entry in `project_index.json`.
    - **Ingestion**: Copy raw data to `data/projects/PROJ_XXX/raw/`.
2.  **Novel Analysis**:
    - Read `novel.txt`.
    - Analyst extracts `Novel Events` (Chapter-wise).
    - Cache results using `ArtifactManager`.
3.  **Script Analysis**:
    - Read `*.srt` files (Ground Truth).
    - Analyst extracts `Script Events` (Time-segment-wise).
4.  **Alignment**:
    - Alignment Engine maps `Script Events` to `Novel Events`.
    - Output `alignment.json`: Defines which Novel Chapters correspond to which Script Segments.
    - **Granularity**: Event-to-Event matching, but Context is aggregated at Chapter level.

### Workflow 2: Training Workflow (`src.workflows.training_workflow.py`)
*Executed to train/optimize the Writer Agent.*

1.  **Initialization**:
    - Inputs: Novel Path, SRT Folder, Workspace Directory.
    - Agents: Analyst, Alignment Engine, Feedback Agent.
2.  **Data Processing**:
    - **Novel**: Reads novel text -> Splits by chapter -> Extracts events (Cached).
    - **Script**: Reads SRTs -> Splits by time/block -> Extracts events.
3.  **Alignment**:
    - Aligns Script Events with Novel Events using `DeepSeekAlignmentEngine`.
4.  **Feedback & Optimization**:
    - `FeedbackAgent` analyzes the alignment.
    - Generates `feedback_report.json` (Score, Issues, Suggestions).
    - Updates `methodology_v1.txt` with extracted insights.

### Workflow 3: Production Generation
*Executed to generate scripts for new novels.*

1.  **Analysis**: Analyst extracts events and scene breakdown from new novel.
2.  **Planning**: Planner (Future) or Logic determines pacing.
3.  **Writing**: Writer generates script chunk by chunk.

---
*Last Updated: 2026-02-03 12:30*
