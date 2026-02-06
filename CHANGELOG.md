# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-02-06

### Added
- **SRT Processing Tools**: Complete SRT file processing and analysis system
  - `srt_processor.py`: Core SRT parsing and processing tool
  - `test_srt_processing.py`: Comprehensive test suite for SRT processing
  - SRT processing documentation and quick start guide

- **Novel Segmentation System**: Advanced novel chapter processing and segmentation
  - `novel_processor.py`: Novel text processing and chapter extraction
  - `novel_chapter_processor.py`: Detailed chapter analysis and segmentation
  - `introduction_validator.py`: LLM-based introduction validation
  - Novel segmentation methodology documentation

- **Project Migration to V2**: Complete project structure overhaul
  - Migration workflow for legacy projects
  - Automated data archiving system
  - Migration report generation
  - Archived PROJ_002 and PROJ_003 with full data preservation

- **Optimization Tools**: New A/B testing and alignment optimization
  - `ab_tester.py`: A/B testing framework for optimization experiments
  - Annotation workflow for alignment optimization
  - Demo annotation system

- **Comprehensive Documentation**:
  - SRT Processing Design (`docs/architecture/SRT_PROCESSING_DESIGN.md`)
  - Novel Segmentation Methodology (`docs/NOVEL_SEGMENTATION_METHODOLOGY.md`)
  - AI Training Tutorial (`docs/AI_TRAINING_TUTORIAL.md`)
  - Methodology Summary (`docs/METHODOLOGY_SUMMARY.md`)
  - Multiple maintenance and implementation guides

- **Prompt Templates**: Externalized prompts for better maintainability
  - Introduction extraction and validation prompts
  - Novel segmentation prompts
  - SRT script processing prompts (with/without novel)

### Changed
- Updated `DEV_STANDARDS.md` with enhanced coding standards
- Improved `PROJECT_STRUCTURE.md` with V2 structure details
- Enhanced `logic_flows.md` with new workflow diagrams
- Refactored `config.py` for better configuration management
- Updated optimization module structure

### Fixed
- LLM-based validation improvements
- Introduction filtering accuracy enhancements
- Hybrid validation strategy implementation

### Migration Notes
- All existing projects should be migrated using `scripts/run_migration.py`
- Legacy data is preserved in `data/projects_archive_20260205/`
- Migration report available in `data/migration_report_20260205.json`

---

## [1.0.0] - Previous Version

### Features
- Initial implementation of ingestion workflow
- Basic alignment and analysis tools
- Core agent and tool architecture
- Production script generation
