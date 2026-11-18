"""Real loopback HTTP/WebSocket acceptance, plus deterministic broadcast races."""
import asyncio
import socket
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import aiohttp

from voxgo.mobile.runtime import MobileRuntime
from voxgo.mobile.server import MobileWebSocketManager, WebSocketConfig


def local_config(port):
    return WebSocketConfig(host='127.0.0.1', port=port,
                           mobile_url=f'http://127.0.0.1:{port}/mobile')


class MobileRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.notify, self.crash = Mock(), Mock()
        self.runtime = MobileRuntime(self.notify, self.crash, lambda: False)
        self.addCleanup(self.runtime.stop)

    async def test_http_websocket_broadcast_reconnect_and_clean_stop(self):
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
        config = local_config(port)
        await asyncio.to_thread(self.runtime.start, config)
        self.assertTrue(self.runtime.server.is_running())
        self.assertEqual(self.runtime.get_mobile_url(), config.mobile_url)
        self.notify.assert_not_called()
        async with aiohttp.ClientSession() as client:
            async with client.get(config.mobile_url) as response:
                self.assertEqual(response.status, 200)
                self.assertIn('/mobile/static/app.js', await response.text())
            async with client.get(f'http://127.0.0.1:{port}/mobile/static/app.js') as response:
                self.assertEqual(response.status, 200)
                self.assertIn('translation', await response.text())
            async with client.ws_connect(f'http://127.0.0.1:{port}/ws') as first:
                self.assertEqual((await first.receive_json(timeout=2))['type'], 'connected')
                await first.send_str('invalid json')
                await first.send_json({'type': 'ping'})
                self.assertEqual(await first.receive_json(timeout=2), {'type': 'pong'})
                async with client.ws_connect(f'http://127.0.0.1:{port}/ws') as second:
                    await second.receive_json(timeout=2)
                    self.runtime.broadcast_translation('fixture speech', 'fixture translation')
                    for connection in (first, second):
                        message = await connection.receive_json(timeout=2)
                        self.assertEqual(message['type'], 'translation')
                        self.assertEqual(message['original'], 'fixture speech')
                        self.assertEqual(message['translated'], 'fixture translation')
            async with client.ws_connect(f'http://127.0.0.1:{port}/ws') as reopened:
                await reopened.receive_json(timeout=2)
                self.runtime.broadcast_translation('after reconnect', 'still works')
                self.assertEqual((await reopened.receive_json(timeout=2))['original'], 'after reconnect')
                # A live browser reads concurrently and acknowledges the close
                # handshake. Keep the client reader active while stopping.
                closing = asyncio.create_task(reopened.receive(timeout=3))
                self.assertTrue(await asyncio.to_thread(self.runtime.stop))
                message = await closing
                self.assertIn(message.type, (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED))
        self.assertFalse(self.runtime.thread.is_alive())
        self.assertTrue(self.runtime.loop.is_closed())
        self.assertFalse(self.runtime.server.is_running())
        self.assertTrue(self.runtime.stop())
        self.crash.assert_not_called()

    async def test_occupied_port_is_not_mistaken_for_our_ready_server(self):
        with socket.socket() as occupied:
            occupied.bind(('127.0.0.1', 0))
            occupied.listen()
            await asyncio.to_thread(self.runtime.start, local_config(occupied.getsockname()[1]))
            self.assertFalse(self.runtime.server.is_running())
            self.assertIsInstance(self.runtime.start_error, RuntimeError)
            self.notify.assert_called_once()
            self.crash.assert_called_once()
        self.assertTrue(await asyncio.to_thread(self.runtime.stop))

    async def test_unavailable_loop_and_failed_future_do_not_escape_to_caller(self):
        self.assertEqual(self.runtime.get_mobile_url(), '')
        self.runtime.broadcast_translation('a', 'b')
        self.runtime.server = Mock()
        self.runtime.loop = SimpleNamespace(is_running=lambda: False)
        self.runtime.broadcast_translation('a', 'b')
        self.runtime.server.broadcast_translation.assert_not_called()
        self.runtime._handle_broadcast_done(Mock(result=Mock(side_effect=RuntimeError('disconnected'))))
        self.assertTrue(self.runtime.stop())


class MobileBroadcastTests(unittest.IsolatedAsyncioTestCase):
    async def test_membership_changes_during_send_and_failed_clients_are_removed(self):
        manager = MobileWebSocketManager()
        late = Mock(send_json=AsyncMock())
        healthy = Mock(send_json=AsyncMock())
        failing = Mock(send_json=AsyncMock(side_effect=RuntimeError('closed')))
        changing = Mock()

        async def disconnect_and_connect(message):
            manager._connections.discard(changing)
            manager._connections.add(late)
            await asyncio.sleep(0)

        changing.send_json = AsyncMock(side_effect=disconnect_and_connect)
        manager._connections.update((healthy, failing, changing))
        await manager.broadcast_translation('original', 'translated')
        healthy.send_json.assert_awaited_once()
        self.assertNotIn(failing, manager._connections)
        self.assertNotIn(changing, manager._connections)
        late.send_json.assert_not_awaited()
        self.assertEqual(manager._connections, {healthy, late})

    async def test_no_clients_and_shutdown_with_a_failed_close(self):
        manager = MobileWebSocketManager()
        await manager.broadcast_translation('a', 'b')
        healthy = Mock(close=AsyncMock())
        failed = Mock(close=AsyncMock(side_effect=RuntimeError('already closed')))
        manager._connections.update((healthy, failed))
        manager._server = SimpleNamespace(should_exit=False)
        await manager.stop_server()
        self.assertEqual(manager._connections, set())
        self.assertTrue(manager._server.should_exit)
        healthy.close.assert_awaited_once()
