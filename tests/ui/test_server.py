"""
FastAPI 服务测试

使用 httpx 进行异步 HTTP 测试。
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.ui.bus import EventBus, get_default_bus
from src.ui.server import UIServer


def test_create_server():
    """测试创建 UIServer"""
    bus = EventBus()
    server = UIServer(event_bus=bus, port=3999)
    
    assert server.event_bus is bus
    assert server.port == 3999
    assert server.hub is not None
    assert server.sse is not None
    assert server.app is not None
    print("✅ test_create_server")


def test_health_endpoint():
    """测试健康检查端点"""
    bus = EventBus()
    server = UIServer(event_bus=bus, port=3998)
    
    from fastapi.testclient import TestClient
    client = TestClient(server.app)
    
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "event_bus" in data
    assert "websocket" in data
    print("✅ test_health_endpoint")


def test_events_history():
    """测试事件历史端点"""
    bus = EventBus()
    
    async def setup():
        await bus.emit("test:event", {"msg": "hello"})
        await asyncio.sleep(0.05)
    
    asyncio.run(setup())
    
    server = UIServer(event_bus=bus, port=3997)
    from fastapi.testclient import TestClient
    client = TestClient(server.app)
    
    resp = client.get("/api/events/history")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1
    print("✅ test_events_history")


def test_system_metrics():
    """测试系统指标端点"""
    bus = EventBus()
    server = UIServer(event_bus=bus, port=3996)
    from fastapi.testclient import TestClient
    client = TestClient(server.app)
    
    resp = client.get("/api/system/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "timestamp" in data
    print("✅ test_system_metrics")


def test_websocket_hub_stats():
    """测试 WebSocket Hub 统计"""
    bus = EventBus()
    server = UIServer(event_bus=bus, port=3995)
    stats = server.hub.get_stats()
    assert stats["connected_clients"] == 0
    print("✅ test_websocket_hub_stats")


if __name__ == "__main__":
    test_create_server()
    test_health_endpoint()
    test_events_history()
    test_system_metrics()
    test_websocket_hub_stats()
    print("\n🎉 所有测试通过")
