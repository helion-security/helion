kramer
======

## Requirements
0. Linux (with write access to `/tmp`)
1. Python 2.7.6
2. MIT Language Modeling Toolkit

### Notes
* I am using SUSE running 3.11.10-17.
* You may need to install [python-daemon
1.5.5](https://pypi.python.org/pypi/python-daemon/ "python-daemon"). See [PEP
3143](http://legacy.python.org/dev/peps/pep-3143/ "PEP 3143") for example usage.
* You must install the [MIT Language Modeling
Toolkit](https://code.google.com/p/mitlm "mitlm"), and the tools must be in your
path.

## Description

See `braind -h` for basic usage. **The exception handling is limited.**

### Configuring the server

The brain estimates two n-gram language models, fixing the vocabulary for each
model to tokens from a specified file. Optionally, you can set the order
(default=3) and you can specify the smoothing algorithm (default='ModKN').
Assuming `braind` is in your path, enter

```bash
$ braind path/to/training/data path/to/vocabulary/file
```

This will estimate a trigram back-off model using Modified Kneser-Ney smoothing
from the training data and write the ARPA file to `/tmp/blm`. It will also
construct a statically interpolated model from component n-gram models and write
the ARPA file to `/tmp/ilm`.

The vocabulary file must have one token on each line. To build an exemplar
vocabulary file from the Shakespeare corpus, enter

```bash
$ estimate-ngram -text shakespeare.txt -write-vocab shakespeare.vocab
```

Tokens in the vocabulary file that are not in the training data will be factored
into the models' unigram estimates.

Then the brain will make two named pipes, `/tmp/fifo0` and `/tmp/fifo1`, to
serve as communication channels to/from the n-gram server before daemonizing the
process.

When the server is started, the first thing it will do is deserialize `/tmp/blm`
and `/tmp/ilm` into distinct key-value stores. Obviously, this is a horribly
inefficient data structure for this purpose, but performance is not the key
concern for our current work. The prompt will return after the server loads the
language models. You can verify the server is running by examining the
output of `ps x`.

### Communicating with the server

Clients can communicate with the language model server by reading/writing JSON
documents to the two named pipes. A client should write requests to `/tmp/fifo0`
and read responses from `/tmp/fifo1`.

A request is a JSON document with four fields: `model`, `flavor`, `history` and
`length`.

* `model` can take one of two values: `backoff` or `interpolate`.

* `flavor` can take one of three values: `up`, `down` or `strange`. `up`
corresponds to the *natural* distribution over a set of tokens. `down`
corresponds to the *unnatural* distribution. `strange` linearly interpolates
`up` and `down` where lambda is 0.5.

* `history` contains the initial prefix as an array of strings. If you do not have
a prefix, then the history field must be the empty string (i.e., `"history" :
[""]`). Also, suppose you estimate a language model where `--order` is greater
than one and you request a stream longer than one token. In this case, if you
don't have a history (or the length of the history is suboptimal), then the
brain will essentially bootstrap the history to length `n-1`, where `n` is the
order of the model. For instance, if you estimated a trigram and you request a
stream four tokens long but you don't have a history, then the brain will query
the unigrams for the first token. Then it will query the bigrams, using the
first token, for the second token. Then it will query the trigrams, using the
first two tokens, for the third token. Finally, it will query the trigrams,
using the two most recent tokens, for the fourth token in the stream.

* `length` is an integer which governs the length of the sentence to query from
the language model.

A minimal request has the form

```json
{ "model" : "backoff", "flavor" : "up", "history" : [""], "length" : 1 }
```

The server will respond with a unigram sample from the back-off model using the
natural distribution over unigrams.

Note that the brain will apply the Markov assumption to your history. In other
words, the history will be sliced according to the order: `history[-(n-1):]`.
This means that if you estimate trigram models, but your history is `["Because",
"I", "could", "get", "Uromysitisis", "poisoning", "and", "die", "."]`, then the
brain will only consider `["die", "."]` when it queries a trigram.

> Because I could get Uromysitisis poisoning and die. That's why! Do you think I
> enjoy living like this? The shame? The humiliation? You know I have been
> issued a public urination pass by the city because of my condition.
> Unfortunately my little brother ran out of the house with it this morning. Him
> and his friends are probably peeing all over the place. You want to call the
> Department of Social Services? Oh, it's Saturday. They're closed today. My
> luck.

The response is a JSON document with one field: `stream`.

`stream` contains the sampled sentence as an array of strings. Here is an
example using the Seinfeld corpus:

```bash
cat request
{ "model" : "backoff", "flavor" : "up", "history" : ["die", "."], "length" : 3 }
cat request > /tmp/fifo0 && cat /tmp/fifo1
{ "stream" : ["That's", "why", "!"] }
```

The response is a sequence of three tokens. The sequence is seeded by the history,
and the tokens are sampled from the back-off model using the natural
distribution over tokens.

### Killing the server

Send a SIGTERM to kill the daemon: `kill PID`. A simple handler has been
implemented to clean up the `/tmp` scratch files.
