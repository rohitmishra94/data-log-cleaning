"""
Pattern Synthesis Engine: LLM-Powered Pattern Interpretation

This module replaces hardcoded if/else rules with LLM-synthesized insights.
It takes raw patterns from ML algorithms and generates contextual, actionable intelligence.

Key Features:
- Domain-agnostic pattern interpretation
- Contextual root cause analysis
- Adaptive intervention strategies
- Natural language insights

Author: Adaptive Retention Engine Team
"""

import json
from typing import Dict, Any, List, Optional
from insights.ai_client import get_ai_response


class PatternSynthesizer:
    """
    LLM-powered synthesis layer for pattern discovery.

    Transforms raw ML patterns into contextualized business insights.
    """

    def __init__(self, business_context: str = "bus ticket booking app"):
        """
        Initialize Pattern Synthesizer.

        Args:
            business_context: Domain context for interpretation (e.g., "e-commerce", "saas app")
        """
        self.business_context = business_context

    def synthesize_all_patterns(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main synthesis method - generates LLM insights for all pattern types.

        Args:
            patterns: Raw pattern dictionary from PatternDiscovery.discover()

        Returns:
            Enhanced patterns with LLM-generated insights
        """
        print("\n🤖 LLM Pattern Synthesis Starting...")
        print("=" * 60)

        synthesized = patterns.copy()

        # 1. Synthesize sequential patterns
        print("\n1️⃣  Synthesizing Sequential Patterns...")
        seq_insights = self.synthesize_sequential_patterns(
            patterns.get('sequential_patterns', {})
        )
        if seq_insights:
            synthesized['sequential_patterns']['llm_insights'] = seq_insights

        # 2. Synthesize user segments
        print("\n2️⃣  Synthesizing User Segments...")
        segment_insights = self.synthesize_user_segments(
            patterns.get('user_segments', {})
        )
        if segment_insights:
            synthesized['user_segments']['llm_insights'] = segment_insights

        # 3. Synthesize friction points
        print("\n3️⃣  Synthesizing Friction Analysis...")
        friction_insights = self.synthesize_friction_points(
            patterns.get('friction_points', {})
        )
        if friction_insights:
            synthesized['friction_points']['llm_insights'] = friction_insights

        # 4. Synthesize intervention strategies
        print("\n4️⃣  Synthesizing Intervention Strategies...")
        intervention_insights = self.synthesize_interventions(
            patterns.get('intervention_rules', {}),
            patterns.get('friction_points', {})
        )
        if intervention_insights:
            synthesized['intervention_rules']['llm_insights'] = intervention_insights

        # 5. Generate executive summary
        print("\n5️⃣  Generating Executive Summary...")
        executive_summary = self.generate_executive_summary(patterns)
        if executive_summary:
            synthesized['llm_executive_summary'] = executive_summary

        print("\n" + "=" * 60)
        print("✅ LLM Synthesis Complete!")

        return synthesized

    def synthesize_sequential_patterns(self, seq_patterns: Dict) -> Optional[str]:
        """
        Generate LLM interpretation of sequential patterns.

        Replaces hardcoded pattern interpretation with contextual understanding.
        """
        if not seq_patterns or not seq_patterns.get('frequent_patterns'):
            return None

        # Build context for LLM
        top_patterns = list(seq_patterns.get('frequent_patterns', {}).items())[:10]
        top_repetitions = list(seq_patterns.get('repetition_patterns', {}).items())[:5]
        dropout_sequences = list(seq_patterns.get('dropout_sequences', {}).items())[:5]

        prompt = f"""You are a product analytics expert analyzing user behavior patterns in a {self.business_context}.

**Sequential Pattern Data:**

Top Frequent Sequences:
{json.dumps(top_patterns, indent=2)}

Top Repetition Patterns:
{json.dumps(top_repetitions, indent=2)}

Common Dropout Sequences:
{json.dumps(dropout_sequences, indent=2)}

**Your Task:**
Analyze these patterns and provide:
1. **Key Insights**: What do these patterns reveal about user behavior?
2. **Root Causes**: Why are users repeating events or dropping off?
3. **Business Impact**: How do these patterns affect conversion/retention?
4. **Recommendations**: What specific actions should the product team take?

Be concise, actionable, and focus on the most critical findings. Use bullet points.
"""

        response = get_ai_response(prompt)

        if response['success']:
            return response['content']
        else:
            print(f"   ⚠️  LLM synthesis failed: {response.get('error')}")
            return None

    def synthesize_user_segments(self, segments_data: Dict) -> Optional[str]:
        """
        Generate LLM interpretation of user segments.

        Creates rich persona descriptions instead of generic labels.
        """
        if not segments_data or not segments_data.get('segments'):
            return None

        segments = segments_data.get('segments', {})

        prompt = f"""You are a user research expert analyzing behavioral segments in a {self.business_context}.

**User Segment Data:**
{json.dumps(segments, indent=2)}

**Your Task:**
For each segment, provide:
1. **Persona Profile**: Describe who these users are and their behavior patterns
2. **Pain Points**: What challenges or frustrations do they face?
3. **Opportunities**: How can we better serve this segment?
4. **Priority Level**: Which segments need immediate attention vs. long-term optimization?

Be specific and actionable. Focus on behavioral characteristics, not just statistics.
"""

        response = get_ai_response(prompt)

        if response['success']:
            return response['content']
        else:
            print(f"   ⚠️  LLM synthesis failed: {response.get('error')}")
            return None

    def synthesize_friction_points(self, friction_data: Dict) -> Optional[str]:
        """
        Generate LLM interpretation of friction points.

        Provides root cause analysis instead of generic friction scores.
        """
        if not friction_data or not friction_data.get('high_friction_events'):
            return None

        high_friction = friction_data.get('high_friction_events', {})

        # Take top 5 friction points
        top_friction = dict(list(high_friction.items())[:5])

        prompt = f"""You are a UX researcher analyzing friction points in a {self.business_context}.

**High Friction Events:**
{json.dumps(top_friction, indent=2)}

**Context:**
- repetition_rate: % of times users repeat this action (high = stuck/confused)
- users_affected: Number of unique users experiencing friction
- friction_score: Overall severity metric

**Your Task:**
For each friction point:
1. **Root Cause Hypothesis**: Why are users getting stuck here?
2. **UX Implications**: What does this repetition reveal about the user experience?
3. **Fix Priority**: Rate as CRITICAL, HIGH, MEDIUM, LOW with reasoning
4. **Recommended Solutions**: Specific, actionable UX improvements

Be tactical and specific. Think like a product designer solving real user problems.
"""

        response = get_ai_response(prompt)

        if response['success']:
            return response['content']
        else:
            print(f"   ⚠️  LLM synthesis failed: {response.get('error')}")
            return None

    def synthesize_interventions(self, intervention_data: Dict, friction_data: Dict) -> Optional[str]:
        """
        Generate LLM-powered intervention strategies.

        Creates contextual, adaptive interventions instead of generic rules.
        """
        if not intervention_data or not intervention_data.get('intervention_triggers'):
            return None

        triggers = intervention_data.get('intervention_triggers', [])[:10]
        high_friction = friction_data.get('high_friction_events', {})

        # Combine data for context
        context = {
            "triggers": triggers,
            "top_friction": dict(list(high_friction.items())[:3])
        }

        prompt = f"""You are a growth engineer designing automated interventions for a {self.business_context}.

**Intervention Trigger Rules:**
{json.dumps(triggers, indent=2)}

**High Friction Context:**
{json.dumps(dict(list(high_friction.items())[:3]), indent=2)}

**Your Task:**
Design specific intervention strategies:

1. **Real-Time Interventions**: What should trigger in-app during the user session?
   - When to show help tooltip/modal
   - When to offer live chat
   - When to simplify the UI

2. **Proactive Outreach**: What should trigger post-session?
   - Email campaigns
   - Push notifications
   - In-app messages on return

3. **Personalization Rules**: How to adapt the experience?
   - A/B test variations
   - Feature toggles
   - Simplified flows for struggling users

4. **Success Metrics**: How to measure if interventions work?

Be specific and implementation-ready. Think like a product engineer building features.
"""

        response = get_ai_response(prompt)

        if response['success']:
            return response['content']
        else:
            print(f"   ⚠️  LLM synthesis failed: {response.get('error')}")
            return None

    def generate_executive_summary(self, patterns: Dict) -> Optional[str]:
        """
        Generate high-level executive summary of all findings.

        Synthesizes all patterns into actionable business recommendations.
        """
        # Extract key metrics
        metadata = patterns.get('metadata', {})
        segments = patterns.get('user_segments', {}).get('segments', {})
        friction = patterns.get('friction_points', {}).get('high_friction_events', {})
        survival = patterns.get('survival_analysis', {})

        # Build concise summary
        summary_data = {
            "total_users": metadata.get('unique_users', 0),
            "total_events": metadata.get('total_events', 0),
            "total_sessions": metadata.get('total_sessions', 0),
            "key_segments": {
                name: {"count": seg.get('count', 0), "pct": seg.get('percentage', 0)}
                for name, seg in list(segments.items())[:4]
            },
            "top_friction": {
                name: {
                    "repetition_rate": f"{data['repetition_rate']:.1%}",
                    "users_affected": data['users_affected']
                }
                for name, data in list(friction.items())[:3]
            },
            "median_session_length": survival.get('median_session_length', 0),
            "critical_dropoffs": survival.get('critical_dropoffs', [])[:3]
        }

        prompt = f"""You are a product executive reviewing analytics for a {self.business_context}.

**Analysis Summary:**
{json.dumps(summary_data, indent=2)}

**Your Task:**
Write a concise executive summary (5-7 bullet points) covering:

1. **Overall Health**: Is the product performing well? Major concerns?
2. **Top 3 Priorities**: What should the team focus on immediately?
3. **Business Impact**: Estimated impact of fixing identified issues
4. **Resource Allocation**: Where to invest engineering/design resources?
5. **Timeline**: What can be quick wins vs. long-term initiatives?

Write for a CEO/VP Product audience. Be direct, quantitative where possible, and action-oriented.
"""

        response = get_ai_response(prompt)

        if response['success']:
            return response['content']
        else:
            print(f"   ⚠️  LLM synthesis failed: {response.get('error')}")
            return None


if __name__ == "__main__":
    print("PatternSynthesizer module loaded successfully!")
    print("Use: synthesizer = PatternSynthesizer(business_context='your app type')")
