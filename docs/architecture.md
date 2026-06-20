# Pipeline architecture

The repository follows a small medallion-style flow: immutable demo inputs are
treated as the raw layer, and only records that pass quality checks enter the
clean layer.

```mermaid
flowchart LR
    subgraph Raw[Raw data layer]
        CSV[CSV files]
        JSON[JSON files]
    end

    CFG[Pipeline configuration]
    EXT[Extractors]
    TRN[Transformation pipeline]
    VAL{Validation gates}
    BAD[Pipeline fails with quality error]
    CLEAN[(Clean data lake<br/>data/clean/*.csv)]

    CSV --> EXT
    JSON --> EXT
    CFG -. selects adapter and steps .-> EXT
    CFG -. defines rules .-> TRN
    EXT --> TRN
    TRN --> VAL
    VAL -->|pass| CLEAN
    VAL -->|fail| BAD
```

## Responsibilities

| Layer | Module | Responsibility |
|---|---|---|
| Extract | `pipeline/extractors.py` | Convert CSV or JSON sources into DataFrames |
| Transform | `pipeline/transformers.py` | Apply ordered, reusable cleaning steps |
| Validate | `pipeline/validators.py` | Enforce schema, null, uniqueness, and range rules |
| Load | `pipeline/loaders.py` | Persist validated records to the clean layer |
| Orchestrate | `pipeline/orchestrator.py` | Run stages and return execution metrics |
| Configure | `pipeline/config.py` | Declare each source without creating another script |
