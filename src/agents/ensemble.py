"""Ensemble agent that combines predictions from multiple models."""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import numpy as np
import logging
from dataclasses import dataclass

from .base_agent import BaseAgent, AgentSignal, SignalAction

logger = logging.getLogger(__name__)


@dataclass
class EnsembleConfig:
    """Configuration for ensemble agent."""
    min_agents_required: int = 3
    consensus_threshold: float = 0.6
    confidence_calibration: bool = True
    weight_by_accuracy: bool = True
    accuracy_window: int = 100


class EnsembleAgent(BaseAgent):
    """
    Combines predictions from multiple agents using weighted voting.
    
    Features:
    - Weighted voting based on historical accuracy
    - Confidence calibration
    - Model diversity tracking
    - Consensus scoring
    """
    
    def __init__(
        self,
        agents: List[BaseAgent],
        config: Optional[EnsembleConfig] = None
    ):
        super().__init__("ensemble", {})
        self.agents = agents
        self.config = config or EnsembleConfig()
        self.weights: Dict[str, float] = self._initialize_weights()
        self.performance_history: List[Dict[str, Any]] = []
        
    def _initialize_weights(self) -> Dict[str, float]:
        """Initialize equal weights for all agents."""
        if not self.agents:
            return {}
        n_agents = len(self.agents)
        return {agent.name: 1.0 / n_agents for agent in self.agents}
    
    async def analyze(self, data: Dict[str, Any]) -> AgentSignal:
        """
        Get predictions from all agents and combine them.
        
        Returns:
            AgentSignal with ensemble decision and confidence
        """
        if not self.agents:
            logger.error("No agents in ensemble")
            return AgentSignal(
                SignalAction.HOLD,
                0.5,
                {"error": "no_agents"},
                "ensemble"
            )
        
        # Update weights based on accuracy if enabled
        if self.config.weight_by_accuracy:
            await self._update_weights_from_performance()
        
        # Get predictions from all agents concurrently
        tasks = [
            self._analyze_with_timeout(agent, data)
            for agent in self.agents
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out failed predictions
        valid_signals: List[Tuple[str, AgentSignal]] = []
        for agent, result in zip(self.agents, results):
            if isinstance(result, Exception):
                self.logger.warning(f"Agent {agent.name} failed: {result}")
                continue
            if self.validate_signal(result):
                valid_signals.append((agent.name, result))
        
        # Check minimum agents
        if len(valid_signals) < self.config.min_agents_required:
            logger.error(
                f"Only {len(valid_signals)} agents responded, "
                f"need {self.config.min_agents_required}"
            )
            return AgentSignal(
                SignalAction.HOLD,
                0.5,
                {
                    "error": "insufficient_agents",
                    "responded": len(valid_signals),
                    "required": self.config.min_agents_required
                },
                "ensemble"
            )
        
        # Perform weighted voting
        weighted_votes = self._weighted_vote(valid_signals)
        final_action = weighted_votes['action']
        confidence = weighted_votes['confidence']
        
        # Calculate consensus score
        consensus = self._calculate_consensus(valid_signals)
        
        # Calibrate confidence if enabled
        if self.config.confidence_calibration:
            confidence = self._calibrate_confidence(confidence, consensus)
        
        metadata = {
            'individual_signals': {
                name: sig.to_dict() for name, sig in valid_signals
            },
            'weights': self.weights,
            'consensus_score': consensus,
            'num_agents_active': len(valid_signals),
            'total_agents': len(self.agents),
            'vote_distribution': weighted_votes.get('all_scores', {})
        }
        
        return AgentSignal(final_action, confidence, metadata, "ensemble")
    
    async def _analyze_with_timeout(
        self,
        agent: BaseAgent,
        data: Dict[str, Any]
    ) -> AgentSignal:
        """Analyze with timeout to prevent hanging."""
        try:
            return await asyncio.wait_for(
                agent.analyze(data),
                timeout=5.0  # 5 second timeout
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"Agent {agent.name} timed out")
    
    def _weighted_vote(
        self,
        signals: List[Tuple[str, AgentSignal]]
    ) -> Dict[str, Any]:
        """
        Perform weighted voting on agent signals.
        
        Strategy:
        1. Convert actions to scores (STRONG_BUY=2, BUY=1, HOLD=0, SELL=-1, STRONG_SELL=-2)
        2. Weight each score by agent weight and confidence
        3. Sum weighted scores
        4. Convert back to action
        """
        action_scores = {
            SignalAction.STRONG_BUY: 2,
            SignalAction.BUY: 1,
            SignalAction.HOLD: 0,
            SignalAction.SELL: -1,
            SignalAction.STRONG_SELL: -2
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for agent_name, signal in signals:
            weight = self.weights.get(agent_name, 0.1)
            weighted_confidence = signal.confidence * weight
            
            weighted_sum += action_scores[signal.action] * weighted_confidence
            total_weight += weighted_confidence
        
        # Normalize
        final_score = weighted_sum / total_weight if total_weight > 0 else 0
        
        # Convert score back to action
        if final_score >= 1.5:
            final_action = SignalAction.STRONG_BUY
        elif final_score >= 0.5:
            final_action = SignalAction.BUY
        elif final_score > -0.5:
            final_action = SignalAction.HOLD
        elif final_score > -1.5:
            final_action = SignalAction.SELL
        else:
            final_action = SignalAction.STRONG_SELL
        
        # Confidence based on score magnitude
        confidence = min(abs(final_score) / 2, 1.0)
        
        # Calculate vote distribution
        vote_counts = Counter(sig.action for _, sig in signals)
        
        return {
            'action': final_action,
            'confidence': confidence,
            'score': final_score,
            'all_scores': dict(vote_counts)
        }
    
    def _calculate_consensus(
        self,
        signals: List[Tuple[str, AgentSignal]]
    ) -> float:
        """Calculate how much agents agree with each other."""
        if len(signals) < 2:
            return 1.0
        
        # Group by action direction
        buys = sum(1 for _, sig in signals if sig.is_buy())
        sells = sum(1 for _, sig in signals if sig.is_sell())
        holds = sum(1 for _, sig in signals if sig.action == SignalAction.HOLD)
        
        # Consensus is % of agents in majority direction
        max_agreement = max(buys, sells, holds)
        return max_agreement / len(signals)
    
    def _calibrate_confidence(
        self,
        raw_confidence: float,
        consensus: float
    ) -> float:
        """
        Calibrate confidence based on consensus.
        
        High consensus should boost confidence, low consensus should reduce it.
        """
        # Weighted average of raw confidence and consensus
        calibration_factor = 0.7
        calibrated = (
            calibration_factor * raw_confidence +
            (1 - calibration_factor) * consensus
        )
        return min(calibrated, 1.0)
    
    async def _update_weights_from_performance(self) -> None:
        """Update agent weights based on recent accuracy."""
        try:
            # Get accuracy from each agent
            performances = {}
            for agent in self.agents:
                accuracy = agent.get_confidence_weighted_accuracy(
                    self.config.accuracy_window
                )
                performances[agent.name] = accuracy
            
            # Softmax weighting
            if performances:
                exp_scores = {
                    k: np.exp(max(v - 0.5, 0) * 4)  # Scale to accentuate differences
                    for k, v in performances.items()
                }
                total = sum(exp_scores.values())
                if total > 0:
                    self.weights = {k: v / total for k, v in exp_scores.items()}
        except Exception as e:
            self.logger.error(f"Failed to update weights: {e}")
    
    def initialize(self) -> None:
        """Initialize all child agents."""
        for agent in self.agents:
            try:
                agent.initialize()
                self.logger.info(f"Initialized agent: {agent.name}")
            except Exception as e:
                self.logger.error(f"Failed to initialize {agent.name}: {e}")
        
        self.is_initialized = True
        
    def get_agent_performance(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics for all agents."""
        return {
            agent.name: {
                "weight": self.weights.get(agent.name, 0),
                "accuracy": agent.get_accuracy(),
                "conf_weighted_accuracy": agent.get_confidence_weighted_accuracy()
            }
            for agent in self.agents
        }
