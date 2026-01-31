"""Specialist agents for deal briefing generation."""

from typing import Any

from app.briefings.agents.base import SpecialistAgent, logger
from app.documents.schemas import RetrievalObservation

# =============================================================================
# Company Researcher Agent
# =============================================================================


class CompanyResearcherAgent(SpecialistAgent):
    """Finds industry insights and market context.

    Queries industry playbooks and case studies to provide
    relevant background for the target company.
    """

    name: str = "company_researcher"
    description: str = "Researches industry context and market insights"

    retrieval_queries: list[str] = []
 
    # Filters to apply to retrieval
    retrieval_filters: dict[str, Any] = {"doc_type": "industry"}

    def _build_queries(self, context: dict[str, Any]) -> list[str]:
        """Build industry research queries from context."""
        industry = context.get("industry", "general")
        company_size = context.get("company_size", "mid-market")

        return [
            f"{industry} industry trends and priorities",
            f"{industry} sector challenges and opportunities",
            f"market context for {company_size} companies",
        ]

   
    def _synthesize(
        self, context: dict[str, Any], retrievals: list[RetrievalObservation]
    ) -> dict[str, Any]:
        """Synthesize industry research into company context."""
        retrieved_context = self._format_retrieval_context(retrievals)

        system_prompt = """You are a sales research analyst. Based on the provided
                        documents, create a brief company context summary.

                        Output valid JSON with these fields:
                        - overview: 2-3 sentence company/industry overview
                        - key_priorities: list of 3-5 industry priorities
                        - relevant_trends: list of 2-3 relevant market trends
                        - considerations: list of 2-3 things to keep in mind for this deal"""

        user_prompt = f"""Company: {context.get("company_name", "Unknown")}
                        Industry: {context.get("industry", "Unknown")}
                        Company Size: {context.get("company_size", "Unknown")}
                        Meeting Type: {context.get("meeting_type", "Unknown")}

                        Retrieved Documents:
                        {retrieved_context}

                        Generate the company context JSON:"""

        try:
            response = self.llm.invoke(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            )
            content = response.content
            if isinstance(content, str):
                # Try to parse JSON from response
                return self._parse_json_response(content)
        except Exception as e:
            logger.warning(f"Synthesis failed: {e}")

        return {
            "overview": f"Research on {context.get('industry', 'unknown')} industry",
            "key_priorities": [],
            "relevant_trends": [],
            "considerations": [],
        }



# =============================================================================
# Similar Deals Finder Agent
# =============================================================================


class SimilarDealsFinderAgent(SpecialistAgent):
    """Identifies past deals with similar characteristics.

    Searches deal records to find relevant precedents
    and extract learnings.
    """

    name: str = "similar_deals_finder"
    description: str = "Finds similar past deals and extracts learnings"

    retrieval_queries: list[str] = []

    def _build_queries(self, context: dict[str, Any]) -> list[str]:
        """Build similar deals queries from context."""
        industry = context.get("industry", "general")
        company_size = context.get("company_size", "mid-market")

        return [
            f"deals in {industry} industry",
            f"{company_size} company deals won",
            f"successful deals {industry}",
        ]

    # Filters for deal records
    retrieval_filters: dict[str, Any] = {"doc_type": "deal"}

    def _synthesize(
        self, context: dict[str, Any], retrievals: list[RetrievalObservation]
    ) -> dict[str, Any]:
        """Synthesize similar deals information."""
        retrieved_context = self._format_retrieval_context(retrievals)

        system_prompt = """You are a sales analyst. Based on the provided deal records,
                        identify similar past deals and extract key learnings.

                        Output valid JSON with these fields:
                        - similar_deals: list of objects with {company, outcome, deal_value, similarity_reason}
                        - common_success_factors: list of 3-5 factors that led to wins
                        - common_objections: list of 2-3 common objections encountered
                        - key_learnings: list of 3-5 actionable learnings"""

        user_prompt = f"""Target Company: {context.get("company_name", "Unknown")}
                        Industry: {context.get("industry", "Unknown")}
                        Company Size: {context.get("company_size", "Unknown")}

                        Past Deal Records:
                        {retrieved_context}

                        Generate the similar deals analysis JSON:"""

        try:
            response = self.llm.invoke(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            )
            content = response.content
            if isinstance(content, str):
                return self._parse_json_response(content)
        except Exception as e:
            logger.warning(f"Synthesis failed: {e}")

        return {
            "similar_deals": [],
            "common_success_factors": [],
            "common_objections": [],
            "key_learnings": [],
        }



