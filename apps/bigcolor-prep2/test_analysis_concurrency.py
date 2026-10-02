import json
import threading
import unittest
import urllib.request
import urllib.error
from unittest.mock import patch
from http.server import ThreadingHTTPServer
import pandas as pd
import prep_app_server as app

class ConcurrencyTest(unittest.TestCase):
    def test_second_analysis_rejected_and_slot_released(self):
        entered, release = threading.Event(), threading.Event()
        def calculation(**kwargs):
            entered.set()
            if not release.wait(5): raise RuntimeError('test release timeout')
            return {}, pd.DataFrame()
        server=ThreadingHTTPServer(('127.0.0.1',0),app.PrepAppHandler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        url='http://127.0.0.1:%s/api/analyze'%server.server_port
        body=b'--TEST\r\nContent-Disposition: form-data; name="mode"\r\n\r\ndemo\r\n--TEST--\r\n'
        def send():
            req=urllib.request.Request(url,data=body,headers={'Content-Type':'multipart/form-data; boundary=TEST'})
            with urllib.request.urlopen(req,timeout=8) as r:return json.load(r)
        result=[]
        try:
            with patch.object(app,'analyze_case',side_effect=calculation) as mock:
                first=threading.Thread(target=lambda:result.append(send()))
                first.start();self.assertTrue(entered.wait(3))
                with self.assertRaises(urllib.error.HTTPError) as err:send()
                self.assertEqual(err.exception.code,429)
                self.assertIn('ocupado',json.load(err.exception)['error'])
                self.assertEqual(mock.call_count,1)
                release.set();first.join(4)
                self.assertTrue(result[0]['ok'])
                self.assertTrue(send()['ok'])
        finally:
            release.set();server.shutdown();server.server_close()

if __name__=='__main__':unittest.main()
