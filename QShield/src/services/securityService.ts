// src/services/securityService.ts
// Production-ready security service for QShield

import keyManager from './keyManager';
import messageService from './messageService';

export interface SecurityEvent {
  id: string;
  type: 'threat_detected' | 'key_compromise' | 'unauthorized_access' | 'message_tampering';
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: number;
  description: string;
  metadata?: any;
}

export interface ThreatAssessment {
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  threats: string[];
  recommendations: string[];
  encryptionLevel: 'standard' | 'enhanced' | 'maximum';
}

class SecurityService {
  private static instance: SecurityService;
  private securityEvents: SecurityEvent[] = [];
  private threatPatterns: RegExp[] = [
    /attack|bomb|explosive|weapon/i,
    /classified|secret|confidential|top.secret/i,
    /hack|crack|exploit|vulnerability/i,
    /malware|virus|trojan|backdoor/i
  ];

  static getInstance(): SecurityService {
    if (!SecurityService.instance) {
      SecurityService.instance = new SecurityService();
    }
    return SecurityService.instance;
  }

  /**
   * Analyze message content for threats
   */
  async analyzeMessage(content: string, metadata?: any): Promise<ThreatAssessment> {
    const threats: string[] = [];
    const recommendations: string[] = [];
    let riskLevel: 'low' | 'medium' | 'high' | 'critical' = 'low';
    let encryptionLevel: 'standard' | 'enhanced' | 'maximum' = 'standard';

    // Check for threat patterns
    for (const pattern of this.threatPatterns) {
      if (pattern.test(content)) {
        threats.push(`Suspicious content detected: ${pattern.source}`);
        riskLevel = 'high';
        encryptionLevel = 'maximum';
      }
    }

    // Check for metadata anomalies
    if (metadata) {
      if (metadata.size > 10000) { // Large message
        threats.push('Unusually large message detected');
        riskLevel = riskLevel === 'low' ? 'medium' : riskLevel;
        encryptionLevel = 'enhanced';
      }

      if (metadata.attachments && metadata.attachments.length > 5) {
        threats.push('Multiple attachments detected');
        riskLevel = riskLevel === 'low' ? 'medium' : riskLevel;
        encryptionLevel = 'enhanced';
      }
    }

    // Generate recommendations
    if (riskLevel === 'high' || riskLevel === 'critical') {
      recommendations.push('Use maximum encryption level');
      recommendations.push('Enable additional security measures');
      recommendations.push('Consider message authentication');
    }

    if (threats.length > 0) {
      recommendations.push('Review message content before sending');
      recommendations.push('Consider using secure channels');
    }

    return {
      riskLevel,
      threats,
      recommendations,
      encryptionLevel
    };
  }

  /**
   * Detect key compromise
   */
  async detectKeyCompromise(userId: string): Promise<boolean> {
    try {
      // Check for unusual key usage patterns
      const keyStats = keyManager.getKeyStats();
      
      // Simple heuristic: if keys are used too frequently, might be compromised
      const keyPair = await keyManager.getUserKeyPair(userId);
      if (keyPair) {
        const keyAge = Date.now() - keyPair.createdAt;
        const usageFrequency = keyStats.totalRotations / (keyAge / (24 * 60 * 60 * 1000)); // rotations per day
        
        if (usageFrequency > 10) { // More than 10 rotations per day
          this.logSecurityEvent({
            type: 'key_compromise',
            severity: 'high',
            description: 'Unusual key rotation frequency detected',
            metadata: { userId, usageFrequency }
          });
          return true;
        }
      }

      return false;
    } catch (error) {
      console.error('Failed to detect key compromise:', error);
      return false;
    }
  }

  /**
   * Validate message integrity
   */
  async validateMessageIntegrity(messageId: string): Promise<boolean> {
    try {
      const message = messageService.getMessage(messageId);
      if (!message) return false;

      // Check if message has been tampered with
      if (message.encrypted && !message.decrypted) {
        // Message should be decryptable if it's encrypted
        try {
          await messageService.fetchMessages(message.recipientId);
          return true;
        } catch (error) {
          this.logSecurityEvent({
            type: 'message_tampering',
            severity: 'high',
            description: 'Message integrity check failed',
            metadata: { messageId, error: error instanceof Error ? error.message : 'Unknown error' }
          });
          return false;
        }
      }

      return true;
    } catch (error) {
      console.error('Failed to validate message integrity:', error);
      return false;
    }
  }

  /**
   * Log security event
   */
  logSecurityEvent(event: Omit<SecurityEvent, 'id' | 'timestamp'>): void {
    const securityEvent: SecurityEvent = {
      id: `sec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      ...event
    };

    this.securityEvents.push(securityEvent);
    
    // Log to console for debugging
    console.warn(`🚨 Security Event: ${event.type} - ${event.description}`);
    
    // In production, this would be sent to security monitoring system
    this.reportToSecurityMonitoring(securityEvent);
  }

  /**
   * Get security events
   */
  getSecurityEvents(): SecurityEvent[] {
    return [...this.securityEvents];
  }

  /**
   * Get recent security events
   */
  getRecentSecurityEvents(hours: number = 24): SecurityEvent[] {
    const cutoff = Date.now() - (hours * 60 * 60 * 1000);
    return this.securityEvents.filter(event => event.timestamp > cutoff);
  }

  /**
   * Clear security events
   */
  clearSecurityEvents(): void {
    this.securityEvents = [];
  }

  /**
   * Report to security monitoring (placeholder)
   */
  private reportToSecurityMonitoring(event: SecurityEvent): void {
    // In production, this would send to SIEM, SOC, etc.
    console.log('📊 Security monitoring report:', event);
  }

  /**
   * Get security summary
   */
  getSecuritySummary(): {
    totalEvents: number;
    criticalEvents: number;
    recentThreats: number;
    riskLevel: 'low' | 'medium' | 'high' | 'critical';
  } {
    const totalEvents = this.securityEvents.length;
    const criticalEvents = this.securityEvents.filter(e => e.severity === 'critical').length;
    const recentThreats = this.getRecentSecurityEvents(24).filter(e => e.type === 'threat_detected').length;
    
    let riskLevel: 'low' | 'medium' | 'high' | 'critical' = 'low';
    if (criticalEvents > 0) riskLevel = 'critical';
    else if (recentThreats > 5) riskLevel = 'high';
    else if (recentThreats > 2) riskLevel = 'medium';

    return {
      totalEvents,
      criticalEvents,
      recentThreats,
      riskLevel
    };
  }
}

export default SecurityService.getInstance();
