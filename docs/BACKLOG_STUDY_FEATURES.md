# Features to Add Later - Study Materials & Speed Runs

## Overview
These valuable features from the old RAG system should be integrated into the Unified GraphRAG after core implementation is complete.

## Features to Preserve

### 1. Speed Run Generation (60-Second Mastery)
- Domain-specific lightning reviews
- Memory tricks and associations
- Rapid-fire format for last-minute prep
- Example format:
  ```
  Domain 1 Lightning Review ⚡
  Supervised = Labeled data = Email spam filter
  Unsupervised = No labels = Customer grouping
  ```

### 2. TREE Method Visual Notes
- Based on "The Ultimate Mind Map Tutorial"
- Visual note-taking methodology
- Central concepts with branching relationships
- Picture-worth-thousand-words approach

### 3. Study Material Auto-Generation Suite
- **Comprehensive Study Guide** - Domain-by-domain breakdown
- **Speed Run** - 60-second mastery checks
- **Mind Maps** - Visual learning using TREE methodology
- **Flashcards** - Interactive learning cards
- **Quick Reference** - One-page summary
- **Visual Diagrams** - Integration with diagram agents

### 4. Auto-Generation Features
- Zero CLI required
- Automatic material creation when KB ready
- Real-time progress tracking
- Multiple format support
- Download individual or bulk

## Implementation Notes

These will be added as methods to UnifiedGraphRAG:

```python
async def generate_speed_run(self, domain: str) -> SpeedRunContent
async def generate_tree_notes(self, topic: str) -> TreeNotes  
async def generate_study_materials(self, domain: str) -> StudyMaterials
```

## Priority
LOW - Add after core platform is operational and API layer is complete.

These are nice-to-have features that enhance the learning experience but are not critical for MVP.
