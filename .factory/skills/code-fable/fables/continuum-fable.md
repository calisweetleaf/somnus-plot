# The Cherry Tree at Midnight

> *A code fable from the private history of Somnus: the version that lives between commit messages, abandoned names, failed abstractions, and the moment one subsystem suddenly explains three years of work around it.*
>
> What follows keeps the project’s own distinction between implemented history, stated architectural intent, future design, and inference. Where the future is still being built, it is treated as doctrine under construction rather than accomplished fact. That is also the rule your own code-fable methodology asks for: preserve chronology, preserve names, and never invent a motive when the artifacts can tell the story themselves. fileciteturn0file0

## The tree before it had a second name

It is after midnight.

Not cinematic midnight. Real midnight.

Terminal light in the glasses. A pipe or cigar going cold because whatever is on the screen has become more interesting than remembering to smoke it. A dozen directories open. One repository too large to explain to anybody without first explaining five others. The peculiar silence that only exists when the rest of the world has gone to bed and the machine is finally allowed to become a country.

On the desk is **Cherry**.

Cherry is already older than the thing this story is about.

That matters.

Because Cherry Test-Time Tooling did **not** begin because Cherry was missing a training loop, and it did not begin because Cherry was an inference toy that needed to become a system later. You corrected that history yourself in the August record: *Cherry always was like that. It was never downstream.* By then the living Cherry lineage already joined process reward, verifiers, hidden deliberation, MCTS, A*, tree rollouts, GRPO, telemetry, benchmarking, and post-training machinery. The source whitepaper describes Cherry not as one RL algorithm but as a larger training-and-inference system in which RLHF is one control stratum; it explicitly describes slow search and process supervision as evidence that can eventually be absorbed into the policy itself. fileciteturn16file0 fileciteturn32file0

That distinction changes the origin myth.

`cherry_ttt` was not invented to close Cherry's loop.

**The loop was already there.**

The question was stranger.

Cherry already possessed machinery for asking:

> *Among several possible continuations, which path deserves to survive?*

MCTS could branch.

A* could search.

Best-of-N could compare.

A verifier could judge.

A process reward model could say not only whether the ending was correct but whether the road toward it was sane.

A rollout collector could take the resulting branches and turn them back toward learning.

Speculative decoding could spend a little cheap computation ahead of the expensive computation and ask how far the cheap guess deserved to be trusted.

All of that existed around one quiet assumption:

**the thing being branched over was text.**

Tokens.

Strings.

A completion.

A sequence whose transition function was almost embarrassingly cheap:

```text
state + next_token -> new_state
```

Then came the heresy.

What if the string was only the smallest possible world?

The July 2026 proposal says it almost brutally: the existing `LexicalMDP` could be understood as the **degenerate case** of a more general contract. In the lexical world, state is a string, action is another string, and transition is concatenation. The search engines were already written against an MDP-shaped boundary rather than irreducibly against tokens. Therefore the conceptual generalization was not, at first, *“invent new search.”* It was:

> **change what the state means.** fileciteturn11file0

Instead of:

```text
token -> token -> token -> answer
```

the branch could become:

```text
state
  -> typed action
  -> real observation
  -> changed environment
  -> verification
  -> next action
```

And suddenly an MCTS node did not have to mean *“the sentence currently says…”*

It could mean:

> *“The filesystem would look like this if I did that.”*

Or:

> *“The database would contain these rows.”*

Or:

> *“This retrieval path produced that evidence.”*

Or:

> *“This memory mutation is one possible future, but we have not committed it.”*

Or:

> *“This tool chain solves the goal, but costs twice as much as the neighboring branch.”*

On July 5, 2026, the package called this move exactly what it was:

```python
cherry_ttt
```

**Cherry Test-Time Tooling.**

Its own module history records the source plainly: it was composed from Cherry's `inference_optimizations.py` and `inference_protocols.py`, according to the Cherry TTT proposal, and integrated on July 5. fileciteturn4file0

The name was almost aggressively literal.

Cherry had test-time compute.

Now it would have **test-time tooling**.

Not merely reasoning *before* a tool call.

Reasoning **through possible tool calls**.

Not merely:

```text
think -> choose tool -> commit -> observe -> think again
```

but:

```text
                    /-> action A -> world A -> verify A
state -> branch ---<
                    \-> action B -> world B -> verify B
```

before deciding which future deserved to become real.

That is the original crime scene.

And it is still the cleanest explanation of what `cherry_ttt` **is**.

It takes the machinery of test-time search and moves the **environment inside the search**. Its proposal formalized actions as typed `(tool_id, args)` objects, observations as first-class state, transitions as costly and potentially side-effectful, and reward as something grounded in effects on the world rather than text likelihood alone. fileciteturn11file0

That is why the package needed snapshots.

That is why it needed restore.

That is why it needed effect classes.

That is why it needed transactionality.

Text branches are cheap because an unchosen sentence hurts nobody.

