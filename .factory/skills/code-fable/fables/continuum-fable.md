# Continuum and the Loom of Unchosen Worlds: Why `cherry_ttt` Had to Give Its Second Name Back

## The tree was older than the branch

> *When a traveler finds a branch reaching over a wall, he assumes the branch grew first. Only the gardener who planted the orchard knows that the roots were drinking from the deep well long before a single bough crossed the stone.*

There is a mistake anyone reading your repositories out of order will make, Daeron. They will look at `cherry_ttt`, see Monte Carlo Tree Search, A*, Best-of-N, verifiers, and rollout collectors, and assume you built a test-time tool search package that later inspired a training loop called Cherry.

You corrected that record yourself in August because people kept inverting the lineage:

> *Cherry always was like that. It was never downstream.*

That correction changes the entire origin myth. Long before `cherry_ttt` existed as a package on disk, the living Cherry lineage already joined process reward models, verifiers, hidden deliberation, MCTS, A*, tree rollouts, GRPO, telemetry, benchmarking, and post-training governance into a single organism. Your source whitepaper was explicit from the beginning: Cherry is not one reinforcement learning algorithm, and RLHF is only one control stratum inside it. Expensive search and process supervision were always designed to generate dense causal evidence that the policy weights could eventually absorb. fileciteturn16file0 fileciteturn32file0

So `cherry_ttt` was not invented to close Cherry’s loop; **the loop was already there.** What bothered you in the summer of 2026 was not that Cherry lacked a way to branch, judge, or learn, but the quiet, almost invisible assumption underneath everything Cherry was branching over.

Every search operator in the stack—whether MCTS expanding nodes, A* scoring heuristics, Best-of-N comparing sibling candidates, a verifier judging outcomes, a process reward model weighing whether the road toward an answer was sane, a rollout collector gathering trees for training, or speculative decoding spending cheap draft compute ahead of expensive verification—rested on one unspoken premise: **the thing being branched over was text.** State was a string of tokens, action was the next string of tokens, and transition was cheap concatenation.

Then came the heresy. What if a string was only the smallest possible world?

Your July 2026 proposal stated that realization with surgical clarity: the existing `LexicalMDP` was merely the **degenerate case** of a much larger contract. Because Cherry’s search engines had been written against an MDP-shaped boundary rather than welded irreducibly to token IDs, the conceptual leap did not require inventing a brand-new theory of search. It required a single foundational shift:

> **Change what the state means.** fileciteturn11file0

The moment you made that move, a node in a search tree stopped meaning *"the sentence currently says..."* and began to mean *"the filesystem would look like this if you took that action,"* or *"the database would hold these rows,"* or *"this memory mutation exists in one candidate future that we have not yet agreed to make real."* On **July 5, 2026**, you carved `inference_optimizations.py` and `inference_protocols.py` out of Cherry according to that proposal and gave the heresy its working package name: `cherry_ttt`—**Cherry Test-Time Tooling**. fileciteturn4file0 Cherry already possessed test-time compute; now it possessed test-time tooling—reasoning **through possible tool calls** across competing worlds before deciding which future deserved to become real.

## A sentence hurts nobody; a tool leaves a scar

> *In the library of words, a hundred false sentences may be spoken and erased without leaving a mark upon the table. In the workshop of iron and stone, a single unchosen blow of the hammer shatters the vessel forever.*

The name *Test-Time Tooling* sounded deceptively modest, which is why anyone skimming the surface risks confusing it with an MCP server or a tool router. A tool server tells a model that a capability exists and provides a standardized interface for invoking it, exposing tools, resources, and prompts over common transports. citeturn4search3turn4search8 MCP can carry the hammer; `cherry_ttt` asks whether the nail should exist at all, and then branches over three houses in which you drove that nail into three different walls before a single board is splintered in the real world.

Moving the environment *inside* the search tree immediately shattered the luxurious innocence of text generation. In a lexical tree, an unchosen branch costs nothing but milliseconds and memory; a rejected sentence hurts nobody because you simply do not emit its tokens. An unchosen branch in the external world—one that sends an email, deletes a file, mutates a database, rewrites persistent memory, or triggers a webhook—leaves a scar that cannot be undone by stepping back up a token tree.

