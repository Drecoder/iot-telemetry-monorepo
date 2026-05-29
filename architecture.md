graph TD
    %% User/Client Layer
    Client([IoT Device / Client]) -->|POST /api/v1/telemetry| ExpressApp[Express Router]

    %% Inbound Ingestion Domain (The Subject)
    subgraph InboundAPI [Apps: telemetry-api Subject]
        ExpressApp -->|Input Payload| ValGate{Validation Gate}
        ValGate -->|Invalid: 400 Bad Request| Client
        ValGate -->|Valid Payload| KinesisProducer[Kinesis Stream Producer]
    end

    %% Event Broker Layer (Terraform Managed)
    subgraph EventBroker [Infra: AWS Kinesis Event Bus]
        KinesisProducer -->|AWS SDK PutRecordCommand| KinesisStream{{"cnh-telemetry-stream (Subject)"}}
    end

    %% Immediate Async Acknowledgement
    KinesisProducer -->|202 Accepted| Client

    %% Outbound Processing Domain (The Observers)
    subgraph StorageObserver [Apps: processor-storage Observer]
        KinesisStream -.->|Async Batch Poll| StorageConsumer[Kinesis Stream Consumer]
        StorageConsumer -->|AWS SDK PutCommand| DynamoDB[(DynamoDB Telemetry Table)]
    end

    subgraph AlertsObserver [Apps: processor-alerts Observer]
        KinesisStream -.->|Async Batch Poll| AlertConsumer[Kinesis Stream Consumer]
        AlertConsumer -->|Mocked Error Injection| ErrHandler[500/Datadog Error Handler]
    end

    %% Component Styling
    style Client fill:#eceff1,stroke:#607d8b,stroke-width:2px
    style InboundAPI fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style EventBroker fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style StorageObserver fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style AlertsObserver fill:#ffebee,stroke:#c62828,stroke-width:2px
    style ValGate fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    style KinesisStream fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    style DynamoDB fill:#ffe0b2,stroke:#ef6c00,stroke-width:2px