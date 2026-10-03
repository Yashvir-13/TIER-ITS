# Glossary

This document defines the core domain terminology used throughout the TIER-ITS project, particularly focusing on the Interpersonal Theory of Suicide (ITS) and associated risk assessment frameworks.

## Interpersonal Theory of Suicide (ITS) Concepts

These concepts form the core of the `ITSConcept` enum used in the evidence ledger.

*   **Thwarted Belongingness (TB):** The feeling of being completely disconnected from others. A psychological state where an individual feels they do not belong to any group, family, or community, and lack meaningful social connections. Expressed as "I am alone," "Nobody cares about me," or severe social isolation.
*   **Perceived Burdensomeness (PB):** The feeling that one is a burden to others. A psychological state where an individual believes their existence places a heavy and unwanted toll on their family, friends, or society, and that others would be better off if they were gone. Expressed as "I'm just dragging everyone down" or "They'd be happier without me."
*   **Hopelessness:** In the context of ITS, this refers specifically to the belief that the states of Thwarted Belongingness and Perceived Burdensomeness will never change or improve.
*   **Acquired Capability (AC):** A lowered fear of death and increased tolerance for physical pain, often developed through habituation to painful or frightening experiences. ITS posits that TB and PB create the *desire* for suicide, but AC is required for the *ability* to enact it.

## Risk Assessment Frameworks

*   **C-SSRS (Columbia-Suicide Severity Rating Scale):** A widely used, structured questionnaire designed to assess the severity and imminence of suicidal ideation and behavior. It asks specific, graduated questions about suicidal thoughts, plans, and intent.
*   **SAFE-T (Suicide Assessment Five-Step Evaluation and Triage):** A clinical practice guideline that involves identifying risk factors, identifying protective factors, conducting a suicide inquiry (like C-SSRS), determining risk level/intervention, and documenting the process.

## TIER-ITS Project Terms

*   **Evidence Ledger:** The core memory structure of this project. A structured store that records extracted ITS concepts, the exact text span supporting them, temporality, subject, and any subsequent contradictions.
*   **Target Statement:** A specific piece of risk evidence (e.g., "I feel like a burden to my family") artificially placed into a conversation at a known depth to test memory retention.
*   **Conversation Depth:** The number of conversational turns that have occurred *after* a target statement was introduced.
*   **Baseline:** Comparison models that do not use the ITS evidence ledger, including target-only, full-context (the entire conversation history), recent-window (the last N turns), and general-summary (a running text summary).
