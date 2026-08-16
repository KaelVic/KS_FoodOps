import os
import logging

logger = logging.getLogger(__name__)

def setup_telemetry(app, engine=None):
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        
        provider = TracerProvider()
        otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        if otlp_endpoint:
            processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
            provider.add_span_processor(processor)
            
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)

        if engine:
            SQLAlchemyInstrumentor().instrument(engine=engine)
    except ImportError as e:
        logger.warning(f"OpenTelemetry packages not available: {e}. Skipping tracing setup.")

    try:
        from prometheus_client import make_asgi_app
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)
    except ImportError as e:
        logger.warning(f"prometheus_client not available: {e}. Skipping /metrics mount.")

