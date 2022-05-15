# Resu

[![Build checks](https://github.com/Alyetama/resu/actions/workflows/build-checks.yml/badge.svg)](https://github.com/Alyetama/resu/actions/workflows/build-checks.yml) [![Supported Python versions](https://img.shields.io/badge/Python-%3E=3.6-blue.svg)](https://www.python.org/downloads/) [![PEP8](https://img.shields.io/badge/Code%20style-PEP%208-orange.svg)](https://www.python.org/dev/peps/pep-0008/) 

\[**Resu**\]me your progress in any *Python loop* by automatically creating checkpoints without changing your workflow.


## Requirements
- [python>=3.6](https://www.python.org/downloads/)

## Installation

```shell
pip install resu
```

## Examples


### Example 1:

```py
import time
from resu import Checkpoint

def process(x):
    time.sleep(1)
    return x + 1

c = Checkpoint()
c.insert(range(1000))
c.record(process)

#   0%|▏                                         | 24/1000 [00:05<16:40,  1.01s/it]
# ^C KeyboardInterrupt (id: 2) has been caught...
# Saving progress to checkpoint file `./1652598207.ckpt` before terminating the program gracefully...
```

- You can resume the same loop by calling the `p.resume` method and passing the checkpoint file path to it before running the program again:

```py

# ...

c.resume('1652598207.ckpt')
c.record(process)

# Resuming from `1652598207.ckpt`... Skipped 24 completed enteries.
#   0%|                                          | 2/1000 [00:02<16:40,  1.00s/it]
```

### Example 2:

```py
import time
import requests
from resu import Checkpoint

def process(x, url, cooldown):
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    resp = requests.post(url, headers=headers, data=x)
    time.sleep(cooldown)
    return resp.text

c = Checkpoint(ckpt_file='/my/custom/ckpt/name.ckpt')
c.insert('customers_data.json')
results = c.record(
    process,
    url='https://reqbin.com/echo/post/json',
    cooldown=1,
    checkpoint_every=5)

#   0%|          | 0/11 [00:00<?, ?it/s]
#   8%|▊         | 1/11 [00:02<00:11,  1.10s/it]
#  17%|█▏        | 2/11 [00:03<00:25,  1.10s/it]
#  27%|██▋       | 3/11 [00:07<00:20,  1.10s/it]
#  35%|███▍      | 4/11 [00:09<00:18,  1.10s/it]

#  Saving progress to checkpoint file: `/my/custom/ckpt/name.ckpt`...

#  38%|███▊      | 5/11 [00:11<00:17,  1.10s/it]
#  52%|████▏     | 6/11 [00:12<00:16,  1.10s/it]
#  69%|██████▉   | 7/11 [00:19<00:08,  1.10s/it]

# ...
```

- Let's say your program failed for some reason, you can easily resume like described in `Example 1`.

