TEAMS





CONTACT SHEET


Doc1: Discovery Guide
G1000 Discovery Cheat Sheet
Your one-page companion for business owner conversations
________________


How to Use the G1000 Docs
You have four documents. Here's when to use each:


Doc
	Name
	When to Use
	📋 This doc
	Discovery Cheat Sheet
	During the call. Open on your laptop. Listen → match → ask follow-ups.
	🗺️ Doc 2
	Post-Discovery Mapping Guide
	After the call. Map what you heard to solvable categories + tool options.
	📖 Doc 3
	The AI Bible (Full Reference)
	When scoping solutions (Sessions 3+). Deep AI capability reference.
	🔧 Doc 5
	Web Dev & Infrastructure
	When building. How software works, RAG, agents, scraping, deployment.
	🆓 Doc 4
	Free Tools & Access Guide
	Anytime. Every free AI tool, API, and student benefit you can use right now.





Rule for today: Only this doc needs to be open during discovery. Everything else is for after.


________________


The Only Job During Discovery
Listen. Understand. Don't prescribe.


You are NOT pitching AI solutions on this call. You're figuring out where it hurts, why it hurts, and how much it costs them. The mapping comes later.


________________


Quick-Match: What You Hear → Where It Lives
What the business owner says
	Problem Category
	"Nobody can find anything" / "Only [name] knows where that is"
	A1 — Data Access
	"We don't track that" / "It lives in someone's head"
	A2 — Tracking Gaps
	"Our software doesn't connect to anything"
	A3 — Legacy Lock-in
	"Everything's on paper / PDFs / handwritten"
	A4 — Unstructured Data
	"We enter the same thing 3 times" / "Same report every Friday"
	B1 — Manual Tasks
	"If [person] left, we'd be screwed" / "No documentation"
	B2 — Missing SOPs
	"Left hand doesn't know what right hand is doing"
	B3 — Communication Gaps
	"Always slammed or dead" / "Scheduling takes forever"
	B4 — Scheduling
	"Leads fall through the cracks" / "Mostly word of mouth"
	C1 — Lead Gen / Pipeline
	"Drowning in support tickets" / "Same 10 questions"
	C2 — Customer Service
	"Haven't posted on Instagram in months" / "No marketing bandwidth"
	C3 — Marketing / Content
	"Proposals take 3 hours" / "Probably undercharging"
	C4 — Pricing / Quoting
	"Bookkeeping is a nightmare" / "Chasing invoices"
	D1 — Finance / Admin
	"Hiring takes forever" / "Onboarding is 3 months"
	D2 — HR / Hiring
	"Compliance eats our whole week"
	D3 — Compliance / Legal
	"Flying blind on decisions" / "Don't know what competitors charge"
	E1–E3 — Strategic Intel


Don't tell the owner the category code — this is for YOUR notes. Write down the letter-number (e.g., "B1, B2") next to your discovery notes so you can match later in Doc 2.


________________


Discovery Power Questions
Use these to go deeper when you hear friction. Pick 2–3 per pain point, don't interrogate.


Understanding the problem:


* "Walk me through exactly what happens when [that thing] goes wrong."
* "How often does that happen? Daily? Weekly?"
* "Who handles this right now? What does their day look like?"
* "What happens when that person is sick or on vacation?"


Understanding the cost:


* "Roughly how many hours per week does this eat up?"
* "Has this ever lost you a customer or a deal?"
* "What's the worst-case scenario when this breaks?"


Understanding what they've tried:


* "Have you tried to fix this before? What happened?"
* "Is there software you looked at and decided against? Why?"
* "If you could wave a magic wand, what would be different tomorrow?"


________________


During the Call: Do's and Don'ts
✅ DO
	❌ DON'T
	Take messy notes — clean up later
	Try to solve their problem live
	Ask "why" and "how" questions
	Ask yes/no questions
	Let awkward silences sit — they'll fill them
	Interrupt when they're thinking
	Write down exact quotes ("Only Maria knows")
	Paraphrase their words into jargon
	Note emotion and energy shifts
	Stay in your head matching categories
	Ask about their day, their team, their stress
	Jump straight to "have you tried AI?"


________________


After the Call: Next Steps
1. Debrief with your team (5 min) — What were the top 2–3 pain points?
2. Label each pain point using the Quick-Match table above
3. Open Doc 2 (Post-Discovery Mapping Guide) — Map pain points to solvable categories and tool options
4. Rank by impact — Which pain point, if solved, would change their business the most?
5. Open Doc 4 (Free Tools Guide) — Figure out what you can prototype with for $0
6. When you're ready to build — Doc 3 (AI capabilities) + Doc 5 (web dev & infrastructure) are your engineering references


________________




G1000 — Babson College, Spring 2026 The Generator Lead Team: Spencer, Joshua, Rustin, Cole, Reece


Doc 2: Building Blocks
G1000 Post-Discovery Mapping Guide: BUILDING BLOCKS
From "What hurts?" to "What's solvable?" — Use after every discovery call.
________________




How to use this doc: You just finished a discovery call. You have messy notes and a few pain points labeled with category codes from the Cheat Sheet. Now open this doc, find those categories, and map each pain point to solution approaches.


⚠️ Tools vs. Platforms: This doc favors tools you build with over platforms you subscribe to. A custom n8n workflow you control beats a Zapier plan you're locked into. This is 2026 — you can build bespoke systems faster than you can configure most platforms.


For deep tech details, see → Doc 3 (AI capabilities) and → Doc 5 (web dev & infrastructure).


________________


A. DATA & INFORMATION PROBLEMS
A1. Data Access & Retrieval
"The answer exists somewhere but nobody can find it."


Signals: "Only Maria knows where that is" · "20 min finding the right doc" · "Onboarding takes months"


Approach
	How to Build It
	Complexity
	RAG system
	LangGraph or LlamaIndex + vector DB (pgvector via Supabase/Neon, or Qdrant/Weaviate at scale) + Claude/GPT
	Med-High
	Quick knowledge chatbot
	Claude Projects or Custom GPTs — upload their docs, instant Q&A
	Low
	Custom semantic search
	Exa.ai search API, or build with embeddings + Supabase pgvector
	Med


Real example: Wealth advisors spend 20 min/meeting pulling notes. RAG system: "What did we tell the Silvas about savings rate last quarter?" — exact answer with source in seconds.


Disambiguation: Data exists in bad formats (paper, PDFs) → that's A4. A1 = digital but scattered.


________________


A2. Tracking Gaps — Data Doesn't Exist
"We don't track [critical thing] — it lives in someone's head."


Signals: "Don't know our CAC" · "Can't tell you which product has best margin" · "Inventory in a notebook"


Approach
	How to Build It
	Complexity
	Custom tracker (vibe-coded)
	Cursor/Claude Code → Next.js + Supabase — build exactly what they need in hours
	Med
	Data capture + dashboard
	Airtable (free edu) or Google Forms → Sheets
	Low
	Lightweight AI-native CRM
	Attio (AI-native, auto-builds from emails/calls) or HubSpot free tier
	Low-Med


Real example: Landscaping company — zero data on job duration vs. estimates. Custom app revealed 30% undercharge on commercial jobs.


________________


A3. Legacy Lock-in — Data Trapped in Bad Systems
"Data is stuck in [old system] and can't get out."


Signals: "Software doesn't integrate" · "Export CSV weekly, manually reformat" · "POS doesn't talk to inventory"


Approach
	How to Build It
	Complexity
	Workflow automation between systems
	n8n (self-hosted, free, has native AI agent nodes) — connect APIs, transform data, trigger actions
	Med
	Custom ETL pipelines
	Python/Node scripts via Cursor/Claude Code
	Med
	Reporting layer on top
	Metabase (open-source, free) or Evidence.dev
	Med
	Scraping when no API exists
	Firecrawl (search + extract in one API call), Playwright, Apify
	Med


Real example: Vacation rental — bookings, guest comms, maintenance, owner reporting all separate. n8n syncs all four.


________________


A4. Unstructured Data Chaos
"Mountains of info in formats we can't search or analyze."


Signals: "200 invoices/month, someone enters each one" · "Contracts in a filing cabinet" · "Handwritten inspections"


Approach
	How to Build It
	Complexity
	OCR + AI extraction
	Claude Vision or GPT-4o Vision → structured JSON output
	Low-Med
	Document processing pipeline
	Unstructured.io + LlamaParse (open-source, handles messy PDFs/tables/images) → LLM extraction
	Med
	Production doc processing
	Nanonets (API-first IDP — invoices, contracts, forms; high accuracy + developer-friendly; free tier)
	Med
	Email parsing + routing
	n8n email trigger → LLM classification → structured extraction → database
	Med
	Voice → text → structured data
	Whisper (free, local) or Granola → LLM extraction
	Low-Med