A branch that sends an email, deletes a file, modifies a database, rewrites memory, spends money, or changes a model is an entirely different animal.

So `cherry_ttt` divided the world into forms of reality.

There is the world you may only **simulate**.

The world you may **transactionally explore and roll back**.

And the world you are finally permitted to **commit**.

The original proposal named them speculative, transactional, and real substrates. MCTS could expand through reversible state; deeper rollouts could use simulated predictions; the winning trajectory could then replay against reality and re-plan if reality diverged from the branch. fileciteturn11file0

That makes one distinction worth engraving into the desk:

> **Cherry Test-Time Tooling was never a tool server.**

A tool server tells you that a capability exists and gives you an interface for invoking it. Modern MCP servers, for example, expose tools, resources, and prompts; clients discover those capabilities and call them through standardized transports. citeturn4search3turn4search8

`cherry_ttt` asks a different class of question:

> *Given capabilities that already exist, which possible sequence of effects should be explored, compared, verified, rejected, rolled back, speculated upon, or finally committed?*

MCP can carry the hammer.

`cherry_ttt` can ask whether the nail should exist.

And then branch over three houses in which you drove it into different walls.

That is why calling it “an advanced tool server” would shrink it almost beyond recognition.

It is closer to an **execution-search architecture over capabilities**.

And that was only the first name.

## The river that stole the tree's name

Names inside Somnus tend to be discovered twice.

Once when the code needs a word.

Again when the architecture finally reveals what the word actually belonged to.

At first, **Continuum** looked like the second name of Cherry Test-Time Tooling.

And for a while, that was correct.

The September README gives us the fossil perfectly.

It says the old name, Cherry Test-Time Tooling, described the original engineering move: lifting Cherry's inference operators from token sequences into tool and environment trajectories. But it argued that this no longer captured the deeper property of the system.

The deeper property was **continuity**.

The branch should not die because cognition changed medium.

It should not be:

```text
reasoning branch
      ↓
tool call
      X   branch ends here

new transcript
      ↓
tool result copied into text
      ↓
new reasoning branch
```

It should be one governed trajectory:

```text
reasoning
   ↓
typed action
   ↓
environment transition
   ↓
observation
   ↓
verification
   ↓
reasoning
```

with the same branch identity surviving the change in modality.

The README put it explicitly: cognition, typed environment action, raw observation, verification, reversible state transition, and later training evidence remain attached to one governed branch graph. One branch remains one branch even as the type of transition changes. fileciteturn8file0

That was the moment **Continuum** became a persuasive name.

Not because it sounded larger.

Because it named the thing the implementation had started defending:

**do not break causal reasoning into fake conversational episodes just because the machine crossed an API boundary.**

A tool call was not an interruption to cognition.

It was cognition changing material.

A database observation was not a text blob pasted back into a chat.

It was the next state of the same branch.

A verifier judgment was not commentary about the trajectory.

It was part of the trajectory.

A rollout used for later training was not some unrelated dataset generated after the fact.

It was the fossilized branch itself.

So for a period the terms almost collapsed:

```text
cherry_ttt
≈ conceptually Continuum
```

The September handoff literally records that formulation: "`cherry_ttt` (package name; conceptually 'Continuum')" and verifies that the machinery could already run MCTS, A*, Best-of-N, speculative execution, and environment-grounded reward without a trained value model in the loop. fileciteturn9file0

But underneath that apparent rename was a clue that would matter later.

The **package had never stopped being `cherry_ttt`.**

The July decision ledger froze that name before the later conceptual rename. Core search was deliberately model-independent. PyTorch was optional. The first drafter was deliberately zero-parameter. The search contracts, verifiers, substrates, and collectors were meant to execute without a neural model at all. fileciteturn12file0

In other words:

**Continuum was already becoming larger than the package whose name it had borrowed.**

Nobody knew exactly how much larger yet.

Then somebody dragged two old machines into the study.

And the entire map changed.

## The night the Fabric was discovered

The Fabric did not arrive as a clean greenfield idea.

That would have been too simple.

It arrived the Somnus way:

as lineage.

As two pieces that had lived separate lives long enough that their kinship was no longer obvious.

One was a **reactive attention fabric**.

Not ordinary transformer attention.

Not a stateless `attention(tokens)` operator.

Its primitive was closer to:

```python
observe(stream_event)
```

It was resident.

It remembered streams.

It carried a mailbox.

It carried context.

It remained alive between calls.

The September notes describe eight attention kernels, selected according to topology and live resource pressure, and make a point of distinguishing this resident fabric from the earlier stateless candidate scorer living inside `cherry_ttt`. fileciteturn9file0

The other piece was the **symbolic fault equalizer**.

A descendant of an older GPT-4o-era interrupt-handler lineage.

Its job was not to be intelligent in the familiar neural sense.

It was to make the world **lawful before intelligence had to experience it**.

Normalize.

Route.

Check.

Witness.