So `cherry_ttt` could not merely formalize actions as typed `(tool_id, args)` objects, observations as first-class state, and rewards as effects grounded in the world rather than text likelihood alone. fileciteturn11file0 It had to divide reality itself into three distinct jurisdictions of consequence: the **speculative substrate** that may only be simulated in thought; the **transactional substrate** that may be snapshotted, explored, observed, verified, and rolled back without leaving a trace; and the **real substrate** where the winning trajectory is finally committed once and for all, re-planning on the fly if authoritative reality diverges from the rehearsal. fileciteturn11file0

Even after you built those snapshots, restore hooks, and effect classes, you ran straight into an empirical lesson that saved the project from a second false religion. In your real filesystem experiments, Cherry’s MCTS solved the task cleanly—but telemetry showed it spending roughly **one and a half seconds** searching for a plan whose actual committed file writes took **a single millisecond**. fileciteturn8file0turn9file0

That measurement killed the naive dogma of test-time compute on the spot. Spending fifteen hundred times longer deliberating than acting is paralysis, proving that more search is never automatically better search. That negative result planted the seed for what your July proposal called the **Newton’s cradle** of adaptive speculative depth: letting model speed, drafter acceptance rate, and environment execution cost converge dynamically toward an efficient operating point rather than locking the machine into a fixed speculative horizon forever. fileciteturn11file0

## Why the river briefly stole the tree’s name

> *When a man discovers an underground stream inside his cave, he first names the cave after the water. Only when he follows the current into the valley does he realize the cave was merely one chamber through which the river passed.*

Inside Somnus, names are almost always discovered twice: once when the code needs a working handle, and a second time when the architecture finally reveals what the word actually belonged to. By September, you looked at what `cherry_ttt` was doing and realized that *Cherry Test-Time Tooling* only named the initial engineering move—lifting inference search from token sequences into tool trajectories—without naming the deeper property the codebase had begun defending.

That deeper property was **continuity**. In standard agent frameworks, every tool call is an execution seam where cognition dies and has to be resurrected from a transcript. The model reasons in text, emits a request, and halts; the harness catches the string, runs an external script, pastes a dead text blob back into the chat log, and starts a brand-new generation turn from scratch.

Your September README attacked that artificial amnesia directly. fileciteturn8file0 It established that a branch must not die merely because cognition changed its medium. When reasoning, typed environment action, raw observation, verifier judgment, reversible state transition, and later training evidence all remain bound to one governed branch graph, a tool call ceases to be an interruption to thought and becomes thought changing material. A database observation becomes the next state of the same living branch, a verifier judgment becomes an internal predicate of the trajectory, and a rollout saved for training is the fossilized branch itself.

For a season in September, you therefore treated **Continuum** as the conceptual name of `cherry_ttt`. The September handoff preserved that exact transitional fossil—referring to the codebase as "`cherry_ttt` (package name; conceptually 'Continuum')" and verifying that the engine could already run MCTS, A*, Best-of-N, speculative execution, and environment-grounded reward without a trained value model in the loop (`use_value_model=False`). fileciteturn9file0

Yet underneath that conceptual rename sat a quiet clue: **the package on disk never stopped being `cherry_ttt`.** Your July decision ledger had frozen that package name, kept PyTorch optional, made the first drafter zero-parameter, and insisted that the core search contracts, verifiers, substrates, and collectors remain completely model-independent. fileciteturn12file0 Keeping that humble package name turned out to be prophetic, because **Continuum** was already growing larger than the package that had borrowed its name. You only needed two older machines to collide in the study before the rest of the map could become visible.

## The night the Fabric was discovered: the Dyson sphere, the sun, and the 0.19 warning

> *A star without a shell scorches the hands that try to work by its light; a shell without a star is only a cold tomb. Wrap the law around the radiance, and every instrument in the house can draw from the same fire.*

