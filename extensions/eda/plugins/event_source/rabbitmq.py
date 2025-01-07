"""rabbitmq.py

An ansible-rulebook event source plugin for receiving events via a RabbitMQ queue.

Arguments:
---------
    host:        The host where rabbitmq is hosted
    port:        The port where the rabbitmq server is listening
    queue:       The queue name to listen for messages on
    user:        The username to use
    password:    The password to use
    exchange:    The exchange to use (optional)
    vhost:       The vhost to use (optional)
    routing_key: The routing key to use (optional)

"""

import asyncio
import aiorabbit
import json
import logging
from typing import Any


async def main(queue: asyncio.Queue, args: dict[str, Any]) -> None:
    """Receive events via a rabbitmq topic."""
    logger = logging.getLogger()

    host = args.get("host")
    port = args.get("port")
    user = args.get("user")
    password = args.get("password")
    queue_name = args.get("queue")
    exchange = args.get("exchange")
    vhost = args.get("vhost")
    routing_key = args.get("routing_key")

    url = f"amqp://{user}:{password}@{host}:{port}/{vhost}"

    async with aiorabbit.connect(url) as client:
        await client.queue_declare(queue_name)
        if exchange and routing_key:
            # Bind to the exchange
            await client.queue_bind(queue_name, exchange, routing_key)
        logger.info('Consuming from %s', queue_name)
        async for msg in client.consume(queue_name):
            data = None
            logger.debug('Received message published to %s: %r',
                         queue_name, msg.body)
            try:
                data = json.loads(msg.body)
            except json.decoder.JSONDecodeError:
                logger.exception("JSON parse error")

            if data:
                await queue.put({"body": data})
            await client.basic_ack(msg.delivery_tag)
            await asyncio.sleep(0)

if __name__ == "__main__":
    """MockQueue if running directly."""

    class MockQueue:
        """A fake queue."""

        async def put(self: "MockQueue", event: dict) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(
        main(
            MockQueue(),
            {"user": "guest", "password": "guest", "host": "localhost", "port": "5672", "queue": "test"},
        ),
    )
