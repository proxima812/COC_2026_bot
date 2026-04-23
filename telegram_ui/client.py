
import json
import urllib.parse
import urllib.request

class TelegramControlClient:
    def __init__(self, token):
        self.api_base = f'https://api.telegram.org/bot{token}'

    def _request(self, method, payload=None, timeout=30):
        data = None
        if payload is not None:
            encoded = urllib.parse.urlencode(payload)
            data = encoded.encode('utf-8')

        request = urllib.request.Request(
            f'{self.api_base}/{method}',
            data=data,
            method='POST',
        )

        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode('utf-8')

        parsed = json.loads(raw)
        if not parsed.get('ok'):
            raise RuntimeError(f'Telegram API error: {parsed}')
        return parsed.get('result')

    def send_message(self, chat_id, text, reply_markup=None):
        payload = {'chat_id': str(chat_id), 'text': text}
        if reply_markup is not None:
            payload['reply_markup'] = json.dumps(reply_markup, ensure_ascii=False)
        return self._request('sendMessage', payload)

    def edit_message(self, chat_id, message_id, text, reply_markup=None):
        payload = {
            'chat_id': str(chat_id),
            'message_id': int(message_id),
            'text': text,
        }
        if reply_markup is not None:
            payload['reply_markup'] = json.dumps(reply_markup, ensure_ascii=False)
        return self._request('editMessageText', payload)

    def set_my_commands(self, commands):
        payload = {'commands': json.dumps(commands, ensure_ascii=False)}
        return self._request('setMyCommands', payload)

    def answer_callback_query(self, callback_query_id, text='OK'):
        payload = {'callback_query_id': callback_query_id, 'text': text}
        return self._request('answerCallbackQuery', payload)

    def delete_message(self, chat_id, message_id):
        payload = {'chat_id': str(chat_id), 'message_id': int(message_id)}
        return self._request('deleteMessage', payload)

    def get_updates(self, offset=None, timeout=20):
        payload = {
            'timeout': int(timeout),
            'allowed_updates': json.dumps(['message', 'callback_query']),
        }
        if offset is not None:
            payload['offset'] = int(offset)
        return self._request('getUpdates', payload, timeout=timeout + 5)