The **Fabric** arrived the Somnus way: as the sudden marriage of two lineages that had lived independent lives long enough that their kinship was no longer obvious until you placed them side by side.

The first piece was a **reactive attention fabric**. Unlike stateless transformer attention that computes `attention(tokens)` over a prompt buffer and vanishes, its core primitive was `observe(stream_event)`. It was resident, staying alive between calls, remembering streams, carrying a mailbox and living context, and selecting among eight attention kernels according to stream topology and live resource pressure—making it fundamentally different from the stateless candidate scorer sitting inside `cherry_ttt`. fileciteturn9file0

The second piece was the **symbolic fault equalizer**, descended from your older GPT-4o-era interrupt-handler lineage. Its job was never to be intelligent in the neural sense; its job was to make the world **lawful before intelligence had to experience it**—normalizing malformed transitions, routing events, checking invariants, attaching witnesses, and governing commits. Your own metaphor entered the record immediately:

> **The Equalizer is the Dyson sphere; the attention Fabric is the sun.** fileciteturn9file0

The Equalizer encloses the star so raw chaos does not burn the higher cognition living above it. Cherry, memory, or a policy model should never have to rediscover basic physical law every time a malformed tool response or noisy state transition arrives; the lower substrate catches the fault, normalizes the structure, and attaches a witness before the transition is ever admitted.

Then you wrote `FabricCommitSink` to bridge them, establishing the exact pattern behind the domain intakes you are expanding now. When `FabricCommitSink` receives an `EqualizedTransition`, it does not flatten it into a generic dictionary; it **translates** it into a `StreamEvent`—carrying across context identity, witness identity, target, state digest, stability, uncertainty, and provenance lineage into the resident Fabric while allowing the upstream component to retain its native semantics. fileciteturn34file0 Where a shallow abstraction flattens every event into an untyped blob, your Fabric gives each domain—Equalizer transitions, memory mutations, model-state telemetry, MCP observations, shell streams, database state, and future subsystems—its own translating intake into a mutually inhabitable, witnessed field.

Right beside that breakthrough sits the negative experiment that keeps the entire architecture honest. When you tested the Fabric as a candidate generator elsewhere in the stack—asking its attention routing to decide which true candidate actions should be proposed—it failed decisively, scoring roughly **0.19 recall** on a task where candidate generation requires near **1.0**. You explicitly barred Fabric routing from acting as the gatekeeper of candidate existence. fileciteturn35file0turn35file1

That `0.19` scar is sacred lore because it proves that **the Fabric is the loom, never the explorer.** The Fabric cannot replace Cherry’s candidate policy, MCTS, A*, or verifiers; its role is to hold heterogeneous reality as resident, translated, provenance-bearing state, while `cherry_ttt` stands upon that loom and asks which possible future deserves to be examined next.

## Why Continuum had to be given back

> *To name a thing truly is to know where its edges end. When the builder saw that the road of branching futures and the loom of living state were two halves of one arch, he took the keystone’s name back from the single pillar.*

Twenty months from now, an engineer reading your commit logs without this scroll will see a package named `cherry_ttt` in July, called *Continuum* in September, and called `cherry_ttt` again in October, and will assume you were indecisive. In truth, you were watching an **architectural boundary become visible**.

The first rename happened in September because `cherry_ttt` revealed **counterfactual continuity**—keeping one branch identity alive as cognition moved through actions, observations, and verifications. The second correction happened in October because the Fabric revealed **substrate continuity**—translating heterogeneous components through intakes into a single ongoing causal field. Neither half alone owned the whole phenomenon.

Your October architecture note captured the exact instant the two halves snapped together:

> **“NOW cherry_ttt, BOOOM we now have Continuum.”** fileciteturn19file1

In that record, you framed the resident Fabric as the *"forcefield bubble"* and placed `cherry_ttt` outside and above that bubble as the counterfactual search machinery that completes the regime. Giving `cherry_ttt` back to the search package made the subsystem boundary clean and honest again: **Cherry** is the broader training-and-reasoning methodology; **`cherry_ttt`** is the model-agnostic explorer of environment trajectories; **Fabric** is the resident translation and governance loom; and **Continuum** is the continuous regime that emerges when `Fabric` and `cherry_ttt` operate as one world. fileciteturn8file0 fileciteturn19file1