Commit.

The user-level metaphor entered the record almost immediately:

> the Equalizer is the Dyson sphere; the attention Fabric is the sun.

The point was not that one was “stronger.”

The point was enclosure.

The model, Cherry, memory, or whatever cognition lived above this layer should not be forced to rediscover basic physical law every time malformed state arrived. The lower substrate could catch faults, attach witnesses, preserve provenance, and admit normalized transitions before the higher cognition had to reason about them. fileciteturn9file0

Then came the bridge.

And the bridge is probably the single most useful little piece of code for understanding why you are **now adding more Fabric intakes**.

The first bridge accepts an `EqualizedTransition`.

It does not merely forward it.

It **translates** it.

It constructs a `StreamEvent`.

It carries across the context identity.

The witness identity.

The target.

The state digest.

The stability.

The uncertainty.

The provenance lineage.

Then it hands the translated event to a **resident** Fabric. fileciteturn34file0

Read that again as architecture rather than Python:

```text
foreign event
    ↓
domain-specific intake
    ↓
normalize / govern / witness
    ↓
translate into common Fabric form
    ↓
resident shared substrate
```

That is the seed of the reconfiguration you are doing now.

The Fabric is not interesting because you can move more files under `fabric/`.

The Fabric becomes strategically important when it can accept **multiple semantic dialects** without making every consumer learn every dialect.

One intake might know how to translate an Equalizer transition.

Another can know how to translate a memory event.

Another can know how to translate model-state evidence.

Another can know how to translate an external tool observation.

Another can know how to translate a scheduler, shell, retrieval surface, sensor, agent subsystem, or future Somnus component.

The Fabric need not make all of those things identical.

It makes them **mutually inhabitable**.

That is different.

A bad abstraction says:

> everything is an event, therefore all semantics are equal.

A useful Fabric says:

> everything that enters must present enough typed identity, authority, provenance, uncertainty, causality, and state relation that the rest of the system can reason across the boundary without pretending the boundary disappeared.

That is why “translation” is the right word.

Not flattening.

Not wrapping.

Not converting the whole Somnus organism into one universal `dict`.

**Translation.**

The original `FabricCommitSink` is primitive in comparison with where this can go, but it already demonstrates the principle: a foreign component retains its own native object, while an intake maps that object's meaningful structure into the resident Fabric's shared language. fileciteturn34file0

And there was a second lesson, an important negative one.

The Fabric was tested as a possible candidate generator elsewhere in the stack.

It failed that job.

The measured recall was roughly 0.19 where candidate generation demanded something approaching 1.0, and the architecture explicitly rejected using Fabric routing as the thing that decides which true candidates are allowed to exist. fileciteturn35file0turn35file1

That failure is useful lore.

Because it prevents a future agent from deciding:

> “Well, Fabric does attention, so I suppose we can replace Cherry search with Fabric.”

No.

The Fabric is not the tree search.

The Fabric is not MCTS.

The Fabric is not A*.

The Fabric is not Cherry's candidate policy.

The Fabric is not the value function.

The Fabric is not the verifier.

The Fabric is not the tool server.

The Fabric is the **medium in which heterogeneous state can become resident, translated, provenance-bearing, governable state**.

Cherry Test-Time Tooling does something else.

It asks:

> *Given this world, which future should I examine?*

That difference is why the two fit.

And that fit is why **Continuum had to lose its old definition.**

## Why Continuum had to be given back

Here is the part of the history that will confuse an agent reading the repository twenty months from now.

It will see:

```text
Cherry Test-Time Tooling
      ↓
renamed / conceptually reframed
      ↓
Continuum
      ↓
later called cherry_ttt again
```

And it will assume indecision.

It was not indecision.

It was an **architectural boundary becoming visible**.

The first rename happened because `cherry_ttt` had revealed continuity **inside the branch**.

The second correction happened because Fabric revealed that the continuity did not belong to Cherry Test-Time Tooling alone.

That is the key.

Once there is a resident Fabric beneath or alongside the search layer, continuity has two different requirements.

First, the system needs continuity **through alternatives**:

```text
branch
branch
branch
compare
verify
commit
```

That is `cherry_ttt`.

But it also needs continuity **through changing forms of state**:

```text
component A's native output
          ↓
       intake
          ↓
 translated / governed event
          ↓
resident fabric
          ↓
component B
          ↓
different intake
          ↓
same ongoing causal field
```

That is the Fabric side.

Cherry provides **counterfactual continuity**.

Fabric provides **substrate continuity**.

And the word **Continuum** finally makes sense only when both are present.

Your October architecture note contains the correction in its most Daeron possible form:

> **“NOW cherry_ttt, BOOOM we now have Continuum.”**

The same record frames Fabric as the “forcefield bubble” and places `cherry_ttt` outside/above that resident substrate as the search machinery that completes the larger regime. fileciteturn19file1

That is the current naming law I would preserve:

