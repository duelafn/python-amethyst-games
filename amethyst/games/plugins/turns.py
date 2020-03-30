# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: LGPL-3.0
__all__ = 'Turns'.split()

from amethyst.core import Attr

from amethyst.games.plugin import EnginePlugin

class Turns(EnginePlugin):
    """
    Configurable attributes
    -----------------------

    These attributes can be set at plugin construction time.

    :ivar setup_rounds: List or tuple of +/-1 indicating the number and
    direction of setup rounds. Setup rounds have string round identifiers
    'setup-0', 'setup-1', .... After the setup rounds complete, the round
    will be set to numeric 0 and play will begin with player 0.


    State Attributes
    ----------------

    Do not modify these attributes directly, use the provided API methods.

    :ivar current_player: Current player number.

    :ivar current_turn: Simple strictly monotonic counter starting at 0
    tracking the current active turn.

    :ivar current_round: Rounds are tracked whenever the current player
    number wraps around, either forward or backward. Games with complicated
    turn order will probably find this value useless and will need to
    create their own round tracker (if needed). If `setup_rounds` is
    non-empty, the setup rounds will not be integers, but instead will be
    strings 'setup-0', 'setup-1', ...

    :ivar setup_state: Current index in the setup_rounds list.
    """
    AMETHYST_PLUGIN_COMPAT  = 1.0
    AMETHYST_ENGINE_METHODS = "_player _player_num _number _round _start _flag _roundflag _playerflag".split()
    AMETHYST_ENGINE_DEFAULT_METHOD_PREFIX = "turn_"

    current_turn   = Attr(int, default=-1)
    current_round  = Attr(default=-1)
    current_player = Attr(int, default=-1)

    setup_rounds   = Attr()
    setup_state    = Attr(default=-1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Catch likely common mistake of passing a number of setup rounds
        if isinstance(self.setup_rounds, int):
            self.setup_rounds = [1] * self.setup_rounds

    def _start(self, engine, player_num=None, round=None, step=1):
        """
            mygame.turn_start()

        Start the next turn.

        Play direction can be controlled by passing the `step` paramter
        (typically 1 or -1).

        Turn can jump to a specific player by passing the `player_num`
        argument.

        Automatic round tracking can be overrideen by passing the `round`
        parameter. Setting the round to a string value will bypass
        automatic round calculation. Setting the round to a numeric value
        bypasses round calculation for the current method call, but future
        calls may auto-increment the round.

        `setup_rounds` examples:

        * Default sequence of round and player_num:

            0: 0, 1, ... N
            1: 0, 1, ... N

        * Two setup rounds using `setup_rounds=2`

            'setup-0': 0, 1, ... N
            'setup-1': 0, 1, ... N
            0: 0, 1, ... N
            1: 0, 1, ... N

        * Switchback start using `setup_rounds=(1,-1)`

            'setup-0': 0, 1, ... N
            'setup-1': N, N-1, ... 0
            0: 0, 1, ... N
            1: 0, 1, ... N
        """
        num_players = len(engine.players)

        # Setup rounds
        if self.setup_rounds and self.setup_state < len(self.setup_rounds) and player_num is None and round is None:
            if self.setup_state == -1:
                self.setup_state = 0
                player_num = 0 if self.setup_rounds[self.setup_state] > 0 else num_players - 1
            else:
                player_num = self.current_player + self.setup_rounds[self.setup_state]
                if player_num < 0 or player_num >= num_players:
                    self.setup_state += 1
                    player_num = 0 if self.setup_state >= len(self.setup_rounds) or self.setup_rounds[self.setup_state] > 0 else num_players - 1
            if self.setup_state < len(self.setup_rounds):
                round = 'setup-{}'.format(self.setup_state)
            else:
                round = 0

        # Normal rounds
        if player_num is None:
            player_num = self.current_player + step

        if round is None and isinstance(self.current_round, int):
            round = self.current_round
            if self.current_player < 0 or player_num < 0 or player_num > num_players:
                round += 1

        # Current turn is guaranteed unique and predictable turn identifier
        self.current_turn += 1
        if round is not None:
            self.current_round = round
        self.current_player = player_num % num_players

    def _player(self, engine):
        """
            mygame.turn_player()

        Return the currently active player object.
        """
        return engine.players[self.current_player]

    def _player_num(self, engine):
        """
            mygame.turn_player_num()

        Return the currently active player number.
        """
        return self.current_player

    def _number(self, engine):
        """
            mygame.turn_number()

        Return a simple strictly monotonic counter starting at 0 tracking
        the current active turn.
        """
        return self.current_turn

    def _round(self, engine):
        """
            mygame.turn_round()

        Return the current round as understood by this object. Will be
        'setup-0', 'setup-1', ... during setup phase and numeric 0, 1, ...
        afterward unless you explicitly set the round parameter in the
        _start method.
        """
        return self.current_round

    def _flag(self, engine, turn=None):
        if turn is None: turn = self.current_turn
        return "turn:turn-{}".format(turn)

    def _roundflag(self, engine, round=None):
        if round is None: round = self.current_round
        return "turn:round-{}".format(round)

    def _playerflag(self, engine, player=None):
        if player is None: player = self.current_player
        return "turn:player-{}".format(player)