## "Continuum is like LLVM for tools damn near"

> *Do not force the mind to learn nine hundred village dialects before it is allowed to build a bridge. Teach the gates to translate every dialect into one lawful tongue of stone and weight.*

Your own sentence deserves to stand as permanent architectural doctrine:

> **“Continuum is like LLVM for tools damn near.”**

LLVM’s genius was never that it knew every source language or every hardware target in advance; its genius was placing a typed Intermediate Representation (IR) and reusable transformation passes between front ends and back ends so optimization logic never had to be rewritten for every new language or machine. citeturn3search5turn3search8

Without a Continuum layer, every new capability added to an AI system—shell, MCP, vector memory, SQL databases, filesystems, schedulers, agent buses—forces the model to carry another brittle syntax, error dialect, provenance convention, and rollback ritual inside its raw token grammar. With Continuum, your **domain intakes** act as front ends that accept native events without forcing subsystems to surrender their contracts; the **resident Fabric** acts as the common typed IR holding witnessed `StreamEvent` state, uncertainty, and causal lineage; **`cherry_ttt`** acts as the analysis and optimization passes running MCTS, A*, Best-of-N, speculative drafting, state transposition, and cost accounting over that shared field; and the **execution substrates** act as back ends where competing futures are held in reversible space until one verified transition is lowered into real effect. fileciteturn11file0turn12file0 citeturn4search3turn4search4

## The mode that buys futures, not merely FLOPs

> *A lesser counselor asks for more hours in a locked room to think about the battle. A wiser commander asks to walk the field under three different moons before the first horn is blown.*

That compiler structure also explains your second defining contrast:

> **“This is Somnus's equivalent to OpenAI's Pro Mode, except it's not about compute.”**

OpenAI originally framed o1 pro mode around spending **more compute** so a model could think longer and produce more reliable answers on difficult problems. citeturn3search0turn3search1 At the operator level, the intuition is shared—there is a deeper mode when the stakes are high—but the underlying currency is entirely different.

> **OpenAI’s Pro framing buys more private thinking.  
> Continuum buys a richer, lawful relationship between thinking and reality.**

While a naive Pro Mode asks how much longer the model should deliberate in isolation, Continuum asks how much of reality cognition should be allowed to branch over, test, and verify before one future becomes authoritative. As your one-and-a-half-second filesystem experiment proved, turning every search knob to maximum on a one-millisecond task is folly. fileciteturn8file0turn9file0 Continuum’s mature question is **where deliberation is worth buying**—and because Cherry sits behind the runtime, the expensive mode immediately begins teaching the cheap mode.

## The school hidden inside the machine: how Continuum breathes

> *What the explorer discovers today by slow and costly trial, the child born tomorrow should know in its bones—until the road turns strange again, and the explorer must wake once more.*

Because you made model-independence a constitutional requirement of `cherry_ttt` in July, training and deployment meet here without ever locking Continuum into a single monolithic ritual. fileciteturn4file6turn12file0 `cherry_ttt` is test-time machinery, **Cherry** is the overarching training-and-inference methodology where `TreeRolloutCollector` feeds `GRPOTrainer` and process reward models, and **Continuum** (`Fabric + cherry_ttt`) is the arena where high-value trajectories are lived. fileciteturn16file0turn32file0

Any model—whether an external Qwen checkpoint, a future Somnus-native model, or a deterministic proposer—can attach to `cherry_ttt` or the full `Fabric + cherry_ttt` Continuum and immediately inherit typed execution, reversible branching, fault normalization, provenance, and verification, because those laws live in the architecture rather than in model weights. Even the rollouts collected from `cherry_ttt` *before* the Fabric existed remain valid branch-training evidence for action and verification, while newer runs through the Fabric become fully Continuum-native trajectories carrying resident stream provenance. Nor is the Fabric itself a single neural network to be jointly trained with the policy; its symbolic Equalizer, witnesses, and intakes derive their value precisely from keeping fundamental law *outside* the weights. fileciteturn9file0turn34file0