# =============================================================================
# Competitor Analyst Agent
# =============================================================================


class CompetitorAnalystAgent(SpecialistAgent):
    """Retrieves competitive positioning information.

    Analyzes competitor documents to provide differentiation
    strategies and objection handling.
    """

    name: str = "competitor_analyst"
    description: str = "Analyzes competitive landscape and positioning"

    retrieval_queries: list[str] = []

    def _build_queries(self, context: dict[str, Any]) -> list[str]:
        """Build competitor analysis queries."""
        return [
            "competitor analysis comparison",
            "competitive differentiation advantages",
            "objection handling responses",
        ]

    # Filters for competitor intelligence
    retrieval_filters: dict[str, Any] = {"doc_type": "competitor"}

    def _synthesize(
        self, context: dict[str, Any], retrievals: list[RetrievalObservation]
    ) -> dict[str, Any]:
        """Synthesize competitive analysis."""
        retrieved_context = self._format_retrieval_context(retrievals)

        system_prompt = """You are a competitive intelligence analyst. Based on the
                        provided competitor analyses, create a competitive positioning summary.

                        Output valid JSON with these fields:
                        - key_competitors: list of {name, strengths, weaknesses}
                        - our_advantages: list of 3-5 key differentiators
                        - their_advantages: list of 2-3 competitor strengths to be aware of
                        - objection_responses: list of {objection, response} pairs
                        - positioning_strategy: 2-3 sentence recommended positioning"""

        user_prompt = f"""Target Company: {context.get("company_name", "Unknown")}
                        Industry: {context.get("industry", "Unknown")}

                        Competitor Intelligence:
                        {retrieved_context}

                        Generate the competitive analysis JSON:"""

        try:
            response = self.llm.invoke(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            )
            content = response.content
            if isinstance(content, str):
                return self._parse_json_response(content)
        except Exception as e:
            logger.warning(f"Synthesis failed: {e}")

        return {
            "key_competitors": [],
            "our_advantages": [],
            "their_advantages": [],
            "objection_responses": [],
            "positioning_strategy": "",
        }



# =============================================================================
# Proposal Drafter Agent
# =============================================================================


class ProposalDrafterAgent(SpecialistAgent):
    """Generates customized talking points and approach.

    Uses proposal templates and product information to
    create tailored recommendations.
    """

    name: str = "proposal_drafter"
    description: str = "Drafts talking points and recommended approach"

    retrieval_queries: list[str] = [
        "{company_size} proposal template approach",
        "pricing guidance {industry}",
        "product features benefits",
    ]

    retrieval_filters: dict[str, Any] = {}  # Search across proposals and products

    def _build_queries(self, context: dict[str, Any]) -> list[str]:
        """Build queries with fallbacks for missing context."""
        queries = []
        company_size = context.get("company_size", "mid-market")
        industry = context.get("industry", "general")

        queries.append(f"{company_size} proposal template approach")
        queries.append(f"pricing guidance {industry}")
        queries.append("product features benefits value proposition")

        return queries

    def _synthesize(
        self, context: dict[str, Any], retrievals: list[RetrievalObservation]
    ) -> dict[str, Any]:
        """Synthesize proposal recommendations."""
        retrieved_context = self._format_retrieval_context(retrievals)

        system_prompt = """You are a sales enablement specialist. Based on the
                        provided materials, create customized talking points and recommendations.

                        Output valid JSON with these fields:
                        - talking_points: list of 5-7 key points to cover in the meeting
                        - discovery_questions: list of 4-6 questions to ask the prospect
                        - value_propositions: list of 3-4 value props relevant to this deal
                        - pricing_guidance: string with pricing recommendation
                        - next_steps: list of 2-3 recommended next steps after the meeting"""

        meeting_type = context.get("meeting_type", "initial_call")
        user_prompt = f"""Target Company: {context.get("company_name", "Unknown")}
                        Industry: {context.get("industry", "Unknown")}
                        Company Size: {context.get("company_size", "Unknown")}
                        Meeting Type: {meeting_type}
                        Specific Questions: {context.get("specific_questions", [])}

                        Reference Materials:
                        {retrieved_context}

                        Generate the proposal recommendations JSON:"""

        try:
            response = self.llm.invoke(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            )
            content = response.content
            if isinstance(content, str):
                return self._parse_json_response(content)
        except Exception as e:
            logger.warning(f"Synthesis failed: {e}")

        return {
            "talking_points": [],
            "discovery_questions": [],
            "value_propositions": [],
            "pricing_guidance": "",
            "next_steps": [],
        }

