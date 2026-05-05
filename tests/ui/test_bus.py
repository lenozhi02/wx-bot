"""
事件总线测试
"""

import asyncio
import sys
import os

# 确保能找到 src 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.ui.bus import EventBus, BusEvent


class TestEventBus:
    """EventBus 单元测试"""
    
    def test_subscribe_and_emit(self):
        """测试订阅和发布"""
        bus = EventBus()
        received = []
        
        def handler(event):
            received.append(event.data["msg"])
        
        bus.on("test:event", handler)
        
        async def run():
            await bus.emit("test:event", {"msg": "hello"})
            await asyncio.sleep(0.1)  # 等待回调执行
        
        asyncio.run(run())
        assert received == ["hello"]
    
    def test_multiple_subscribers(self):
        """测试多订阅者"""
        bus = EventBus()
        results = []
        
        bus.on("test:multi", lambda e: results.append(f"a:{e.data['v']}"))
        bus.on("test:multi", lambda e: results.append(f"b:{e.data['v']}"))
        
        async def run():
            await bus.emit("test:multi", {"v": 1})
            await asyncio.sleep(0.1)
        
        asyncio.run(run())
        assert len(results) == 2
        assert "a:1" in results
        assert "b:1" in results
    
    def test_wildcard(self):
        """测试通配符订阅"""
        bus = EventBus()
        all_events = []
        
        bus.on("*", lambda e: all_events.append(e.event))
        
        async def run():
            await bus.emit("a:1", {})
            await bus.emit("b:2", {})
            await asyncio.sleep(0.1)
        
        asyncio.run(run())
        assert all_events == ["a:1", "b:2"]
    
    def test_history(self):
        """测试历史记录"""
        bus = EventBus()
        
        async def run():
            await bus.emit("test:h", {"i": 1})
            await bus.emit("test:h", {"i": 2})
            await asyncio.sleep(0.1)
        
        asyncio.run(run())
        history = bus.get_history("test:h")
        assert len(history) == 2
        assert history[0].data["i"] == 1
        assert history[1].data["i"] == 2
    
    def test_no_subscriber(self):
        """测试无订阅者时不报错"""
        bus = EventBus()
        
        async def run():
            await bus.emit("no:subscriber", {"x": 1})
        
        asyncio.run(run())  # 不应抛出异常
    
    def test_callback_exception(self):
        """测试回调异常不影响其他回调"""
        bus = EventBus()
        results = []
        
        def bad_handler(event):
            raise ValueError("bad")
        
        def good_handler(event):
            results.append("ok")
        
        bus.on("test:err", bad_handler)
        bus.on("test:err", good_handler)
        
        async def run():
            await bus.emit("test:err", {})
            await asyncio.sleep(0.1)
        
        asyncio.run(run())
        assert results == ["ok"]


if __name__ == "__main__":
    test = TestEventBus()
    test.test_subscribe_and_emit()
    print("✅ test_subscribe_and_emit")
    
    test.test_multiple_subscribers()
    print("✅ test_multiple_subscribers")
    
    test.test_wildcard()
    print("✅ test_wildcard")
    
    test.test_history()
    print("✅ test_history")
    
    test.test_no_subscriber()
    print("✅ test_no_subscriber")
    
    test.test_callback_exception()
    print("✅ test_callback_exception")
    
    print("\n🎉 所有测试通过")
