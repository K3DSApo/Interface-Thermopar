import argparse, json, mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from sesiones import APIError

def create_server(manager,port=8765):
    class Handler(BaseHTTPRequestHandler):
        def send_json(self,status,obj):
            b=json.dumps(obj,ensure_ascii=False,allow_nan=False).encode(); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
        def do_GET(self):
            try:
                if self.path=='/api/state':return self.send_json(200,manager.state())
                if self.path=='/api/ports':
                    try:
                        from serial.tools import list_ports; ports=[p.device for p in list_ports.comports()]
                    except Exception: ports=[]
                    return self.send_json(200,{'ports':ports})
                if self.path=='/api/export':
                    b=manager.export_csv().encode(); self.send_response(200); self.send_header('Content-Type','text/csv'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b); return
                if self.path=='/api/results': return self.send_json(200,manager.state())
                if self.path in ('/','/index.html','/app.js'):
                    name = 'app.js' if self.path == '/app.js' else 'index.html'
                    p=Path(__file__).parent/'app'/'web'/name
                    if not p.exists(): self.send_error(404); return
                    b=p.read_bytes(); self.send_response(200); self.send_header('Content-Type',('text/javascript' if name == 'app.js' else 'text/html')+'; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b); return
                self.send_error(404)
            except Exception as e:self.send_json(500,{'error':str(e)})
        def do_POST(self):
            try:
                n=int(self.headers.get('Content-Length','0')); raw=self.rfile.read(n); data=json.loads(raw or b'{}')
                if not isinstance(data,dict): raise ValueError('JSON objeto requerido')
                fn={'/api/config':manager.configure,'/api/start':lambda _:manager.start(),'/api/stop':lambda _:manager.stop(),'/api/point':lambda _:manager.capture_point(),'/api/dynamic/start':manager.dynamic_start,'/api/dynamic/finish':lambda _:manager.dynamic_finish(),'/api/reset':lambda _:manager.reset()}.get(self.path)
                if not fn: return self.send_json(404,{'error':'ruta no encontrada'})
                return self.send_json(200,fn(data))
            except APIError as e:self.send_json(e.status,{'error':str(e)})
            except (ValueError,KeyError,TypeError,json.JSONDecodeError) as e:self.send_json(400,{'error':str(e)})
            except Exception as e:self.send_json(503,{'error':str(e)})
        def log_message(self,*args): pass
    return ThreadingHTTPServer(('127.0.0.1',port),Handler)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--port',type=int,default=8765); ap.add_argument('--data-dir',default='sesiones'); a=ap.parse_args()
    from sesiones import SessionManager
    manager=SessionManager(a.data_dir)
    s=create_server(manager,a.port)
    print(f'http://127.0.0.1:{a.port}',flush=True)
    try:
        s.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop()
        s.server_close()
if __name__=='__main__':main()
