import operator # Wouldn't need this module with python3...

# ...nor this function because itertools has its own accumulate
def accumulate(iterable, func=operator.add):
  it = iter(iterable)
  total = next(it)
  yield total
  for element in it:
    total = func(total, element)
    yield total

# The natural distribution over tokens
def up(probabilities):
  return probabilities

# The unnatural distribution over tokens
def down(probabilities):
  probabilities.reverse()
  return probabilities

# Linearly interpolate up and down...
def strange(probabilities):
  # ...where the mixture parameter is hard-coded as 0.5
  return [sum(t) / 2 for t in zip(*[probabilities, probabilities[::-1]])]

def categorical_sample(tokens, probabilities, flavor):
  from bisect import bisect
  from random import random
  # from itertools import accumulate

  # sort the distribution to make the transformations trivial
  probabilities, tokens = [list(t) for t in zip(*sorted(zip(probabilities, tokens)))]

  flavors = { 'up' : up, 'down' : down, 'strange' : strange }
  probabilities = flavors[flavor](probabilities)

  cumulative_probabilities = list(accumulate(probabilities))
  # Normalize the cumulative probabilities which is necessary because of...
  uniform_variate = random() * cumulative_probabilities[-1] # ...smoothing
  sample_index = bisect(cumulative_probabilities, uniform_variate)

  return tokens[sample_index]

class Ngram(object):
  def __init__(self, lm_file, model_type):
    from collections import defaultdict
    from copy import deepcopy

    self._arpa_model_header = []
    self._ngram_buckets = []
    self._ngram_bw_store = {}
    self._distribution = {}
    self.model_type = model_type

    with open(lm_file) as f:
      next(f) # skip 1st line
      next(f) # skip 2nd line

      for line in f:
        if not line.strip():
          break
        self._arpa_model_header.append(int(line.strip().split('=')[-1]))

      for bucket in xrange(len(self._arpa_model_header)):
        next(f) # skip r'\\\d+-grams:'
        ngram_cp_store = defaultdict(list) if bucket else {}
        for line in f:
          if not line.strip():
            break
          try:
            cp, ngram, bw = line.strip().split('\t')
            self._ngram_bw_store[ngram] = float(bw)
          except ValueError:
            cp, ngram = line.strip().split('\t')
          if ngram.count(' '):
            prefix, suffix = ngram.rsplit(' ', 1)
            ngram_cp_store[prefix].append((suffix, float(cp)))
          else:
            ngram_cp_store[ngram] = float(cp)
        self._ngram_buckets.append(ngram_cp_store)

    self._distribution = deepcopy(self._ngram_buckets[0])

  def _ngram_backoff(self, flavor, history, n):
    # The lambda transforms a dictionary into tokens and probabilities...
    f = lambda x: zip(*[(k, 10 ** v) for k, v in x])

    # We already applied the Markov assumption to the history but recall the...
    n = min(len(history) + 1, n) # ...history length can be less than n-1...
    # ...this effectively limits the model order so we must reconcile the two

    # The key-value stores index the ngrams by their prefix
    prefix = ' '.join(history)

    # Recurse on the order until we find the prefix...
    if n == 1: # ...where unigrams serve as the base case
      # The 0th bucket is a dictionary of unigrams...
      tokens, probabilities = f(self._ngram_buckets[0].items())
      return categorical_sample(tokens, probabilities, flavor)
    # The buckets are zero-indexed so the current highest order...
    elif prefix in self._ngram_buckets[n-1]: # ...is n-1 where the...
      # ...list of tuples is a conditional distribution for the next token
      tokens, probabilities = f(self._ngram_buckets[n-1][prefix])
      return categorical_sample(tokens, probabilities, flavor)
    else: # If we haven't reached the base case then truncate the history and...
      # ...recurse on the order but this won't work unless the history length...
      return self._ngram_backoff(flavor, history[1:], n-1) # ...and the order...
      # ...are synchronized

  def _ngram_interpolate(self, flavor, history, n):
    # Init the distribution before each order has a chance to contribute...
    for token in self._distribution: # ...probability mass to the distribution
      self._distribution[token] = 0.0

    # Init the backoff weight to 1.0 for the highest order
    backoff_weight = 1.0

    # We already applied the Markov assumption to the history but recall the...
    n = min(len(history) + 1, n) # ...history length can be less than n-1...
    # ...this effectively limits the model order so we must reconcile the two

    # Loop through the orders rather than use recursion
    for order in xrange(n, 0, -1): # Start at the highest order and walk down
      # Update the history by applying the Markov assumption after an...
      history = history[-(order-1):] # ...iteration decrements the order
      prefix = ' '.join(history)

      # Find the highest order that contains a prefix slice...
      if prefix not in self._ngram_buckets[order-1]:
        # ...the orders that don't contain a prefix slice...
        continue # ...will not factor into the interpolation

      if order == 1:
        # Loop through the unigram distribution
        for token, probability in self._ngram_buckets[0].items():
          # Probabilities are still in log space where we should probably stay
          self._distribution[token] += backoff_weight * (10 ** probability)
      else:
        for token, probability in self._ngram_buckets[order-1][prefix]:
          # Probabilities are still in log space where we should probably stay
          self._distribution[token] += backoff_weight * (10 ** probability)
        # Weights are stored in log space too and we only update them when...
        backoff_weight *= (10 ** self._ngram_bw_store[prefix]) # ...order > 1

    tokens, probabilities = zip(*[(k, v) for k, v in self._distribution.items()])

    return categorical_sample(tokens, probabilities, flavor)

  def stream(self, flavor='up', history=[], length=1):
    from copy import deepcopy
    # If the history length from the client is less than n-1 then H will...
    H = deepcopy(history) # ...anchor the history to bootstrap the context

    n = len(self._arpa_model_header) # The order of the language model

    # Apply the Markov assumption to the history which ensures the history...
    history = history[-(n-1):] # ...length is \leq n-1 but note that the...
    # ...history length may be less than n-1 which would effectively limit n

    # sentence is the list of strings that will constitute the stream field...
    sentence = [] # ...in the server's response document

    # Generate a sentence with length number of words
    for i in xrange(length):
      if self.model_type is 'backoff':
        # Use backoff to generate the next word in the sentence
        sentence.append(self._ngram_backoff(flavor, history, n))
      elif self.model_type is 'interpolate':
        # Use interpolate to generate the next word in the sentence
        sentence.append(self._ngram_interpolate(flavor, history, n))
      # Models larger than unigrams need to update their context after...
      if n > 1: # ...appending a word but note that H will be useless...
        # ...if/when the sentence length reaches n-1
        history = (H + sentence)[-(n-1):]

    return sentence