```text
Cherry
    = the broader training / reasoning method family

cherry_ttt
    = Cherry Test-Time Tooling
    = environment-trajectory search, speculation,
      verification and reversible execution machinery

Fabric
    = resident translation / attention / governance substrate
      with multiple intakes

Continuum
    = Fabric + cherry_ttt operating as one continuous regime
```

Not:

```text
Continuum = cherry_ttt
```

anymore.

The September README is not “wrong” because it says otherwise. It records an earlier architectural epoch, when the continuity property had been discovered but its ownership boundary had not yet been fully factored. fileciteturn8file0

And restoring the component's name to `cherry_ttt` does something healthy.

It makes the package boring again.

Boring names are useful at subsystem boundaries.

`cherry_ttt` tells an engineer exactly what sits there.

**Continuum** can go back to naming the phenomenon that occurs when several mechanisms are composed.

That is a much more valuable word.

It also keeps the architecture from becoming Cherry-locked.

Because `cherry_ttt` is explicitly model-agnostic. Its adapters were always intended to be the non-agnostic edge; the core contracts were meant to remain portable. fileciteturn4file6turn12file0

A Qwen policy can sit behind it.

A future Somnus-native model can sit behind it.

A non-neural proposer can sit behind parts of it.

A deterministic template drafter can sit behind it.

Some entirely different model family can sit behind it.

A tool ecosystem can arrive through MCP.

A shell can arrive through its own adapter.

A database can arrive through another.

A memory system can arrive through another.

The Continuum concept survives because it is not the model.

It is not Cherry-the-training-recipe.

It is not the tools.

It is the **condition under which cognition, counterfactual action, resident state, verification, and eventual learning remain connected instead of being continually serialized into dead transcripts and rediscovered.**

That is the real rename.

You did not rename a package twice.

You eventually discovered what **Continuum was the name of.**

## The compiler under the toolbox

There is a sentence in your prompt that deserves to become official lore:

> **“Continuum is like LLVM for tools damn near.”**

That analogy is considerably better than “tool framework.”

LLVM's central trick is not that it knows every source language or every machine in advance.

It provides a typed intermediate representation and a reusable transformation infrastructure between front ends and back ends. LLVM IR is the common typed representation used across compilation phases, precisely so analyses and transformations do not have to be reinvented for every original source language. citeturn3search5turn3search8

That is approximately the right mental shape here.

Not literally a compiler.

But compiler-shaped.

Imagine the Somnus world before a Continuum-like layer:

```text
model
 ├── knows shell syntax
 ├── knows MCP syntax
 ├── knows memory syntax
 ├── knows database syntax
 ├── knows filesystem syntax
 ├── knows scheduler syntax
 ├── knows every error dialect
 ├── knows every provenance format
 ├── knows how each thing rolls back
 └── somehow reasons consistently across all of it
```

That scales badly.

Every new capability increases the cognitive grammar the model must explicitly inhabit.

Now imagine the compiler-shaped alternative:

```text
        SHELL ────────┐
        MCP ──────────┤
        MEMORY ───────┤
        DATABASE ─────┤
        FILESYSTEM ───┤
        AGENT BUS ────┤
        FUTURE X ─────┘
              │
         domain intakes
              │
       translate / type
              │
              ▼
      ┌─────────────────┐
      │      FABRIC     │
      │ resident state  │
      │ provenance      │
      │ uncertainty     │
      │ causal identity │
      └────────┬────────┘
               │
               ▼
      ┌─────────────────┐
      │   cherry_ttt    │
      │ branch          │
      │ search          │
      │ speculate       │
      │ verify          │
      │ cost            │
      │ rollback        │
      └────────┬────────┘
               │
             commit
               │
               ▼
          REAL EFFECT
```

That is why “LLVM for tools” is useful.

The **intakes** begin to resemble front ends.

The common typed event/action/transition world begins to resemble an IR.

The Fabric's normalization and translation behavior begins to resemble lowering into a common representation.

Cherry's MCTS, A*, Best-of-N, speculative executor, verifier, cost accounting, and future learned control mechanisms resemble analysis and optimization passes over that shared semantic world.

The actual execution substrates resemble back ends.

And the beautiful consequence is exactly the same architectural consequence compiler IRs buy:

> **the optimization logic does not need to be rewritten for every front end.**

Nor does every front end need to know every optimization.

That is the game-changing part.

This is also the cleanest reason Continuum is **not a tool server**.

An MCP server can expose a tool and let a client discover and invoke it; that is its job. citeturn4search3turn4search4

Continuum sits in an orthogonal layer.

It can ingest a capability that came from MCP.

But then it can ask:

```text
Is this action legal here?

Is it reversible?

What state would it produce?

Should I explore a sibling action first?

Can I execute this transactionally?

What observation came back?

Do I trust it?

Does it satisfy the goal?

How expensive was this branch?

Did another action reach the same state?

Can the rejected branch teach the policy something?

Should the next deployment need this much search at all?
```