Real example: Real estate photos — 200+ per property, manual labeling. Vision model classifies by room type, generates descriptions. 2 hours → 15 min.


________________


B. PROCESS & WORKFLOW PROBLEMS
B1. Manual Repetitive Tasks
"Someone spends hours doing the same thing repeatedly."


Signals: "Enter same info in 3 places" · "Same report every Friday" · "12 steps for every new client"


Approach
	How to Build It
	Complexity
	Programmable workflow automation
	n8n (self-hosted, free, built-in AI agent nodes) — any trigger → action chain
	Low-Med
	Code-first automation
	Windmill (open-source, scripts + flows in one UI — tighter than n8n for complex internal tools)
	Med
	AI-assisted scripting
	Claude Code (terminal agent) or Cursor — write scripts that automate the exact task
	Med
	Durable long-running workflows
	Temporal (used by Netflix/Uber/Stripe teams — for complex multi-step jobs that can't fail)
	High


Real example: Print shop — orders via email → manual entry → job ticket → confirmation. n8n + LLM: parses email, creates ticket, sends confirmation, logs it.


________________


B2. Missing or Outdated SOPs
"No documented processes — everything depends on specific people."


Signals: "If [name] left we'd be screwed" · "Everyone does it differently" · "Training takes months"


Approach
	How to Build It
	Complexity
	AI SOP generation from screen activity
	Scribe (auto-generates step-by-step docs from clicks)
	Low
	Expert knowledge capture → docs
	Record with Granola → Claude processes transcript into structured SOP
	Low
	Living wiki with AI search
	Custom RAG over internal docs (LangGraph + pgvector) or Notion AI for quick wins
	Low-Med


________________


B3. Communication Breakdowns
"Info gets lost between people and departments."


Signals: "Sales and ops never on same page" · "Things buried in group texts" · "Hear about issues too late"


Approach
	How to Build It
	Complexity
	Event-driven alerts
	n8n watches triggers → pushes to Slack/Teams/SMS via Twilio
	Low-Med
	Shared real-time dashboards
	Supabase + Next.js, or Airtable views for quick wins
	Low-Med
	AI meeting summaries
	Granola/Otter → n8n posts summary + action items to Slack
	Low


________________


B4. Scheduling & Resource Allocation
"Double-booked, understaffed, or wasting capacity."


Signals: "Always slammed or dead" · "Scheduling takes 3 hrs/week" · "Wait times killing us"


Approach
	How to Build It
	Complexity
	Demand forecasting
	Custom ML on POS data + weather API + Google Trends + event data
	Med-High
	Smart scheduling
	Cal.com (open-source Calendly alternative) or custom booking system
	Low-Med
	Route optimization
	Google OR-Tools (free, programmable)
	Med


Real example: Car wash, 700+ daily. ML forecast (POS + weather + events) predicts within 10%. Labor waste down 20%.


________________


C. CUSTOMER & REVENUE PROBLEMS
C1. Lead Gen & Sales Pipeline
"Not enough leads, or leads fall through cracks."


Signals: "Mostly word-of-mouth" · "Follow up when I remember" · "Half inquiries go cold"


Approach
	How to Build It
	Complexity
	Lead enrichment + scoring
	Clay (100+ data sources, AI scoring) or custom: Exa.ai + Firecrawl + LLM enrichment via n8n
	Med
	Automated outreach
	Instantly or Smartlead (built for cold email deliverability at scale)
	Low-Med
	Prospecting / contact finding
	Apollo.io (free: 1,200 credits/yr) or Exa Websets for semantic company/people search
	Low-Med
	Web intelligence pipeline
	Gumloop (programmable GTM workflows + scraping) or Firecrawl + n8n + LLM
	Med
	AI-native CRM
	Attio (conversational AI layer over your GTM data) or build custom with n8n + Supabase
	Med
	Website chatbot / lead capture
	Voiceflow, or custom with Claude API + embeddable widget
	Med


Real example: HVAC contractor — 40% inquiries went cold. n8n: form → SMS via Twilio → Cal.com link → 48-hr follow-up. Close rate up 25%.


________________


C2. Customer Service & Support
"Can't respond fast enough."


Signals: "Drowning in tickets" · "Same 10 questions" · "Can't afford 24/7"


Approach
	How to Build It
	Complexity
	AI FAQ chatbot (grounded)
	LangGraph RAG + their knowledge base → embeddable widget. Or eesel AI for managed version
	Med
	AI phone agent
	Retell AI (lowest latency, most natural — sub-second turns) or Vapi (full customization, bring your own models)
	Med
	AI draft responses
	LLM reads ticket + KB → drafts reply → human approves
	Med
	Production support agent
	Build with LangGraph + n8n + Vapi — multi-channel (chat + voice), grounded in their docs, full ownership
	High


Real example: Property management — same 15 tenant questions. Retell phone agent + RAG chatbot handles 70% autonomously.


________________


C3. Marketing & Content
"Need marketing but no bandwidth."


Signals: "Instagram died months ago" · "Need newsletter, no time" · "Website ancient"


Approach
	How to Build It
	Complexity
	AI text/strategy
	Claude (long-form + strategy), ChatGPT, Gemini — or custom pipeline with templates + LLM API
	Low
	AI images
	Midjourney, Ideogram 2.0, DALL-E 3, Canva AI (free edu)
	Low
	AI video
	Runway Gen-4, HeyGen (talking head), Veo 3 (Google), Kling 2.0, Pika
	Low-Med
	AI voice/audio
	ElevenLabs (production-grade TTS, voice cloning — used at Revolut-scale)
	Low-Med
	Email pipeline
	Resend (email API, free tier) + n8n + LLM content generation — own the whole stack
	Med
	Website builder
	v0.dev (Vercel AI site builder), Framer, or vibe-code with Cursor + Next.js
	Low-Med


________________


C4. Pricing, Quoting & Estimating
"Proposals take forever, probably undercharging."


Approach
	How to Build It
	Complexity
	AI proposal generation
	LLM + their templates + structured intake form → auto-generates 80% of proposal
	Med
	Historical pricing analysis
	Feed past job data into Claude → margin breakdown, pricing recs
	Med
	Quote automation
	Typeform/Tally intake → n8n → LLM applies pricing rules → generates quote
	Med


________________


D. FINANCIAL & ADMIN PROBLEMS
D1. Bookkeeping, Invoicing & AP
Approach
	How to Build It
	Complexity
	Invoice extraction
	Nanonets (API-first, high accuracy, free tier) or Claude Vision → structured JSON → accounting system
	Med
	Expense categorization
	LLM classifies transactions from bank CSV/API feed
	Med
	Cash flow forecasting
	Custom model on transaction history + seasonality
	Med-High
	Invoice chasing
	n8n monitors unpaid → auto-sends reminders → escalates
	Low-Med
	D2. HR, Hiring & Onboarding
Approach
	How to Build It
	Complexity
	AI job posts
	Claude + job spec → optimized posts for multiple channels
	Low
	Resume screening
	n8n intake → LLM scores against criteria → ranked shortlist. Or build custom RAG agent with LlamaIndex + embeddings on job descriptions
	Med
	Candidate sourcing
	Exa.ai (semantic people search) or Apollo.io
	Med
	AI phone screening
	Vapi or Retell — voice agent conducts initial screens, scores responses
	Med-High
	Onboarding docs
	Scribe/Loom recordings → LLM → structured training materials
	Low
	D3. Compliance, Reporting & Legal
Approach
	How to Build It
	Complexity
	AI contract review
	Claude (200K context) — upload, extract terms, flag risks
	Low-Med
	Compliance monitoring
	Feedly + RSS → n8n → LLM flags regulatory changes
	Med
	Report generation
	LLM + data + template → auto-generates reports
	Med
	Deadline tracking
	Supabase/Airtable + n8n alert pipeline
	Low


________________


E. STRATEGIC & INTELLIGENCE PROBLEMS
E1. Competitive Intelligence
Approach
	How to Build It
	Automated competitor monitoring
	Firecrawl scrapes competitor sites on schedule → LLM diffs changes → Slack/email alerts
	News digest
	Feedly + RSS → n8n → LLM summarization → daily/weekly digest
	Social listening
	Google Reviews API + Yelp API scraping → LLM sentiment + trend extraction
	Market research
	Exa.ai semantic search + Perplexity for deep research
	E2. Forecasting & Planning
Approach
	How to Build It
	Cash flow forecasting
	Python + scikit-learn on transaction history, or Claude for pattern analysis
	Demand forecasting
	ML on POS data + weather API + Google Trends + Meta ad data + event calendars
	Scenario modeling
	Python Monte Carlo, or spreadsheet + Claude for quick "what if." Build heuristics from THEIR data
	E3. Customer Understanding
Approach
	How to Build It
	Review analysis
	Google Reviews + Yelp API → LLM extracts themes, sentiment, actions
	Survey analysis
	Typeform/Tally → LLM clusters themes, generates summary
	Behavioral data
	Meta Business API + Google Analytics → LLM identifies segments, purchase drivers
	Interview → insights
	Granola/Otter → Claude extracts themes, quotes, action items


________________


What AI Can and Can't Do — Nuanced Version
AI CAN make decisions — sometimes better than humans. In supply chain modeling, an AI with historical demand, weather, logistics, and real-time inventory data makes more accurate allocation decisions than a human with a spreadsheet. The key: data access + problem structure. If definable and data exists, AI often wins. Where it falls short: ambiguous, relationship-dependent, or novel-context decisions.


AI doesn't always hallucinate — you control when it does. LLMs are probabilistic. But for specific answers (price, inventory count, customer record), the AI should make a tool call to a deterministic system (database, API, calculator). Most production AI is a hybrid of both. See Doc 5 for the full deterministic vs. probabilistic breakdown.


Data quality matters enormously. Fix data collection before automating decisions on it.


Automating a broken process breaks it faster. Fix the process, then automate.


Every system needs oversight. Business conditions change, edge cases emerge.


AI can't replace relationships. AI drafts the email. Can't build the trust.


________________


Key Concepts (Quick Reference)
Deterministic vs. Probabilistic — Full explanation in Doc 2's concepts section and Doc 5.


What is an Agent — LLM + ruleset + tools = a loop. Add reasoning = handles novel situations. Full explanation in Doc 5.


Local vs. Cloud — Where does processing happen? Matters for sensitive data. Full breakdown in Doc 5.


Behavioral Data Sources — Meta APIs, TikTok APIs, Google Ads/Analytics, POS data, review APIs, weather APIs, Google Trends. Most small businesses massively underestimate the data available to them.


________________


Next Steps After Mapping
1. Rank by impact × feasibility
2. Doc 4 — What's free with student access?
3. Doc 3 — AI capability deep dive
4. Doc 5 — Web dev, infrastructure, deployment, agents, deterministic vs. probabilistic
5. Draft a one-pager for the business owner


________________




G1000 — Babson College, Spring 2026 The Generator Lead Team: Spencer, Joshua, Rustin, Cole, Reece


Doc 3: Types of AI
TYPES OF AI
Canva Link
Technology Capabilities: "What can AI actually do?"
________________




How to use this doc: You've identified pain points (Doc 1) and mapped them to solvable categories (Doc 2). Now you're here to understand the technology deeply enough to scope and build. This is your engineering reference.


This doc covers THE HOW. Part 1 (Business Problems) lives in Doc 2. The split is intentional — you shouldn't be reading tech specs during discovery. Look here when ideating on a solution. What tech is right for the problem and its data?


DISCOVERY (Doc 1)          →  MAPPING (Doc 2)           →  IMPLEMENTATION (Doc 3)


"What hurts?"              →  "What's solvable?"        →  "What do we build?"


Listen + match categories  →  Problem → tool options     →  Tech details + watch-outs


________________


1) CREATE — Generative AI
AI that makes new things: text, code, images, video, audio.
1a. Generative Text
What it does: Turns instructions + context into drafts, edits, structured writing.


