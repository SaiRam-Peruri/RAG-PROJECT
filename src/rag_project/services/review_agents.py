"""
Multi-agent review system for proposal quality assurance.
Five specialized bots evaluate different aspects of generated content.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import re

from ..logging_config import get_logger

logger = get_logger("review_agents")


@dataclass
class ReviewResult:
    """Structured result from a review bot."""
    agent: str
    score: float  # 0-1 scale
    passed: bool
    issues: List[str]
    recommendations: List[str]


class ComplianceBot:
    """
    FAR/DFAR/Section L/M compliance checker.
    Verifies compliance with federal acquisition regulations and solicitation requirements.
    """
    
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
        self.agent_name = "ComplianceBot"
    
    def evaluate(self, sections: Dict[str, str], context: Dict) -> ReviewResult:
        """
        Check policy compliance across all sections.
        
        Args:
            sections: Dict mapping section names to generated content
            context: Metadata (opportunity_id, stage, requirements, etc.)
        
        Returns:
            ReviewResult with compliance assessment
        """
        issues = []
        recommendations = []
        score = 1.0
        
        # Check 1: Required sections exist
        stage = context.get("stage", "rfp").lower()
        required_sections = {
            "rfi": ["executive_summary", "technical"],
            "rfp": ["executive_summary", "technical", "management", "past_performance"],
        }
        
        expected = required_sections.get(stage, [])
        missing = [sec for sec in expected if sec not in sections or not sections[sec].strip()]
        
        if missing:
            issues.append(f"Missing required sections: {', '.join(missing)}")
            score -= 0.3 * len(missing) / len(expected)
        
        # Check 2: Page limit compliance (estimate 500 words = 1 page)
        for section_name, content in sections.items():
            word_count = len(content.split())
            if word_count < 100:
                issues.append(f"{section_name}: Too short ({word_count} words, min 100)")
                score -= 0.1
            elif word_count > 5000:
                recommendations.append(f"{section_name}: Very long ({word_count} words), consider condensing")
        
        # Check 3: Look for compliance keywords
        compliance_keywords = [
            "FAR", "DFAR", "requirement", "comply", "compliant", 
            "regulation", "clause", "specification"
        ]
        
        total_sections = len(sections)
        sections_with_compliance = 0
        
        for content in sections.values():
            if any(kw.lower() in content.lower() for kw in compliance_keywords):
                sections_with_compliance += 1
        
        if sections_with_compliance < total_sections * 0.5:
            issues.append("Few sections reference compliance requirements")
            recommendations.append("Explicitly reference applicable FAR/DFAR clauses")
            score -= 0.15
        
        # Check 4: Formatting issues (placeholder check)
        for section_name, content in sections.items():
            # Check for placeholder text
            if "[INSERT" in content or "TODO" in content or "XXX" in content:
                issues.append(f"{section_name}: Contains placeholder text")
                score -= 0.1
        
        score = max(0.0, min(1.0, score))
        passed = score >= self.threshold
        
        if not issues:
            recommendations.append("Policy compliance looks good")
        
        logger.info("%s: score=%.2f, passed=%s, issues=%d", 
                   self.agent_name, score, passed, len(issues))
        
        return ReviewResult(
            agent=self.agent_name,
            score=score,
            passed=passed,
            issues=issues,
            recommendations=recommendations
        )


class TechArchitectBot:
    """
    Technical solution lead - evaluates architecture, approach, and technical depth.
    """
    
    def __init__(self, threshold: float = 0.75):
        self.threshold = threshold
        self.agent_name = "TechArchitectBot"
    
    def evaluate(self, sections: Dict[str, str], context: Dict) -> ReviewResult:
        """
        Assess technical accuracy and citation quality.
        
        Args:
            sections: Dict mapping section names to generated content
            context: Metadata (opportunity_id, citations, etc.)
        
        Returns:
            ReviewResult with accuracy assessment
        """
        issues = []
        recommendations = []
        score = 1.0
        
        # Check 1: Citation density (look for [Source: ...] or similar)
        citation_patterns = [
            r'\[Source:',
            r'\[Ref:',
            r'\[Citation:',
            r'\[Reference:',
        ]
        
        for section_name, content in sections.items():
            if section_name not in ["technical", "management", "past_performance"]:
                continue
            
            word_count = len(content.split())
            citation_count = sum(
                len(re.findall(pattern, content, re.IGNORECASE)) 
                for pattern in citation_patterns
            )
            
            # Expect at least 1 citation per 500 words
            expected_citations = max(1, word_count // 500)
            
            if citation_count < expected_citations:
                issues.append(f"{section_name}: Low citation density ({citation_count} found, {expected_citations} expected)")
                score -= 0.15
        
        # Check 2: Avoid weak or vague claims
        weak_phrases = [
            "we believe", "we think", "may be", "could be", "possibly",
            "probably", "perhaps", "might", "should work"
        ]
        
        for section_name, content in sections.items():
            weak_count = sum(
                content.lower().count(phrase) for phrase in weak_phrases
            )
            if weak_count > 3:
                issues.append(f"{section_name}: Contains {weak_count} weak/uncertain phrases")
                recommendations.append(f"{section_name}: Replace weak language with definitive statements backed by evidence")
                score -= 0.1
        
        # Check 3: Technical terminology (presence indicates technical depth)
        technical_indicators = [
            "architecture", "infrastructure", "protocol", "integration",
            "API", "framework", "platform", "methodology", "algorithm",
            "security", "encryption", "authentication", "compliance"
        ]
        
        technical_sections = [s for s in sections.keys() if "technical" in s.lower()]
        for section_name in technical_sections:
            content = sections.get(section_name, "")
            tech_term_count = sum(
                1 for term in technical_indicators 
                if term.lower() in content.lower()
            )
            
            if tech_term_count < 3:
                issues.append(f"{section_name}: Lacks technical depth (few technical terms)")
                recommendations.append(f"{section_name}: Add more specific technical details and terminology")
                score -= 0.15
        
        # Check 4: Unsubstantiated superlatives
        superlatives = [
            "best", "fastest", "most secure", "industry-leading",
            "cutting-edge", "world-class", "revolutionary"
        ]
        
        for section_name, content in sections.items():
            superlative_count = sum(
                content.lower().count(term) for term in superlatives
            )
            if superlative_count > 2:
                recommendations.append(f"{section_name}: {superlative_count} superlatives found - ensure claims are substantiated")
                score -= 0.05
        
        score = max(0.0, min(1.0, score))
        passed = score >= self.threshold
        
        if not issues:
            recommendations.append("Technical content appears well-supported")
        
        logger.info("%s: score=%.2f, passed=%s, issues=%d", 
                   self.agent_name, score, passed, len(issues))
        
        return ReviewResult(
            agent=self.agent_name,
            score=score,
            passed=passed,
            issues=issues,
            recommendations=recommendations
        )


class NarrativeWriterBot:
    """
    Storytelling specialist - evaluates executive summaries, win themes, and narrative flow.
    """
    
    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold
        self.agent_name = "NarrativeWriterBot"
    
    def evaluate(self, sections: Dict[str, str], context: Dict) -> ReviewResult:
        """
        Assess narrative quality and readability.
        
        Args:
            sections: Dict mapping section names to generated content
            context: Metadata
        
        Returns:
            ReviewResult with narrative assessment
        """
        issues = []
        recommendations = []
        score = 1.0
        
        # Check 1: Paragraph structure (look for overly long paragraphs)
        for section_name, content in sections.items():
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            
            if len(paragraphs) < 2 and len(content.split()) > 200:
                issues.append(f"{section_name}: Lacks paragraph breaks (wall of text)")
                recommendations.append(f"{section_name}: Break into multiple paragraphs for readability")
                score -= 0.15
            
            # Check for overly long paragraphs (>300 words)
            for i, para in enumerate(paragraphs):
                word_count = len(para.split())
                if word_count > 300:
                    recommendations.append(f"{section_name}: Paragraph {i+1} is very long ({word_count} words)")
                    score -= 0.05
        
        # Check 2: Sentence variety (avoid repetitive sentence starts)
        for section_name, content in sections.items():
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if len(sentences) < 3:
                continue
            
            first_words = [s.split()[0] for s in sentences if s.split()]
            if len(first_words) > 5:
                unique_starts = len(set(first_words))
                variety_ratio = unique_starts / len(first_words)
                
                if variety_ratio < 0.5:
                    issues.append(f"{section_name}: Repetitive sentence structure")
                    recommendations.append(f"{section_name}: Vary sentence beginnings for better flow")
                    score -= 0.1
        
        # Check 3: Transition words (indicates good flow)
        transition_words = [
            "however", "therefore", "furthermore", "additionally",
            "moreover", "consequently", "nevertheless", "meanwhile",
            "specifically", "for example", "in contrast", "similarly"
        ]
        
        for section_name, content in sections.items():
            word_count = len(content.split())
            if word_count < 200:
                continue
            
            transition_count = sum(
                1 for tw in transition_words 
                if tw.lower() in content.lower()
            )
            
            # Expect at least 1 per 200 words
            expected = word_count // 200
            if transition_count < expected:
                recommendations.append(f"{section_name}: Could use more transition words for better flow")
                score -= 0.05
        
        # Check 4: Redundancy detection (simple: repeated phrases)
        for section_name, content in sections.items():
            # Look for repeated 3-word phrases
            words = content.lower().split()
            trigrams = [' '.join(words[i:i+3]) for i in range(len(words)-2)]
            
            if len(trigrams) > 10:
                trigram_counts = {}
                for tg in trigrams:
                    trigram_counts[tg] = trigram_counts.get(tg, 0) + 1
                
                repeated = [tg for tg, count in trigram_counts.items() if count > 2]
                if len(repeated) > 3:
                    issues.append(f"{section_name}: Detected {len(repeated)} repeated phrases")
                    recommendations.append(f"{section_name}: Review for redundancy")
                    score -= 0.1
        
        # Check 5: Reading level (sentence length as proxy)
        for section_name, content in sections.items():
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                continue
            
            avg_words_per_sentence = sum(len(s.split()) for s in sentences) / len(sentences)
            
            if avg_words_per_sentence > 35:
                recommendations.append(f"{section_name}: Long sentences (avg {avg_words_per_sentence:.0f} words) - consider simplifying")
                score -= 0.05
            elif avg_words_per_sentence < 10:
                recommendations.append(f"{section_name}: Very short sentences - may lack detail")
                score -= 0.05
        
        score = max(0.0, min(1.0, score))
        passed = score >= self.threshold
        
        if not issues:
            recommendations.append("Narrative flow appears good")
        
        logger.info("%s: score=%.2f, passed=%s, issues=%d", 
                   self.agent_name, score, passed, len(issues))
        
        return ReviewResult(
            agent=self.agent_name,
            score=score,
            passed=passed,
            issues=issues,
            recommendations=recommendations
        )


class RiskAssessorBot:
    """
    Flags commitments, risky statements, and dependencies that create liability.
    """
    
    def __init__(self, threshold: float = 0.8):
        self.threshold = threshold
        self.agent_name = "RiskAssessorBot"
    
    def evaluate(self, sections: Dict[str, str], context: Dict) -> ReviewResult:
        """
        Assess risk exposure in proposal language.
        
        Args:
            sections: Dict mapping section names to generated content
            context: Metadata
        
        Returns:
            ReviewResult with risk assessment
        """
        issues = []
        recommendations = []
        score = 1.0
        high_risk_items = []
        
        # Check 1: Absolute commitments (high risk)
        absolute_terms = [
            "guarantee", "guaranteed", "will never", "always", "100%",
            "zero downtime", "complete security", "impossible to",
            "never fails", "perfectly", "absolutely"
        ]
        
        for section_name, content in sections.items():
            for term in absolute_terms:
                if term.lower() in content.lower():
                    high_risk_items.append(f"{section_name}: Absolute commitment '{term}'")
                    score -= 0.1
        
        if high_risk_items:
            issues.append(f"Found {len(high_risk_items)} absolute commitments (high liability risk)")
            recommendations.append("Replace absolute terms with qualified language (e.g., 'designed to', 'typically', 'target')")
        
        # Check 2: Overpromising (performance claims)
        performance_claims = [
            r'\d+%\s+(?:increase|improvement|faster|better)',
            r'within\s+\d+\s+(?:hours?|days?|minutes?)',
            r'up to\s+\d+x',
        ]
        
        for section_name, content in sections.items():
            claim_count = sum(
                len(re.findall(pattern, content, re.IGNORECASE))
                for pattern in performance_claims
            )
            
            if claim_count > 3:
                issues.append(f"{section_name}: {claim_count} specific performance claims")
                recommendations.append(f"{section_name}: Ensure all performance claims are backed by data/references")
                score -= 0.05
        
        # Check 3: Unqualified future tense (creates obligations)
        risky_future = [
            "will deliver", "will provide", "will ensure", "will achieve",
            "will implement", "will complete", "will meet"
        ]
        
        future_commitments = []
        for section_name, content in sections.items():
            for phrase in risky_future:
                count = content.lower().count(phrase)
                if count > 0:
                    future_commitments.append((section_name, phrase, count))
        
        if len(future_commitments) > 5:
            issues.append(f"{len(future_commitments)} strong future commitments ('will' statements)")
            recommendations.append("Consider softening with 'designed to', 'intended to', 'plans to'")
            score -= 0.1
        
        # Check 4: Third-party dependencies without qualifications
        dependency_terms = [
            "vendor will", "partner will", "subcontractor will",
            "third party", "rely on", "dependent on"
        ]
        
        for section_name, content in sections.items():
            dep_count = sum(
                content.lower().count(term) for term in dependency_terms
            )
            
            if dep_count > 2:
                recommendations.append(f"{section_name}: Multiple third-party dependencies - ensure risks are mitigated")
                score -= 0.05
        
        # Check 5: Compliance gaps (missing disclaimers/qualifications)
        for section_name, content in sections.items():
            word_count = len(content.split())
            if word_count < 100:
                continue
            
            # Look for qualifying language
            qualifying_terms = [
                "subject to", "contingent", "pending", "proposed",
                "estimated", "approximate", "target", "goal"
            ]
            
            has_qualifiers = any(
                term.lower() in content.lower() 
                for term in qualifying_terms
            )
            
            # Check if section makes commitments but lacks qualifiers
            has_commitments = any(
                term in content.lower() 
                for term in ["will", "guarantee", "ensure", "deliver"]
            )
            
            if has_commitments and not has_qualifiers:
                recommendations.append(f"{section_name}: Contains commitments but lacks qualifying language")
                score -= 0.05
        
        # Check 6: Security/privacy absolute claims
        security_absolutes = [
            "unhackable", "impenetrable", "completely secure",
            "total privacy", "absolute security", "breach-proof"
        ]
        
        for section_name, content in sections.items():
            for term in security_absolutes:
                if term.lower() in content.lower():
                    issues.append(f"{section_name}: Unrealistic security claim '{term}'")
                    score -= 0.15
                    high_risk_items.append(f"{section_name}: Security absolute '{term}'")
        
        score = max(0.0, min(1.0, score))
        passed = score >= self.threshold
        
        if high_risk_items:
            issues.append(f"HIGH RISK: {len(high_risk_items)} critical items need review")
        
        if not issues:
            recommendations.append("Risk exposure appears acceptable")
        
        logger.info("%s: score=%.2f, passed=%s, issues=%d, high_risk=%d", 
                   self.agent_name, score, passed, len(issues), len(high_risk_items))
        
        return ReviewResult(
            agent=self.agent_name,
            score=score,
            passed=passed,
            issues=issues,
            recommendations=recommendations
        )


class PolicyAnalystBot:
    """
    Policy/stats and government guidance checker.
    Verifies alignment with current policies, regulations, and government guidance documents.
    """
    
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
        self.agent_name = "PolicyAnalystBot"
    
    def evaluate(self, sections: Dict[str, str], context: Dict) -> ReviewResult:
        """
        Assess policy alignment and use of government guidance.
        
        Args:
            sections: Dict mapping section names to generated content
            context: Metadata
        
        Returns:
            ReviewResult with policy assessment
        """
        issues = []
        recommendations = []
        score = 1.0
        
        # Check 1: References to current policies and regulations
        policy_indicators = [
            "FAR", "DFAR", "NIST", "FISMA", "FedRAMP", "OMB",
            "Executive Order", "E.O.", "CFR", "USC", "statute",
            "policy", "regulation", "directive", "memorandum"
        ]
        
        policy_references = 0
        for section_name, content in sections.items():
            refs_in_section = sum(
                1 for indicator in policy_indicators
                if indicator.lower() in content.lower()
            )
            policy_references += refs_in_section
        
        if policy_references == 0:
            issues.append("No references to federal policies or regulations found")
            recommendations.append("Add references to applicable FAR/DFAR clauses and federal policies")
            score -= 0.3
        elif policy_references < 3:
            recommendations.append("Consider adding more policy/regulation references for credibility")
            score -= 0.1
        
        # Check 2: Statistical claims should be cited
        stats_patterns = [
            r'\d+%',
            r'\d+x\s+(?:faster|better|more|less)',
            r'(?:increased|decreased|improved)\s+by\s+\d+',
        ]
        
        uncited_stats = []
        for section_name, content in sections.items():
            sentences = re.split(r'[.!?]+', content)
            for sent in sentences:
                has_stat = any(re.search(pattern, sent) for pattern in stats_patterns)
                has_citation = any(indicator in sent for indicator in ["[Source:", "[Ref:", "[Citation:", "according to"])
                
                if has_stat and not has_citation:
                    uncited_stats.append(section_name)
        
        if len(uncited_stats) > 2:
            issues.append(f"{len(uncited_stats)} sections contain uncited statistics")
            recommendations.append("All statistical claims should include sources")
            score -= 0.15
        
        # Check 3: Government guidance alignment keywords
        guidance_terms = [
            "zero trust", "cloud-first", "customer experience", "CX",
            "data-driven", "evidence-based", "agile", "DevSecOps",
            "AI/ML", "automation", "modernization", "digital transformation"
        ]
        
        guidance_alignment = 0
        for content in sections.values():
            for term in guidance_terms:
                if term.lower() in content.lower():
                    guidance_alignment += 1
                    break  # Count each section once
        
        if guidance_alignment < len(sections) * 0.3:
            recommendations.append("Consider referencing current government IT/digital guidance themes")
            score -= 0.05
        
        # Check 4: Policy version/date awareness (check for outdated terms)
        outdated_terms = [
            "FISMA 2002",  # Use FISMA 2014
            "NIST 800-53 Rev 4",  # Rev 5 is current
            "IPv4 only",
            "SHA-1",  # Deprecated
            "TLS 1.0", "TLS 1.1",  # Deprecated
        ]
        
        for section_name, content in sections.items():
            for term in outdated_terms:
                if term.lower() in content.lower():
                    issues.append(f"{section_name}: References potentially outdated standard '{term}'")
                    recommendations.append(f"{section_name}: Verify using current version of standards")
                    score -= 0.1
        
        # Check 5: Section L/M compliance indicators
        section_lm_terms = [
            "Section L", "Section M", "evaluation criteria",
            "evaluation factor", "subfactor", "selection criteria",
            "award factor", "technical merit"
        ]
        
        has_lm_references = any(
            any(term.lower() in content.lower() for term in section_lm_terms)
            for content in sections.values()
        )
        
        stage = context.get("stage", "").lower()
        if stage == "rfp" and not has_lm_references:
            recommendations.append("RFP response should reference Section L/M evaluation criteria")
            score -= 0.05
        
        # Check 6: Government agency-specific guidance
        agency_guidance = {
            "DoD": ["CMMC", "cybersecurity maturity", "DIB"],
            "DHS": ["CDM", "Einstein", "continuous diagnostics"],
            "GSA": ["MAS", "schedule", "GWAC"],
            "VA": ["VIP", "EHR modernization"],
        }
        
        # Check if opportunity is for specific agency (from context)
        opp_id = context.get("opportunity_id", "").upper()
        for agency, terms in agency_guidance.items():
            if agency in opp_id:
                has_agency_terms = any(
                    any(term.lower() in content.lower() for term in terms)
                    for content in sections.values()
                )
                if not has_agency_terms:
                    recommendations.append(f"Consider referencing {agency}-specific guidance and requirements")
        
        score = max(0.0, min(1.0, score))
        passed = score >= self.threshold
        
        if not issues:
            recommendations.append("Policy alignment appears good")
        
        logger.info("%s: score=%.2f, passed=%s, issues=%d", 
                   self.agent_name, score, passed, len(issues))
        
        return ReviewResult(
            agent=self.agent_name,
            score=score,
            passed=passed,
            issues=issues,
            recommendations=recommendations
        )
