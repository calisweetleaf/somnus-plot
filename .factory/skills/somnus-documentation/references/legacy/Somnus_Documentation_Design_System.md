> **Superseded reference.** Preserved for historical lineage, not current guidance. Read [the current design schema](../design-schema.md) and [source lineage](../source-lineage.md) first.

# Somnus Documentation Design System

### Rolling Snippet Library — v3

<div align="center">

<svg width="480" height="120" viewBox="0 0 480 120" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="titleGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#c9a0dc;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#8ec5fc;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#c9a0dc;stop-opacity:1" />
    </linearGradient>
    <filter id="softGlow">
      <feGaussianBlur stdDeviation="2.5" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="480" height="120" fill="#0d1117" rx="12"/>
  <line x1="40" y1="92" x2="440" y2="92" stroke="#1e2430" stroke-width="1"/>
  <text x="240" y="56" font-family="'Courier New', monospace" font-size="28" fill="url(#titleGrad)" text-anchor="middle" filter="url(#softGlow)" font-weight="bold" letter-spacing="6">SNIPPET LIBRARY</text>
  <text x="240" y="78" font-family="'Courier New', monospace" font-size="11" fill="#6e7681" text-anchor="middle" letter-spacing="4">SOMNUS SOVEREIGN SYSTEMS</text>
  <text x="240" y="110" font-family="'Courier New', monospace" font-size="10" fill="#484f58" text-anchor="middle">Documentation Design System v3 — Terminal-First Architecture</text>
</svg>

</div>

---

> *"Every README is a landing page. Every doc is a detailed walkthrough. The reader should feel as if they are behind my eyes while I sit at a desk with just a lamp and the darkness of the room."*

No emojis. No AI-vibe color schemes. No collapsibles hiding architecture diagrams like they're an afterthought. Every diagram lives in a terminal window — because this is a running system, and it should look like one. Artistic freedom is encouraged. Mediocrity is not.

---

## Index

