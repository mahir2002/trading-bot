"""Abstract base class for all trading agents."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SignalAction(Enum):
    """Trading signal actions."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class AgentSignal:
    """Standardized signal output from any agent."""
    action: SignalAction
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    agent_name: str = "unknown"
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")
        if self.timestamp is None:
            self.timestamp = __import__('time').time()
    
    def is_buy(self) -> bool:
        return self.action in (SignalAction.BUY, SignalAction.STRONG_BUY)
    
    def is_sell(self) -> bool:
        return self.action in (SignalAction.SELL, SignalAction.STRONG_SELL)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.value,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "agent_name": self.agent_name,
            "timestamp": self.timestamp
        }


class BaseAgent(ABC):
    """Abstract base class for trading agents."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"agents.{name}")
        self.is_initialized = False
        self._performance_history: List[Dict[str, Any]] = []
    
    @abstractmethod
    async def analyze(self, data: Dict[str, Any]) -> AgentSignal:
        """
        Analyze market data and return trading signal.
        
        Args:
            data: Market data including OHLCV, sentiment, etc.
            
        Returns:
            AgentSignal with action and confidence
        """
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize agent resources (models, data, etc.)."""
        pass
    
    def validate_signal(self, signal: AgentSignal) -> bool:
        """Validate that signal meets requirements."""
        if not isinstance(signal.action, SignalAction):
            return False
        if not 0 <= signal.confidence <= 1:
            return False
        return True
    
    def record_performance(self, prediction: AgentSignal, actual_return: float) -> None:
        """Record prediction accuracy for weight updates."""
        correct = (
            (prediction.is_buy() and actual_return > 0) or
            (prediction.is_sell() and actual_return < 0) or
            (prediction.action == SignalAction.HOLD and abs(actual_return) < 0.01)
        )
        
        self._performance_history.append({
            "correct": correct,
            "predicted": prediction.action.value,
            "actual_return": actual_return,
            "confidence": prediction.confidence,
            "timestamp": __import__('time').time()
        })
        
        # Keep last 1000 records
        if len(self._performance_history) > 1000:
            self._performance_history = self._performance_history[-1000:]
    
    def get_accuracy(self, window: int = 100) -> float:
        """Calculate recent accuracy."""
        if len(self._performance_history) < window:
            return 0.5
        
        recent = self._performance_history[-window:]
        correct = sum(1 for r in recent if r["correct"])
        return correct / len(recent)
    
    def get_confidence_weighted_accuracy(self, window: int = 100) -> float:
        """Calculate accuracy weighted by confidence."""
        if len(self._performance_history) < window:
            return 0.5
        
        recent = self._performance_history[-window:]
        weighted_correct = sum(
            r["confidence"] if r["correct"] else 0
            for r in recent
        )
        total_confidence = sum(r["confidence"] for r in recent)
        
        return weighted_correct / total_confidence if total_confidence > 0 else 0.5
