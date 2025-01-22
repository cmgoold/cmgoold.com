The third series of BBC's *The Traitors* is entering its
final week. We watch very little reality TV, but
this is a bit of an exception. If you haven't seen it, 
contestants live together for a number of weeks
and complete challenges to add money to a prize pot.
An unknown number of the contestants are chosen at the
start to be *traitors*, while the rest are *faithful*.
It's the traitors' job to choose people to 'murder', i.e.
banish from the game, faithfuls, hopefully taking the whole
prize money home themselves when there are no faithfuls left.
It's the faithfuls' job to, through daily round-table
discussions, figure out who the traitors are, and banish
them from the game, taking the prize money between themselves.
Chaos ensues.

There's are multiple
psychological, economic, and statistical 
topics that could be analysed here.
One it lends itself conveniently to is the
world of Bayesian model averaging and, relatedly,
mixture modelling.

John Kruschke, the author of *Doing Bayesian Data Analysis*,
defines Bayesian analysis as a reallocation of credibility
across possible parameter values. 
Bayesian model averaging is, similarly,
a reallocation of credibility across possible models.
Those models are different views of the data generating
processes, and Bayesian model averaging's goal is to
provide us with each model's posterior probability consistent
with the data. These probabilities are the
*posterior model probabilities*.

Imagine the round-table discussions on *The Traitors*.
For each player in the game, denoted \\(i = 1, ..., N\\),
they each make a vote, \\(v_{i}\\), at each round-table
for who they believe the traitor is. Votes are a discrete
random variable assigning either a 1, if their vote correctly
identifies a traitor, or
0, if uncorrect. 
While there certaintly are some backstabbing strategies
where traitors vote for eachother, we'd usually expect traitors
to be less likely to vote for their fellow murderers than
faithfuls, all else being equal and assuming rational game-play.
In reality, faithfuls are anything but rational.

Here's the model $x \sim Normal$

Let's write a model down for these assumptions.
Votes for each player $v_{i}$ are assumed
Bernoulli distributed:

\[
\begin{align}
    v_{i} &\sim \text{Bernoulli}(\theta_{z_{i}}) \\
    \theta_{z_{i}} &\sim \text{Beta}(\alpha, \beta) \\
    z_{k} &\sim \text{Categorical}(w) \\
    w &\sim Dirichlet(\gamma)
\end{align}
\]

The designation for traitor or faithful is denoted
by the discrete random variable 
\\(Z = \\{\mathrm{traitor}, \mathrm{faithful}\\}\\).
