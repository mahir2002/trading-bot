#!/usr/bin/env python3
"""
📉 Drawdown Control Management System
Addresses: "Drawdown Control: Implement mechanisms to limit maximum drawdown."
Solution: Comprehensive drawdown control with multiple protection layers and dynamic adjustments
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod

class DrawdownSeverity(Enum):
    """Drawdown severity levels"""
    MINIMAL = "minimal"      # 0-2%
    LOW = "low"             # 2-5%
    MODERATE = "moderate"   # 5-10%
    HIGH = "high"           # 10-15%
    SEVERE = "severe"       # 15-20%
    CRITICAL = "critical"   # 20%+

class DrawdownAction(Enum):
    """Actions to take based on drawdown"""
    MONITOR = "monitor"
    REDUCE_EXPOSURE = "reduce_exposure"
    HALT_NEW_POSITIONS = "halt_new_positions"
    CLOSE_LOSING_POSITIONS = "close_losing_positions"
    EMERGENCY_LIQUIDATION = "emergency_liquidation"

class RecoveryPhase(Enum):
    """Portfolio recovery phases"""
    DRAWDOWN = "drawdown"
    STABILIZING = "stabilizing"
    RECOVERING = "recovering"
    RECOVERED = "recovered"

@dataclass
class DrawdownEvent:
    """Individual drawdown event tracking"""
    event_id: str
    start_time: datetime
    start_value: float
    peak_value: float
    trough_value: float
    current_value: float
    max_drawdown_pct: float
    current_drawdown_pct: float
    duration_hours: float
    severity: DrawdownSeverity
    is_active: bool = True
    end_time: Optional[datetime] = None
    recovery_time: Optional[datetime] = None
    actions_taken: List[str] = field(default_factory=list)

@dataclass
class DrawdownLimits:
    """Drawdown control limits and thresholds"""
    # Maximum drawdown limits
    max_daily_drawdown: float = 0.05      # 5% daily
    max_weekly_drawdown: float = 0.10     # 10% weekly
    max_monthly_drawdown: float = 0.15    # 15% monthly
    max_absolute_drawdown: float = 0.20   # 20% absolute maximum
    
    # Action thresholds
    reduce_exposure_threshold: float = 0.03    # 3% - start reducing exposure
    halt_new_positions_threshold: float = 0.05 # 5% - stop new positions
    close_losing_threshold: float = 0.08       # 8% - close losing positions
    emergency_liquidation_threshold: float = 0.15  # 15% - emergency stop
    
    # Recovery thresholds
    recovery_confirmation_pct: float = 0.02    # 2% gain to confirm recovery
    stabilization_period_hours: float = 24     # 24 hours stable to confirm
    
    # Position sizing adjustments
    drawdown_position_multipliers: Dict[DrawdownSeverity, float] = field(default_factory=lambda: {
        DrawdownSeverity.MINIMAL: 1.0,    # Normal sizing
        DrawdownSeverity.LOW: 0.8,        # 80% of normal
        DrawdownSeverity.MODERATE: 0.5,   # 50% of normal
        DrawdownSeverity.HIGH: 0.3,       # 30% of normal
        DrawdownSeverity.SEVERE: 0.1,     # 10% of normal
        DrawdownSeverity.CRITICAL: 0.0    # No new positions
    })

@dataclass
class PortfolioSnapshot:
    """Portfolio state snapshot for drawdown tracking"""
    timestamp: datetime
    total_value: float
    cash_balance: float
    position_value: float
    unrealized_pnl: float
    realized_pnl_today: float
    open_positions: int
    daily_high: float
    daily_low: float
    weekly_high: float
    monthly_high: float

class DrawdownCalculator:
    """Advanced drawdown calculation methods"""
    
    @staticmethod
    def calculate_drawdown_metrics(equity_curve: List[float]) -> Dict[str, float]:
        """Calculate comprehensive drawdown metrics"""
        if len(equity_curve) < 2:
            return {
                'max_drawdown': 0.0,
                'current_drawdown': 0.0,
                'avg_drawdown': 0.0,
                'drawdown_duration': 0,
                'recovery_factor': 1.0,
                'pain_index': 0.0
            }
        
        equity_series = pd.Series(equity_curve)
        
        # Calculate running maximum (peak)
        running_max = equity_series.expanding().max()
        
        # Calculate drawdown series
        drawdown_series = (equity_series - running_max) / running_max
        
        # Maximum drawdown
        max_drawdown = abs(drawdown_series.min())
        
        # Current drawdown
        current_drawdown = abs(drawdown_series.iloc[-1])
        
        # Average drawdown
        negative_drawdowns = drawdown_series[drawdown_series < 0]
        avg_drawdown = abs(negative_drawdowns.mean()) if len(negative_drawdowns) > 0 else 0.0
        
        # Drawdown duration (periods in drawdown)
        in_drawdown = drawdown_series < -0.001  # More than 0.1% drawdown
        drawdown_duration = in_drawdown.sum()
        
        # Recovery factor (how quickly portfolio recovers)
        if max_drawdown > 0:
            recovery_factor = (equity_series.iloc[-1] / equity_series.max()) / (1 - max_drawdown)
        else:
            recovery_factor = 1.0
        
        # Pain index (average drawdown over time)
        pain_index = abs(drawdown_series.mean())
        
        return {
            'max_drawdown': max_drawdown,
            'current_drawdown': current_drawdown,
            'avg_drawdown': avg_drawdown,
            'drawdown_duration': drawdown_duration,
            'recovery_factor': recovery_factor,
            'pain_index': pain_index
        }
    
    @staticmethod
    def classify_drawdown_severity(drawdown_pct: float) -> DrawdownSeverity:
        """Classify drawdown severity"""
        if drawdown_pct < 0.02:
            return DrawdownSeverity.MINIMAL
        elif drawdown_pct < 0.05:
            return DrawdownSeverity.LOW
        elif drawdown_pct < 0.10:
            return DrawdownSeverity.MODERATE
        elif drawdown_pct < 0.15:
            return DrawdownSeverity.HIGH
        elif drawdown_pct < 0.20:
            return DrawdownSeverity.SEVERE
        else:
            return DrawdownSeverity.CRITICAL
    
    @staticmethod
    def calculate_time_based_drawdowns(snapshots: List[PortfolioSnapshot]) -> Dict[str, float]:
        """Calculate time-based drawdown metrics"""
        if not snapshots:
            return {'daily': 0.0, 'weekly': 0.0, 'monthly': 0.0}
        
        current_value = snapshots[-1].total_value
        
        # Daily drawdown
        daily_high = max(s.daily_high for s in snapshots[-24:] if s.daily_high)  # Last 24 hours
        daily_drawdown = (daily_high - current_value) / daily_high if daily_high > 0 else 0.0
        
        # Weekly drawdown
        weekly_high = max(s.weekly_high for s in snapshots[-168:] if s.weekly_high)  # Last 168 hours
        weekly_drawdown = (weekly_high - current_value) / weekly_high if weekly_high > 0 else 0.0
        
        # Monthly drawdown
        monthly_high = max(s.monthly_high for s in snapshots[-720:] if s.monthly_high)  # Last 720 hours
        monthly_drawdown = (monthly_high - current_value) / monthly_high if monthly_high > 0 else 0.0
        
        return {
            'daily': max(0, daily_drawdown),
            'weekly': max(0, weekly_drawdown),
            'monthly': max(0, monthly_drawdown)
        }

class DrawdownControlManager:
    """Comprehensive drawdown control and management system"""
    
    def __init__(self, initial_capital: float = 100000, limits: Optional[DrawdownLimits] = None, 
                 logger: Optional[logging.Logger] = None):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.limits = limits or DrawdownLimits()
        self.logger = logger or self._setup_logger()
        
        # Portfolio tracking
        self.portfolio_snapshots: List[PortfolioSnapshot] = []
        self.equity_curve: List[float] = [initial_capital]
        self.daily_highs: List[float] = [initial_capital]
        self.weekly_highs: List[float] = [initial_capital]
        self.monthly_highs: List[float] = [initial_capital]
        
        # Drawdown tracking
        self.active_drawdown_events: Dict[str, DrawdownEvent] = {}
        self.historical_drawdown_events: List[DrawdownEvent] = []
        self.current_drawdown_severity = DrawdownSeverity.MINIMAL
        self.recovery_phase = RecoveryPhase.RECOVERED
        
        # Control states
        self.emergency_mode = False
        self.new_positions_halted = False
        self.exposure_reduction_active = False
        self.last_action_time = datetime.now()
        
        # Performance tracking
        self.drawdown_statistics = {}
        self.protection_actions_taken = []
        self.recovery_events = []
        
        self.logger.info(f"🛡️ Drawdown Control Manager initialized with ${initial_capital:,.2f} capital")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for drawdown control"""
        logger = logging.getLogger('DrawdownControl')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def update_portfolio_value(self, total_value: float, cash_balance: float = 0, 
                             position_value: float = 0, unrealized_pnl: float = 0,
                             realized_pnl_today: float = 0, open_positions: int = 0):
        """Update portfolio value and check for drawdown triggers"""
        
        current_time = datetime.now()
        
        # Update equity curve
        self.current_capital = total_value
        self.equity_curve.append(total_value)
        
        # Update time-based highs
        self._update_time_based_highs(total_value, current_time)
        
        # Create portfolio snapshot
        snapshot = PortfolioSnapshot(
            timestamp=current_time,
            total_value=total_value,
            cash_balance=cash_balance,
            position_value=position_value,
            unrealized_pnl=unrealized_pnl,
            realized_pnl_today=realized_pnl_today,
            open_positions=open_positions,
            daily_high=self.daily_highs[-1],
            daily_low=min(self.equity_curve[-24:]) if len(self.equity_curve) >= 24 else total_value,
            weekly_high=self.weekly_highs[-1],
            monthly_high=self.monthly_highs[-1]
        )
        
        self.portfolio_snapshots.append(snapshot)
        
        # Limit snapshot history (keep last 30 days)
        if len(self.portfolio_snapshots) > 720:  # 30 days * 24 hours
            self.portfolio_snapshots = self.portfolio_snapshots[-720:]
        
        # Check for drawdown triggers
        self._check_drawdown_triggers(snapshot)
        
        # Update recovery phase
        self._update_recovery_phase(snapshot)
        
        self.logger.debug(f"Portfolio updated: ${total_value:,.2f}, Drawdown: {self.get_current_drawdown():.2%}")
    
    def _update_time_based_highs(self, current_value: float, current_time: datetime):
        """Update daily, weekly, and monthly highs"""
        
        # Daily high (reset every 24 hours)
        if len(self.portfolio_snapshots) == 0 or \
           (current_time - self.portfolio_snapshots[-1].timestamp).total_seconds() >= 86400:
            self.daily_highs.append(current_value)
        else:
            self.daily_highs[-1] = max(self.daily_highs[-1], current_value)
        
        # Weekly high (reset every 7 days)
        if len(self.portfolio_snapshots) == 0 or \
           (current_time - self.portfolio_snapshots[0].timestamp).total_seconds() >= 604800:
            self.weekly_highs.append(current_value)
        else:
            self.weekly_highs[-1] = max(self.weekly_highs[-1], current_value)
        
        # Monthly high (reset every 30 days)
        if len(self.portfolio_snapshots) == 0 or \
           (current_time - self.portfolio_snapshots[0].timestamp).total_seconds() >= 2592000:
            self.monthly_highs.append(current_value)
        else:
            self.monthly_highs[-1] = max(self.monthly_highs[-1], current_value)
    
    def _check_drawdown_triggers(self, snapshot: PortfolioSnapshot):
        """Check if drawdown triggers any protective actions"""
        
        # Calculate current drawdowns
        drawdown_metrics = self.get_drawdown_metrics()
        current_dd = drawdown_metrics['current_drawdown']
        
        # Calculate time-based drawdowns
        time_drawdowns = DrawdownCalculator.calculate_time_based_drawdowns(self.portfolio_snapshots)
        
        # Check absolute drawdown limits
        if current_dd >= self.limits.emergency_liquidation_threshold:
            self._trigger_emergency_liquidation(current_dd)
        elif current_dd >= self.limits.close_losing_threshold:
            self._trigger_close_losing_positions(current_dd)
        elif current_dd >= self.limits.halt_new_positions_threshold:
            self._trigger_halt_new_positions(current_dd)
        elif current_dd >= self.limits.reduce_exposure_threshold:
            self._trigger_reduce_exposure(current_dd)
        
        # Check time-based limits
        if time_drawdowns['daily'] >= self.limits.max_daily_drawdown:
            self._trigger_daily_limit_breach(time_drawdowns['daily'])
        elif time_drawdowns['weekly'] >= self.limits.max_weekly_drawdown:
            self._trigger_weekly_limit_breach(time_drawdowns['weekly'])
        elif time_drawdowns['monthly'] >= self.limits.max_monthly_drawdown:
            self._trigger_monthly_limit_breach(time_drawdowns['monthly'])
        
        # Update drawdown severity
        self.current_drawdown_severity = DrawdownCalculator.classify_drawdown_severity(current_dd)
        
        # Track active drawdown events
        self._track_drawdown_events(snapshot, current_dd)
    
    def _trigger_emergency_liquidation(self, drawdown_pct: float):
        """Trigger emergency liquidation procedures"""
        if not self.emergency_mode:
            self.emergency_mode = True
            action = f"EMERGENCY LIQUIDATION triggered at {drawdown_pct:.2%} drawdown"
            self.protection_actions_taken.append({
                'timestamp': datetime.now(),
                'action': 'emergency_liquidation',
                'drawdown': drawdown_pct,
                'description': action
            })
            self.logger.critical(f"🚨 {action}")
    
    def _trigger_close_losing_positions(self, drawdown_pct: float):
        """Trigger closing of losing positions"""
        action = f"CLOSE LOSING POSITIONS triggered at {drawdown_pct:.2%} drawdown"
        self.protection_actions_taken.append({
            'timestamp': datetime.now(),
            'action': 'close_losing_positions',
            'drawdown': drawdown_pct,
            'description': action
        })
        self.logger.warning(f"⚠️ {action}")
    
    def _trigger_halt_new_positions(self, drawdown_pct: float):
        """Trigger halt of new position opening"""
        if not self.new_positions_halted:
            self.new_positions_halted = True
            action = f"NEW POSITIONS HALTED at {drawdown_pct:.2%} drawdown"
            self.protection_actions_taken.append({
                'timestamp': datetime.now(),
                'action': 'halt_new_positions',
                'drawdown': drawdown_pct,
                'description': action
            })
            self.logger.warning(f"🛑 {action}")
    
    def _trigger_reduce_exposure(self, drawdown_pct: float):
        """Trigger exposure reduction"""
        if not self.exposure_reduction_active:
            self.exposure_reduction_active = True
            action = f"EXPOSURE REDUCTION activated at {drawdown_pct:.2%} drawdown"
            self.protection_actions_taken.append({
                'timestamp': datetime.now(),
                'action': 'reduce_exposure',
                'drawdown': drawdown_pct,
                'description': action
            })
            self.logger.info(f"📉 {action}")
    
    def _trigger_daily_limit_breach(self, daily_drawdown: float):
        """Handle daily drawdown limit breach"""
        action = f"DAILY LIMIT BREACH: {daily_drawdown:.2%} daily drawdown"
        self.protection_actions_taken.append({
            'timestamp': datetime.now(),
            'action': 'daily_limit_breach',
            'drawdown': daily_drawdown,
            'description': action
        })
        self.logger.error(f"🚫 {action}")
    
    def _trigger_weekly_limit_breach(self, weekly_drawdown: float):
        """Handle weekly drawdown limit breach"""
        action = f"WEEKLY LIMIT BREACH: {weekly_drawdown:.2%} weekly drawdown"
        self.protection_actions_taken.append({
            'timestamp': datetime.now(),
            'action': 'weekly_limit_breach',
            'drawdown': weekly_drawdown,
            'description': action
        })
        self.logger.error(f"🚫 {action}")
    
    def _trigger_monthly_limit_breach(self, monthly_drawdown: float):
        """Handle monthly drawdown limit breach"""
        action = f"MONTHLY LIMIT BREACH: {monthly_drawdown:.2%} monthly drawdown"
        self.protection_actions_taken.append({
            'timestamp': datetime.now(),
            'action': 'monthly_limit_breach',
            'drawdown': monthly_drawdown,
            'description': action
        })
        self.logger.error(f"🚫 {action}")
    
    def _track_drawdown_events(self, snapshot: PortfolioSnapshot, current_drawdown: float):
        """Track individual drawdown events"""
        
        # Check if we're in a new drawdown
        if current_drawdown > 0.001 and not self.active_drawdown_events:  # More than 0.1%
            # Start new drawdown event
            event_id = f"dd_{int(time.time())}"
            peak_value = max(self.equity_curve) if self.equity_curve else snapshot.total_value
            
            event = DrawdownEvent(
                event_id=event_id,
                start_time=snapshot.timestamp,
                start_value=snapshot.total_value,
                peak_value=peak_value,
                trough_value=snapshot.total_value,
                current_value=snapshot.total_value,
                max_drawdown_pct=current_drawdown,
                current_drawdown_pct=current_drawdown,
                duration_hours=0,
                severity=DrawdownCalculator.classify_drawdown_severity(current_drawdown)
            )
            
            self.active_drawdown_events[event_id] = event
            self.logger.info(f"📉 New drawdown event started: {event_id} at {current_drawdown:.2%}")
        
        # Update active drawdown events
        for event_id, event in self.active_drawdown_events.items():
            event.current_value = snapshot.total_value
            event.current_drawdown_pct = current_drawdown
            event.max_drawdown_pct = max(event.max_drawdown_pct, current_drawdown)
            event.trough_value = min(event.trough_value, snapshot.total_value)
            event.duration_hours = (snapshot.timestamp - event.start_time).total_seconds() / 3600
            event.severity = DrawdownCalculator.classify_drawdown_severity(event.max_drawdown_pct)
        
        # Check for drawdown recovery
        if current_drawdown < 0.001 and self.active_drawdown_events:  # Less than 0.1%
            for event_id, event in list(self.active_drawdown_events.items()):
                event.is_active = False
                event.end_time = snapshot.timestamp
                event.recovery_time = snapshot.timestamp
                
                self.historical_drawdown_events.append(event)
                del self.active_drawdown_events[event_id]
                
                self.logger.info(f"📈 Drawdown event recovered: {event_id}, "
                               f"Max DD: {event.max_drawdown_pct:.2%}, "
                               f"Duration: {event.duration_hours:.1f}h")
    
    def _update_recovery_phase(self, snapshot: PortfolioSnapshot):
        """Update portfolio recovery phase"""
        
        current_drawdown = self.get_current_drawdown()
        
        if current_drawdown > 0.05:  # 5%+
            self.recovery_phase = RecoveryPhase.DRAWDOWN
        elif current_drawdown > 0.02:  # 2-5%
            self.recovery_phase = RecoveryPhase.STABILIZING
        elif current_drawdown > 0.005:  # 0.5-2%
            self.recovery_phase = RecoveryPhase.RECOVERING
        else:
            if self.recovery_phase != RecoveryPhase.RECOVERED:
                self.recovery_phase = RecoveryPhase.RECOVERED
                self._reset_protection_measures()
    
    def _reset_protection_measures(self):
        """Reset protection measures after recovery"""
        self.emergency_mode = False
        self.new_positions_halted = False
        self.exposure_reduction_active = False
        
        self.recovery_events.append({
            'timestamp': datetime.now(),
            'description': 'Portfolio recovered - protection measures reset'
        })
        
        self.logger.info("✅ Portfolio recovered - protection measures reset")
    
    def get_current_drawdown(self) -> float:
        """Get current drawdown percentage"""
        if len(self.equity_curve) < 2:
            return 0.0
        
        peak = max(self.equity_curve)
        current = self.equity_curve[-1]
        return (peak - current) / peak if peak > 0 else 0.0
    
    def get_drawdown_metrics(self) -> Dict[str, float]:
        """Get comprehensive drawdown metrics"""
        return DrawdownCalculator.calculate_drawdown_metrics(self.equity_curve)
    
    def get_position_size_multiplier(self) -> float:
        """Get position size multiplier based on current drawdown"""
        return self.limits.drawdown_position_multipliers.get(
            self.current_drawdown_severity, 1.0
        )
    
    def should_allow_new_positions(self) -> Tuple[bool, str]:
        """Check if new positions should be allowed"""
        
        if self.emergency_mode:
            return False, "Emergency mode active"
        
        if self.new_positions_halted:
            return False, f"New positions halted due to {self.get_current_drawdown():.2%} drawdown"
        
        current_dd = self.get_current_drawdown()
        if current_dd >= self.limits.halt_new_positions_threshold:
            return False, f"Drawdown limit exceeded: {current_dd:.2%}"
        
        # Check time-based limits
        time_drawdowns = DrawdownCalculator.calculate_time_based_drawdowns(self.portfolio_snapshots)
        
        if time_drawdowns['daily'] >= self.limits.max_daily_drawdown:
            return False, f"Daily drawdown limit exceeded: {time_drawdowns['daily']:.2%}"
        
        return True, "New positions allowed"
    
    def should_reduce_exposure(self) -> Tuple[bool, float]:
        """Check if exposure should be reduced and by how much"""
        
        current_dd = self.get_current_drawdown()
        
        if current_dd >= self.limits.reduce_exposure_threshold:
            # Calculate reduction percentage based on drawdown severity
            if current_dd >= self.limits.close_losing_threshold:
                return True, 0.7  # Reduce by 70%
            elif current_dd >= self.limits.halt_new_positions_threshold:
                return True, 0.5  # Reduce by 50%
            else:
                return True, 0.3  # Reduce by 30%
        
        return False, 0.0
    
    def get_recommended_actions(self) -> List[Dict[str, Any]]:
        """Get recommended actions based on current drawdown state"""
        
        actions = []
        current_dd = self.get_current_drawdown()
        time_drawdowns = DrawdownCalculator.calculate_time_based_drawdowns(self.portfolio_snapshots)
        
        # Emergency actions
        if current_dd >= self.limits.emergency_liquidation_threshold:
            actions.append({
                'priority': 'CRITICAL',
                'action': 'emergency_liquidation',
                'description': f'Emergency liquidation required - {current_dd:.2%} drawdown',
                'immediate': True
            })
        
        # Position management actions
        elif current_dd >= self.limits.close_losing_threshold:
            actions.append({
                'priority': 'HIGH',
                'action': 'close_losing_positions',
                'description': f'Close losing positions - {current_dd:.2%} drawdown',
                'immediate': True
            })
        
        elif current_dd >= self.limits.halt_new_positions_threshold:
            actions.append({
                'priority': 'MEDIUM',
                'action': 'halt_new_positions',
                'description': f'Halt new positions - {current_dd:.2%} drawdown',
                'immediate': False
            })
        
        elif current_dd >= self.limits.reduce_exposure_threshold:
            actions.append({
                'priority': 'LOW',
                'action': 'reduce_exposure',
                'description': f'Reduce exposure - {current_dd:.2%} drawdown',
                'immediate': False
            })
        
        # Time-based limit actions
        if time_drawdowns['daily'] >= self.limits.max_daily_drawdown:
            actions.append({
                'priority': 'HIGH',
                'action': 'daily_limit_breach',
                'description': f'Daily limit breached - {time_drawdowns["daily"]:.2%}',
                'immediate': True
            })
        
        return actions
    
    def get_drawdown_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive drawdown control dashboard"""
        
        current_dd = self.get_current_drawdown()
        metrics = self.get_drawdown_metrics()
        time_drawdowns = DrawdownCalculator.calculate_time_based_drawdowns(self.portfolio_snapshots)
        allow_positions, position_reason = self.should_allow_new_positions()
        reduce_exposure, reduction_pct = self.should_reduce_exposure()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'portfolio': {
                'current_value': self.current_capital,
                'initial_value': self.initial_capital,
                'total_return': (self.current_capital / self.initial_capital - 1),
                'recovery_phase': self.recovery_phase.value
            },
            'drawdown_metrics': {
                'current_drawdown': f"{current_dd:.2%}",
                'max_drawdown': f"{metrics['max_drawdown']:.2%}",
                'avg_drawdown': f"{metrics['avg_drawdown']:.2%}",
                'pain_index': f"{metrics['pain_index']:.2%}",
                'recovery_factor': f"{metrics['recovery_factor']:.2f}",
                'drawdown_duration': f"{metrics['drawdown_duration']:.0f} periods"
            },
            'time_based_drawdowns': {
                'daily': f"{time_drawdowns['daily']:.2%}",
                'weekly': f"{time_drawdowns['weekly']:.2%}",
                'monthly': f"{time_drawdowns['monthly']:.2%}"
            },
            'severity': {
                'current_severity': self.current_drawdown_severity.value,
                'position_multiplier': f"{self.get_position_size_multiplier():.1%}"
            },
            'limits': {
                'max_daily': f"{self.limits.max_daily_drawdown:.1%}",
                'max_weekly': f"{self.limits.max_weekly_drawdown:.1%}",
                'max_monthly': f"{self.limits.max_monthly_drawdown:.1%}",
                'max_absolute': f"{self.limits.max_absolute_drawdown:.1%}"
            },
            'controls': {
                'emergency_mode': self.emergency_mode,
                'new_positions_halted': self.new_positions_halted,
                'exposure_reduction_active': self.exposure_reduction_active,
                'allow_new_positions': allow_positions,
                'position_restriction_reason': position_reason,
                'should_reduce_exposure': reduce_exposure,
                'exposure_reduction_pct': f"{reduction_pct:.1%}"
            },
            'active_events': {
                'active_drawdown_events': len(self.active_drawdown_events),
                'total_historical_events': len(self.historical_drawdown_events),
                'protection_actions_taken': len(self.protection_actions_taken),
                'recovery_events': len(self.recovery_events)
            },
            'recommended_actions': self.get_recommended_actions()
        }
    
    def get_historical_analysis(self) -> Dict[str, Any]:
        """Get historical drawdown analysis"""
        
        if not self.historical_drawdown_events:
            return {'message': 'No historical drawdown events'}
        
        # Analyze historical events
        max_historical_dd = max(event.max_drawdown_pct for event in self.historical_drawdown_events)
        avg_historical_dd = np.mean([event.max_drawdown_pct for event in self.historical_drawdown_events])
        avg_duration = np.mean([event.duration_hours for event in self.historical_drawdown_events])
        
        # Severity distribution
        severity_counts = {}
        for event in self.historical_drawdown_events:
            severity = event.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'total_events': len(self.historical_drawdown_events),
            'max_historical_drawdown': f"{max_historical_dd:.2%}",
            'avg_historical_drawdown': f"{avg_historical_dd:.2%}",
            'avg_duration_hours': f"{avg_duration:.1f}",
            'severity_distribution': severity_counts,
            'recent_events': [
                {
                    'event_id': event.event_id,
                    'max_drawdown': f"{event.max_drawdown_pct:.2%}",
                    'duration_hours': f"{event.duration_hours:.1f}",
                    'severity': event.severity.value,
                    'start_time': event.start_time.isoformat()
                }
                for event in self.historical_drawdown_events[-5:]  # Last 5 events
            ]
        }

# Convenience functions for easy integration
def create_drawdown_protected_position(symbol: str, base_position_size: float, 
                                     drawdown_manager: DrawdownControlManager) -> float:
    """Create position with drawdown protection"""
    
    # Get position size multiplier based on current drawdown
    multiplier = drawdown_manager.get_position_size_multiplier()
    
    # Check if new positions are allowed
    allow_positions, reason = drawdown_manager.should_allow_new_positions()
    
    if not allow_positions:
        return 0.0  # No position allowed
    
    # Apply drawdown-based position sizing
    protected_size = base_position_size * multiplier
    
    return protected_size

def setup_drawdown_monitoring(initial_capital: float = 100000, 
                            custom_limits: Optional[Dict] = None) -> DrawdownControlManager:
    """Setup drawdown monitoring with custom limits"""
    
    limits = DrawdownLimits()
    
    if custom_limits:
        for key, value in custom_limits.items():
            if hasattr(limits, key):
                setattr(limits, key, value)
    
    return DrawdownControlManager(initial_capital=initial_capital, limits=limits)

if __name__ == "__main__":
    # Example usage and testing
    print("🛡️ Drawdown Control Manager - Testing")
    
    # Create manager with custom limits
    custom_limits = {
        'max_daily_drawdown': 0.03,      # 3% daily limit
        'max_absolute_drawdown': 0.15,   # 15% absolute limit
        'reduce_exposure_threshold': 0.02 # 2% exposure reduction trigger
    }
    
    manager = setup_drawdown_monitoring(100000, custom_limits)
    
    # Simulate portfolio performance with drawdown
    print("\n📊 Simulating Portfolio Performance...")
    
    # Phase 1: Normal performance
    for day in range(10):
        change = np.random.normal(0.001, 0.01)  # Small positive drift
        new_value = manager.current_capital * (1 + change)
        manager.update_portfolio_value(new_value)
    
    print(f"Phase 1 Complete - Value: ${manager.current_capital:,.2f}")
    
    # Phase 2: Drawdown period
    print("\n📉 Simulating Drawdown Period...")
    for day in range(15):
        change = np.random.normal(-0.02, 0.015)  # Negative drift
        new_value = manager.current_capital * (1 + change)
        manager.update_portfolio_value(new_value)
        
        if day % 5 == 0:
            dashboard = manager.get_drawdown_dashboard()
            print(f"   Day {day}: DD={dashboard['drawdown_metrics']['current_drawdown']}, "
                  f"Severity={dashboard['severity']['current_severity']}")
    
    # Phase 3: Recovery
    print("\n📈 Simulating Recovery...")
    for day in range(10):
        change = np.random.normal(0.015, 0.01)  # Positive recovery
        new_value = manager.current_capital * (1 + change)
        manager.update_portfolio_value(new_value)
    
    # Final dashboard
    print("\n📊 FINAL DRAWDOWN DASHBOARD")
    print("=" * 40)
    
    dashboard = manager.get_drawdown_dashboard()
    
    print(f"💰 Portfolio Status:")
    print(f"   Current Value: ${dashboard['portfolio']['current_value']:,.2f}")
    print(f"   Total Return: {dashboard['portfolio']['total_return']:.1%}")
    print(f"   Recovery Phase: {dashboard['portfolio']['recovery_phase'].upper()}")
    
    print(f"\n📉 Drawdown Metrics:")
    print(f"   Current Drawdown: {dashboard['drawdown_metrics']['current_drawdown']}")
    print(f"   Max Drawdown: {dashboard['drawdown_metrics']['max_drawdown']}")
    print(f"   Pain Index: {dashboard['drawdown_metrics']['pain_index']}")
    print(f"   Recovery Factor: {dashboard['drawdown_metrics']['recovery_factor']}")
    
    print(f"\n⏰ Time-Based Drawdowns:")
    print(f"   Daily: {dashboard['time_based_drawdowns']['daily']}")
    print(f"   Weekly: {dashboard['time_based_drawdowns']['weekly']}")
    print(f"   Monthly: {dashboard['time_based_drawdowns']['monthly']}")
    
    print(f"\n🚨 Control Status:")
    print(f"   Emergency Mode: {dashboard['controls']['emergency_mode']}")
    print(f"   New Positions Allowed: {dashboard['controls']['allow_new_positions']}")
    print(f"   Exposure Reduction: {dashboard['controls']['should_reduce_exposure']}")
    print(f"   Position Multiplier: {dashboard['severity']['position_multiplier']}")
    
    print(f"\n📋 Event Summary:")
    print(f"   Active Events: {dashboard['active_events']['active_drawdown_events']}")
    print(f"   Historical Events: {dashboard['active_events']['total_historical_events']}")
    print(f"   Protection Actions: {dashboard['active_events']['protection_actions_taken']}")
    
    # Show recommended actions
    if dashboard['recommended_actions']:
        print(f"\n⚡ Recommended Actions:")
        for action in dashboard['recommended_actions']:
            print(f"   {action['priority']}: {action['description']}")
    
    # Historical analysis
    historical = manager.get_historical_analysis()
    if 'total_events' in historical:
        print(f"\n📈 Historical Analysis:")
        print(f"   Total Events: {historical['total_events']}")
        print(f"   Max Historical DD: {historical['max_historical_drawdown']}")
        print(f"   Avg Duration: {historical['avg_duration_hours']} hours") 