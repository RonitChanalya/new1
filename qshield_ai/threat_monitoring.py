# threat_monitoring.py
"""
Real-time Threat Monitoring and Response System
Monitors model performance, detects drift, and triggers adaptive responses
"""
import numpy as np
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from collections import deque
import threading
import logging

class ThreatMonitoringSystem:
    """Real-time monitoring and adaptive response system"""
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.performance_history = deque(maxlen=window_size)
        self.threat_history = deque(maxlen=window_size)
        self.drift_alerts = deque(maxlen=100)
        self.adaptive_responses = []
        
        # Performance thresholds
        self.performance_thresholds = {
            'accuracy_drop': 0.05,  # 5% accuracy drop triggers alert
            'drift_threshold': 2.0,  # Z-score threshold for drift
            'uncertainty_threshold': 0.3,  # High uncertainty threshold
            'response_time_threshold': 0.1  # 100ms response time threshold
        }
        
        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread = None
        self.last_model_update = time.time()
        
    def start_monitoring(self):
        """Start real-time monitoring"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logging.info("[ThreatMonitoring] Started real-time monitoring")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logging.info("[ThreatMonitoring] Stopped monitoring")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                self._check_performance_drift()
                self._check_model_degradation()
                self._check_adaptive_threats()
                time.sleep(1)  # Check every second
            except Exception as e:
                logging.error(f"[ThreatMonitoring] Error in monitor loop: {e}")
                time.sleep(5)
    
    def log_prediction(self, prediction_data: Dict):
        """Log a prediction for monitoring"""
        self.performance_history.append({
            'timestamp': time.time(),
            'risk_score': prediction_data.get('risk_score', 0),
            'uncertainty': prediction_data.get('uncertainty_score', 0),
            'response_time': prediction_data.get('response_time', 0),
            'features': prediction_data.get('features', []),
            'model_version': prediction_data.get('model_version', 'unknown')
        })
    
    def log_threat_event(self, threat_data: Dict):
        """Log a detected threat event"""
        self.threat_history.append({
            'timestamp': time.time(),
            'threat_level': threat_data.get('threat_level', 'unknown'),
            'risk_score': threat_data.get('risk_score', 0),
            'action_taken': threat_data.get('action', 'none'),
            'features': threat_data.get('features', []),
            'confidence': threat_data.get('confidence', 0)
        })
    
    def _check_performance_drift(self):
        """Check for performance degradation"""
        if len(self.performance_history) < 50:
            return
        
        recent_performance = list(self.performance_history)[-50:]
        older_performance = list(self.performance_history)[-100:-50] if len(self.performance_history) >= 100 else []
        
        if not older_performance:
            return
        
        # Calculate performance metrics
        recent_uncertainty = np.mean([p['uncertainty'] for p in recent_performance])
        older_uncertainty = np.mean([p['uncertainty'] for p in older_performance])
        
        recent_response_time = np.mean([p['response_time'] for p in recent_performance])
        
        # Check for performance degradation
        uncertainty_increase = recent_uncertainty - older_uncertainty
        
        if uncertainty_increase > self.performance_thresholds['accuracy_drop']:
            self._trigger_drift_alert('performance_degradation', {
                'uncertainty_increase': uncertainty_increase,
                'recent_uncertainty': recent_uncertainty,
                'older_uncertainty': older_uncertainty
            })
        
        if recent_response_time > self.performance_thresholds['response_time_threshold']:
            self._trigger_drift_alert('response_time_degradation', {
                'response_time': recent_response_time,
                'threshold': self.performance_thresholds['response_time_threshold']
            })
    
    def _check_model_degradation(self):
        """Check for model degradation patterns"""
        if len(self.performance_history) < 100:
            return
        
        recent_data = list(self.performance_history)[-100:]
        
        # Check for increasing uncertainty trend
        uncertainties = [p['uncertainty'] for p in recent_data]
        uncertainty_trend = np.polyfit(range(len(uncertainties)), uncertainties, 1)[0]
        
        if uncertainty_trend > 0.01:  # Increasing uncertainty
            self._trigger_drift_alert('model_degradation', {
                'uncertainty_trend': uncertainty_trend,
                'current_uncertainty': uncertainties[-1]
            })
        
        # Check for score distribution changes
        risk_scores = [p['risk_score'] for p in recent_data]
        score_std = np.std(risk_scores)
        
        if score_std > 30:  # High variance in predictions
            self._trigger_drift_alert('prediction_instability', {
                'score_std': score_std,
                'score_range': [min(risk_scores), max(risk_scores)]
            })
    
    def _check_adaptive_threats(self):
        """Check for adaptive threat patterns"""
        if len(self.threat_history) < 50:
            return
        
        recent_threats = list(self.threat_history)[-50:]
        
        # Check for evasion attempts
        blocked_threats = [t for t in recent_threats if t['action_taken'] == 'block']
        if len(blocked_threats) > 10:
            # Analyze blocked threat patterns
            risk_scores = [t['risk_score'] for t in blocked_threats]
            avg_blocked_score = np.mean(risk_scores)
            
            if avg_blocked_score > 40:  # High-risk threats being blocked
                self._trigger_drift_alert('adaptive_threats', {
                    'blocked_count': len(blocked_threats),
                    'avg_risk_score': avg_blocked_score,
                    'time_window': 'recent_50_events'
                })
    
    def _trigger_drift_alert(self, alert_type: str, alert_data: Dict):
        """Trigger a drift alert and adaptive response"""
        alert = {
            'timestamp': time.time(),
            'alert_type': alert_type,
            'severity': self._calculate_alert_severity(alert_type, alert_data),
            'data': alert_data,
            'recommended_action': self._get_recommended_action(alert_type)
        }
        
        self.drift_alerts.append(alert)
        
        # Log the alert
        logging.warning(f"[ThreatMonitoring] Drift Alert: {alert_type} - {alert_data}")
        
        # Trigger adaptive response
        self._trigger_adaptive_response(alert)
    
    def _calculate_alert_severity(self, alert_type: str, alert_data: Dict) -> str:
        """Calculate alert severity"""
        if alert_type == 'performance_degradation':
            uncertainty_increase = alert_data.get('uncertainty_increase', 0)
            if uncertainty_increase > 0.1:
                return 'critical'
            elif uncertainty_increase > 0.05:
                return 'high'
            else:
                return 'medium'
        
        elif alert_type == 'adaptive_threats':
            blocked_count = alert_data.get('blocked_count', 0)
            if blocked_count > 20:
                return 'critical'
            elif blocked_count > 10:
                return 'high'
            else:
                return 'medium'
        
        return 'low'
    
    def _get_recommended_action(self, alert_type: str) -> str:
        """Get recommended action for alert type"""
        action_map = {
            'performance_degradation': 'retrain_model',
            'model_degradation': 'retrain_model',
            'response_time_degradation': 'optimize_model',
            'prediction_instability': 'retrain_model',
            'adaptive_threats': 'update_adversarial_training'
        }
        return action_map.get(alert_type, 'investigate')
    
    def _trigger_adaptive_response(self, alert: Dict):
        """Trigger adaptive response based on alert"""
        response = {
            'timestamp': time.time(),
            'alert_id': len(self.drift_alerts),
            'action': alert['recommended_action'],
            'severity': alert['severity'],
            'status': 'triggered'
        }
        
        self.adaptive_responses.append(response)
        
        # Implement automatic responses for critical alerts
        if alert['severity'] == 'critical':
            if alert['recommended_action'] == 'retrain_model':
                self._schedule_model_retrain()
            elif alert['recommended_action'] == 'update_adversarial_training':
                self._schedule_adversarial_update()
    
    def _schedule_model_retrain(self):
        """Schedule model retraining"""
        logging.info("[ThreatMonitoring] Scheduling model retrain due to critical drift")
        # This would trigger the robust retrain process
        # Implementation would depend on your retrain system
    
    def _schedule_adversarial_update(self):
        """Schedule adversarial training update"""
        logging.info("[ThreatMonitoring] Scheduling adversarial training update")
        # This would trigger adversarial training with new threat patterns
    
    def get_monitoring_report(self) -> Dict:
        """Get comprehensive monitoring report"""
        if not self.performance_history:
            return {'status': 'no_data'}
        
        recent_performance = list(self.performance_history)[-100:] if len(self.performance_history) >= 100 else list(self.performance_history)
        
        return {
            'monitoring_status': 'active' if self.is_monitoring else 'inactive',
            'total_predictions': len(self.performance_history),
            'total_threats': len(self.threat_history),
            'active_alerts': len(self.drift_alerts),
            'adaptive_responses': len(self.adaptive_responses),
            'recent_performance': {
                'avg_uncertainty': np.mean([p['uncertainty'] for p in recent_performance]),
                'avg_response_time': np.mean([p['response_time'] for p in recent_performance]),
                'avg_risk_score': np.mean([p['risk_score'] for p in recent_performance])
            },
            'recent_alerts': list(self.drift_alerts)[-10:],  # Last 10 alerts
            'system_health': self._calculate_system_health()
        }
    
    def _calculate_system_health(self) -> str:
        """Calculate overall system health"""
        if not self.performance_history:
            return 'unknown'
        
        recent_performance = list(self.performance_history)[-50:] if len(self.performance_history) >= 50 else list(self.performance_history)
        
        avg_uncertainty = np.mean([p['uncertainty'] for p in recent_performance])
        avg_response_time = np.mean([p['response_time'] for p in recent_performance])
        
        if avg_uncertainty < 0.1 and avg_response_time < 0.05:
            return 'excellent'
        elif avg_uncertainty < 0.2 and avg_response_time < 0.1:
            return 'good'
        elif avg_uncertainty < 0.3 and avg_response_time < 0.2:
            return 'fair'
        else:
            return 'poor'

# Global monitoring instance
threat_monitor = ThreatMonitoringSystem()