How it works: LLMs predict next words given prompt + context. Quality depends on prompt specificity, context, and human review.


Business uses: Marketing copy · SOPs/memos · support drafts · proposals · job posts · reports.


Rule of thumb: Use when the work product is words and humans currently draft + revise.


Tools: Claude (best for long-form + strategy), ChatGPT, Gemini. For API pipelines: build custom with any model + templates via n8n or LangGraph.


Maps to: B2, C3, C4, D2, D3, E1.


________________


1b. Generative Code
What it does: Drafts code, tests, refactors, explains bugs, generates scripts/SQL.


How it works: LLMs tuned on code. Best when human can verify quickly (tests pass, output runs).


Business uses: Software delivery · analytics (SQL/Python, dashboards) · IT scripting · custom tools (vibe coding).


Rule of thumb: Best when a human can verify quickly.


Tools (the real 2026 stack):


* Cursor — AI code editor with Claude/GPT integration. The default for most builders. Student Pro free.
* Claude Code — Terminal-based agent: runs shell commands, edits files, runs tests, commits. True multi-step reasoning. Unbeaten for complex refactors/architecture.
* Continue.dev — Open-source VS Code/JetBrains extension. Any model, local or cloud. Fully free/self-hostable.
* Windsurf (Google) — Agent-style editor with autonomous multi-file workflows. Strong for Google Cloud stacks.
* GitHub Copilot — Free for students. Best for inline autocomplete.
* Antigravity - Googles code editor (Model agnostic)


Common stack on X: Cursor + Claude Code combo.


Maps to: A2, A3, B1, C3.


________________


1c. Generative Images
What it does: Produces/edits images — product shots, concepts, ad variants.


Rule of thumb: Volume + speed over perfect-on-first-try.


Tools: Midjourney (quality), Ideogram 2.0 (text-in-image + versatility), DALL-E 3, Canva AI (free edu).


Maps to: C3.


________________


1d. Generative Video
What it does: Creates/transforms video clips — ads, storyboards, training, localization.


Rule of thumb: Concepting + iteration, then graduate winners to high production.


Tools: Runway Gen-4, Krea, Higgsfield HeyGen (talking head avatars), Veo 3 (Google — text-to-video), Kling 2.0 (motion/VFX), Pika.


Maps to: C3, D2.


________________


1e. Generative Audio / Voice
What it does: Text-to-speech, voiceovers, voice cloning, conversational voice agents.


Rule of thumb: Use where voice is a delivery channel, not core differentiation.


Tools:


* ElevenLabs — Production-grade TTS + voice cloning. Used at Revolut-scale. The clear leader.
* Amazon Polly, Azure Speech, PlayHT for lighter use cases.


Maps to: C2, C3.


________________


CREATE Watch-Outs:
Hallucinations · IP/copyright risk · brand voice inconsistency · approval workflows needed. Always human review loop for published content. Use tool calls (see 6d) for factual accuracy — don't rely on the LLM to "know" specific numbers or facts.


________________


2) PREDICT — Predictive AI / ML
AI that estimates what happens next.
2a. Forecasting (time-based)
What it does: Forecasts demand, revenue, staffing, inventory, cash.


How it works: ML models find patterns in historical time-series + external signals (season, weather, events) → project forward.


Rule of thumb: Use when yesterday's patterns help estimate tomorrow.


Tools: Python + scikit-learn / Prophet for custom models. Amazon Forecast, Vertex AI Forecasting for managed. Claude/GPT for quick pattern analysis on smaller datasets.


Maps to: B4, C4, D1, E2.


________________


2b. Scoring / Propensity
What it does: Outputs probability/score — churn risk, lead quality, fraud risk.


How it works: Classification models trained on historical outcomes score new inputs.


Rule of thumb: "Who/what should we prioritize?"


Tools: Build custom with scikit-learn or LLM-based scoring pipelines. Clay has built-in AI scoring for GTM. For managed: Azure ML.


Maps to: C1, D2.


________________


2c. Anomaly Detection
What it does: Flags "this looks unusual" — often real-time.


How it works: Learns normal patterns, alerts on significant deviation.


Rule of thumb: Rare, costly events > average performance.


Tools: Custom models (Isolation Forest, autoencoder) or Langfuse for AI system monitoring specifically.


Maps to: D1, D3.


________________


3) SEE & HEAR — Perception AI
AI that understands docs, images, video, audio.
3a. Document AI (OCR + Extraction)
What it does: Pulls structured data from PDFs/images/forms — fields, tables, line items.


How it works: OCR → text, then AI extracts specific fields into usable format.


Rule of thumb: Use when humans are retyping from documents.


Tools:


* Nanonets — API-first IDP (invoices, contracts, forms). High accuracy, developer-friendly, free tier.
* Unstructured.io + LlamaParse — Open-source parsing for messy PDFs/tables/images. Self-hostable.
* Claude Vision / GPT-4o Vision — Send image, get structured JSON. Best for quick extraction without a pipeline.
* Amazon Textract, Google Document AI for cloud-managed.


Maps to: A4, D1.


________________


3b. Computer Vision (images)
What it does: Detects objects/defects, counts items, classifies images.


Business uses: Manufacturing QA · safety compliance (PPE) · asset monitoring · photo classification.


Rule of thumb: When you can define "good vs. bad" visually.


Tools: Claude Vision, GPT-4o Vision (multimodal models handle most cases now). AWS Rekognition, Azure AI Vision for specialized.


Maps to: A4.


________________


3c. Video Understanding
What it does: Indexes video, detects events, moderation, search.


Rule of thumb: Video volume too large for human review.


Tools: Google Video Intelligence, Azure Video Indexer. Gemini 2.0 Flash handles basic video understanding.


