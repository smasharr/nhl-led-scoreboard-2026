import ast
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import Mock, patch

source = Path(__file__).with_name('nhl_scoreboard_led.py').read_text()
tree = ast.parse(source)
selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('get_timezone', 'get_display_date', 'fetch_games', 'fetch_display_games')]
ns = dict(datetime=datetime, timezone=timezone, timedelta=timedelta, ZoneInfo=ZoneInfo,
          TIMEZONE_FILE='/nonexistent/timezone.txt', GAME_DAY_ROLLOVER_HOUR=4,
          SCORE_TMPL='https://api-web.nhle.com/v1/score/{DATE}', requests=Mock())
exec(compile(ast.Module(body=selected, type_ignores=[]), '<scoreboard functions>', 'exec'), ns)

class RolloverTests(unittest.TestCase):
    def test_boundaries_and_dst(self):
        for instant, expected in [
            ('2026-10-01T23:00:00-05:00', '2026-10-01'),
            ('2026-10-02T00:00:00-05:00', '2026-10-01'),
            ('2026-10-02T03:59:59-05:00', '2026-10-01'),
            ('2026-10-02T04:00:00-05:00', '2026-10-02'),
            ('2026-01-01T02:00:00-06:00', '2025-12-31'),
            ('2026-03-08T03:59:59-05:00', '2026-03-07'),
            ('2026-03-08T04:00:00-05:00', '2026-03-08'),
            ('2026-11-01T01:30:00-05:00', '2026-10-31'),
            ('2026-11-01T01:30:00-06:00', '2026-10-31'),
            ('2026-11-01T04:00:00-06:00', '2026-11-01')]:
            with self.subTest(instant=instant):
                self.assertEqual(ns['get_display_date'](datetime.fromisoformat(instant)), expected)
    def test_timezone_settings_and_fallback(self):
        self.assertEqual(str(ns['get_timezone']()), 'America/Chicago')
        with patch('builtins.open', unittest.mock.mock_open(read_data='invalid/zone')):
            self.assertEqual(str(ns['get_timezone']()), 'America/Chicago')
        with patch('builtins.open', unittest.mock.mock_open(read_data='America/Los_Angeles')):
            self.assertEqual(ns['get_display_date'](datetime.fromisoformat('2026-10-02T11:00:00+00:00')), '2026-10-02')
    def test_explicit_endpoint_and_empty_response(self):
        req = ns['requests']
        req.get.return_value.json.return_value = {'games': []}
        self.assertEqual(ns['fetch_games']('2026-10-01'), [])
        req.get.assert_called_with('https://api-web.nhle.com/v1/score/2026-10-01', timeout=10)
    def test_bad_response_preserves_failure(self):
        ns['requests'].get.return_value.json.return_value = {'error': 'bad'}
        self.assertIsNone(ns['fetch_games']('2026-10-01'))
    def test_late_live_game_and_restart(self):
        original = ns['fetch_games']
        try:
            for state in ('LIVE', 'CRIT'):
                ns['fetch_games'] = Mock(return_value=[{'id': 1, 'gameState': state}])
                self.assertEqual(ns['fetch_display_games']('2026-10-02')[0]['id'], 1)
                ns['fetch_games'].assert_called_once_with('2026-10-01')
            ns['fetch_games'] = Mock(side_effect=[[{'gameState': 'FINAL'}], []])
            self.assertEqual(ns['fetch_display_games']('2026-10-02'), [])
            ns['fetch_games'] = Mock(return_value=None)
            self.assertIsNone(ns['fetch_display_games']('2026-10-02'))
        finally:
            ns['fetch_games'] = original

if __name__ == '__main__':
    unittest.main()
