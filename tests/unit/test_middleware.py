import asyncio

import pytest

from shared.middleware.circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitBreaker:

    @pytest.fixture
    def circuit_breaker(self):
        return CircuitBreaker(name='test', failure_threshold=3, recovery_timeout=1, half_open_max_calls=2)

    @pytest.mark.asyncio
    async def test_initial_state_closed(self, circuit_breaker):
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.is_closed is True

    @pytest.mark.asyncio
    async def test_can_execute_when_closed(self, circuit_breaker):
        can_execute = await circuit_breaker.can_execute()
        assert can_execute is True

    @pytest.mark.asyncio
    async def test_opens_after_failures(self, circuit_breaker):
        for _ in range(3):
            await circuit_breaker.record_failure()
        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.is_open is True

    @pytest.mark.asyncio
    async def test_rejects_when_open(self, circuit_breaker):
        for _ in range(3):
            await circuit_breaker.record_failure()
        can_execute = await circuit_breaker.can_execute()
        assert can_execute is False

    @pytest.mark.asyncio
    async def test_transitions_to_half_open(self, circuit_breaker):
        for _ in range(3):
            await circuit_breaker.record_failure()
        assert circuit_breaker.state == CircuitState.OPEN
        await asyncio.sleep(1.1)
        can_execute = await circuit_breaker.can_execute()
        assert can_execute is True
        assert circuit_breaker.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_closes_after_successes(self, circuit_breaker):
        for _ in range(3):
            await circuit_breaker.record_failure()
        await asyncio.sleep(1.1)
        await circuit_breaker.can_execute()
        for _ in range(2):
            await circuit_breaker.record_success()
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_reopens_on_half_open_failure(self, circuit_breaker):
        for _ in range(3):
            await circuit_breaker.record_failure()
        await asyncio.sleep(1.1)
        await circuit_breaker.can_execute()
        assert circuit_breaker.state == CircuitState.HALF_OPEN
        await circuit_breaker.record_failure()
        assert circuit_breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_get_stats(self, circuit_breaker):
        stats = circuit_breaker.get_stats()
        assert stats['name'] == 'test'
        assert stats['state'] == 'closed'
        assert 'failure_count' in stats
        assert 'success_count' in stats