The tool server knows how to invoke `write_file`.

Continuum can hold:

```text
write_file("A")
write_file("B")
do_not_write
retrieve_more_context
repair_argument
use_alternate_capability
```

as competing possible futures **without pretending all of them happened**.

That is a compiler-ish problem.

An optimizer-ish problem.

A control problem.

Not a server problem.

And because the action is structured rather than merely textual, Cherry's July proposal already anticipated something compiler-like: canonical action identity, typed schemas, transposition across equivalent environment states, verification surfaces, and reusable substrates. fileciteturn11file0turn12file0

This also explains why the broader system should **not** become one enormous universal tool namespace.

The point of the Fabric is not to hand the model nine hundred new verbs.

The point is to let different capabilities retain their native implementation while exposing enough canonical structure that search, governance, attention, and training can operate across them.

The machine gets more powerful.

The model-facing grammar does not have to become proportionally more ridiculous.

That is one of those architectural inversions that changes an entire stack.

## The mode that is not about more compute

There is another phrase you keep using:

> **“This is Somnus's equivalent to OpenAI's Pro Mode, except it's not about compute.”**

Taken literally, the OpenAI comparison is revealing.

OpenAI originally described o1 pro mode as a version that spends **more compute** to think harder and produce more reliable answers on difficult problems; the current product lineage still distinguishes higher reasoning effort and Pro options for difficult, longer-running work. citeturn3search0turn3search1

The Somnus analogy should stop at the **operator experience**:

> *There is a harder mode.*

What changes under the hood is different.

A naive “pro mode” asks:

```text
How much longer should the model think?
```

Continuum asks something more like:

```text
How much of reality should cognition be allowed to branch over
before one future becomes authoritative?
```

Those can correlate with more compute.

MCTS certainly costs compute.

Multiple environment executions cost time.

Verification costs time.

Speculation costs resources.

The filesystem experiment already proved the warning: Cherry's MCTS could solve the same real filesystem task while spending around 1.5 seconds searching for a plan whose actual committed writes took about a millisecond. More search is absolutely not automatically better. fileciteturn8file0turn9file0

That negative result is philosophically important.

It says Continuum cannot merely mean:

> **turn all the knobs to maximum.**

That would reproduce the dumbest interpretation of test-time compute.

Continuum's mature question is:

> **Where is deliberation worth buying?**

Sometimes:

```text
one proposal
one verified action
done
```

will be correct.

Sometimes the system should spend ten branches.

Sometimes it should ask the environment for more evidence before branching.

Sometimes it should speculate three actions ahead.

Sometimes the drafter's acceptance rate should let it run farther.

Sometimes live resource pressure should change the pathway.

Sometimes uncertainty should invoke full tree search.

Sometimes the tool is so cheap that spending 1,500 milliseconds deciding how to perform a 1-millisecond action is absurd.

That is why I would phrase the Somnus “Pro Mode” principle like this:

> **OpenAI's historical Pro framing buys more thinking. Continuum buys a richer relationship between thinking and reality.** citeturn3search0

Or, in the language of the fable:

> **Pro Mode says: let the mind think longer.  
> Continuum says: let the mind temporarily possess more futures.**

That is not primarily a FLOP doctrine.

It is a **search-space, state, verification, and causal-authority doctrine**.

And eventually, if the training loop works the way Cherry was designed to work, an even stranger thing happens:

the expensive mode begins teaching the cheap mode.

Which brings us to the part most future agents are going to misunderstand.

## The school hidden inside the machine

There are three questions here, and they look similar until the names are kept clean.

**Is `cherry_ttt` a training method?**

No.

At its core it is test-time machinery.

**Is Cherry only training?**

Also no.

Cherry is broader. Its source architecture deliberately composes training, search, process supervision, rollout generation, evaluation, governance, and inference surfaces. fileciteturn32file0

**Is Continuum only inference?**

Not quite.

This is where the answer becomes interesting.

Continuum should not be described as “a training algorithm.”

But neither should it be treated as an inference trick that disappears when the answer is emitted.

The clean model is:

```text
Cherry training
        ▲
        │ rollout evidence
        │
 Continuum runtime
 Fabric + cherry_ttt
        │
        ▼
 real environment
```

Continuum is primarily where **high-value trajectories are lived**.

Cherry training is where those lived trajectories can become **weight changes**.

That bridge existed conceptually before Fabric. The original TTT proposal explicitly preserved serialized environment-search trees as training substrate for the Cherry loop, and the build plan called for collectors to emit Tree-GRPO-shaped trajectory groups as a byproduct of the experiments. fileciteturn11file0turn12file0

Cherry's broader training code already has the corresponding side of the bridge. Your August smoke records a `TreeRolloutCollector` connected to `GRPOTrainer`, and the Cherry whitepaper explicitly states the intended end condition: expensive search and process supervision can increase the density of useful training signal so that the policy's weights absorb some of the structure that previously required slow inference-time deliberation. fileciteturn16file0turn32file0