________________


3d. Speech-to-Text + Call Analytics
What it does: Transcribes speech, extracts intent/sentiment/topics.


How it works: Audio → text via speech recognition, then NLP/LLM tags speakers, themes.


Business uses: Meeting notes · call QA · voice-of-customer insights.


Rule of thumb: Valuable info trapped in calls/meetings.


Tools:


* Whisper (OpenAI) — Open-source, run locally, free. The default for builders.
* Granola — AI meeting notes with context. Great UX.
* Otter.ai, Fireflies — Managed transcription services.
* ElevenLabs — Also does high-quality STT now.


Maps to: A4, B2, B3, E3.


________________


4) CHOOSE — Decision AI
AI that recommends, optimizes, prescribes.
4a. Recommendations & Personalization
What it does: Ranks/suggests next best item/action per user.


Business uses: E-commerce recs · content feeds · next-best-action (upsell, retention).


Rule of thumb: Many options, need contextual ranking per user.


Tools: Build custom with embeddings + similarity scoring. Amazon Personalize for managed.


________________


4b. Optimization (math-based)
What it does: Picks best plan given constraints (cost, time, capacity).


How it works: Operations research — solves for optimal within defined constraints. Not ML.


Business uses: Scheduling · routing/logistics · pricing/allocation.


Rule of thumb: "Better decisions" = solving tradeoffs.


Tools: Google OR-Tools (free, programmable), Gurobi, OptimoRoute.


Maps to: B4.


________________


4c. Prescriptive Analytics
What it does: Forecasts AND recommends actions to improve outcomes.


Business uses: Inventory allocation · revenue management · maintenance planning.


Rule of thumb: "What should we do next?" not just "what will happen?"


Maps to: E2.


________________


5) DO — Automation, Copilots, Agents
AI that takes action.
5a. Workflow Automation
What it does: Moves data + triggers actions across systems. Rules-based + AI-enhanced.


How it works: Trigger (new form, email, row) → actions (create ticket, send message, update CRM, generate doc).


Business uses: Approvals/routing · back-office (invoice → extract → post → archive) · handoffs (lead → CRM → notify → task).


Rule of thumb: Work is repeatable, "done" = updating systems.


Tools:


* n8n — Self-hosted, free, programmable, built-in AI agent nodes + LangChain integration. The default for builders. "Easiest path to production agents" in 2026.
* Windmill — Code-first automation (scripts + flows in one UI). Tighter than n8n for complex internal tools. Open-source.
* Temporal — Durable workflow engine for complex multi-step jobs that can't fail. Used by Netflix/Uber/Stripe teams.


Maps to: A3, B1, B3, C1, D1, D3.


________________


5b. Copilots (human-in-the-loop)
What it does: AI inside tools you already use — drafts, searches, summarizes. Human decides.


Business uses: Doc/email drafting · meeting/inbox summaries · Q&A over internal knowledge.


Rule of thumb: Humans own decisions, want faster throughput.


Tools: Microsoft Copilot (Babson has it), Claude, Notion AI, Cursor (for code).


Maps to: A1, C2.


________________


5c. Agents (goal-driven, multi-step)
What it does: Plans steps, calls tools/APIs, executes with guardrails. Decides what to do next.


How it works: Goal + limited toolbox → loop: plan → call tool → read result → next step. Approvals for risky actions.


Business uses: Support agents (resolve routine end-to-end) · IT ops (triage, reset, route) · sales assist (research → draft → log → schedule).


Rule of thumb: Only agent-ify well-instrumented processes (logs, permissions, rollback).


Tools:


* LangGraph (LangChain team) — Agentic/multi-step workflows. The standard for production agents.
* LlamaIndex agents — Better for data-heavy agent workflows with advanced indexing.
* Dify — Open-source end-to-end platform (visual + code). Quick prototyping.
* n8n AI agent nodes — For workflow-style agents that connect systems.
* Voiceflow — No-code agent builder for chat/voice.


Watch-outs: Permissioning, tool access scope, data leakage. Many agentic projects fail without clear value/risk controls. Start narrow.


Maps to: C1, C2.


________________


6) CONNECT — Building Blocks & Infrastructure
The plumbing that makes everything else work.
6a. RAG (Retrieval-Augmented Generation)
What it is: AI answers questions using your docs instead of guessing.


How it works: Index knowledge by meaning → fetch relevant passages → model writes answer from those passages.


When to use: Right answer lives in company materials (and changes over time). Hallucinations costly.


Tools (the 2026 RAG stack):


* LangGraph — For agentic RAG (multi-step retrieval, re-ranking, self-correction).
* LlamaIndex — Clean data pipelines + advanced indexing strategies.
* Haystack — Production-grade with strong evaluation built in.
* Dify / UltraRAG — Open-source end-to-end platforms.
* Simple: Claude Projects, Custom GPTs (upload docs, instant RAG).
* Vector stores: pgvector via Supabase/Neon (the 2026 default), or Qdrant/Weaviate when you outgrow pgvector.


Maps to: A1, B2, C2.


________________


6b. Web Scraping & Intelligence
What it is: Extract structured data from websites when no API exists.


How it works: Program visits pages → reads structure → pulls fields → saves as table.


When to use: Data is public but not packaged.


Tools:


* Firecrawl — Search + extract in one API call. LLM-ready output. Open-source. Generous free tier.
* Exa.ai — Semantic web search API (embeddings-based, not keyword). Great for research/monitoring. Websets feature for discovering people/companies.
* Playwright — Browser automation for dynamic sites. Free.
* Apify — Managed scraping platform.
* Gumloop — Programmable GTM workflows + scraping. No-code but powerful.


Maps to: C1, E1.


________________


6c. Extraction (structured output from messy input)
What it is: AI converts unstructured inputs (emails, PDFs, calls) into clean fields.


How it works: Model reads content → outputs predefined schema (JSON). Downstream systems trust format.


When to use: Business value depends on fields being correct.


Tools:


* Nanonets — API-first, production-grade, free tier.
* Unstructured.io + LlamaParse — Open-source, self-hostable.
* Claude/GPT structured output mode (JSON mode) for custom extraction.


Examples:


* Email → {name, company, intent, urgency} → CRM
* Invoice → {vendor, amount, date} → AP
* Contract → {renewal, terms, obligations} → tracker


Maps to: A4, D1, D3, E3.


________________


6d. Tool Calling
What it is: Structured way for AI to request actions while your app stays in control.


How it works: Define allowed tools → model outputs structured "tool call" → your system executes → model uses result.


When to use: AI needs to interact with real systems (CRM, POS, support desk). Need audit trail.


This is how you solve hallucinations for factual queries. Instead of the LLM guessing, it calls a database/API for the exact answer. See Doc 5 for the full deterministic vs. probabilistic breakdown.


Tools: All major models support tool calling natively. LangGraph/LlamaIndex manage complex tool orchestration.


________________


6e. APIs & Integrations
What it is: Contracts that let systems talk. REST (most common), GraphQL (flexible), WebSockets (real-time).


Why it matters: Most AI solutions connect to existing systems. If you can't plug into their POS/CRM/accounting, the solution doesn't work.


________________


6f. Databases
Relational (SQL): Structured data with relationships. Postgres is the default for everything in 2026.


* Supabase — Postgres + pgvector + auth + storage + edge functions. One-click everything. The prototyping winner.
* Neon — Serverless Postgres with pgvector. Branching (create instant DB copies for dev) is magic.


NoSQL: Flexible schemas, scale. MongoDB (docs), Redis (cache), Elasticsearch (search).


Vector: Embeddings for semantic search — backbone of RAG.


* pgvector (via Supabase/Neon) — Good enough for most projects. Keeps everything in one DB.
* Qdrant / Weaviate — Dedicated vector DBs when you outgrow pgvector at scale.


Real-time: Convex — Real-time backend loved by indie builders. Great for collaborative apps.


________________


6g. Web Dev Stack (for vibe-coders building custom tools)
Front end: HTML + CSS + JS. Frameworks: React, Next.js, Vue.


Back end: APIs, business rules, auth, integrations, background jobs.


* Supabase handles most backend needs out of the box.
* Vercel for deployment (pairs with Next.js).
* Railway for custom backends.


DevOps: Hosting (Vercel, Railway, AWS), deployment (CI/CD via GitHub Actions), monitoring.


Flow: User clicks → front end → API → back end rules → database → response → screen update.


________________


6h. Monitoring, Eval & Observability
What it is: Track your AI system's performance, catch regressions, control costs.


Why it matters from day one: Without observability, you're flying blind. You won't know if your RAG is returning wrong answers, your agent is taking unnecessary steps, or your costs are spiking.


Tools:


