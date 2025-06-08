import asyncio
import json
import logging
from kafka import KafkaConsumer
from typing import Any

logger = logging.getLogger(__name__)

KAFKA_TOPIC = "raw-data-stream"
KAFKA_BROKER_URL = "kafka:9092"

async def consume_messages() -> None:
    """Consume Kafka messages indefinitely in an async-friendly wrapper."""
    loop = asyncio.get_event_loop()
    logger.info("Kafka consumer starting ...")

    consumer: KafkaConsumer[str, Any] = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKER_URL,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="palantir-group",
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    )
    logger.info("Subscribed to topic '%s'", KAFKA_TOPIC)

    def _blocking_read():
        for message in consumer:
            try:
                logger.info("Received message: %s", message.value)
                # TODO: integrate with pipeline executor
            except Exception as exc:
                logger.error("Failed processing message: %s", exc)

    # Run the blocking Kafka loop in a thread to avoid blocking the event loop.
    await loop.run_in_executor(None, _blocking_read) 