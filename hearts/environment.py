# d6617
# The hearts environment, has all the functions and plays the game

# need to be able to call
# env.reset()
# env.step()

# This is the same irrespective of how the agent is built

# observation = (card's played, highest card played, my cards)

import numpy as np
import logging

logger = logging.getLogger('run-sim.environment')

def card_num_to_tuple(card):
    # Ultimatly doesn't matter which is 0,1,2,3 as it was just random stuff to being with
    if card < 14:
        # Heart
        return (0, card)
    elif card < 27:
        # Clubs
        return (1, card - 13)
    elif card < 40:
        # Spades
        return (2, card - 13 - 13)
    else:
        # Diamond
        return (3, card - 13 - 13 - 13)

def deal_hands(players=4):
    # Deal the cards
    cards = np.arange(1, 53)  # All cards dealt
    np.random.shuffle(cards)
    length = int(52//players)

    hands = np.zeros((players, 4, 14))

    for player in range(players):
        hand = cards[player*length:player*length+length]  # get "your" cards
        for card in hand:
            suit, card = card_num_to_tuple(card)
            hands[player, suit, card] = 1
        logger.debug('Player ' + str(player) + "'s hand\n" + str(hands[player]))
    logger.debug('Sum of player hands =' + str(np.sum(hands)))

    if length*players is not 52:
        # There are some undealt cards
        logger.warning('Undealt cards of ' + str(52-length*players) + ' -> Creating kitty.')
        left = cards[length*players:]
        kitty = []
        for card in left:
            kitty.append(card_num_to_tuple(card))
        logger.debug('Kitty of ' + str(kitty))
        logger.debug('Final sum of ' + str(np.sum(hands) + len(kitty)))
    else:
        kitty = None

    return hands, kitty


class Simulator():
    def __init__(self, players, observations='limited', scoring='face'):
        logger.info('Hearts engine initilised')

        # CONSTANTS
        self.hands, self.kitty = deal_hands(players)  # all cards
        self.players = players
        self.first_score = True  # Turned false once first player recieves a score

        assert scoring == 'face' or 'single'
        self.scoring = scoring  # either face or single

        logger.warning('Only limited mode is implemented')
        assert observations == 'limited' or 'expanded' or 'full' or 'super'
        self.mode = observations  # Higher observations convey more infomation, but need a more complex machine
        # limited = (index, suit, card) index=0 played cards (only highest card shown), index=1 cards available
        # expanded = (index, suit, card) index=0 all played cards (card 0 is required suit), index=1 cards available
        # full = (index, suit, card) index=0 all played cards, index=1 cards available, index=2 all cards played (game)
        # super = (index, suit, card) same as full, but index=2,3,4 is cards other plays have played

        # Variables (Changes each game)
        self.current_hands = self.hands  # only cards left
        self.played = []  # Cards played this round
        self.suit = 0  # What suit?
        self.scores = np.zeros(self.players)

        # List of what cards the model holds
        self.hearts = 0
        self.clubs = 1
        self.spades = 2
        self.diamonds = 3
        self.queen = (self.spades, 12)  # The QUEEN OF SPADES!!!

    def load_algorithms(self, algorithms):
        assert algorithms.__len__() == self.players  # Make sure right number is entered
        self.algs = algorithms  # These will be the models

    def get_highest_card(self):
        highest_card = 0
        for play in self.played:  # Get the highest card of the right suit
            if play[0] == self.suit and play[1] > highest_card:
                highest_card = play[1]
        logger.debug('Highest card played ' + str(highest_card))
        return highest_card

    def print_cards(self):
        logger.debug('--- Current cards ---')
        for player in range(self.players):
            logger.debug('Player' + str(player) + "'s hand\n" + str(self.current_hands[player]))

    def init_state(self, player):
        # Can choose any card... but choosing a suit is harder.
        suit, card = self.algs[player].choose_first_card(self.current_hands[player])
        self.played = []
        self.suit = suit
        return suit, card

    def gen_state(self, turn):
        # Played is cards played, turn is player's turn
        # create observation
        num_cards = len(self.played)
        highest_card = self.get_highest_card()
        if self.mode is 'limited':
            # limited = (index, suit, card) index=0 played cards (only highest card shown), index=1 cards available
            o = np.zeros((2, 4, 14))
            logger.debug('Obseration shape' + str(o.shape))
            o[0,self.suit,highest_card] = 1  # only one hot largest card
            o[1, :, :] = self.current_hands[turn]  # add the player's hand
            return o
        else:
            logger.error('Invalid mode')
            raise TypeError('Mode not implemeted')

    def choose(self, turn, state):
        # Choose what card to play from the state
        return self.algs[turn].think(self.mode, state)

    def step(self, turn, action):
        # Step in direction of action.
        # action = (suit, card)
        self.current_hands[turn, action[0], action[1]] = 0  # Use the card
        self.played.append(action)
        logger.debug('Cards Played' + str(self.played))

    def score_cards(self, cards):
        # Score the played hands
        score = 0
        for suit, card in cards:
            if suit == self.hearts:
                if self.scoring is 'face':
                    score += card
                elif self.scoring is 'single':
                    score += 1
                else:
                    logger.error('Scoring type is not set')
                    raise ValueError('Score type is not set')
            elif suit == self.queen[0] and card == self.queen[1]:
                # Oh no queen of spades
                logger.debug('Can we get a F in chat for that Queen of spades?')
                if self.scoring is 'face':
                    score += 50
                elif self.scoring is 'single':
                    score += 13
                else:
                    logger.error('Scoring type is not set')
                    raise ValueError('Score type is not set')
        return score

    def find_winner(self, start):
        # start = who started
        # find highest card of starting suit
        highest = (0,0)
        player = 0
        i = start
        logger.debug('Cards Played' + str(self.played))
        for suit, card in self.played:
            if suit == self.suit and card > highest[1]:
                highest = (suit, card)
                player = i
            i += 1
            if i > self.players-1:
                i = 0

        score = self.score_cards(self.played)
        if score > 0 and self.first_score and self.kitty is not None:
            # Add on the kitty
            kitty = self.score_cards(self.kitty)
            logger.debug('First points for round detected. Adding kitty of ' + str(kitty))
            score += kitty
            self.first_score = False

        logger.debug('Score of ' + str(score) + ' for player ' + str(player))
        self.scores[player] += score
        return player

    def reset(self):
        # Resetting environment
        logger.debug('Resetting env.')

        self.hands, self.kitty = deal_hands(self.players)
        self.first_score = True

        self.current_hands = self.hands  # only cards left
        self.played = []  # Cards played this round
        self.suit = 0  # What suit?
        self.scores = np.zeros(self.players)
