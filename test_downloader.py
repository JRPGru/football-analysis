import unittest

from playwright.sync_api import sync_playwright

from data_downloader import click_load_more, extract_leaderboard_with_js


class LeaderboardTests(unittest.TestCase):
    def test_load_more_waits_for_delayed_rows(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.set_content('''
                    <a class="playerRow">First player</a>
                    <button onclick="this.disabled=true; setTimeout(() => {
                        const row = document.createElement('a');
                        row.className = 'playerRow';
                        row.textContent = 'Second player';
                        document.body.appendChild(row);
                        this.remove();
                    }, 1200)">Load more</button>
                ''')
                click_load_more(page)
                self.assertEqual(page.locator('a.playerRow').count(), 2)
            finally:
                browser.close()

    def test_card_and_link_rows_exclude_rank_and_other_statistics(self):
        rows = ''.join(
            f'<a class="playerRow" href="/en/player/player-{i}">'
            f'<span class="rank">{i}</span>'
            f'<span class="playerName">Player {i}</span>'
            f'<span class="value">{800-i}</span></a>'
            for i in range(2, 11)
        )
        html = (
            '<section><a href="/en/player/leader"><div class="card-stats">'
            '<h2>Sprints</h2><span class="card-stats__rank">1</span>'
            '<span class="card-stats__name">Test Leader</span>'
            '<span class="card-stats__value">800</span></div></a>'
            + rows + '</section><section><h2>Goals</h2>'
            '<a class="playerRow" href="/en/player/other">'
            '<span class="playerName">Other Player</span>'
            '<span class="value">36</span></a></section>'
        )
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.set_content(html)
                result = extract_leaderboard_with_js(page, 'Sprints')
            finally:
                browser.close()
        self.assertEqual(len(result), 10)
        self.assertEqual(result.iloc[0].to_dict(), {
            'bundesliga_player': 'Test Leader', 'value': 800.0,
        })
        self.assertEqual(result.iloc[-1].to_dict(), {
            'bundesliga_player': 'Player 10', 'value': 790.0,
        })


if __name__ == '__main__':
    unittest.main()
