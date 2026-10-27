"""Native Qt routing smoke with a loopback-only fixture, never real translation.

No settings/key/model/telemetry loads. Not speech, translation quality, game FPS,
or packaged-client acceptance. Every displayed fixture says protocol-only.
"""
import argparse
from collections import defaultdict
import ctypes
import ipaddress
import json
import os
from pathlib import Path
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def loopback_connect(original):
    def connect(sock,address):
        if not isinstance(address,tuple) or not ipaddress.ip_address(address[0]).is_loopback:
            raise RuntimeError('External network forbidden in native protocol smoke')
        return original(sock,address)
    return connect


def run(output,platform):
    if output.exists():raise FileExistsError('Fresh native evidence directory required')
    output.mkdir(parents=True)
    os.environ['QT_QPA_PLATFORM']=platform
    # Same optional-library exclusions as the shipped Windows build.
    sys.modules['torch']=None;sys.modules['transformers']=None
    from loguru import logger
    logger.remove()
    from PyQt5.QtWidgets import QApplication
    from voxgo.app import VoxGoApp
    from voxgo.ui.overlay_window import GameOverlay
    from voxgo.ui.config_models import OverlayConfig
    from voxgo.translation import TranslationConfig
    from voxgo.translation.runtime import TranslationRuntime
    from voxgo.runtime.events import EventBus,TranslationReady
    from voxgo.languages import ONLINE_DIRECTIONS
    from voxgo.translation.prompt import translation_system_prompt
    requests=[]
    class Fixture(BaseHTTPRequestHandler):
        def log_message(self,*a):pass
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            source,target=self.server.expected_pair
            assert body['messages'][0]['content']==translation_system_prompt(source,target)
            assert body['model']=='fixture-only'
            requests.append(dict(source=source,target=target,payload=body))
            data=json.dumps(dict(choices=[dict(message=dict(content=f'[本地协议测试，非真实翻译] {source} -> {target}'),finish_reason='stop')])).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    server=ThreadingHTTPServer(('127.0.0.1',0),Fixture)
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    qt=QApplication.instance() or QApplication([])
    config=TranslationConfig(provider='openai_compatible',endpoint=f'http://127.0.0.1:{server.server_address[1]}/v1',model='fixture-only',api_key='',enable_local_phrase_cache=False)
    overlay=GameOverlay(config=OverlayConfig(mobile_url='http://127.0.0.1:18765'),translation_config=config)
    overlay.show();qt.processEvents()
    if platform=='windows' and qt.platformName()!='windows':raise RuntimeError('Native Windows Qt required')
    if platform=='windows':
        from ctypes import wintypes
        visible=ctypes.windll.user32.IsWindowVisible
        visible.argtypes=[wintypes.HWND];visible.restype=wintypes.BOOL
        if not visible(int(overlay.winId())):raise RuntimeError('Win32 window is not visible')
    owner=VoxGoApp.__new__(VoxGoApp);owner._stopping=False;owner._stats=defaultdict(int);owner._latency_traces={};owner._language_flow_revision=1
    owner._overlay=overlay;owner._mobile=SimpleNamespace(server=None);owner._analytics=None
    bus=EventBus();runtime=TranslationRuntime(bus,owner._stats,owner._latency_traces,lambda:overlay)
    runtime.set_language_revision_getter(lambda:owner._language_flow_revision)
    bus.subscribe(TranslationReady,owner._handle_translation_ready)
    source_texts={'zh':'不要开火，左边两个人。','en':'Do not shoot. Two on the left.','ja':'左に二人。まだ撃たないで。','ko':'왼쪽에 두 명이야. 아직 쏘지 마.','ru':'Слева двое. Пока не стреляй.'}
    rows=[]
    try:
        with patch.object(socket.socket,'connect',loopback_connect(socket.socket.connect)),patch.object(socket.socket,'connect_ex',loopback_connect(socket.socket.connect_ex)):
            runtime.initialize(config)
            for index,(source,target) in enumerate(sorted(ONLINE_DIRECTIONS)):
                server.expected_pair=(source,target);owner._language_flow_revision=index+1
                overlay.clear_history();overlay._apply_language_flow(source,target)
                assert overlay._source_lang_combo.currentData()==source and overlay._target_lang_combo.currentData()==target
                assert overlay._target_lang_combo.count()==4
                id='fixture-'+str(index);overlay.add_translation_with_id(id,source_texts[source],'[本地协议测试] 等待回环响应')
                runtime.translate_async(id,source_texts[source],source,1.,source,target,index+1)
                end=time.monotonic()+5
                while time.monotonic()<end:
                    qt.processEvents();time.sleep(.01)
                    item=next((x for x in overlay._translations if x.item_id==id and x.copyable),None)
                    if item:break
                if not item:raise RuntimeError('Native fixture did not reach Qt: '+source+'->'+target)
                qt.processEvents()
                rows.append(dict(source=source,target=target,widget_text=item.translated,native_visible=overlay.isVisible(),window_handle=int(overlay.winId()),translation_quality=None))
                if (source,target) in {('ja','ru'),('ko','ja'),('ru','ja')}:
                    overlay.grab().save(str(output/(source+'-'+target+'-protocol.png')))
            before=[(x.item_id,x.translated) for x in overlay._translations]
            owner._handle_translation_ready(TranslationReady(original='stale fixture',translated='must not display',source_lang='ja',target_lang='ko',trace_id='old-flow',language_revision=1))
            qt.processEvents();assert before==[(x.item_id,x.translated) for x in overlay._translations]
            assert len(requests)==20
    finally:
        runtime.close();overlay._allow_close=True;overlay.close();qt.processEvents()
        server.shutdown();server.server_close();worker.join(3)
    report=dict(platform=qt.platformName(),win32_visible_checked=platform=='windows',rows=rows,loopback_http_requests=len(requests),real_api_requests=0,stale_event_rejected=True,
        worker_stopped=not worker.is_alive(),runtime_thread_stopped=not runtime.thread or not runtime.thread.is_alive(),
        source='source-level GameOverlay + TranslationRuntime + actual app TranslationReady handler; fixture responses',
        speech_quality=None,translation_quality=None,physical_loopback=False,game_fps=None,human_acceptance='pending')
    (output/'native-protocol.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'loopback-requests.json').write_text(json.dumps(requests,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--platform',choices=['windows','offscreen'],default='windows');a=p.parse_args();run(a.output,a.platform)
