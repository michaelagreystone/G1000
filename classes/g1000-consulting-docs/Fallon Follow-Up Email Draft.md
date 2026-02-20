# Fallon Company – Follow-Up Email Draft
**To:** Danny (The Fallon Company)
**Subject:** Follow-Up from G1000 | Insights & A Few Questions

---

Hi Danny,

Thank you again for taking the time to speak with us — it was genuinely one of the more insightful conversations we've had in this class. Your ability to walk us through the full arc of a development deal, from market selection all the way to disposition, gave us a clear foundation to actually think critically about where AI fits into a business like yours.

---

**The Core Issue — As We See It**

The biggest bottleneck we kept coming back to isn't any one workflow in isolation. It's the speed at which market reality reaches your business plan — and then travels from the investments team to the development team.

You described it well with the 2018-to-COVID example: projects underwritten at one set of assumptions had to be restructured when interest rates, investor return thresholds, and office market dynamics all shifted simultaneously. The challenge wasn't that the team didn't know the world had changed — it's that the process of recognizing it, quantifying it, and updating the business plan across verticals was slow and manual. In a business where a 100 basis point gap between your projected return and the current market expectation can derail a multi-year project, that lag is expensive.

---

**Pain Points We Identified**

1. **Cross-vertical information gaps** — You mentioned that when the development team goes into execution mode, they can drift from the original business plan. Without a continuous feedback loop from the investments team — informed by real-time broker conversations, cap rate movements, and financing conditions — the development team is executing on assumptions that may already be stale.

2. **Contract negotiation** — You were clear about this one: hundreds of pages, millions in legal bills, and a back-and-forth redline process that consumes enormous time and money on every deal. You have historical precedent documents; the challenge is putting them to work.

3. **Deal sourcing** — Currently dependent on broker relationships and manual outreach. You described the ideal: a system that surfaces sites matching your criteria (acreage, proximity, municipality, ownership structure) and helps initiate contact with landowners. You're essentially doing sales on land, and right now it's entirely human-driven.

4. **Financial modeling** — You're already using Claude to review models, but the manual construction of 100+ variable pro formas from scratch is still slow. The opportunity to get to 90% of a working model before your team touches it is clearly on your radar.

---

**Three Follow-Up Questions**

1. **On contracts:** When you go into a new loan agreement or JV negotiation, how much of it is truly net-new versus referencing prior deal structures? Understanding the ratio of "redline from precedent" to "genuinely novel terms" would help us scope how much a RAG-based contract tool could actually automate versus what still requires lawyer judgment.

2. **On the investments-to-development handoff:** Is there a defined moment — a document, a meeting, a formal approval — where the business plan is handed from the investments team to development? Or is it more of a continuous informal process? Knowing where the seam is would tell us where an intelligence layer would have the most impact.

3. **On data aggregation:** You mentioned the idea of a two-step process — first aggregate your internal data, then have models run off it. Do you have a sense of where your most valuable proprietary data currently lives? (Email threads, internal memos, deal files, spreadsheets?) That inventory matters a lot for what's actually buildable.

---

**What We're Not Recommending**

We're not recommending a generic AI platform or off-the-shelf tool — and we want to be direct about why. Fallon's edge is in the nuance of its business planning and deal-making. An 18-person team managing a $6B pipeline succeeds because of judgment, not volume. Tools built for high-volume sales teams or generic document workflows would underfit your actual problem and add noise rather than signal. We're also not recommending starting with the deal sourcing bot, even though it's a compelling use case. The reason: deal sourcing depends on real-time human context (broker calls, community relationships, municipal programs like MBTA development) that is difficult to systematize before you've solved the internal data infrastructure problem. Building outward before building inward is usually the wrong order.

---

**Our Recommendation**

**Build a closed-environment RAG system over your historical contract library — starting with loan agreements and JV documents.**

Here's what this looks like in practice:

You have a library of past loan agreements, joint venture agreements, construction contracts, and architect agreements. Right now, that institutional knowledge lives in PDFs and your lawyers' heads. A RAG system would index all of it — making it semantically searchable — so that when you enter a new negotiation, you can ask questions like:

- *"What did our last three construction contracts say about delay penalties?"*
- *"What indemnification language did we use in our JV agreements with pension fund LPs?"*
- *"What's the range of developer fee structures we've accepted across recent projects?"*

The model doesn't negotiate for you. It surfaces your own precedent, instantly, so your lawyers are redlining from a strong foundation rather than drafting from memory. The closed data environment (your own contracts, not the open web) also directly addresses the privacy concern you raised — nothing leaves your system.

**Tech stack this would require:** A document ingestion pipeline (LlamaParse or Marker for PDF parsing), a vector database (pgvector via Supabase), and a retrieval layer (LangGraph or LlamaIndex) connected to Claude's API. This is buildable. The same infrastructure, once built, becomes the foundation for the financial model layer and eventually the market intelligence system you described.

---

We'd love to set up a second conversation to go deeper on the contract use case and show you what a prototype could look like. We're also happy to bring this to the G1000 AI Boot Camp in April if you'd like to use it as a live working session.

Thank you again, Danny — and we'll follow up shortly with the Boot Camp details as Spencer mentioned.

Best,
Michael Greystone
G1000 | Babson College
