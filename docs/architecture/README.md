# Architecture Recovery Engine — Architecture Context

## Current development reports

The following documents summarize the implementation state and are useful for
contributors or coding agents. They are status reports, not architectural
decisions; consult accepted ADRs first when interpreting conflicts.

- [Algorithm Development Status](ALGORITHM_STATUS.md)
- [Raw Graph Semantic Status](RAW_GRAPH_STATUS.md)
- [Benchmark and Quality Status](BENCHMARK_STATUS.md)
- [Algorithm Next Steps](NEXT_STEPS.md)
- [Algorithm Refinement Investigation](ALGORITHM_REFINEMENT_INVESTIGATION.md)

## Purpose

This directory contains the architectural knowledge governing the Architecture Recovery Engine.

The project is not intended to be merely a diagram generator.

Its purpose is to perform software architecture recovery from source repositories using deterministic program analysis, graph construction, evidence aggregation and architectural inference.

The central principle is:

> Analysis discovers and justifies architecture. Rendering only visualizes an already validated architectural representation.

---

# System Goal

Given a software repository, the engine should progressively determine:

```text
Repository
    ↓
Technology Stack
    ↓
Code Structure
    ↓
Program Relationships
    ↓
Infrastructure Relationships
    ↓
Architectural Components
    ↓
Architectural Hypotheses
    ↓
Architecture IR
    ↓
Visualization
```

The system should be able to identify or infer concepts such as:

* languages;
* runtimes;
* frameworks;
* databases;
* infrastructure;
* modules;
* services;
* repositories;
* controllers;
* APIs;
* external systems;
* deployment units;
* architectural patterns.

Architectural patterns may eventually include:

```text
Layered Architecture
MVC
MVT
Monolith
Modular Monolith
Microservices
Hexagonal Architecture
Clean Architecture
Event-Driven Architecture
Hybrid Architectures
```

Architecture classification is not expected to always produce a single answer.

Real repositories may contain multiple architectural styles.

---

# Fundamental Principle

The project deliberately separates observation from interpretation.

Conceptually:

```text
Source Code
     ↓
Observed Program Facts
     ↓
Raw Code Graph
     ↓
Aggregation
     ↓
Architectural Facts
     ↓
Architectural Graph
     ↓
Pattern Inference
     ↓
Architectural Hypotheses
```

An architectural hypothesis must not rewrite the observed program facts that support it.

---

# Graph Model

The project uses a typed directed graph model.

Formally:

```text
G = (V, E)
```

where:

```text
V = typed nodes
E = typed directed relationships
```

Nodes and edges may contain properties including:

* source location;
* origin;
* confidence;
* evidence;
* status;
* architectural role.

Example low-level relationships:

```text
CALLS
IMPORTS
EXTENDS
IMPLEMENTS
INSTANTIATES
READS
WRITES
```

Example architectural relationships:

```text
DEPENDS_ON
USES
ROUTES_TO
QUERIES
PUBLISHES
CONSUMES
CONNECTS_TO
DEPLOYS
```

The vocabulary is expected to evolve carefully.

---

# Abstraction Levels

The system may represent several levels:

```text
Repository
System / Application
Component
Module / Package
File
Class / Interface
Function / Method
Statement / AST Node
```

Lower levels primarily provide evidence.

Higher levels primarily provide architectural understanding.

A useful architecture diagram should normally operate at higher abstraction levels.

---

# Evidence

Evidence is a first-class concept.

Important claims should answer:

```text
Why does the engine believe this?
```

Potential evidence sources include:

```text
AST
IMPORT
SYMBOL_RESOLUTION
CALL_GRAPH
DEPENDENCY_FILE
CONFIGURATION
DOCKERFILE
DOCKER_COMPOSE
KUBERNETES
TERRAFORM
FRAMEWORK_CONVENTION
DIRECTORY_STRUCTURE
CI_CONFIGURATION
RUNTIME_CONFIGURATION
DOCUMENTATION
```

Future probabilistic reasoning may add:

```text
LLM_INFERENCE
```

but LLM inference must remain distinguishable from deterministic observation.

---

# Confidence

Confidence expresses uncertainty.

It must not be used to disguise inference as observation.

For example:

```text
status = OBSERVED
confidence = 1.0
```

and:

```text
status = INFERRED
confidence = 0.82
```

represent different semantic states.

`UNKNOWN` is valid when evidence is insufficient.

---

# Architecture IR

Architecture IR is the stable structured representation consumed by downstream systems.

Potential consumers include:

* validators;
* renderers;
* architecture reasoning engines;
* LLM reasoning;
* graph databases;
* APIs;
* architecture comparison tools.

The IR should not be designed around the needs of a single renderer.

---

# Renderer Boundary

Renderers consume architecture.

They do not discover architecture.

A renderer must not create an edge because drawing the graph would look better with one.

If a node is disconnected, the analysis/validation stages must decide whether that is:

* valid;
* unknown;
* external;
* incomplete analysis;
* an error.

The renderer must preserve that truth.

---

# Deterministic and Probabilistic Analysis

The project distinguishes deterministic analysis from probabilistic interpretation.

## Deterministic

Examples:

```text
AST parsing
imports
direct calls
dependency manifests
Docker Compose services
graph cycles
connected components
```

## Probabilistic / Inferential

Examples:

```text
"This resembles Clean Architecture."

"These clusters may represent bounded contexts."

"This repository is probably a modular monolith."

"These deployment units are likely microservices."
```

The latter may eventually use rules, statistical models or LLMs.

---

# Architecture Documentation

This directory uses three mechanisms.

## DECISIONS.md

Provides the index of current architectural decisions.

## ANALYSIS_LOG.md

Contains chronological observations and experiments.

Entries are not automatically authoritative.

## ADRs

Architecture Decision Records document durable architectural decisions.

Statuses:

```text
Proposed
Accepted
Deprecated
Superseded
Rejected
```

Only `Accepted` ADRs are authoritative unless a newer accepted ADR explicitly supersedes them.

---

# Current High-Level Pipeline

The intended pipeline is:

```text
Repository Acquisition
        ↓
Repository Scanner
        ↓
Stack Detection
        ↓
Parsing
        ↓
Symbol Resolution
        ↓
Raw Code Graph
        ↓
Source Origin Classification
        ↓
Graph Aggregation
        ↓
Architectural Graph
        ↓
Architecture IR
        ↓
Validation
        ↓
Architecture Inference
        ↓
LLM Reasoning (future / optional)
        ↓
Renderer
```

This pipeline may evolve through future ADRs.

---

# Current Development Strategy

Development should remain incremental.

The initial focus is Python.

Initial framework targets include:

```text
FastAPI
Django
Flask
```

Infrastructure analysis begins with:

```text
Dockerfile
docker-compose
GitHub Actions
```

The project should not attempt perfect multi-language semantic analysis prematurely.

The priority is a deterministic, explainable and testable pipeline.

---

# Benchmark Philosophy

Architecture recovery requires ground truth.

Controlled fixture repositories should be maintained for cases such as:

```text
simple Python application
FastAPI layered application
Django MVT application
Flask application
layered monolith
modular monolith
clean architecture
hexagonal architecture
REST microservices
event-driven microservices
ambiguous architecture
circular dependencies
```

Each benchmark should eventually define expected:

* stack;
* components;
* important relationships;
* architecture;
* intentionally ambiguous facts.

The benchmark is intended to measure progress rather than merely demonstrate output.
