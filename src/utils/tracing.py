import logging

from opentelemetry import trace
from typing import Sequence
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter, SpanExportResult

logger = logging.getLogger("mcp-yahoo-stock")


class LogSpanExporter(SpanExporter):
    """Custom exporter that writes spans directly to our file logger."""

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        for span in spans:
            if span.end_time and span.start_time:
                dur = (span.end_time - span.start_time) / 1e9
                logger.info(f"TRACE: {span.name} | Duration: {dur:.3f}s")
        return SpanExportResult.SUCCESS



# Configure Tracer
provider = TracerProvider()
processor = BatchSpanProcessor(LogSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer("mcp-yahoo-stock")