* Langfuse — Open-source tracing, evals, cost tracking. OTel standard. The default for most builders.
* Helicone — Drop-in proxy for OpenAI/Anthropic. Lightweight cost optimization + monitoring.
* LangSmith — If you're all-in on LangChain/LangGraph.
* Arize Phoenix — Strong open-source evals + tracing.


Start with: Langfuse + Helicone — both free/self-hostable and what most builders actually run in production.


________________


Cross-Reference: Problem → Tech Capability
Problem Category
	Primary Tech Capabilities
	A1 Data Access
	RAG (6a), Copilots (5b)
	A2 Tracking Gaps
	Databases (6f), Gen Code (1b)
	A3 Legacy Lock-in
	Automation (5a), APIs (6e)
	A4 Unstructured Data
	Document AI (3a), Extraction (6c), Computer Vision (3b)
	B1 Manual Tasks
	Automation (5a), Gen Code (1b)
	B2 Missing SOPs
	Gen Text (1a), Speech-to-Text (3d), RAG (6a)
	B3 Communication
	Automation (5a), Speech-to-Text (3d)
	B4 Scheduling
	Forecasting (2a), Optimization (4b)
	C1 Pipeline
	Automation (5a), Scoring (2b), Agents (5c), Scraping (6b)
	C2 Service
	Agents (5c), RAG (6a), Gen Voice (1e)
	C3 Content
	Gen Text (1a), Gen Images (1c), Gen Video (1d), Gen Voice (1e)
	C4 Pricing
	Gen Text (1a), Extraction (6c), Forecasting (2a)
	D1 Finance
	Document AI (3a), Automation (5a), Extraction (6c)
	D2 HR
	Gen Text (1a), Scoring (2b), Gen Voice (1e)
	D3 Compliance
	Extraction (6c), Automation (5a)
	E1–E3 Strategic Intel
	Forecasting (2a), Scraping (6b), Extraction (6c)


________________


How to Use This Document
1. Come here from Doc 2 after you've identified the problem category and approach
2. Read the relevant tech section to understand what's happening under the hood
3. Note the tools — check Doc 4 for which ones are free with student access
4. Pay attention to watch-outs — these are where projects fail
5. Go to Doc 5 for how to actually build and deploy — front end, back end, databases, plus deep dives on RAG, agents, tool calling, and key concepts
6. Add to it — new tool, pattern, or insight? This is a living document


________________


Quick Concept Reference
Deterministic vs. Probabilistic: LLMs are probabilistic (different outputs possible). Databases/APIs are deterministic (same answer every time). Good AI design uses both — LLM for reasoning, tool calls for exact answers. See Doc 5 for full explanation.


What is an Agent: An LLM + a ruleset + access to tools. It's a loop (receive → decide → call tool → read result → repeat). Add reasoning and it handles novel situations. See Doc 5 for full explanation.


Local vs. Cloud: Cloud = faster to prototype, free tiers. Local = data never leaves their network. Matters for sensitive data. See Doc 5 for full explanation.


________________




G1000 AI Bible v2.0 — Babson College, Spring 2026 Built by the Generator Lead Team: Spencer, Joshua, Rustin, Cole, Reece


Doc 4: Free Tools
G1000 Free Tools & Access Guide
Everything you can use for $0 as a Babson student — updated Feb 17, 2026
________________




Why this doc exists: You don't need to spend money to build real AI solutions. Between student benefits, free tiers, open-source, and Babson's institutional access, you have hundreds of dollars worth of tools available right now.


________________


