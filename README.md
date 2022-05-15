# Resu

\[Resu\]me your progress in any Python loop


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
from resu import Progress

def process(x):
    time.sleep(1)

p = Progress()
p.insert(range(1000))
p.record(process)

#   0%|▏                                         | 24/1000 [00:05<16:40,  1.01s/it]
# ^C KeyboardInterrupt (id: 2) has been caught...
# Saving progress before terminating the program gracefully...
# Progress was saved to: `./1652598207.ckpt`
```

- Then you can resume with:

```py

# ...

p.resume('1652598207.ckpt')
p.record(process)

# Resuming... Skipped 24 completed enteries.
#   0%|                                          | 2/1000 [00:02<16:40,  1.00s/it]
```

### Example 2:

```py
import time
import requests
from resu import Progress

def process(x, url, cooldown):
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    resp = requests.post(url, headers=headers, data=x)
    time.sleep(cooldown)
    return resp.text

p = Progress()
p.insert('customers_data.json')
results = p.record(
    process,
    url='https://reqbin.com/echo/post/json',
    cooldown=1,
    checkpoint_every=5)

#   0%|          | 0/11 [00:00<?, ?it/s]
#   8%|▊         | 1/11 [00:02<00:11,  1.10s/it]
#  17%|█▏        | 2/11 [00:03<00:25,  1.10s/it]
#  27%|██▋       | 3/11 [00:07<00:20,  1.10s/it]
#  35%|███▍      | 4/11 [00:09<00:18,  1.10s/it]

#  Writing a checkpoint...

#  38%|███▊      | 5/11 [00:11<00:17,  1.10s/it]
#  52%|████▏     | 6/11 [00:12<00:16,  1.10s/it]
#  69%|██████▉   | 7/11 [00:19<00:08,  1.10s/it]

# ...failed for some reason.
```

- Assuming the program failed for some reason, you can easily resume like described in `Example 1`.