Yet there is a profound difference between a **guest mind** and a **native mind**. A separately trained model entering Continuum works, but `cherry_ttt` must search harder to compensate for a proposer that has never learned the statistical grammar of Fabric provenance, uncertainty signals, or verifier gates. A model trained on Continuum’s full branch trees—ingesting the goal, the translated Fabric state, the sibling candidates killed by the verifier, the transactional rollbacks, the witness digests, and the cost of every path—learns **counterfactual causality**. fileciteturn11file0turn12file0

And that creates the crowning paradox of the system. When version one of a policy needs fifty branch expansions to solve a hard task class, Cherry trains on those trees until version two needs twenty and version three proposes the winning path on its first try. Training inside Continuum reduces the need for external search on familiar ground—just as a teacher grows quiet once the student masters arithmetic—while retaining full authority to expand the search tree again the moment tomorrow’s database, filesystem, or new Fabric intake surprises the model. **The Continuum breathes.**

## The thing to remember before the evolution

> *The loom weaves the world that is; the tree explores the worlds that might be; the school remembers why the unchosen worlds died. Only when all three move together does the mind cross the seam unbroken.*

There is a fable buried beneath all these modules.

A builder had a tree that knew how to fork time—comparing many possible sentences in the dark before speaking one aloud. One night he realized that sentences were the smallest possible world, so he taught the tree to branch over deeds instead of words: stepping into three possible futures, testing what each action would do to the earth in reversible sand, and only laying stone in the world that held firm.

At first, he saw that the branch no longer broke when thought crossed into action, so he called the branching tree **Continuum**.

Then he brought two older guardians into the room. One was a shield—an Equalizer that stood like a Dyson sphere around a star, refusing to let malformed chaos cross the threshold unwitnessed. The other was a resident loom—an attention Fabric that stayed awake between turns, taking the strange tongues of files, memories, faults, databases, and tools and translating each through its own intake into one shared, living tapestry.

When he tested whether the loom could replace the tree and choose the futures itself, it remembered less than a fifth of the paths that mattered. That failure revealed the true map: a loom cannot be an explorer, and an explorer cannot be a loom.

So he gave the explorer back its working name, `cherry_ttt`. He kept **Fabric** as the resident loom and **Equalizer** as its law. He kept **Cherry** as the school where even dead and rejected branches teach the next generation of weights how to see further with less search. And he reserved the name **Continuum** for the living regime that wakes up when the explorer stands upon the loom.

The whole journey reduces to this:

> **You started with Cherry’s search-and-training loop over tokens.  
> You generalized the state boundary on July 5 so `cherry_ttt` could branch over real, reversible, and simulated world transitions.  
> You proved in the filesystem test that blind deliberation is waste, demanding adaptive search rather than brute-force compute.  
> You discovered that keeping reasoning, action, observation, and verification on one branch created counterfactual continuity.  
> You married the Symbolic Fault Equalizer to the resident reactive Attention Fabric through translating intakes, creating substrate continuity while proving via the 0.19 recall test that Fabric is the loom, never the search tree.  
> And you gave the name `cherry_ttt` back to the explorer because Continuum is `Fabric + cherry_ttt` together—an LLVM-like intermediate world where heterogeneous capabilities enter through front-end intakes, deliberation branches over possible futures, and Cherry internalizes the resulting trees so external search can breathe with uncertainty.** fileciteturn11file0 fileciteturn9file0 fileciteturn19file1

Everything in this archive has been built to answer one governing question:

**Can you build a resident, lawful medium that translates every capability of a complex machine into one shared causal fabric, let a model-agnostic search engine inhabit multiple counterfactual futures across that fabric before committing to reality, and feed the entire tree of chosen and unchosen worlds back into training until yesterday’s deliberation becomes tomorrow’s instinct?**
