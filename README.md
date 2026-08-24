# Architecture Recovery Engine

MVP determinístico para transformar um repositório Python em uma Architecture
Intermediate Representation (Architecture IR), com evidências rastreáveis e
exportação para JSON, GraphML e Mermaid.

## Grafos e Architecture IR

O analisador produz duas visões. O `Raw Code Graph` preserva arquivos,
módulos, símbolos, imports, chamadas e dependências externas. Cada node possui
uma origem (`first_party`, `third_party`, `standard_library`, `generated` ou
`unknown`). O `Architectural Graph` agrega o código do repositório em
aplicação/componentes e dependências externas em pacotes, sem perder a
referência às edges brutas que justificaram cada relação.

O JSON usa `schema_version` `0.2` e contém `raw_graph`,
`architectural_graph`, `classifications`, `evidence` e `validation`. Os campos
legados `nodes` e `edges` continuam apontando para o Raw Code Graph.

## Instalação

```bash
python -m pip install -e ".[dev]"
```

## Uso local

```bash
architecture-recovery analyze . --output architecture.json --graph architecture.graphml
```

Para inspecionar a fronteira e a origem de cada node:

```bash
architecture-recovery analyze . \
  --classification-report classification.json
```

Por padrão, a standard library é omitida do Architectural Graph e nodes
`unknown`/`generated` são preservados. Esse comportamento pode ser ajustado:

```bash
architecture-recovery analyze . \
  --include-standard-library \
  --exclude-unknown
```

Também é possível escolher a representação principal (`json`, `graphml` ou
`mermaid`):

```bash
architecture-recovery analyze . --format mermaid --output architecture.mmd
```

## Benchmarks determinísticos

As fixtures controladas e seus ground truths ficam em `benchmarks/`. Para
executá-los e gerar métricas de origem, símbolos, edges, contagens e
determinismo:

```bash
python -m benchmarks.runner
```

## Uso remoto

URLs HTTPS, SSH e Git são clonadas com profundidade 1 em um diretório
temporário. A revisão pode ser informada com `--ref` ou `--branch`:

```bash
architecture-recovery analyze https://github.com/org/project.git \
  --branch main --output architecture.json --graph architecture.graphml
```

A IR preserva a origem em `repository.source_url`. Dockerfiles e arquivos
Docker Compose são analisados junto com o código e suas relações de deploy e
dependência aparecem no grafo.

O parser usa Tree-sitter quando disponível. Um fallback baseado no módulo
`ast` da biblioteca padrão permite executar o MVP sem dependências nativas
adicionais.
