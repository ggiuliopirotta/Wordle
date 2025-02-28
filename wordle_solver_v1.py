from collections import Counter, defaultdict
from logging import raiseExceptions
from math import log2
import os


class WordleSolver():

    def __init__(self):
        with open(os.path.join(os.getcwd(), "words-a.txt"), "r") as f:
            self.allowed_words = f.read().splitlines()
        with open(os.path.join(os.getcwd(), "words-p.txt"), "r") as f:
            self.wordlist = f.read().splitlines()
        self.allowed_candidates = self.allowed_words.copy()
        self.candidates = self.wordlist.copy()
        self.tried = []
        self.feedbacks = []
        self.first_guess = self.guess()
        self.max_h = log2(len(self.wordlist))


    @property
    def attempts(self):
        return (self.tried, self.feedbacks)


    @attempts.setter
    def attempts(self, value):
        self.tried.append(value[0])
        self.feedbacks.append(value[1])


    def restart_game(self):
        self.allowed_candidates = self.allowed_words.copy()
        self.candidates = self.wordlist.copy()
        self.tried = []
        self.feedbacks = []


    def get_matches(self, word: str, guess: str) -> str:
        '''
        Get the feedback string for a guess checked against a word.

        :param word: word to check against
        :param guess: guessed word
        :return: feedback
        '''

        counts = Counter(word)
        result = []

        for i, letter in enumerate(guess):
            if guess[i] == word[i]:
                result += guess[i]
                counts[guess[i]] -= 1
            else:
                result += '+'

        for i, letter in enumerate(guess):
            if guess[i] != word[i] and guess[i] in word:
                if counts[guess[i]] > 0:
                    counts[guess[i]] -= 1
                    result[i] = '-'

        return "".join(result)


    def update_candidates(self, result: str):
        '''
        Update the possible candidates based on the feedback received.

        :param result: feedback string
        :return: None
        '''

        _allowed_candidates = [
            word for word in self.allowed_candidates
            if self.get_matches(word, self.tried[-1]) == result
        ]
        _candidates = [
            word for word in self.candidates
            if self.get_matches(word, self.tried[-1]) == result
        ]

        self.allowed_candidates = _allowed_candidates
        self.candidates = _candidates


    def compute_letters_freq(self):
        '''
        For each letter in the word list, compute both:
        - its overall freq
        - its freq for each position

        :return: a tuple with the overall freq and the freq in each position
        '''

        letters_freq = dict(Counter("".join(self.candidates)))
        pos_letters_freq = {i: dict(Counter([word[i] for word in self.candidates])) for i in range(5)}

        for letter, freq in letters_freq.items():
            assert freq == sum(
                [positions_freq.get(letter, 0) for positions_freq in pos_letters_freq.values()]
            ), f"Unmatched frequencies for letter '{letter}'"

        return letters_freq, pos_letters_freq


    def get_top_words_prob(self, letters_freq, pos_letters_freq, allowed=False, k=10):
        '''
        Get the top k words based on their letters distribution.

        :param letters_freq: overall freq of each letter
        :param pos_letters_freq: freq of each letter in each position
        :param possible: whether to consider just the possible candidates or all allowed words
        :param k: number of words to return
        :return: top k words
        '''

        top_words = {}
        for word in (self.allowed_candidates if allowed else self.candidates):
            score = sum(
                [letters_freq.get(letter, 0) + pos_letters_freq[i].get(letter, 0) for i, letter in enumerate(word)]
            )
            score *= len(set(word)) / 5
            top_words[word] = score

        top_words = list(dict(sorted(
            top_words.items(), key=lambda item: item[1], reverse=True)[:k]
        ).keys())
        return top_words


    def compute_h_guess(self, guess: str) -> float:
        '''
        Compute the entropy of a guess against all possible feedbacks.

        :param guess: guessed word
        :return: h(guess)
        '''

        pattern_counts = defaultdict(int)
        for word in self.candidates:
            pattern_counts[self.get_matches(word, guess)] += 1

        prob = [count / len(self.candidates) for count in pattern_counts.values()]
        h_guess = -sum([p * log2(p) for p in prob])
        return abs(h_guess)


    def guess(self):
        '''
        Make the guess based on the game state:
        - first narrow the candidates if the number at the beginning of the game
        - then pick the best h(x)

        :return: the guess and its h(x)
        '''

        if len(self.tried) < 1:
            letters_freq, pos_letters_freq = self.compute_letters_freq()
            guesses = self.get_top_words_prob(
                letters_freq=letters_freq,
                pos_letters_freq=pos_letters_freq,
                allowed=True,
                k=10
            )
        else:
            guesses = self.candidates

        best_guess = None
        best_h = 0
        for guess in guesses:
            entropy = self.compute_h_guess(guess)
            if entropy >= best_h:
                best_guess = guess
                best_h = entropy

        return best_guess, best_h


    def get_guess(self):
        if not self.tried:
            guess, h = self.first_guess
        else:
            self.update_candidates(result=self.feedbacks[-1])
            guess, h = self.guess()
            if not guess:
                raise ValueError("No candidates left")

        return guess, h
