---
title: "Veinborn multiplayer playtest: how to run a two-player game in the TUI"
type: guide
beth_topics:
  - veinborn
  - multiplayer
  - playtest
  - tui
---

# Multiplayer playtest

How to play a co-op game with two (up to four) people in the terminal UI, what the
rules are today, and what to look for. The client is the normal game screen on a
`RemoteDriver` (plan phase 4, [architecture/MULTIPLAYER_ARCHITECTURE_PLAN.md](architecture/MULTIPLAYER_ARCHITECTURE_PLAN.md));
the same flow runs headless in `tests/ui/test_two_clients.py`.

## Start a game

```bash
cd ~/src/projects/veinborn

# Terminal 1: the server (listens on 0.0.0.0:8765; VEINBORN_HOST / VEINBORN_PORT to change)
python3 src/server/run_server.py

# Terminal 2: Alice creates a game
python3 run_multiplayer.py --name Alice --class warrior --create-game --game-name "Playtest"

# Alice's status bar shows:  Lobby 'Playtest' id <game-id> | Alice (warrior) | R: ready ...
# Terminal 3: Bob joins with that id
python3 run_multiplayer.py --name Bob --class mage --game-id <game-id>
```

Each player presses **R** (shift-r) when ready; the game starts when every seat is
ready. Another machine connects with `--host <server-ip>`.

## Rules today

- **Rounds:** each living player gets exactly one turn-consuming action per round; the
  monsters move when everyone has acted. The status bar says `Round N: waiting on ...`.
  A second action before the others have acted is refused (`Waiting for the party: Bob`).
  Free actions (equip, unequip, listings) do not use your turn.
- **Stairs:** any one player on the stairs pressing `>` takes the whole party down.
- **Death:** a dead player spectates (`DEAD (spectating)`); the run ends when everyone is dead.
- **Vision:** fog of war: you see what is in your line of sight (radius 9) and remember the
  terrain you have seen (dimmed). Monsters and items show only while in sight; allies always show
  (cyan `@`). For a dev game with no fog, start the creator with `--reveal-map` (sidebar:
  `[MAP REVEALED: no fog]`).
- **Leaving:** if a client quits or loses its connection, the round waits for that seat
  (status bar: `Bob (disconnected, 1:45)`, counting down) for 2 minutes, then drops it: the
  character leaves the floor and the party plays on.
- **Coming back:** run `python run_multiplayer.py --name Bob` again (no `--game-id`). The client
  remembers its token and game id (`~/.local/state/veinborn/multiplayer_session.json`, `--no-resume`
  ignores it), so a seat still in its grace is reconnected and a dropped one is taken back: the
  character returns with its hp, level and gear next to a party member, and the round owes it an
  action from the next round. Without the saved token a name match works only while exactly one
  dropped seat has that name. A character that died comes back as a spectator.
- **Not in multiplayer:** save, load and restart (they say so).
- Keys are the single-player ones (`i`, `:`, `e`, `d`, `g`, `w`, `s`, `z`, `.`, `>`), plus
  `c`/Enter for chat.

## What to look for

The numbers (balance, bot runs) are measured elsewhere; a human playtest answers what
they cannot:
- Does the strict round feel slow or fair? Is "waiting on" enough to know whose turn it is?
- Is it clear what your partner did (shared message log) and where they are?
- Does "anyone descends, everyone descends" cause trouble in practice?
- Refusals and errors: does every refused key say why?
- Anything that looks out of sync between the two screens.

Write findings as `tt add` tasks in this repo (`tt grep` first) with the seed, the two
classes and what each screen showed. Logs: `logs/` (client) and the server terminal.
