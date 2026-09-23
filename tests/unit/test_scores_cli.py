"""veinborn-scores prints whichever leaderboard file it is pointed at."""

from core.highscore import HighScoreEntry, HighScoreManager
from core.scores_cli import main


def _entry(name, score):
    return HighScoreEntry(
        player_name=name, timestamp="2026-09-23T00:00:00", score=score, floor_reached=3,
        turns_survived=50, player_level=2, xp_gained=10, monsters_killed=4, damage_dealt=20,
        damage_taken=5, ore_mined=1, ore_surveyed=1, best_ore_purity=60, victory=False)


def test_prints_top_scores_from_the_given_file(tmp_path, capsys):
    path = tmp_path / "scores.json"
    manager = HighScoreManager(path)
    manager.add_score(_entry("Low", 100))
    manager.add_score(_entry("High", 9000))

    assert main(["--file", str(path), "--limit", "1"]) == 0

    out = capsys.readouterr().out
    assert "High" in out and "Low" not in out


def test_coop_flag_uses_the_multiplayer_leaderboard(capsys):
    # tests/conftest.py points the multiplayer singleton at an empty temp file
    HighScoreManager.get_multiplayer_instance().add_score(_entry("Alice", 4242))

    assert main(["--coop"]) == 0

    out = capsys.readouterr().out
    assert "CO-OP HIGH SCORES" in out and "Alice" in out