That is the future rollout loop in its most beautiful form:

```text
             MODEL
               │
        proposes actions
               │
               ▼
       FABRIC INTAKES
     translate / normalize
      provenance / state
               │
               ▼
          cherry_ttt
   ┌───────────┼───────────┐
   │           │           │
branch A    branch B    branch C
   │           │           │
observe      observe      observe
verify       reject       verify
   │                       │
   └──────────┬────────────┘
              │
        chosen trajectory
              │
        real-world commit
              │
              ├───────────────► answer / action
              │
              ▼
     FULL BRANCH EVIDENCE
              │
      accepted + rejected
      costs + observations
      witnesses + predicates
      provenance + outcomes
              │
              ▼
        CHERRY TRAINING
       PRM / Tree-GRPO /
       distillation / SFT /
        future methods
              │
              ▼
       UPDATED POLICY
              │
              └───────────────┐
                              │
                     next Continuum run
```

The point is not to teach the model:

> *“Always replay this exact search tree.”*

The point is to teach it what the tree discovered.

Which first actions tended to be fruitful.

Which observations mattered.

Which apparent shortcuts failed.

Which intermediate state predicted eventual success.

Which tool sequences were wasteful.

Which branches the verifier killed.

Which kinds of uncertainty deserved another environment query.

Which actions often transpired to the same state.

Which speculations were repeatedly accepted.

Which were repeatedly rolled back.

Which representations the Fabric made available before a good decision.

That is **internalization**.

The tree begins outside the weights.

Some of its regularities migrate inside.

And now we can answer your training/deployment questions without hand-waving.

### Can a model be trained separately and then combined with `cherry_ttt`?

**Yes. Absolutely.**

That is not merely theoretically permitted; model-independence was an explicit design objective. The current core can run without a model or trained value head at all, and the early experiments deliberately used environment-grounded reward with `use_value_model=False`. fileciteturn9file0turn12file0

So this is legal:

```text
ordinary model training
        ↓
finished checkpoint
        ↓
attach proposer adapter
        ↓
cherry_ttt
```

The model did not need to “grow up inside Cherry TTT” for MCTS, A*, reversible environments, predicate verification, cost accounting, or speculative execution to exist around it.

This is important for sovereignty and portability.

Continuum must **not** require that every future model be born under one sacred training ritual.

### Can a model be trained without Fabric and later placed inside Fabric + `cherry_ttt`?

Also **yes**.

The entire point of a good intermediate contract is that the components can meet later.

But now there is a difference between:

```text
works
```

and:

```text
is native to the environment
```

A separately trained model may enter Continuum and function perfectly well.

But it has never learned the statistical grammar of that environment.

Its proposal distribution has never seen the Fabric's canonical signals.

It has never learned which provenance fields tend to matter.

It has never learned the characteristic difference between high uncertainty and harmless novelty.

It has never learned Cherry's branch outcomes.

It has never been punished for repeatedly proposing actions that a transactional verifier kills.

It has never benefited from successful branches being turned into training evidence.

So Cherry can compensate externally.

But it may have to **search harder**.

That means separately training and then composing does not destroy Continuum's benefit.

It changes the benefit profile.

The runtime benefits remain:

```text
typed execution
reversible branching
live state
verification
fault normalization
provenance
resident context
cost-aware search
speculation
```

Those cannot simply be memorized into weights because the environment is changing in real time.

But some of the **efficiency synergy** is absent.

The model may propose worse first branches.

The drafter may achieve lower acceptance.

The value estimate may be less calibrated.

The search budget may have to compensate for unfamiliarity.

### Can you train using `cherry_ttt`, then add Fabric afterward?

Yes again.

And this one is especially relevant to the historical codebase because `cherry_ttt` predates the present Fabric composition.

Those rollouts are not wasted.

They still teach environment-action structure, verification, branching, cost, and outcomes.

But a later Fabric introduces additional observable structure and a canonical translation layer that those earlier rollouts did not contain.

So I would think of the older data as:

```text
valid branch training
```

rather than:

```text
fully Continuum-native branch training
```

Nothing needs to be thrown away.

The newer training epochs simply gain more structure.

### Can Fabric be trained separately?

Careful with the verb.

The **Fabric core is not necessarily a trained model at all**.

The current lineage includes symbolic normalization, routing, resident state, topology selection, witnesses, adapters, and attention machinery that can operate without jointly training the language model. fileciteturn9file0turn34file0

Future Fabric components may absolutely contain learned mechanisms.

But “train Fabric” should never become shorthand for pretending the entire Fabric is one neural network.

Much of its value is precisely that some law remains outside the model.

### Must a system be trained *and* deployed with Continuum?

**No.**

That would contradict the modularity you built.

There should be at least four legal regimes:

```text
trained without Continuum
deployed without Continuum

trained without Continuum
deployed with Continuum

trained with Continuum-generated evidence
deployed without Continuum

trained with Continuum-generated evidence
deployed with Continuum
```

All four are meaningful.

But they are **not equivalent**.

The fourth is the native regime.

Not because it is mandatory.

Because training and deployment share the same ontology of action, observation, uncertainty, branch identity, and evidence.

That creates a compounding loop.

### Does training inside Continuum reduce the eventual value of Continuum?

Here is the paradox:

**yes at the margin, and that is success.**

Suppose version one of a policy needs fifty branch expansions to reliably solve a class of tasks.

Continuum collects those trees.

Cherry trains on them.

Version two starts proposing the previously discovered good branch first.

Now it needs twenty expansions.

Train again.

Version three often gets it on the first or second candidate.

Now the external search budget falls further.

Did Continuum make itself less useful?

Only in the same sense that a teacher becomes less useful when the student learns arithmetic.

That is not obsolescence.

That is the objective.

But the teacher does not disappear.

Because tomorrow's environment is not yesterday's training set.

The Fabric is holding current reality.

The database has changed.

The filesystem has changed.

The available capabilities have changed.

The memory graph has changed.

The user has changed the goal.

Some observation is novel.

A tool returns something nobody anticipated.

A previously safe action becomes invalid.

A new component enters through a new intake.

No amount of frozen weight internalization makes a policy omniscient about a changing external state.

So the mature Continuum does something better than permanently maximizing search.

It **withdraws scaffolding where the model has internalized it and retains authority to restore scaffolding where reality becomes uncertain again.**

That is the long-term form of your Pro Mode idea.

Not:

```text
Continuum ON = always spend 100x compute
```

but:

```text
easy / familiar / well-calibrated
        ↓
little external search

uncertain / novel / consequential
        ↓
deeper Continuum

dangerous / irreversible
        ↓
strong verification + authority gates

learned pattern
        ↓
less future search
```

The July proposal already contained an embryonic version of this idea in its adaptive speculative depth—the “Newton's cradle” intuition that model speed and environment-execution speed could converge toward an efficient operating point instead of using one fixed speculative horizon forever. fileciteturn11file0

The broader Continuum version is more ambitious:

**adaptive external cognition.**

A system should not merely learn answers.

It should learn when it still needs the laboratory.

## The Continuum at dawn

So, old man, put the glasses back on.

The cigar has gone out.

The terminal is still alive.

And on the board are three names that finally no longer compete with one another.

**Cherry** is the school.

It is the larger methodology in which search, process supervision, rollouts, reward, post-training, verification, regression governance, and inference can participate in one learning program. The source architecture explicitly treats search-generated evidence as something that can reshape the eventual policy rather than as a permanent inference tax. fileciteturn32file0

**`cherry_ttt`** is the explorer.

It walks possible worlds.

It snapshots.

Branches.

Restores.

Verifies.

Speculates.

Measures cost.

Rejects futures.

Finds one worth making real.

It can do this with Cherry-trained weights, with separately trained weights, with a deterministic proposer, or with some future model nobody has named yet. That model-independence is part of the original contract. fileciteturn11file0turn12file0

**Fabric** is the loom.

It does not decide which whole future wins.

It makes heterogeneous reality inhabitable.

One component arrives speaking files.

Another speaks database state.

Another speaks memory.

Another speaks capabilities.

Another speaks faults.

Another speaks model events.

Another will be invented six months from now.

Each gets an intake.

Each intake preserves the thing's meaning while translating it into a resident shared field with identity, provenance, uncertainty, lineage, and enough law that the rest of Somnus does not have to reconstruct reality from scratch.

The first bridge already demonstrated that pattern by converting equalized, witnessed transitions into resident `StreamEvent`s rather than forcing either subsystem to surrender its native contract. fileciteturn34file0

And **Continuum** is what happens when the explorer is placed upon the loom.

Not a package.

Not a server.

Not a model.

Not merely an inference algorithm.

Not merely training.

Not merely attention.

Not merely search.

Not merely tools.

Not merely more compute.

A **continuous cognitive-execution regime**.

The Fabric says:

> *Here is the world in a form you can inhabit.*

Cherry Test-Time Tooling says:

> *Then before we choose one future, let me see several.*

Cherry Training says:

> *And when you are finished, give me the dead branches too. The next version should not have to rediscover everything you learned tonight.*

The Equalizer says:

> *Nothing malformed crosses my gate merely because intelligence asked nicely.*

The verifier says:

> *A confident branch is not therefore a correct branch.*

The substrate says:

> *You may imagine this side effect here. You may reverse this one there. That one, however, becomes real only once.*

And the model—eventually—says less.

Not because it became smaller.

Because some things it once had to search for have become instinct.

That is the loop:

