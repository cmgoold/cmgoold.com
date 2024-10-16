One of the easiest entries into generative modelling
is learning about ordinal models.
Ordinal data is highly prevalent in a number of
research fields, but is frequently modelled
as metric, which can lead to a number of problems.

## The ordinal data-generating process

Invisage a latent, metric random variable, \\(X\\),
which we assume is normally distributed with location
\\(\mu\\) and scale \\(\sigma\\):

\\[
\begin{equation}
X \sim \mathrm{Normal}(\mu, \sigma)\\ 
\end{equation}
\\]

Here's some `code`:

```python
from typing import List

def function(x: str) -> List[str]:
    x = [x for _ in range(10)]
    return x

class X(object):
    pass
```
