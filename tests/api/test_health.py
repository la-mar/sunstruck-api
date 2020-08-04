import logging

import pytest
import starlette.status as codes

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


async def test_health_check(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == codes.HTTP_200_OK
    assert {"status": "ok"} == response.json()
