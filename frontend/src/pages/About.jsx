import { Link } from 'react-router-dom'

// ------------------------------
// Pipeline step
// ------------------------------

function PipelineStep({ number, title, description, last }) {
  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div className="w-8 h-8 rounded-full bg-cyan-600 text-white text-sm font-bold flex items-center justify-center shrink-0">
          {number}
        </div>
        {!last && <div className="w-px flex-1 bg-gray-200 dark:bg-gray-800 mt-2" />}
      </div>
      <div className={`pb-8 ${last ? '' : ''}`}>
        <p className="text-sm font-semibold text-gray-800 dark:text-gray-100 mt-1">{title}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 leading-relaxed">{description}</p>
      </div>
    </div>
  )
}

// ------------------------------
// Use case card
// ------------------------------

function UseCaseCard({ title, description }) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl px-4 py-4">
      <p className="text-sm font-semibold text-gray-100">{title}</p>
      <p className="text-xs text-gray-400 mt-1 leading-relaxed">{description}</p>
    </div>
  )
}

// ------------------------------
// Tech card
// ------------------------------

function TechCard({ name, role }) {
  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900/50 px-4 py-3">
      <p className="text-sm font-semibold text-gray-800 dark:text-gray-100">{name}</p>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{role}</p>
    </div>
  )
}

// ------------------------------
// About page
// ------------------------------

export default function About() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12 space-y-12">

      {/* Hero */}
      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">What is AgentMesh?</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
          AgentMesh is a multi-agent AI system that reviews your code, fixes what it finds, and
          then checks its own work. Three specialized AI agents hand off to each other in sequence —
          if the fix isn't good enough, the system automatically retries. Every decision streams to
          your screen in real time.
        </p>
        <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
          It was built to demonstrate what a real agentic pipeline looks like in practice: not a
          single model doing everything, but distinct agents with structured inputs, outputs, and
          handoffs — the same pattern used in production AI systems.
        </p>
      </section>

      {/* How It Works */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">How It Works</h2>
        <div className="mt-2">
          <PipelineStep
            number="1"
            title="You submit code"
            description="Paste code or upload a file. The system auto-detects the language if you don't specify one."
          />
          <PipelineStep
            number="2"
            title="Reviewer agent analyzes it"
            description="The Reviewer reads your code and produces a structured list of issues — each tagged with a severity level (critical, warning, or suggestion) and a line reference."
          />
          <PipelineStep
            number="3"
            title="Fixer agent corrects the issues"
            description="The Fixer receives the original code and the Reviewer's issue list, then returns a corrected version with a changelog mapping each fix back to the original issue."
          />
          <PipelineStep
            number="4"
            title="Evaluator agent scores the fix"
            description="The Evaluator sees everything — original code, issues, fixed code, and changelog — and scores the fix across three dimensions: correctness, completeness, and code quality."
          />
          <PipelineStep
            number="5"
            title="Retry if needed"
            description="If the score falls short, the pipeline loops back to the Fixer for a second pass. This retry logic is built into the graph itself, not bolted on as an afterthought."
            last
          />
        </div>
      </section>

      {/* Where This Gets Used */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Where This Gets Used</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
          Most teams have content that gets reviewed and revised — but the review happens inconsistently,
          slowly, or not at all. A pipeline that can catch issues, apply corrections, and verify the
          result before anything reaches the end user has value well beyond code. Here's where it fits.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <UseCaseCard
            title="Customer Support"
            description="Review agent responses for accuracy and tone before they're sent. Flag answers that contradict policy or leave the issue unresolved."
          />
          <UseCaseCard
            title="Content and Marketing"
            description="Check drafts for brand voice, factual accuracy, and compliance with style guidelines. Automatically revise and re-score before publishing."
          />
          <UseCaseCard
            title="Sales Proposals"
            description="Analyze proposal drafts for missing value statements, pricing errors, or off-message claims. Return a corrected version with a change log for rep review."
          />
          <UseCaseCard
            title="HR Policy Documents"
            description="Scan new or revised HR documents for ambiguous language, missing clauses, or legal risk. Generate a corrected draft and score completeness."
          />
          <UseCaseCard
            title="Contract Review"
            description="Identify non-standard clauses, missing indemnity language, or jurisdiction mismatches in contract drafts — then apply and evaluate targeted corrections."
          />
          <UseCaseCard
            title="Internal Audit Reports"
            description="Review draft audit findings for completeness, consistency with supporting evidence, and required disclosure language before final sign-off."
          />
        </div>
      </section>

      {/* What Was Built */}
      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">What Was Built</h2>
        <ul className="space-y-2">
          {[
            'Three-agent LangGraph StateGraph with structured inter-agent handoffs and a conditional retry edge',
            'Real-time SSE streaming — every agent decision appears on screen as it happens',
            'Structured output enforced via JSON mode and XML tag parsing (different strategies per agent, chosen to handle code safely)',
            'FastAPI backend with dual input: raw text paste and multipart file upload',
            'Fully containerized with Docker; deployed to Hugging Face Spaces with zero-config cold starts',
            'React frontend with syntax highlighting, collapsible panels, dark mode, and an activity log with elapsed timestamps',
            'Tenacity retry logic on all Groq API calls with exponential backoff',
            'Automated language detection — heuristic fallback with LLM confirmation',
            'pytest suite covering Pydantic schema validation, fixer XML parser edge cases, graph routing logic, and the SSE endpoint (mocked graph — no API keys needed); separate E2E test class for live pipeline validation',
          ].map((item) => (
            <li key={item} className="flex gap-2 text-sm text-gray-600 dark:text-gray-400">
              <span className="text-cyan-500 shrink-0 mt-0.5">✓</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </section>

      {/* Tech Stack */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Tech Stack</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <TechCard name="LangGraph" role="Multi-agent StateGraph orchestration" />
          <TechCard name="FastAPI" role="Backend API and SSE streaming" />
          <TechCard name="Groq" role="LLM inference (llama-3.3-70b)" />
          <TechCard name="React + Vite" role="Frontend framework and build tool" />
          <TechCard name="Tailwind CSS" role="Styling and dark mode" />
          <TechCard name="highlight.js" role="Syntax highlighting in Fixer panel" />
          <TechCard name="Docker" role="Multi-stage containerized build" />
          <TechCard name="Hugging Face Spaces" role="Cloud deployment (Docker SDK)" />
          <TechCard name="Pydantic" role="Schema validation and settings" />
        </div>
      </section>

      {/* Links */}
      <section className="flex flex-wrap gap-3 pt-2">
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-medium transition-colors"
        >
          Try the App
        </Link>
        <a
          href="https://github.com/eholt723/agentmesh"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 text-sm font-medium transition-colors"
        >
          View on GitHub
        </a>
      </section>

    </div>
  )
}
