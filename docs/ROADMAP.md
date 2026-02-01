# Deal Intelligence Platform (The Brain) — Roadmap

## Overview

This project focuses on **high-level reasoning, knowledge synthesis, and multi-modal analysis**. It serves as the "Brain" that ingests vast amounts of unstructured data (documents, calls, briefings) and converts them into structured strategic intelligence.

---

## The Cognitive Engine

In the modern AI landscape, "RAG" has evolved into **Cognitive Architectures**. We are not just retrieving text; we are building a dynamic knowledge model of the business.

- **From Vector Search to GraphRAG**: Understanding relationships between entities (People, Companies, Deals).
- **Multi-Modal Native**: Treating audio, video (slides), and text as equal citizens.
- **Agentic Reasoning**: Using specialized agents for deep research, not just summarization.

---

## Roadmap Status

| Milestone | Focus | Status |
|-----------|-------|:------:|
| Phase 1: Foundation | | |
| M0: Core Infrastructure | Architecture | ✅ |
| M1: Use Case Definition | Strategy | ✅ |
| M2: Vector Database | Memory | ✅ |
| M3: Retriever Agent | RAG | ✅ |
| M4: Multi-Agent Orchestration | Coordination | ✅ |
| Phase 2: Advanced Cognition | | |
| M5: Knowledge Graph Integration | Reasoning | ⏳ |
| M6: Graph-Enhanced UI | interface | ⏳ |
| Phase 3: Perception (Voice & Vision) | | |
| M7: Audio Intelligence & Playback | STT | ⏳ |
| M8: Visual Intelligence & Slides | Vision | ⏳ |
| Phase 4: Delivery & Quality | | |
| M9: Behavioral NLP & Timeline | Analysis | ⏳ |
| M10: Strategic Dashboard | Experience | ⏳ |
| M11: Agentic Evaluation | Quality | ⏳ |

---

## Detailed Milestones

### Phase 2: Advanced Cognition

**Goal:** Move beyond simple text retrieval to deep structural understanding and visual reasoning.

#### Milestone 5: Knowledge Graph (GraphRAG)
*Vectors find existing text, Graphs find hidden connections.*
- [ ] Implement a Graph Database (Neo4j or simple NetworkX memory)
- [ ] Extract nodes: `Person`, `Company`, `Product`, `Objection`
- [ ] **Graph-enhanced Retrieval**: "Find deals where *Pricing* was an objection involving *Competitor X*"
- [ ] Integration with Microsoft GraphRAG concepts

#### Milestone 6: Cognitive Interface (Graph Explorer)
*Visualizing the relationships discovered by the brain.*
- [ ] Interactive Node-Link Diagram UI
- [ ] Contextual sidebar for "Entity Deep Dive"
- [ ] Visual query builder (filtering by relationship types)

### Phase 3: Perception (Voice & Vision)

**Goal:** Turn unstructured multi-modal data into structured, navigable insights.

#### Milestone 7: Audio Intelligence & Playback
- [ ] **Whisper Integration**: Transcription & Speaker Diarization
- [ ] **Click-to-Play UI**: Synchronized transcript with audio seeker
- [ ] Speaker highlights and automated call segmentation

#### Milestone 8: Visual Intelligence & Slide Analysis
- [ ] GPT-4o Vision integration for OCR and Frame Description
- [ ] **Slide Navigator UI**: Grid view of slides extracted from video
- [ ] Correlation of "Slide Shown" with Transcript timestamps

### Phase 4: Delivery & Quality

**Goal:** Synthesize all intelligence into an actionable executive experience.

#### Milestone 9: Behavioral NLP & Deal Timeline
- [ ] Sentiment Analysis per speaker & NER extraction
- [ ] **Interactive Timeline UI**: Visual history of sentiment shifts and key events
- [ ] Topic modeling segments displayed on the seeker bar

#### Milestone 10: The Strategic Dashboard
*The unified experience for deal intelligence.*
- [ ] **Briefing View**: Automated pre-meeting research
- [ ] **Debrief View**: Post-meeting analysis ("What did we miss?")
- [ ] Streamlit (or Next.js) implementation of the full suite

#### Milestone 11: Agentic Evaluation (Quality Assurance)
- [ ] Implement **Ragas** or **DeepEval** framework
- [ ] **Quality Leaderboard UI**: Tracking agent performance over time
- [ ] Automated regression testing for retrieval quality