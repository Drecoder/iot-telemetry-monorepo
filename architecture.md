flowchart TD
    %% Inbound Ingestion Domain
    subgraph InboundAPI [Apps: telemetry-api Subject]
        ExpressApp[Express App] -->|Input Payload| ValGate{Validation Gate}
        ValGate -->|Invalid| Client[Client]
        ValGate -->|Valid| KinesisProducer[Kinesis Stream Producer]
    end

    %% Event Broker Layer
    subgraph EventBroker [Infra: AWS Kinesis Event Bus]
        KinesisStream[(cnh-telemetry-stream)]
    end

    KinesisProducer -->|PutRecordCommand| KinesisStream
    KinesisProducer -->|202 Accepted| Client

    %% Outbound Processing Domain
    subgraph StorageObserver [Apps: processor-storage Observer]
        StorageConsumer[Kinesis Stream Consumer] -->|PutCommand| DynamoDB[(DynamoDB Table)]
    end

    subgraph AlertsObserver [Apps: processor-alerts Observer]
        AlertConsumer[Kinesis Stream Consumer] -->|Error Injection| ErrHandler[Error Handler]
    end

    KinesisStream -.->|Async Batch Poll| StorageConsumer
    KinesisStream -.->|Async Batch Poll| AlertConsumer

    %% Styling
    style Client fill:#eceff1,stroke:#607d8b,stroke-width:2px
    style InboundAPI fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style EventBroker fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style StorageObserver fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style AlertsObserver fill:#ffebee,stroke:#c62828,stroke-width:2px
    style ValGate fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    style KinesisStream fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    style DynamoDB fill:#ffe0b2,stroke:#ef6c00,stroke-width:2px