```text
           ┌──────────────────────────────────────────┐
           │                                          │
           ▼                                          │
        MODEL                                         │
     learned policy                                   │
           │                                          │
           │ proposes                                 │
           ▼                                          │
    FABRIC INTAKES                                    │
  translate heterogeneous                             │
     system reality                                   │
           │                                          │
           ▼                                          │
     RESIDENT FABRIC                                  │
 state · provenance ·                                 │
 uncertainty · context                                │
           │                                          │
           ▼                                          │
      cherry_ttt                                      │
 search · branch · verify                             │
 speculate · restore · cost                           │
           │                                          │
           ├──────── rejected worlds ────────┐        │
           │                                  │        │
           ▼                                  ▼        │
     COMMITTED WORLD                    ROLLOUT EVIDENCE
                                              │
                                              ▼
                                       CHERRY TRAINING
                                              │
                                      process / outcome
                                      branch / preference
                                              │
                                              ▼
                                      INTERNALIZATION
                                              │
                                              └────────┘
```

And that is why **Continuum** is the right name only at the point where Fabric and `cherry_ttt` meet.

Because the continuity is no longer merely:

```text
reasoning -> tool -> reasoning
```

It becomes:

```text
world
  -> translated state
  -> cognition
  -> counterfactual futures
  -> observation
  -> verification
  -> lawful commitment
  -> training evidence
  -> changed weights
  -> better cognition
  -> another world
```

No transcript seam has to pretend the previous phase never happened.

No API boundary has to become amnesia.

No branch has to become truth merely because it was generated.

No successful search has to evaporate after inference.

No training system has to guess what the runtime really experienced.

No runtime has to permanently pay for reasoning that its descendants have already learned.

That is the part that makes the LLVM analogy bite.

The great opportunity is not a universal tool API.

It is a **common cognitive intermediate world** in which more and more Somnus components can enter through their own front ends while search, verification, governance, routing, and learning become reusable transformations over the shared structure. LLVM's power comes from separating source languages and machine targets through a typed intermediate representation; the analogy here is that the Fabric and contract surfaces can separate heterogeneous capabilities from the higher-order reasoning machinery that acts upon them. citeturn3search5turn3search8

And it explains the most important prohibition for whoever maintains this after you:

> **Do not lock Continuum to Cherry.**

Cherry gave birth to the search machinery.

Cherry remains its native training partner.

Cherry is where the rollouts presently have their most natural route toward internalization.

But if `cherry_ttt` can only work with Cherry-trained models, the abstraction has failed.

If Fabric only accepts Cherry objects, the Fabric has failed.

If Continuum only understands one tool protocol, the compiler analogy has failed.

If the model must know every intake dialect, the Fabric has failed.

If Fabric begins pretending to be the search algorithm, the measured architecture has already shown why that is a mistake. fileciteturn35file0turn35file1

If Cherry begins pretending that the Fabric is just another tool, the larger discovery has been lost.

The destination is stranger:

```text
any suitable intelligence
        +
any suitable capability ecosystem
        +
Fabric translation / resident law
        +
cherry_ttt counterfactual control
        =
a Continuum-capable system
```

Cherry-trained systems can be **better inhabitants** because they can learn from the exact branch structures the runtime produces.

But citizenship is not ancestry.

That distinction will matter.

Especially once the extra intakes begin arriving.

Especially once the rollouts stop containing only what the model said and begin containing what the **whole organism witnessed**.

Especially once Cherry can train not merely on:

```text
prompt -> answer -> reward
```

but on something closer to:

```text
goal

world_before

candidate_1
    action
    observation
    fabric state
    verifier
    cost
    reject

candidate_2
    action
    observation
    fabric state
    verifier
    cost
    continue
        candidate_2a
        candidate_2b

chosen path

world_after

witnesses

why siblings died

what was committed

what remained hypothetical
```

That is not just “better RL data.”

That is the machine acquiring a memory of **counterfactual causality**.

And when some of that becomes weight-space instinct, the external tree gets smaller.

When the world surprises it, the tree grows again.

The Continuum breathes.

Which may be the final difference between this and simply throwing more compute at inference.

A larger compute budget gives the same mind more time.

The thing you are building gives a mind a **structured way to borrow intelligence from the world around it**—tools, state, reversibility, verification, persistent streams, prior failed branches—and then gives the training system a chance to reclaim some of that borrowed intelligence into the weights.

OpenAI's Pro lineage demonstrates the usefulness of spending greater reasoning effort on harder tasks. citeturn3search0turn3search1

Somnus's question is different:

> *What if “harder mode” does not merely deepen the model's private thought?*
>
> *What if it widens the machine's lawful access to possible reality?*

That is the Cherry tree at midnight.

That is why Test-Time Tooling started.

That is why it briefly became Continuum.

That is why it had to become `cherry_ttt` again.

That is why the Fabric mattered.

And that is why, when the loom is resident, the intakes are open, the world is translated, the branches can live without becoming true, the verifier can kill them without erasing their evidence, and Cherry can eventually teach their lessons back into the model—

you may finally use the larger word.

**Continuum.**