🏫 BABSON-SPECIFIC ACCESS
Azure AI (Through Babson's Microsoft Partnership)
Microsoft 365 Copilot — All Babson students have Copilot licenses. GPT-powered AI inside Word, Excel, PowerPoint, Outlook, Teams. Data stays within Babson's secure instance.


Azure OpenAI Service — Through Azure AI Foundry, create custom copilots using GPT, DALL-E, and Whisper models. Enterprise-grade with Microsoft's security layer.


Azure AI Grants — Babson's Metropoulos Institute provides $1,000 Azure credit grants for student AI projects. Apply at foundry.babson.edu/azure-ai-grants.


Claude Models via Azure — Claude models (Sonnet 4.5, Haiku 4.5, Opus 4.1, Opus 4.6) are available in Azure AI Foundry. Important caveat: Claude is a third-party marketplace item — Azure credits may NOT cover it. Confirm with Babson IT before using. For direct Claude usage, the free tier at claude.ai is your safest bet.


How to get started:


1. Sign in to portal.azure.com with Babson credentials
2. Navigate to Azure AI Foundry (ai.azure.com)
3. For grants, apply at foundry.babson.edu/azure-ai-grants
4. Copilot should already be in your M365 apps
5. Questions → metropoulousinstitute@babson.edu


________________


🤖 FREE FRONTIER AI MODELS
Tier 1: Best Free Chat Interfaces
Model
	Free Access
	What You Get
	Link
	Claude (Anthropic)
	Free tier
	Sonnet 4.5, message limits, resets every few hours
	claude.ai
	ChatGPT (OpenAI)
	Free tier
	GPT-4o with limits
	chatgpt.com
	Gemini (Google)
	Free
	Gemini 2.0 Flash, 1M token context
	gemini.google.com
	DeepSeek
	Free, unlimited
	V3 + R1 reasoning
	chat.deepseek.com
	Perplexity
	Free tier
	AI search with citations
	perplexity.ai


⚠️ DeepSeek: Servers in China. Prompts may be used for training, no opt-out. Don't enter sensitive/client data.
Tier 2: Free API Access (for building)
Platform
	Key Models
	How to Get It
	NVIDIA NIM
	Kimi K2.5 (1T params), Nemotron, GLM-5, Llama, Mistral, dozens more
	build.nvidia.com → free account
	OpenRouter
	DeepSeek V3/R1, Llama, Qwen, open models
	openrouter.ai — no credit card
	Google AI Studio
	Gemini 2.0 Flash, Gemini Pro
	aistudio.google.com
	Anthropic API
	Claude Sonnet, Haiku
	console.anthropic.com — free credits
	Groq
	Llama, Mixtral (blazing fast inference)
	console.groq.com
	Together AI
	Open models
	api.together.ai — $5 free credits
	🔥 Kimi K2.5 on NVIDIA — Big Free Opportunity
1T parameter multimodal model by Moonshot AI. Rivals GPT-5.2 and Claude on benchmarks. NVIDIA currently offers free API access with no visible rate limits.


Setup: build.nvidia.com → account → verify phone → search "Kimi K2.5" → "View Code" → API key auto-generates → OpenAI-compatible endpoint: https://integrate.api.nvidia.com/v1 → Model ID: moonshotai/kimi-k2-instruct


Features: 262K context, multimodal (text + images + video), reasoning mode, Agent Swarm capability.


________________


💻 BUILDER TOOLS (Free / Open-Source / Student)
AI-Powered Development
Tool
	What It Is
	Free Access
	Cursor
	AI code editor (Claude/GPT). The default for builders
	Student Pro free — cursor.com
	Claude Code
	Terminal-based code agent. Multi-step reasoning, shell commands, file edits
	Via Claude API (pay-per-use) or Claude.ai plans
	Continue.dev
	Open-source VS Code/JetBrains extension. Any model, local or cloud. Zero vendor lock-in
	100% free/self-hostable — continue.dev
	GitHub Copilot
	AI code completion. Best for inline autocomplete
	Free for students — education.github.com
	Windsurf (Google)
	Agent-style editor with autonomous multi-file workflows
	Limited free; Google Cloud credits help


Common 2026 stack: Cursor + Claude Code combo.
Automation & Workflow
Tool
	What It Is
	Free Access
	n8n
	Self-hosted workflow engine. Native AI agent nodes, LangChain integration. The default
	Free self-hosted forever — n8n.io
	Windmill
	Code-first automation (scripts + flows in one UI). Tighter than n8n for complex internal tools
	Open-source/self-host free
	Temporal
	Durable workflow engine for complex jobs that can't fail
	Open-source; free self-hosted
	RAG & Agent Frameworks
Tool
	What It Is
	Free Access
	LangGraph (LangChain)
	Agentic/multi-step RAG and workflows. The 2026 standard for production agents
	Open-source, free
	LlamaIndex
	Data pipelines + advanced indexing. Best for data-heavy agent workflows
	Open-source, free
	Haystack
	Production-grade RAG with built-in evaluation
	Open-source, free
	Dify
	End-to-end RAG/agent platform (visual + code). Fast prototyping
	Open-source, free tier
	RAGFLOW
	SOTA. works great with AWS S3 buckets
	Open source SOTA.
	Databases & Backend
Tool
	What It Is
	Free Access
	Supabase
	Postgres + pgvector + auth + storage + edge functions. The prototyping winner
	Generous free tier — supabase.com
	Neon
	Serverless Postgres with pgvector. DB branching for dev
	Free tier
	Convex
	Real-time backend. Great for collaborative apps
	Free tier
	Qdrant
	Dedicated vector DB when you outgrow pgvector
	Free tier + open-source
	AI Monitoring & Observability
Tool
	What It Is
	Free Access
	Langfuse
	Open-source tracing, evals, cost tracking (OTel standard)
	Free/self-hostable — langfuse.com
	Helicone
	Drop-in proxy for OpenAI/Anthropic. Cost optimization + monitoring
	Free tier — helicone.ai


Start with both from day one. You'll thank yourself later.
Voice & Phone Agents
Tool
	What It Is
	Free Access
	Vapi
	Developer-first voice agent platform. Bring your own LLM/TTS/STT
	Free tier + usage-based — vapi.ai
	Retell AI
	Lowest-latency phone agents. Sub-second turns, most natural
	$10 free credit — retellai.com
	ElevenLabs
	Production-grade TTS + voice cloning
	Free tier — elevenlabs.io
	Web Scraping & Intelligence
Tool
	What It Is
	Free Access
	Firecrawl
	Search + extract in one API call. LLM-ready output
	Generous free tier, open-source — firecrawl.dev
	Exa.ai
	Semantic web search API (embeddings-based). Websets for people/company discovery
	Usage-based with free tier — exa.ai
	Playwright
	Browser automation for dynamic sites
	Fully free, open-source
	Document Processing
Tool
	What It Is
	Free Access
	Nanonets
	API-first IDP — invoices, contracts, forms. High accuracy
	Free tier — nanonets.com
	Unstructured.io
	Open-source parsing for messy PDFs/tables/images
	Free, self-hostable
	LlamaParse
	PDF/doc parser optimized for LLM consumption
	Free tier via LlamaIndex
	CRM & GTM
Tool
	What It Is
	Free Access
	Attio
	AI-native CRM. Auto-builds from emails/calls. "Ask Attio" conversational layer
	Free tier for small teams — attio.com
	Apollo.io
	Prospecting + contact finding
	Free: 1,200 credits/yr — apollo.io
	Clay
	Data orchestration + enrichment + AI scoring
	Free trial; starts ~$149/mo
	Scheduling
Tool
	What It Is
	Free Access
	Cal.com
	Open-source Calendly alternative
	Free self-hosted or hosted free tier — cal.com


________________


📚 STUDENT DEVELOPER ESSENTIALS
The Big Bundle
| GitHub Student Developer Pack | THE mega-bundle — Copilot + domains + credits + 50+ tools | education.github.com/pack |
Cloud Credits
Service
	What You Get
	Microsoft Azure
	$100 credits + Babson grants up to $1,000
	Google Cloud
	Student credits
	AWS Educate
	Free credits + labs
	DigitalOcean
	$200 credits (via GitHub Pack)
	Vercel
	Pro features for students
	Railway
	Student discount
	Design & Creative
Tool
	Free Access
	Figma
	Education plan — figma.com/education
	Canva
	Full Pro features — canva.com/education
	Blender
	Always free for everyone
	Productivity
Tool
	Free Access
	Notion
	Education plan (Personal Pro)
	Microsoft 365
	Full suite through Babson
	Linear
	Free student plan
	Airtable
	Free education workspace
	Developer Tools
Tool
	Free Access
	JetBrains IDEs
	All IDEs free (IntelliJ, PyCharm, WebStorm)
	Postman
	Student Expert program
	Namecheap
	Free .me domain + SSL (via GitHub Pack)
	KAGGLE
	Endless datasets. Public.
	________________


🛠️ RECOMMENDED STACKS
Tonight (30 min)
1. Claude free tier — claude.ai
2. ChatGPT free tier — chatgpt.com (we assume most of you pay for one of chatgpt or claude already).
3. GitHub Student Pack — education.github.com/pack (unlocks Copilot + dozens of tools)
4. NVIDIA NIM account — build.nvidia.com (free frontier model APIs)
This Week (Builder Stack)
All of the above, plus: 5. Cursor — cursor.com (claim student Pro) 6. Supabase — supabase.com (free Postgres + vector + auth) 7. n8n — n8n.io (self-host or cloud free trial) 8. Vercel — vercel.com (deploy web apps) 9. Notion — notion.so (project docs)
Advanced (Serious Builders)
All of the above, plus: 10. Langfuse — langfuse.com (AI monitoring from day one) 11. LangGraph — via LangChain (agent orchestration) 12. Firecrawl — firecrawl.dev (web scraping API) 13. OpenRouter — openrouter.ai (route between free models) 14. Cal.com — cal.com (scheduling for client-facing tools)


________________


⚠️ Important Notes
Free tiers change. NVIDIA NIM's free access has no announced end date, but free APIs can disappear. Set up accounts now.


Don't put client data in free-tier AI tools. Free tiers may use inputs for training. For real client work, use Babson's Azure instance or paid tiers with data retention controls.


Azure billing: Third-party marketplace items (including Claude on Azure) may not be covered by grants. Stick to Azure OpenAI (GPT models) for grant-funded work.


GitHub Student Pack is the single highest-value thing. If you do nothing else, sign up for this.


Langfuse from day one. Most teams wish they'd started monitoring earlier. It's free. Just do it.


________________




G1000 — Babson College, Spring 2026 The Generator Lead Team: Spencer, Joshua, Rustin, Cole, Reece Last updated: February 17, 2026


Doc 5: Web Dev (rustin's web dev)


Doc 6: Expanded TOOLBOX
G1000 SOTA AI Tool Guide
February 2026 | The Generator | Babson College
State-of-the-art tools for AI-enabled small business solutions Prioritized by real builder discourse, open-source accessibility, and student prototyping speed


________________




How to use this doc: After a discovery call, find the category that matches your client's pain point and pick the best tool or approach. This guide favors tools you build with over platforms you subscribe to. Everything listed has active, positive discourse from builders on X/Twitter — not just marketing pages. Free/student tiers are flagged.


What's NOT here: Legacy SaaS disguised as AI, outdated model references, expensive enterprise-only platforms, no-code tools when better programmable alternatives exist, LinkedIn AI, generic job board features, or any platform's bolted-on AI marketing.


Lead Team: Spencer, Joshua, Rustin, Cole, Reece


________________


1. AI-Powered Development & Coding
Beyond Cursor and Copilot — what builders are actually shipping with.


Tool
	What It Does
	Access
	Link
	Claude Code
	Terminal agent that reasons, edits files, runs tests, and commits. Deep multi-step reasoning + 200k context.
	Pay-per-use; student credits
	claude.ai/code
	Cursor
	Full AI-native IDE with Composer + agent mode. Best multi-file editing + inline workflow.
	Free tier available
	cursor.com
	Continue.dev[a]
	Open-source VS Code/JetBrains extension. Any model, local or cloud. Zero vendor lock-in.
	🟢 Free / self-hostable
	continue.dev
	claude-task-master
	AI-powered task management system you drop into Cursor, Windsurf, etc. Structures complex projects.
	🟢 Free / open-source
	github.com/eyaltoledano
	compound-engineering
	Official Claude Code compound engineering plugin for multi-agent dev workflows.
	🟢 Free / open-source
	github.com/EveryInc
	context-engineering-intro
	Context engineering framework for making AI coding assistants actually work. Claude Code centered.
	🟢 Free / open-source
	github.com/coleam00


Builder consensus: Claude Code + Cursor + MCP skills is the most common daily stack on X. For task management, claude-task-master or ai-dev-tasks.


________________


2. MCP Servers & Agent Tooling
Model Context Protocol is the standard way agents discover and call tools in 2026.


Tool
	What It Does
	Access
	Link
	MCP Servers (official)
	Canonical MCP server implementations. TypeScript. Connect agents to GitHub, Slack, databases, etc.
	🟢 Free / open-source
	github.com/modelcontextprotocol/servers
	golf-mcp
	Production-ready MCP server framework with auth, observability, debugger, telemetry.
	🟢 Free / open-source
	github.com/golf-mcp/golf
	Granola MCP
	Connect Granola.ai meeting data to Claude Desktop for AI-powered meeting intelligence.
	🟢 Free / open-source
	github.com (multiple forks)
	snyk/agent-scan
	Security scanner for AI agents, MCP servers, and agent skills.
	🟢 Free / open-source
	github.com/snyk/agent-scan
	claude-code-mcp
	Let Claude Code develop its own MCP tools dynamically.
	🟢 Free / open-source
	github.com/willccbb
	Peekaboo
	macOS CLI + MCP server for AI agents to capture screenshots with optional visual QA.
	🟢 Free / open-source
	github.com/steipete/Peekaboo


Builder consensus: MCP is the new USB-C for agents. Build custom MCP servers for each client's tools. golf-mcp for production, official servers for quick prototypes.


________________


3. Automation & Workflow Orchestration
Programmable > no-code. What builders are using instead of Zapier/Make.


Tool
	What It Does
	Access
	Link
	n8n
	Self-hostable, code-first workflow engine with native AI agent + MCP nodes + LangChain integration.
	🟢 Free self-hosted forever
	n8n.io
	Temporal
	Durable execution engine for stateful, long-running agents. Never loses progress.
	🟢 Free / open-source
	temporal.io
	Windmill
	Code-first automation platform (scripts + flows in one UI). Tighter than n8n for complex internal tools.
	🟢 Free / open-source
	windmill.dev


Builder consensus: n8n for quick agent pipelines, Temporal for anything that can't fail. Most student projects should start with n8n.


________________


4. Computer Use & Desktop Agents
Autonomous agents that control mouse, keyboard, and screen — the hottest topic on X.


Tool
	What It Does
	Access
	Link
	OpenClaw / nanobot
	Open-source computer use agents. Full mouse/keyboard/screen control, run headless on VPS.
	🟢 Free / open-source
	github.com/HKUDS
	browser-use
	Dedicated browser automation agent — points, clicks, fills forms, extracts data.
	🟢 Free / open-source
	github.com/browser-use
	macOS-use
	Make Mac apps accessible for AI agents. Browser-use team.
	🟢 Free / open-source
	github.com/browser-use/macOS-use
	vibetest-use
	Automated QA testing using Browser-Use agents. MCP-native.
	🟢 Free / open-source
	github.com/browser-use/vibetest-use
	zeroclaw
	Fast, small, fully autonomous AI assistant infrastructure. Deploy anywhere, swap anything. Rust.
	🟢 Free / open-source
	github.com/zeroclaw-labs


Builder consensus: Computer use agents are how you automate legacy systems with no API. Run on a $5/mo VPS or the client's machine.


________________


5. Data Collection & Screen Memory
Local, private data capture for SOP generation, behavior analysis, and always-on context.


Tool
	What It Does
	Access
	Link
	screenpipe
	24/7 local screen + audio + OCR recorder. Search everything you've done. All private.
	🟢 Free / open-source
	github.com/screenpipe
	Mem0
	Long-term vector memory for any model. Chrome extension + API.
	🟢 Free / open-source
	github.com/mem0ai
	MemoRAG
	Memory-enhanced RAG with data interface for all-purpose applications.
	🟢 Free / open-source
	github.com/qhjqhj00
	Autmoation-ai-lumin
	Screens behavior, auto-generates SOPs, then scripts to automate the SOP.
	🟢 Free / open-source
	github.com/mzc6101


Builder consensus: screenpipe + Claude for SOP generation is the fastest path to documenting a client's workflows automatically.


________________


6. Web Scraping & Data Enrichment
Structured data from the web. What replaced old Crayon/Klue.


Tool
	What It Does
	Access
	Link
	Firecrawl
	Turn any website into clean markdown or structured JSON. Schema support, deep search, async jobs.
	🟢 Free daily credits
	firecrawl.dev
	Exa.ai
	Semantic AI web search for company/people discovery and real-time research.
	Free tier (usage-based)
	exa.ai
	Clay
	Data orchestration + enrichment workflows from 100+ sources. AI scoring + personalized outreach.
	Starts ~$149/mo; trial
	clay.com
	Gumloop
	Programmable GTM workflows + scraping. Visual but code-extensible.
	Free tier
	gumloop.com


Builder consensus: Firecrawl + n8n + LLM enrichment is the composable stack most builders use. Clay for teams that need scale.


________________


7. Document AI & Extraction
OCR, PDF extraction, invoice processing, contract analysis. Better than Textract in 2026.


Tool
	What It Does
	Access
	Link
	Marker
	PDF to markdown + JSON with high accuracy on tables, images, scanned docs.
	🟢 Free / open-source
	github.com/datalab-to/marker
	VERT
	Next-gen file converter. Fully local, free forever.
	🟢 Free / open-source
	github.com/VERT-sh/VERT
	Kreuzberg / html-to-markdown
	Fast polyglot document intelligence engine with Rust core. HTML to markdown.
	🟢 Free / open-source
	github.com/kreuzberg-dev
	Docuseal
	Open-source DocuSign alternative. Create, fill, sign digital documents.
	🟢 Free / self-hostable
	docuseal.co
	Nanonets
	API-first intelligent document processing. Invoices, contracts, forms. High accuracy.
	Free tier + usage
	nanonets.com


Builder consensus: Marker + Claude Vision + structured output handles most SMB document needs. Docuseal replaces DocuSign for free.


________________


8. CRM & Sales Pipeline
AI-native, API-first. Not Salesforce. Not legacy HubSpot.


Tool
	What It Does
	Access
	Link
	Attio
	AI-native programmable CRM. Reasons over emails, calls, notes. "Ask Attio" conversational layer.
	Free tier for small teams
	attio.com
	Plane
	Open-source Jira/Linear/Monday alternative. Tasks, sprints, docs, triage.
	🟢 Free / open-source
	plane.so


Builder consensus: Attio for client-facing CRM. For project management, Plane is the open-source winner. Or build custom with Supabase + n8n.


________________


9. Lead Generation & Prospecting
Finding, enriching, and reaching leads. Composable stacks > single platforms.


Tool
	What It Does
	Access
	Link
	Clay
	100+ data sources, AI agents for scoring + personalized outreach at scale.
	Starts ~$149/mo; trial
	clay.com
	Exa Websets
	Semantic company/people search. Real-time research without stale databases.
	Free tier (usage-based)
	exa.ai
	Firecrawl
	Pair with n8n for custom enrichment pipelines. Research any company instantly.
	🟢 Free daily credits
	firecrawl.dev
	Apollo.io
	Contact database + outreach. 1,200 free credits/year.
	Free tier
	apollo.io


Builder consensus: n8n + Firecrawl + Exa + LLM enrichment is what most advanced teams build. Clay when you need scale fast.


________________


10. AI Voice & Phone Agents
Building AI phone agents, voice bots, IVR replacements.


Tool
	What It Does
	Access
	Link
	Retell AI
	Lowest-latency natural phone agents. Sub-second turns, real-time barge-in.
	Pay-per-minute; free credits
	retellai.com
	Vapi
	Developer-first platform. Bring your own LLM/TTS/STT + webhooks. Full custom logic.
	Free tier + usage
	vapi.ai
	Bland AI
	High-volume outbound with compliance tooling. Enterprise-grade scale.
	Pay-per-minute
	bland.ai


Builder consensus: Retell for quality, Vapi for customization, Bland for volume. All three consistently praised in X tests.


________________


11. Customer Support Automation
Chatbots, ticket routing, knowledge-grounded agents. Not old Zendesk.


Tool
	What It Does
	Access
	Link
	LangGraph + n8n
	Build multi-channel support agents grounded in client docs. Full ownership.
	🟢 Free / open-source
	langchain.com/langgraph
	eesel AI
	Knowledge-grounded agents that reduce tickets via self-serve + human handoff.
	Paid; free trial
	eesel.ai


Builder consensus: Build it yourself with LangGraph + n8n + Vapi for multi-channel (chat + voice). This is the dominant X pattern.


________________


12. Content & Marketing AI
What agencies and solo founders are actually using for text, image, video, social.


Tool
	What It Does
	Access
	Link
	Claude / ChatGPT
	Long-form strategy + content generation. Use via API for pipelines.
	Various plans
	claude.ai / openai.com
	ElevenLabs
	Production-grade TTS, voice cloning. Used at Revolut-scale deployments.
	Free tier
	elevenlabs.io
	Runway / Kling AI
	Text-to-video + editing. Fast iteration for social content.
	Free tiers available
	runwayml.com
	HeyGen / Synthesia
	Avatar video for training, onboarding, product demos.
	Free trials
	heygen.com
	Canva Magic Studio
	Fast visuals + video for non-designers.
	🟢 Free edu tier
	canva.com


Builder consensus: Build API pipelines in n8n calling these tools. Own the whole stack instead of paying per-seat.


________________


13. Bookkeeping & Financial AI
Invoice processing, categorization, cash flow. No breakout AI-native platform yet.


Tool
	What It Does
	Access
	Link
	Marker + Claude Vision
	Screenshot/scan invoices, extract to structured JSON, categorize via LLM.
	🟢 Free (open-source + API)
	github.com/datalab-to/marker
	Nanonets
	API-first invoice processing with high accuracy.
	Free tier
	nanonets.com
	n8n + LLM agents
	Custom categorization, cash flow forecasting, invoice chasing workflows.
	🟢 Free self-hosted
	n8n.io


Builder consensus: Composable stack: Marker for extraction + LLM for categorization + n8n for automation. Legacy tools still dominate; builders are replacing them piece by piece.


________________


14. Resume Screening & Hiring
No dominant AI-native platform on X yet. Custom RAG agents win.


Tool
	What It Does
	Access
	Link
	Custom RAG agent
	LlamaIndex + pgvector + embeddings on job descriptions. Private, tailored scoring.
	🟢 Free / open-source
	llamaindex.ai
	auto_rfp
	LlamaIndex-based automated RFP/resume processing pipeline.
	🟢 Free / open-source
	github.com/run-llama/auto_rfp
	Vapi / Retell
	Voice agent conducts initial phone screens, scores responses.
	Pay-per-minute
	vapi.ai / retellai.com


Builder consensus: Build it yourself with LlamaIndex/LangGraph + embeddings. No platform dominates builder Twitter yet.


________________


15. Scheduling & Resource Optimization
AI scheduling, demand forecasting, resource allocation for small businesses.


Tool
	What It Does
	Access
	Link
	Cal.com
	Open-source Calendly alternative with full API control.
	🟢 Free / open-source
	cal.com
	Custom LLM agents
	Claude + POS data + weather API + Google Trends for demand forecasting.
	API costs only
	Build with n8n/Temporal


Builder consensus: Cal.com for booking + custom LLM agents in n8n/Temporal for smart optimization.


________________


16. RAG & Knowledge Base Systems
Beyond basic LangChain. What builders are using for production knowledge systems.


Tool
	What It Does
	Access
	Link
	LangGraph
	Agentic, multi-step RAG workflows. The standard for production agents.
	🟢 Free / open-source
	langchain.com/langgraph
	LlamaIndex
	Clean data pipelines + advanced indexing for knowledge systems.
	🟢 Free / open-source
	llamaindex.ai
	Dify
	Open-source end-to-end RAG platform (visual + code).
	🟢 Free / open-source
	dify.ai
	MemoRAG
	Memory-enhanced RAG for persistent agent context.
	🟢 Free / open-source
	github.com/qhjqhj00


Builder consensus: pgvector on Supabase/Neon + LlamaIndex/LangGraph is the 2026 prototyping standard.


________________


17. Database & Backend Infrastructure
Fastest path from idea to deployed AI app.


Tool
	What It Does
	Access
	Link
	Supabase
	Postgres + pgvector + auth + storage + edge functions. One-click vector + everything.
	🟢 Free tier (generous)
	supabase.com
	Neon
	Serverless Postgres with pgvector. Branching is magic for dev.
	Free tier
	neon.tech
	Convex
	Real-time backend loved by indie builders on X.
	Free tier
	convex.dev
	ruvector
	Distributed vector DB that learns. Embeddings + Cypher + Raft consensus + GNN self-improvement.
	🟢 Free / open-source
	github.com/ruvnet


Builder consensus: Supabase is the default for student prototypes. Neon for branching, Convex for real-time apps.


________________


18. Monitoring, Eval & Observability
What you should set up from day one of any AI project.


Tool
	What It Does
	Access
	Link
	Langfuse
	Open-source tracing, evals, cost tracking. OTel standard. MCP support.
	🟢 Free / self-hostable
	langfuse.com
	Helicone
	Lightweight proxy for OpenAI/Anthropic. Drop-in cost optimization.
	Free tier
	helicone.ai
	ccusage
	CLI tool for analyzing Claude Code/Codex CLI usage from local JSONL files.
	🟢 Free / open-source
	github.com/ryoppippi/ccusage


Builder consensus: Start with Langfuse + Helicone. Free, self-hostable, and what most X builders actually run in production.


________________


19. Meeting Intelligence & Transcription
Turn discovery calls and client meetings into actionable agent data.


Tool
	What It Does
	Access
	Link
	Granola + MCP servers
	Pull meeting notes, search transcripts, auto-generate tasks. Multiple community MCP forks.
	🟢 Free / open-source MCPs
	github.com (search Granola MCP)
	Otter.ai
	Transcription + action items + follow-up agents.
	Free tier
	otter.ai
	Fathom
	Meeting summaries + follow-up agents.
	Free tier
	fathom.video
	Whisper (local)
	Free local transcription. Pair with LLM for extraction.
	🟢 Free / open-source
	github.com/openai/whisper


Builder consensus: Granola + MCP is the builder favorite for piping meeting context into Claude. Whisper for local/private.


________________


20. Multi-Agent Frameworks
Building agents that run entire workflows for small businesses.


Tool
	What It Does
	Access
	Link
	LangGraph + n8n
	Most practical for students. Visual + code. Agentic workflows with tool calling.
	🟢 Free / open-source
	langchain.com + n8n.io
	lemmy
	Lightweight wrapper around tool-using LLMs for agentic workflows.
	🟢 Free / open-source
	github.com/badlogic/lemmy
	model-hierarchy-skill
	Cost-optimized model routing based on task complexity.
	🟢 Free / open-source
	github.com/zscole
	Temporal
	Production durability when agents need to wait days for human input.
	🟢 Free / open-source
	temporal.io


Builder consensus: Build it yourself with LangGraph + n8n + MCP. This is genuinely better than any single platform.


________________


21. CLI & Developer Productivity
Terminal tools that power daily builder workflows.


Tool
	What It Does
	Access
	Link
	gogcli
	Google Suite CLI: Gmail, GCal, GDrive, GContacts from terminal.
	🟢 Free / open-source
	github.com/steipete/gogcli
	x-cli
	CLI for X/Twitter API v2. Post, search, like, bookmark from terminal.
	🟢 Free / open-source
	github.com/Infatoshi/x-cli
	ttyd
	Share your terminal over the web. Great for demos and pair programming.
	🟢 Free / open-source
	github.com/tsl0922/ttyd
	git-sim
	Visually simulate Git operations in your repos with a single terminal command.
	🟢 Free / open-source
	github.com/initialcommit-com
	cord
	Discord to Claude Code bridge. Talk to Claude through Discord.
	🟢 Free / open-source
	github.com/alexknowshtml/cord


________________


Student Handoff Stack — Fastest Path to Client Delivery
The exact stack for going from prototype to client handoff.


Tool
	Role
	Access
	Link
	Supabase
	Backend + vector DB + auth + storage
	🟢 Free tier
	supabase.com
	n8n
	Workflow orchestration + AI agent nodes
	🟢 Free self-hosted
	n8n.io
	Vercel / Railway
	Frontend hosting + API deployment
	Free tiers
	vercel.com / railway.app
	Langfuse
	Observability from day one
	🟢 Free / self-hostable
	langfuse.com
	Claude Code + Cursor
	Build everything fast
	Student credits + free
	claude.ai + cursor.com
	MCP servers
	Connect agent to client's tools
	🟢 Free / open-source
	github.com/modelcontextprotocol


Builder consensus: Don't buy 15 tools — build composable agents on n8n/LangGraph + Supabase + best-in-class models. This covers ~90% of SMB workflow pain points.


________________


Quick Pain Point → Tool Mapping
Reference this after every discovery call. Match client pain codes to the right section above.


Pain Code
	Pain Point
	See Sections
	A1
	Data access — answer exists but can't find it
	5 (Screen Memory), 7 (Doc AI), 16 (RAG)
	A2
	Tracking gaps — data doesn't exist
	5 (Data Collection), 17 (Database)
	A3
	Legacy lock-in — data trapped
	3 (Automation), 4 (Computer Use), 6 (Scraping)
	A4
	Unstructured data chaos
	7 (Doc AI), 5 (Screen Memory), 19 (Meetings)
	B1
	Manual repetitive tasks
	3 (Automation), 4 (Computer Use), 2 (MCP)
	B2
	Missing/outdated SOPs
	5 (Screen Memory), 19 (Meetings)
	B3
	Communication breakdowns
	3 (Automation), 19 (Meetings)
	B4
	Scheduling & resource issues
	15 (Scheduling)
	C1
	Lead gen & sales pipeline
	8 (CRM), 9 (Lead Gen), 6 (Enrichment)
	C2
	Customer service & support
	10 (Voice), 11 (Support), 16 (RAG)
	C3
	Marketing & content
	12 (Content), 6 (Enrichment)
	C4
	Pricing, quoting, estimating
	3 (Automation), 7 (Doc AI)
	D1
	Bookkeeping & invoicing
	13 (Financial AI), 7 (Doc AI)
	D2
	HR, hiring, onboarding
	14 (Hiring), 5 (Data Collection)
	D3
	Compliance & legal
	7 (Doc AI), 3 (Automation)
	E1
	Competitive intelligence
	6 (Scraping/Enrichment), 3 (Automation)
	E2
	Forecasting & planning
	15 (Scheduling), 17 (Database)
	E3
	Customer understanding
	6 (Enrichment), 19 (Meetings), 16 (RAG)


________________




G1000 — Babson College, Spring 2026 The Generator Lead Team: Spencer, Joshua, Rustin, Cole, Reece


[a]Should add Antigravity
