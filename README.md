# Helion
![](https://img.shields.io/badge/python-3.7-brightgreen.svg) 

Helion is a data-driven framework that models the regularities of user-driven home automation, generates natural home automation scenarios, and provides stakeholders with tools to use the scenarios and obtain actionable outcomes.

## Getting Started
To make it easier to run, respective library files are included in the project itself.

### Quick Setup:
#### 1. Add proper directories to your path:

Execute the Following commands or add them to your .bash_profile to set up your $PATH. **Be sure to replace the paths with 
local paths on your machine**

```
export PYTHONPATH=$PYTHONPATH:/Path/to/helion/libs/Daemon/python-daemon-2.2.0/
export PYTHONPATH=$PYTHONPATH:/Path/to/helion/libs/Daemon/python-daemon-2.2.0/daemon/ 
export PATH=$PATH:/Path/to/helion/libs/mitlm-master/
export PATH=$PATH:/Path/to/helion/libs/kramer-master/
```
#### 2. Follow the instruction for respective scripts file.

### Alternative Method:
If the quick setup method does not work, please install the latest version of libraries.
#### 1. Download necessary files:
* [MITLM](https://github.com/mitlm/mitlm) - MIT Language Modeling Toolkit
* [Python Daemon 1.5.5](https://pypi.python.org/pypi/python-daemon/) - Library to implement a well-behaved Unix daemon process.
* [Brain Files](https://github.com/martingwhite/kramer) - The language model server script which reads/writes JSON documents to named pipes. 

#### 2. Untar MITLM and Python Daemon:

Execute the following command to un-tar the the MITLM and python daemon packages:

`$ tar-xzf <package_name.tar.gz>`

#### 3. Add proper directories to your path:

Execute the Following commands or add them to your .bash_profile to set up your $PATH. **Be sure to replace the paths with 
local paths on your machine**

```
export PYTHONPATH=$PYTHONPATH:/Path/to/Python/Daemon/python-daemon-1.5.5/
export PYTHONPATH=$PYTHONPATH:/Path/to/Python/Daemon/python-daemon-1.5.5/daemon/ 
export PYTHONPATH=$PYTHONPATH:/Path/to/Python/Daemon/python-daemon-1.5.5/daemon/version/ 
export PATH=$PATH:/Path/to/MITLM/mitlm-0.4.1/ 
export PATH=$PATH:/Path/to/Brain/Files/
```
#### 4. Build MITLM: 

Navigate to the mitlm-0.4.1/ directory and execute the following commands:

```
$ ./configure
$ make
```

After both of these commands have been executed, you should be able to see the estimate-ngram, evaluate-ngram, and interpolate-ngram executables in the mitlm-0.4.1/ directory.

#### 5. Instantiate the Brain:

Navigate to the folder where your training and vocabulary files are located.  Then instantiate the brain by running:

```
$ braind data/helion.train data/helion.vocab
```

For more detailed instructions on how to interact and instantiate the Brain, see the [README](https://github.com/martingwhite/kramer).


### Acknowledgements:
* [Kramer](https://github.com/martingwhite/kramer)
* [MITLM](https://github.com/mitlm/mitlm)
