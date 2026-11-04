"""Bound request buffering before JSON parsing, including chunked uploads."""
from starlette.responses import JSONResponse


class RequestSizeLimit:
    def __init__(self, app, maximum=524288):
        self.app = app
        self.maximum = maximum

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['method'] != 'POST':
            return await self.app(scope, receive, send)
        chunks = []
        total = 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            chunk = message.get('body', b'')
            total += len(chunk)
            if total > self.maximum:
                return await JSONResponse({'detail':'Request exceeds the 512 KiB transport limit.'}, status_code=413)(scope, receive, send)
            chunks.append(chunk)
            if not message.get('more_body', False):
                break
        pending = True
        async def replay():
            nonlocal pending
            if pending:
                pending = False
                return {'type':'http.request', 'body':b''.join(chunks), 'more_body':False}
            return await receive()
        await self.app(scope, replay, send)
