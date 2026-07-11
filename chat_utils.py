import json


def parse_json_request_body(request):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
        if isinstance(payload, dict):
            return payload
        return {}
    except Exception:
        return {}