1. [The Terminal Frame — Universal Container](#1-the-terminal-frame--universal-container)
2. [Terminal: Architecture Diagrams](#2-terminal-architecture-diagrams)
3. [Terminal: Code Blocks (Fixed)](#3-terminal-code-blocks-fixed)
4. [Terminal: Multi-Pane Split View](#4-terminal-multi-pane-split-view)
5. [Terminal: System Monitor View](#5-terminal-system-monitor-view)
6. [Terminal: Research Session](#6-terminal-research-session)
7. [Terminal: Diff View](#7-terminal-diff-view)
8. [Banners and Identity Blocks](#8-banners-and-identity-blocks)
9. [Tag and Badge Systems](#9-tag-and-badge-systems)
10. [Intelligence Report Panels](#10-intelligence-report-panels)
11. [Metric Dashboards](#11-metric-dashboards)
12. [Signal and Evidence Blocks](#12-signal-and-evidence-blocks)
13. [Pipeline Flow Visualizations](#13-pipeline-flow-visualizations)
14. [Principles and Anti-Patterns](#14-principles-and-anti-patterns)

---

<!-- ============================================================ -->
<!-- GLOBAL STYLES — include once per document                    -->
<!-- ============================================================ -->

<style>
/* ── Terminal Shell ─────────────────────────────────────────── */
.t {
  background: #141414;
  border-radius: 10px;
  box-shadow: 0 12px 40px rgba(0,0,0,0.55), 0 0 0 1px #2a2a2a;
  margin: 22px 0;
  font-family: 'Menlo', 'Monaco', 'Cascadia Code', 'Courier New', monospace;
  overflow: hidden;
}
.t-hdr {
  background: #252525;
  padding: 11px 16px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #1e1e1e;
  user-select: none;
}
.t-btn { width: 13px; height: 13px; border-radius: 50%; margin-right: 8px; flex-shrink: 0; }
.t-btn.r { background: #ff5f57; box-shadow: 0 0 4px #ff5f5780; }
.t-btn.y { background: #febc2e; box-shadow: 0 0 4px #febc2e80; }
.t-btn.g { background: #28c840; box-shadow: 0 0 4px #28c84080; }
.t-title {
  color: #888;
  font-size: 12.5px;
  margin-left: 10px;
  letter-spacing: 0.4px;
}
.t-tag {
  margin-left: auto;
  background: #1e1e1e;
  border: 1px solid #333;
  color: #555;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 3px;
  letter-spacing: 1px;
  text-transform: uppercase;
}
.t-body {
  padding: 18px 20px;
  font-size: 13px;
  line-height: 1.65;
  color: #d4d4d4;
  overflow-x: auto;
}
/* ── Terminal Typography ─────────────────────────────────────── */
.prompt { color: #28c840; }
.dim    { color: #555; }
.info   { color: #667eea; }
.ok     { color: #28c840; }
.warn   { color: #febc2e; }
.err    { color: #ff5f57; }
.accent { color: #c9a0dc; }
.cmd    { margin-bottom: 2px; }
.out    { margin-bottom: 3px; }
.indent { padding-left: 18px; border-left: 2px solid #2a2a2a; margin-left: 2px; margin-bottom: 3px; }
.result { padding-left: 14px; border-left: 2px solid #667eea; margin-left: 4px; color: #c9d1d9; margin-bottom: 3px; }
/* ── Cursor ──────────────────────────────────────────────────── */
.cur {
  display: inline-block;
  width: 8px; height: 14px;
  background: #d4d4d4;
  vertical-align: text-bottom;
  animation: blink 1.1s step-end infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
/* ── Progress Bar ─────────────────────────────────────────────── */
.prog-row { display: flex; align-items: center; margin: 6px 0; }
.prog-label { margin-right: 12px; color: #888; min-width: 80px; }
.prog-track {
  background: #252525;
  height: 8px;
  flex-grow: 1;
  border-radius: 2px;
  margin-right: 12px;
  overflow: hidden;
  position: relative;
}
.prog-fill {
  position: absolute; top: 0; left: 0;
  height: 100%;
  border-radius: 2px;
  animation: progIn 2.4s cubic-bezier(.4,0,.2,1);
}
.prog-fill.full  { width: 100%; background: linear-gradient(90deg, #667eea, #764ba2); }
.prog-fill.hi    { width: 84%;  background: linear-gradient(90deg, #28c840, #667eea); }
.prog-fill.mid   { width: 55%;  background: linear-gradient(90deg, #febc2e, #28c840); }
.prog-fill.lo    { width: 28%;  background: linear-gradient(90deg, #ff5f57, #febc2e); }
.prog-pct { color: #667eea; font-weight: bold; min-width: 36px; text-align: right; }
@keyframes progIn { 0%{width:0} 100%{} }
/* ── Diagram (pre inside terminal) ───────────────────────────── */
.t-diag {
  white-space: pre;
  font-size: 12.5px;
  line-height: 1.35;
  color: #c9d1d9;
  overflow-x: auto;
  padding: 18px 20px;
  margin: 0;
  font-family: 'Menlo', 'Monaco', 'Cascadia Code', 'Courier New', monospace;
}
/* ── Code inside terminal (fixed mobile overflow) ────────────── */
.t-code {
  white-space: pre;
  font-size: 12.5px;
  line-height: 1.6;
  overflow-x: auto;
  padding: 18px 20px;
  margin: 0;
  color: #d4d4d4;
  font-family: 'Menlo', 'Monaco', 'Cascadia Code', 'Courier New', monospace;
}
.kw  { color: #c678dd; }   /* keywords */
.fn  { color: #61afef; }   /* functions / class names */
.str { color: #98c379; }   /* strings */
.cmt { color: #5c6370; }   /* comments */
.num { color: #d19a66; }   /* numbers */
.op  { color: #56b6c2; }   /* operators */
/* ── Divider inside terminal ──────────────────────────────────── */
.t-sep {
  height: 1px;
  background: #1e1e1e;
  margin: 2px 0;
}
/* ── Split pane ───────────────────────────────────────────────── */
.split { display: flex; gap: 0; }
.split .t-body { flex: 1; min-width: 0; }
.split-div { width: 1px; background: #1e1e1e; flex-shrink: 0; }
/* ── System monitor row ───────────────────────────────────────── */
.mon-row {
  display: grid;
  grid-template-columns: 140px 1fr 48px;
  align-items: center;
  margin-bottom: 5px;
  font-size: 12.5px;
}
.mon-label { color: #888; }
.mon-bar { background: #1e1e1e; height: 9px; border-radius: 2px; overflow: hidden; position: relative; }
.mon-fill { height: 100%; border-radius: 2px; }
.mon-val { color: #c9d1d9; text-align: right; font-size: 11px; }
/* ── Diff view ────────────────────────────────────────────────── */
.diff-add { color: #98c379; background: #0d1f0d; display: block; padding: 0 2px; }
.diff-del { color: #ff5f57; background: #1f0d0d; display: block; padding: 0 2px; }
.diff-ctx { color: #555;                         display: block; padding: 0 2px; }
.diff-hdr { color: #667eea;                      display: block; padding: 0 2px; margin-bottom: 4px; }
/* ── Intel panel ──────────────────────────────────────────────── */
.intel {
  background: #0d1117;
  border: 1px solid #21262d;
  border-radius: 8px;
  margin: 20px 0;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  overflow: hidden;
}
.intel-hdr {
  background: #161b22;
  padding: 10px 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #21262d;
}
.intel-cls { color: #667eea; font-size: 10px; font-weight: bold; letter-spacing: 4px; }
.intel-id  { color: #484f58; font-size: 11px; }
.intel-body { padding: 12px 18px; }
.intel-row {
  display: flex;
  padding: 7px 0;
  border-bottom: 1px solid #0d1117;
  font-size: 13px;
  line-height: 1.5;
}
.intel-row:last-child { border-bottom: none; }
.intel-lbl { color: #8b949e; min-width: 130px; flex-shrink: 0; }
.intel-val { color: #c9d1d9; }
/* ── Code header (for standalone use, not terminal) ──────────── */
.ch {
  background: #161b22;
  padding: 8px 16px;
  font-family: 'Menlo','Monaco','Courier New',monospace;
  font-size: 12px;
  border-radius: 6px 6px 0 0;
  border: 1px solid #21262d;
  border-bottom: none;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 14px;
}
.ch-file { color: #c9d1d9; font-weight: bold; }
.ch-lang { color: #667eea; font-size: 10px; letter-spacing: 2px; text-transform: uppercase; }
</style>

---

# 1. The Terminal Frame — Universal Container

The terminal window is the design atom of this library. Every diagram, every code block, every architecture visualization, every log stream lives inside one. Not because it's trendy — because this is a running system. The terminal frame communicates that. It says: *this is real, it executes, it has state.*

The frame is built from three elements: the chrome (header with macOS-style traffic light buttons), the title bar, and the body. The body accepts four content types: command/output text, `<pre>` for diagrams, `<pre>` for code, and the split-pane layout for side-by-side views.

**The Rule:** No architecture diagram lives in a collapsible `<details>` block. It lives in a terminal window, fully visible, because if it's worth documenting it's worth showing.

---

## 2. Terminal: Architecture Diagrams

<div class="t">
  <div class="t-hdr">
    <div class="t-btn r"></div><div class="t-btn y"></div><div class="t-btn g"></div>
    <span class="t-title">research-subsystem · architecture</span>
    <span class="t-tag">DIAGRAM</span>
  </div>
<pre class="t-diag">
                       ┌──────────────────────────┐
                       │      USER INTERFACE       │
                       │   Query  |  Controls      │
                       └─────────────┬────────────┘
                                     │ ResearchQuery
               ┌─────────────────────▼──────────────────────┐
               │           DEEP RESEARCH PLANNER              │
               │   Complexity Analysis · Sub-question Gen     │
               │   Collaboration Plan · Agent Assignment      │
               └─────────────────────┬──────────────────────┘
                                     │ ResearchPlan
               ┌─────────────────────▼──────────────────────┐
               │          RESEARCH EXECUTION ENGINE           │
               │                                             │
               │  MEMORY ─▶ EXPLORE ─▶ DIVE ─▶ VALIDATE     │
               │      └─── SYNTH ◀── REPORT ◀──┘            │
               │                                             │
               │  State Machine · 6-Phase Pipeline           │
               │  Plan Adaptation · User Intervention        │
               └──┬──────────┬──────────┬──────────────────┘
                  │          │          │
    ┌─────────────▼┐  ┌──────▼──────┐  ┌▼──────────────────┐
    │   BROWSER    │  │ INTELLIGENCE │  │  COGNITIVE CACHE   │
    │   AGENT      │  │   ENGINE     │  │                    │
    │              │  │              │  │  HOT  — Redis      │
    │  Playwright  │  │  10-Dim QA   │  │  WARM — RocksDB    │
    │  Selenium    │  │  Semantic    │  │  COLD — Memory     │
    │  Multi-engine│  │  Gap Detect  │  │                    │
    │  NLP Pipeline│  │  Bias Decomp │  │  Breath Phases     │
    │  Content Ext │  │  Contradict  │  │  Quality Guard     │
    └──────────────┘  └─────────────┘  └───────────────────┘
                  │          │          │
               ┌──▼──────────▼──────────▼────────────────────┐
               │               RESEARCH SESSION               │
               │  Entities · Contradictions · Bias Records    │
               │  Entity Graph (contradicts / supports)       │
               │  ResearchMetrics · Processing History        │
               └─────────────────────┬──────────────────────┘
                                     │
               ┌─────────────────────▼──────────────────────┐
               │              REPORT EXPORTER                │
               │  HTML · Markdown · JSON · PDF · Artifact    │
               │  Transform: Website · Slides · Infographic  │
               └─────────────────────────────────────────────┘
               ╔═════════════════════════════════════════════╗
               ║      STREAM MANAGER  ·  WebSocket Layer      ║
               ║   Real-time events to/from all components    ║
               ╚═════════════════════════════════════════════╝
</pre>
</div>

---

<div class="t">
  <div class="t-hdr">
    <div class="t-btn r"></div><div class="t-btn y"></div><div class="t-btn g"></div>
    <span class="t-title">cognitive-cache · tri-layer architecture</span>
    <span class="t-tag">DIAGRAM</span>
  </div>
<pre class="t-diag">
  ┌────────────────────────────────────────────────────────────┐
  │                  COGNITIVE RESONANCE CACHE                  │
  ├────────────────────────────────────────────────────────────┤
  │                                                            │
  │   BREATH PHASES                                            │
  │   ──────────────────────────────────────────────────────   │
  │   INHALE   ──▶  Acquisition open  · Cache accepts writes   │
  │   HOLD_IN  ──▶  Analysis mode     · Read-heavy operations  │
  │   EXHALE   ──▶  Synthesis output  · Consolidation pass     │
  │   HOLD_OUT ──▶  Reflection audit  · Quality Guardian runs  │
  │                                                            │
  │   STORAGE TIERS                                            │
  │   ──────────────────────────────────────────────────────   │
  │                                                            │
  │   ┌──────────────────────────────────────────────────┐    │
  │   │  HOT  ·  Redis                                   │    │
  │   │  Metadata headers · Access decisions · Sub-ms    │    │
  │   └──────────────────────────────────────────────────┘    │
  │                     │ cache miss                           │
  │   ┌──────────────────▼───────────────────────────────┐    │
  │   │  WARM ·  RocksDB                                 │    │
  │   │  Full TriaxialKnowledgeEntity · Fast retrieval   │    │
  │   └──────────────────────────────────────────────────┘    │
  │                     │ eviction / archive                   │
  │   ┌──────────────────▼───────────────────────────────┐    │
  │   │  COLD ·  Memory System                           │    │
  │   │  Permanent archive · Pattern learning history    │    │
  │   └──────────────────────────────────────────────────┘    │
  │                                                            │
  │   QUALITY GUARDIAN VERDICTS                                │
  │   ──────────────────────────────────────────────────────   │
  │   RETAIN            ──▶  Include in synthesis              │
  │   PURGE             ──▶  Exclude, log reason               │
  │   FLAG_WITH_WARNING ──▶  Include with explicit caveat      │
  │   TRIGGER_SYNTHESIS ──▶  Route to contradiction resolution │
  │                                                            │
  └────────────────────────────────────────────────────────────┘
</pre>
</div>

---

# 3. Terminal: Code Blocks (Fixed)

The cutoff problem in v2 happened because the HTML header div and the markdown code fence were separate DOM nodes with no shared overflow container. The fix is total consolidation — everything inside one `<div class="t">` block, the code in a `<pre class="t-code">` element. No markdown fences. One container, one overflow rule, zero truncation on mobile.

<div class="t">
  <div class="t-hdr">
    <div class="t-btn r"></div><div class="t-btn y"></div><div class="t-btn g"></div>
    <span class="t-title">research_engine.py</span>
    <span class="t-tag">PYTHON</span>
  </div>
<pre class="t-code">
<span class="kw">class</span> <span class="fn">ResearchExecutionEngine</span>:
    <span class="str">"""
    The cognitive research orchestrator that executes research plans.
    Coordinates all research subsystems to transform strategic plans
    into actionable insights.
    """</span>

    <span class="kw">async def</span> <span class="fn">_execute_step</span>(self, step: ResearchStep) -&gt; Dict[str, Any]:
        <span class="kw">match</span> step.step_type:
            <span class="kw">case</span> StepType.PRELIMINARY_MEMORY_SEARCH:
                result = <span class="kw">await</span> self.<span class="fn">_execute_memory_search</span>(step)
            <span class="kw">case</span> StepType.EXPLORATORY_SEARCH:
                result = <span class="kw">await</span> self.<span class="fn">_execute_browser_search</span>(step, depth=<span class="str">'exploratory'</span>)
            <span class="kw">case</span> StepType.DEEP_DIVE:
                result = <span class="kw">await</span> self.<span class="fn">_execute_browser_search</span>(step, depth=<span class="str">'deep'</span>)
            <span class="kw">case</span> StepType.SYNTHESIS:
                result = <span class="kw">await</span> self.<span class="fn">_execute_collaborative_synthesis</span>(step)
            <span class="kw">case</span> StepType.VALIDATION_AND_CONTRADICTION_RESOLUTION:
                result = <span class="kw">await</span> self.<span class="fn">_execute_validation</span>(step)
            <span class="kw">case</span> StepType.REPORT_GENERATION:
                result = <span class="kw">await</span> self.<span class="fn">_execute_report_generation</span>(step)
        <span class="kw">return</span> result
</pre>
</div>

<div class="t">
  <div class="t-hdr">
    <div class="t-btn r"></div><div class="t-btn y"></div><div class="t-btn g"></div>
    <span class="t-title">research_cache_engine.py  ·  Cache Layer Definition</span>
    <span class="t-tag">PYTHON</span>
  </div>
<pre class="t-code">
<span class="kw">class</span> <span class="fn">CacheLayer</span>(str, Enum):
    HOT  = <span class="str">"hot"</span>   <span class="cmt"># Redis    — metadata headers for rapid access decisions</span>
    WARM = <span class="str">"warm"</span>  <span class="cmt"># RocksDB  — full TriaxialKnowledgeEntity objects</span>
    COLD = <span class="str">"cold"</span>  <span class="cmt"># Memory   — permanent archive and learning history</span>

<span class="kw">class</span> <span class="fn">BreathPhase</span>(str, Enum):
    INHALE   = <span class="str">"inhale"</span>    <span class="cmt"># Knowledge acquisition phase</span>
    HOLD_IN  = <span class="str">"hold_in"</span>   <span class="cmt"># Integration and analysis phase</span>
    EXHALE   = <span class="str">"exhale"</span>    <span class="cmt"># Synthesis and output phase</span>
    HOLD_OUT = <span class="str">"hold_out"</span>  <span class="cmt"># Reflection and evaluation phase</span>

<span class="kw">class</span> <span class="fn">CacheVerdict</span>(str, Enum):
    RETAIN            = <span class="str">"retain"</span>
    PURGE             = <span class="str">"purge"</span>
    FLAG_WITH_WARNING = <span class="str">"flag_with_warning"</span>
    TRIGGER_SYNTHESIS = <span class="str">"trigger_synthesis"</span>
</pre>
</div>

---

# 4. Terminal: Multi-Pane Split View

For showing two related processes running in parallel — a planner on the left, an executor on the right — use the split layout. Both panes share the same terminal chrome.

<div class="t">
  <div class="t-hdr">
    <div class="t-btn r"></div><div class="t-btn y"></div><div class="t-btn g"></div>
    <span class="t-title">somnus · dual-process view</span>
    <span class="t-tag">SPLIT</span>
  </div>
  <div class="split">
    <div class="t-body" style="border-right: 1px solid #1e1e1e;">
      <div class="out dim">[PLANNER] Analyzing query...</div>
      <div class="out dim">[PLANNER] Complexity: EXPERT</div>
      <div class="out dim">[PLANNER] Domains: ai, systems</div>
      <div class="out info">[PLANNER] Generated 12 sub-Qs</div>
      <div class="out info">[PLANNER] Collaboration: PARALLEL</div>
      <div class="out info">[PLANNER] Agents assigned: 3</div>
      <div class="out ok" style="margin-top:8px">[PLANNER] Plan ready ✓</div>
    </div>
    <div class="t-body">
      <div class="out dim">[ENGINE] Waiting for plan...</div>
      <div class="out dim">[ENGINE] Plan received.</div>
      <div class="out info">[ENGINE] Phase 1: Memory Search</div>
      <div class="out info">[ENGINE] Memories: 8 | Entities: 6</div>
      <div class="out info">[ENGINE] Phase 2: Explore</div>
      <div class="out warn">[ENGINE] Contradiction detected</div>
      <div class="out ok" style="margin-top:8px">[ENGINE] Phase 3 queued</div>
    </div>
  </div>
</div>

---

# 5. Terminal: System Monitor View

For development status overviews, subsystem health, or benchmark summaries — the monitor view replaces boring tables with something that looks like it came from a live system.

<div class="t">
  <div class="t-hdr">
    <div class="t-btn r"></div><div class="t-btn y"></div><div class="t-btn g"></div>
    <span class="t-title">somnus · subsystem monitor</span>
    <span class="t-tag">STATUS</span>
  </div>
  <div class="t-body">
    <div class="out dim" style="margin-bottom:10px;">Somnus Sovereign Systems — Implementation Status — 2026.05.22</div>
    <div class="mon-row">
      <span class="mon-label">Memory Core</span>
      <span class="mon-bar"><span class="mon-fill prog-fill full" style="width:100%;animation:none;"></span></span>
      <span class="mon-val ok">100%</span>
    </div>
    <div class="mon-row">
      <span class="mon-label">VM Orchestrator</span>
      <span class="mon-bar"><span class="mon-fill prog-fill" style="width:95%;background:linear-gradient(90deg,#28c840,#667eea);animation:none;"></span></span>
      <span class="mon-val ok"> 95%</span>
    </div>
    <div class="mon-row">
      <span class="mon-label">Research Engine</span>
      <span class="mon-bar"><span class="mon-fill prog-fill" style="width:80%;background:linear-gradient(90deg,#667eea,#764ba2);animation:none;"></span></span>
      <span class="mon-val info"> 80%</span>
    </div>
    <div class="mon-row">
      <span class="mon-label">Browser Agent</span>
      <span class="mon-bar"><span class="mon-fill prog-fill" style="width:75%;background:linear-gradient(90deg,#667eea,#764ba2);animation:none;"></span></span>
      <span class="mon-val info"> 75%</span>
    </div>
    <div class="mon-row">
      <span class="mon-label">Cache Engine</span>
      <span class="mon-bar"><span class="mon-fill prog-fill" style="width:70%;background:linear-gradient(90deg,#667eea,#764ba2);animation:none;"></span></span>
      <span class="mon-val info"> 70%</span>
    </div>
    <div class="mon-row">
      <span class="mon-label">Stream Manager</span>
      <span class="mon-bar"><span class="mon-fill prog-fill full" style="width:100%;animation:none;"></span></span>
      <span class="mon-val ok">100%</span>
    </div>
    <div class="mon-row">
      <span class="mon-label">Frontend UI</span>
      <span class="mon-bar"><span class="mon-fill prog-fill" style="width:30%;background:linear-gradient(90deg,#febc2e,#28c840);animation:none;"></span></span>
      <span class="mon-val warn"> 30%</span>
    </div>
    <div class="mon-row">
      <span class="mon-label">Integration Tests</span>
      <span class="mon-bar"><span class="mon-fill prog-fill" style="width:15%;background:linear-gradient(90deg,#ff5f57,#febc2e);animation:none;"></span></span>
      <span class="mon-val err"> 15%</span>
    </div>
    <div class="t-sep" style="margin:12px 0;"></div>
    <div class="out dim">Total: 69+ files  ·  48,000+ lines  ·  9 major subsystems</div>
    <div class="cmd" style="margin-top:6px;"><span class="prompt">sovereign@somnus:~$</span> <span class="cur"></span></div>
  </div>
</div>

---

# 6. Terminal: Research Session

The full research session terminal — showing the 6-phase pipeline from query to report. This is the flagship pattern: what an actual Somnus research session looks like from the outside.

<div class="t">
  <div class="t-hdr">
    <div class="t-btn r"></div><div class="t-btn y"></div><div class="t-btn g"></div>
    <span class="t-title">somnus-research · session SIC-2026-0042</span>
    <span class="t-tag">LIVE</span>
  </div>
  <div class="t-body">
    <div class="cmd"><span class="prompt">researcher@somnus:~$</span> somnus research --query "Anthropic memory architecture" --depth exhaustive</div>
    <div class="out dim" style="margin-top:6px;">[PLAN] Analyzing query complexity...</div>
    <div class="out dim">[PLAN] Complexity: EXPERT  |  Domains: ai_architecture, systems</div>
    <div class="out dim">[PLAN] Generated 12 sub-questions across 4 query families</div>
    <div class="out dim">[VM]   Provisioning research-vm-0x7a3f  ·  Playwright + Selenium ready</div>
    <div class="t-sep" style="margin:8px 0;"></div>
    <div class="out info">[PHASE 1] Memory Search — INHALE</div>
    <div class="result">Retrieved 8 memories  |  6 entities created  |  saturation 0.34</div>
    <div class="t-sep" style="margin:8px 0;"></div>
    <div class="out info">[PHASE 2] Exploratory Search — INHALE</div>
    <div class="result">23 sources found  |  19 entities created</div>
    <div class="result warn">3 contradictions detected  →  queued for Phase 4</div>
    <div class="t-sep" style="margin:8px 0;"></div>
    <div class="out info">[PHASE 3] Deep Dive — HOLD_IN</div>
    <div class="prog-row">
      <span class="prog-label">Analyzing</span>
      <span class="prog-track"><span class="prog-fill full"></span></span>
      <span class="prog-pct">100%</span>
    </div>
    <div class="result">2 failure modes identified  |  5 undocumented behaviors  |  2 bias flags</div>
    <div class="t-sep" style="margin:8px 0;"></div>
    <div class="out dim">[CHECK] Synthesis Checkpoint ─────────────────────────────────────</div>
    <div class="out dim">        Completeness: 0.71  |  Diversity: 0.83  |  Credibility: 0.79</div>
    <div class="out warn">        Hypothesis v1 → v2  (FR-003 killed initial framing)</div>
    <div class="t-sep" style="margin:8px 0;"></div>
    <div class="out info">[PHASE 4] Contradiction Resolution — EXHALE</div>
    <div class="result ok">2/3 resolved  |  FR-007 unresolved (requires non-public access)</div>
    <div class="t-sep" style="margin:8px 0;"></div>
    <div class="out info">[PHASE 5] System Reconstruction — EXHALE</div>
    <div class="result">14 components mapped  |  3 inferred  |  1 contradicted</div>
    <div class="t-sep" style="margin:8px 0;"></div>
    <div class="out info">[PHASE 6] Report Generation — HOLD_OUT</div>
    <div class="prog-row">
      <span class="prog-label">Exporting</span>
      <span class="prog-track"><span class="prog-fill full"></span></span>
      <span class="prog-pct">100%</span>
    </div>
    <div class="result">Artifacts: research_artifact  ·  markdown  ·  json</div>
    <div class="t-sep" style="margin:8px 0;"></div>
    <div class="out dim">[STOP] Condition 2 reached — duplicates across 3+ query families</div>
    <div class="out ok" style="margin-top:8px;">Session complete  ·  42 entities  ·  3 contradictions (2 resolved)  ·  efficiency 0.87</div>
    <div class="cmd" style="margin-top:8px;"><span class="prompt">researcher@somnus:~$</span> <span class="cur"></span></div>
  </div>
</div>

---

# 7. Terminal: Diff View

For hypothesis evolution, architecture deltas, or anything where version-to-version changes need to be visible and permanent.

<div class="t">
  <div class="t-hdr">
    <div class="t-btn r"></div><div class="t-btn y"></div><div class="t-btn g"></div>
    <span class="t-title">hypothesis-evolution · SIC-2026-0042</span>
    <span class="t-tag">DIFF</span>
  </div>
<pre class="t-code">
<span class="diff-hdr">--- hypothesis/v1  (initial)</span>
<span class="diff-hdr">+++ hypothesis/v2  (current — updated on Phase 4 resolution)</span>
<span class="diff-ctx"> ─────────────────────────────────────────────────────────────</span>
<span class="diff-ctx"> Session: SIC-2026-0042  |  Target: Anthropic Memory System</span>
<span class="diff-ctx"> ─────────────────────────────────────────────────────────────</span>

<span class="diff-del">- "Anthropic uses full context retention with no eviction policy."</span>
<span class="diff-del">- Basis: Official documentation (Tier 1)  |  Confidence: 85%</span>

<span class="diff-add">+ "Anthropic uses tiered retention with importance-weighted eviction"</span>
<span class="diff-add">+ "under sustained context pressure, likely sliding window at ~150K."</span>
<span class="diff-add">+ Basis: S-014 telemetry + S-021 changelog (Tier 2)  |  Confidence: 72%</span>

<span class="diff-ctx"> Kill Evidence for v1:</span>
<span class="diff-ctx">   S-014: Observable context degradation at ~150K tokens (HN thread)</span>
<span class="diff-ctx">   S-021: "Improved context management" implies active eviction policy</span>

<span class="diff-ctx"> Unresolved: FR-007 — official docs vs telemetry requires empirical test</span>
</pre>
</div>

---

<div class="t">
  <div class="t-hdr">
    <div class="t-btn r"></div><div class="t-btn y"></div><div class="t-btn g"></div>
    <span class="t-title">architecture-playbook · research-engine-v2</span>
    <span class="t-tag">DELTA</span>
  </div>
<pre class="t-code">
<span class="diff-ctx"> IMPLEMENTATION DELTA ────────────────────────────────────────────</span>

<span class="diff-add">+ [KEEP]    6-phase execution pipeline — architecture is correct</span>
<span class="diff-add">+ [KEEP]    Breath phase sync on cache — INHALE/EXHALE rhythm</span>
<span class="diff-add">+ [KEEP]    4-axis entity assessment (credibility/reliability/bias/completeness)</span>

<span class="diff-del">- [SPLIT]   ResearchIntelligenceEngine mock inside research_engine.py</span>
<span class="diff-add">+           → Separate stub from research_intelligence.py implementation</span>

<span class="diff-add">+ [ADD]     Hypothesis versioning with explicit kill/replace logging</span>
<span class="diff-add">+ [ADD]     Phase 4 contradictions feed back into Phase 2 query expansion</span>
<span class="diff-add">+ [ADD]     Signal-to-noise budget ceiling (3 attempts max per lead)</span>

<span class="diff-del">- [RENAME]  "synthesis_results" → ambiguous, refers to entity list</span>
<span class="diff-add">+           → rename to "synthesis_entities"</span>

<span class="diff-add">+ [UPGRADE] _check_plan_adaptation() — uncomment and wire to intelligence metrics</span>
<span class="diff-add">+           Currently commented in run() loop, plan adaptation disabled</span>
</pre>
</div>

---

# 8. Banners and Identity Blocks

### Pattern: Full SVG Identity Banner

<div align="center">

<svg width="460" height="200" viewBox="0 0 460 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="eclogueGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#764ba2;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#f093fb;stop-opacity:1" />
    </linearGradient>
    <filter id="eclogueGlow">
      <feGaussianBlur stdDeviation="3.5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="460" height="200" fill="#0d1117" rx="14"/>
  <rect x="1" y="1" width="458" height="198" fill="none" stroke="#1e2430" stroke-width="1" rx="14"/>
  <text x="230" y="98" font-family="'Courier New', monospace" font-size="56" fill="url(#eclogueGrad)" text-anchor="middle" filter="url(#eclogueGlow)" font-weight="bold">Eclogue Ø</text>
  <text x="230" y="135" font-family="'Courier New', monospace" font-size="13" fill="#8b949e" text-anchor="middle" letter-spacing="1">Dense Cognitive Architecture</text>
  <text x="230" y="158" font-family="'Courier New', monospace" font-size="11" fill="#484f58" text-anchor="middle">3.5T Active Parameters  |  4M Context  |  6-Modal I/O</text>
  <line x1="130" y1="172" x2="330" y2="172" stroke="#21262d" stroke-width="1"/>
  <text x="230" y="190" font-family="'Courier New', monospace" font-size="9" fill="#2d333b" text-anchor="middle" letter-spacing="5">SOMNUS SOVEREIGN SYSTEMS</text>
</svg>

</div>

### Pattern: Minimal Subsystem Banner

<div align="center">
<svg width="400" height="56" viewBox="0 0 400 56" xmlns="http://www.w3.org/2000/svg">
  <rect width="400" height="56" fill="#0d1117" rx="8"/>
  <text x="200" y="30" font-family="'Courier New', monospace" font-size="19" fill="#c9d1d9" text-anchor="middle" font-weight="bold" letter-spacing="8">RESEARCH ENGINE</text>
  <line x1="110" y1="42" x2="290" y2="42" stroke="#764ba2" stroke-width="2" opacity="0.55"/>
</svg>
</div>

---

# 9. Tag and Badge Systems

### Primary Specification Tags

<p align="center">
  <img src="https://img.shields.io/badge/Parameters-3.5T%20Dense-667eea?style=for-the-badge" alt="Parameters"/>
  <img src="https://img.shields.io/badge/Context-4M%20Tokens-764ba2?style=for-the-badge" alt="Context"/>
  <img src="https://img.shields.io/badge/Vocab-524K%20Tokens-f093fb?style=for-the-badge" alt="Vocab"/>
</p>
<p align="center">
  <img src="https://img.shields.io/badge/Architecture-Dense%20Transformer-ff6b6b?style=for-the-badge" alt="Architecture"/>
  <img src="https://img.shields.io/badge/Modalities-6%20In%20%7C%206%20Out-4ecdc4?style=for-the-badge" alt="Modalities"/>
  <img src="https://img.shields.io/badge/Status-Alpha%20Design-45b7d1?style=for-the-badge" alt="Status"/>
</p>
<p align="center">
  <img src="https://img.shields.io/badge/-Sovereign%20Open%20Source-ffd93d?style=flat-square" alt="Sovereign"/>
  <img src="https://img.shields.io/badge/-Local%20First-6bcf7f?style=flat-square" alt="Local"/>
  <img src="https://img.shields.io/badge/-Constitutional%20AI-ff8a65?style=flat-square" alt="Constitutional"/>
  <img src="https://img.shields.io/badge/License-Apache%202.0-96ceb4?style=flat-square" alt="License"/>
</p>

### Status Tags

<p align="center">
  <img src="https://img.shields.io/badge/Memory%20Core-Production-28c840?style=flat-square" alt="Memory"/>
  <img src="https://img.shields.io/badge/Research%20Engine-Advanced-667eea?style=flat-square" alt="Research"/>
  <img src="https://img.shields.io/badge/VM%20Orchestrator-Production-28c840?style=flat-square" alt="VM"/>
  <img src="https://img.shields.io/badge/Frontend-In%20Progress-febc2e?style=flat-square" alt="Frontend"/>
  <img src="https://img.shields.io/badge/Integration%20Tests-Pending-ff5f57?style=flat-square" alt="Tests"/>
</p>

**Color Palette Reference**

| Purpose | Hex | Use |
| --- | --- | --- |
| Production / Pass | `#28c840` | Stable, deployed, verified |
| Active / In Progress | `#667eea` | Under development, functional |
| Warning / Partial | `#febc2e` | Incomplete, needs work |
| Critical / Fail | `#ff5f57` | Broken, blocked, missing |
| Brand Purple | `#764ba2` | Somnus brand, highlights |
| Brand Pink | `#f093fb` | Secondary accent |
| Neutral | `#8b949e` | Metadata, version, license |

---

# 10. Intelligence Report Panels

<div class="intel">
  <div class="intel-hdr">
    <span class="intel-cls">ASSESSMENT</span>
    <span class="intel-id">SIC-2026-0042  ·  2026.05.22</span>
  </div>
  <div class="intel-body">
    <div class="intel-row">
      <span class="intel-lbl">Target</span>
      <span class="intel-val">Anthropic Memory System — Context Window Management</span>
    </div>
    <div class="intel-row">
      <span class="intel-lbl">Confidence</span>
      <span class="intel-val" style="color:#28c840;">HIGH  72%</span>
    </div>
    <div class="intel-row">
      <span class="intel-lbl">Sources</span>
      <span class="intel-val">4 Tier-1  |  7 Tier-2  |  3 Tier-3</span>
    </div>
    <div class="intel-row">
      <span class="intel-lbl">Contradictions</span>
      <span class="intel-val" style="color:#febc2e;">2 unresolved — see FR-003, FR-007</span>
    </div>
    <div class="intel-row">
      <span class="intel-lbl">Key Finding</span>
      <span class="intel-val">Documented "unlimited context" contradicted by empirical degradation at ~150K tokens under load. Tiered eviction is inferred, not confirmed.</span>
    </div>
    <div class="intel-row">
      <span class="intel-lbl">Hypothesis</span>
      <span class="intel-val">v2 — Initial hypothesis killed by S-014 telemetry. Revised: importance-weighted eviction with sliding window approximation.</span>
    </div>
    <div class="intel-row">
      <span class="intel-lbl">Stop Condition</span>
      <span class="intel-val">Condition 2 — duplicate returns across 3 query families. FK-007 requires empirical test.</span>
    </div>
  </div>
</div>

---

# 11. Metric Dashboards

### Pure Markdown Bars

| Subsystem | Coverage |
| --- | --- |
| Memory Core | `████████████████████` 100% |
| VM Orchestrator | `███████████████████░` 95% |
| Research Engine | `████████████████░░░░` 80% |
| Browser Agent | `███████████████░░░░░` 75% |
| Cache Engine | `██████████████░░░░░░` 70% |
| Stream Manager | `████████████████████` 100% |
| Frontend UI | `██████░░░░░░░░░░░░░░` 30% |
| Integration Tests | `███░░░░░░░░░░░░░░░░░` 15% |

### Benchmark Comparison

```
Cherry (Qwen3-1.7B, RL-tuned) ████████████████████░░░░   84.2%
Qwen3-1.7B (baseline)         ████████████████░░░░░░░░   68.1%
Phi-3-mini (3.8B)             █████████████████░░░░░░░   71.4%
Gemma-2B                      ██████████████░░░░░░░░░░   59.8%

Hardware:  Ryzen 5 2400G / 12GB RAM / No GPU
Method:    q*-adjacent RL, 800 curated training pairs
Result:    +16.1% over baseline on constrained hardware
```

---

# 12. Signal and Evidence Blocks

> **CLAIM-042:** Anthropic uses importance-weighted eviction under sustained context pressure.
>
> **Status:** `INFERRED`  |  **Confidence:** 72%  |  **Tier:** 2
>
> **Evidence For:**
> > S-014: Observable recall degradation past ~150K tokens — HN thread, 2025-03. Multiple independent reports.
> > S-021: "Improved context management for long conversations" in API changelog, 2025-01. Implies active management.
>
> **Evidence Against:**
> > S-008: Official docs claim "full context retention" — Tier 1 but potentially stale.
>
> **Resolution:** Requires controlled experiment at 100K / 150K / 200K token boundaries. See Unknown UK-003.

---

# 13. Pipeline Flow Visualizations

```
 ╔═══════════╗    ╔═══════════╗    ╔═══════════╗
 ║  PHASE 1  ║───▶║  PHASE 2  ║───▶║  PHASE 3  ║
 ║  Memory   ║    ║  Explore  ║    ║ Deep Dive ║
 ║  INHALE   ║    ║  INHALE   ║    ║ HOLD_IN   ║
 ╚═══════════╝    ╚═══════════╝    ╚═════╤═════╝
                                         │
                              ╔══════════▼══════════╗
                              ║ SYNTHESIS CHECKPOINT ║
                              ║ 10-Dim Assessment    ║
                              ║ Hypothesis Mutation? ║
                              ╚══════════╤══════════╝
                                         │
 ╔═══════════╗    ╔═══════════╗    ╔═════▼═════╗
 ║  PHASE 6  ║◀───║  PHASE 5  ║◀───║  PHASE 4  ║
 ║  Report   ║    ║  Reconst  ║    ║ Validate  ║
 ║  HOLD_OUT ║    ║  EXHALE   ║    ║ EXHALE    ║
 ╚═══════════╝    ╚═══════════╝    ╚═══════════╝
```

---

# 14. Principles and Anti-Patterns

**The terminal is the frame.** Not a collapsible. Not a code fence. A terminal window. Because this is a running system — document it like one.

**The fix for mobile code cutoff:** never mix HTML header divs with markdown fences. One HTML container, one `<pre class="t-code">`, one overflow rule. Done.

**Every diagram is a first-class citizen.** If it's collapsed behind `<details>`, the reader will not read it. If it lives in a terminal window, it is part of the page.

**The styling rules:**

- Dark backgrounds: `#0d1117`, `#141414`, `#161b22`
- Monospace typography throughout: Menlo, Monaco, Cascadia Code, Courier New
- Accent colors that mean something: green = ok, blue = info, yellow = warn, red = err, purple = brand
- No rainbow gradients, no pastel, no white backgrounds, no Inter/Roboto
- Animation only where it communicates state: progress bars animate, cursors blink, everything else is static

**What doesn't belong here:**

- Emojis in headers
- Collapsible architecture diagrams
- `<details>` blocks hiding anything important
- Badges that say nothing ("Built with Love", "Open Source")
- Tables of contents with emoji bullets
- Anything that looks like it was generated by asking a chatbot to make your README "look good"

---

<div align="center">

<svg width="400" height="48" viewBox="0 0 400 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="400" height="48" fill="#0d1117" rx="6"/>
  <line x1="60" y1="24" x2="170" y2="24" stroke="#21262d" stroke-width="1"/>
  <line x1="230" y1="24" x2="340" y2="24" stroke="#21262d" stroke-width="1"/>
  <text x="200" y="28" font-family="'Courier New', monospace" font-size="10" fill="#484f58" text-anchor="middle" letter-spacing="3">SOMNUS SOVEREIGN SYSTEMS</text>
</svg>

</div>
