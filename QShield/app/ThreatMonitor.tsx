import React from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { ActivityIcon, AlertTriangleIcon, CheckCircleIcon, ShieldIcon, TrendingUpIcon } from '../components/icons';

interface ThreatAssessment {
  id: string;
  title: string;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  description: string;
  aiAnalysis: string;
  timestamp: string;
  icon: React.ReactElement;
}

export default function ThreatMonitor() {
  const assessments: ThreatAssessment[] = [
    {
      id: '1',
      title: 'Unusual Login Pattern Detected',
      riskLevel: 'LOW',
      description: 'Login from new device in authorized region',
      aiAnalysis: 'Pattern matches standard mobile authentication. Risk: Minimal.',
      timestamp: '2 min ago',
      icon: <AlertTriangleIcon size={16} color="#F59E0B" />,
    },
    {
      id: '2',
      title: 'Encrypted Channel Stability',
      riskLevel: 'MEDIUM',
      description: 'Brief connection fluctuation on Channel 3',
      aiAnalysis: 'Network latency spike resolved. No security compromise detected.',
      timestamp: '15 min ago',
      icon: <AlertTriangleIcon size={16} color="#F59E0B" />,
    },
    {
      id: '3',
      title: 'Message Volume Analysis',
      riskLevel: 'LOW',
      description: 'Normal communication patterns maintained',
      aiAnalysis: 'All metrics within expected parameters.',
      timestamp: '1 hour ago',
      icon: <CheckCircleIcon size={16} color="#10B981" />,
    },
  ];

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'LOW': return 'hsl(150, 70%, 40%)'; // --success
      case 'MEDIUM': return 'hsl(30, 95%, 44%)'; // --warning
      case 'HIGH': return 'hsl(0, 84%, 60%)'; // --destructive
      default: return 'hsl(150, 70%, 40%)'; // --success
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <Text style={styles.title}>AI Threat Monitor</Text>
          <Text style={styles.subtitle}>Real-time security analysis and threat assessment</Text>
        </View>
        <View style={styles.monitoringStatus}>
          <ActivityIcon size={20} color="hsl(210, 40%, 98%)" />
          <Text style={styles.monitoringText}>Active Monitoring</Text>
        </View>
      </View>

      {/* Metrics Cards */}
      <View style={styles.metricsContainer}>
        <View style={styles.metricCard}>
          <View style={[styles.metricIconContainer, { backgroundColor: 'hsl(150, 70%, 40%, 0.2)' }]}>
            <CheckCircleIcon size={20} color="hsl(150, 70%, 40%)" />
          </View>
          <View style={styles.metricContent}>
            <Text style={styles.metricTitle}>Security Status</Text>
            <Text style={[styles.metricValue, { color: 'hsl(150, 70%, 40%)' }]}>Secure</Text>
          </View>
        </View>

        <View style={styles.metricCard}>
          <View style={[styles.metricIconContainer, { backgroundColor: 'hsl(180, 94%, 29%, 0.2)' }]}>
            <ShieldIcon size={20} color="hsl(180, 94%, 29%)" />
          </View>
          <View style={styles.metricContent}>
            <Text style={styles.metricTitle}>Active Channels</Text>
            <Text style={styles.metricValue}>8</Text>
          </View>
        </View>

        <View style={styles.metricCard}>
          <View style={[styles.metricIconContainer, { backgroundColor: 'hsl(30, 95%, 44%, 0.2)' }]}>
            <AlertTriangleIcon size={20} color="hsl(30, 95%, 44%)" />
          </View>
          <View style={styles.metricContent}>
            <Text style={styles.metricTitle}>Active Alerts</Text>
            <Text style={styles.metricValue}>3</Text>
          </View>
        </View>

        <View style={styles.metricCard}>
          <View style={[styles.metricIconContainer, { backgroundColor: 'hsl(180, 94%, 29%, 0.2)' }]}>
            <TrendingUpIcon size={20} color="hsl(180, 94%, 29%)" />
          </View>
          <View style={styles.metricContent}>
            <Text style={styles.metricTitle}>AI Confidence</Text>
            <Text style={styles.metricValue}>98.7%</Text>
          </View>
        </View>
      </View>

      {/* Recent Threat Assessments */}
      <View style={styles.assessmentsContainer}>
        <Text style={styles.sectionTitle}>Recent Threat Assessments</Text>
        
        <ScrollView style={styles.assessmentsList}>
          {assessments.map((assessment) => (
            <View key={assessment.id} style={styles.assessmentCard}>
              <View style={styles.assessmentHeader}>
                <Text style={[styles.assessmentIcon, { color: getRiskColor(assessment.riskLevel) }]}>
                  {assessment.icon}
                </Text>
                <View style={styles.assessmentContent}>
                  <View style={styles.assessmentTitleRow}>
                    <Text style={styles.assessmentTitle}>{assessment.title}</Text>
                    <View style={[styles.riskBadge, { backgroundColor: getRiskColor(assessment.riskLevel) }]}>
                      <Text style={styles.riskText}>{assessment.riskLevel}</Text>
                    </View>
                  </View>
                  
                  <Text style={styles.assessmentDescription}>{assessment.description}</Text>
                  
                  <View style={styles.aiAnalysisContainer}>
                    <View style={styles.aiAnalysisHeader}>
                      <Text style={styles.aiAnalysisLabel}>AI Analysis</Text>
                      <ActivityIcon size={16} color="hsl(210, 40%, 98%)" />
                    </View>
                    <Text style={styles.aiAnalysisText}>{assessment.aiAnalysis}</Text>
                  </View>
                  
                  <Text style={styles.assessmentTimestamp}>{assessment.timestamp}</Text>
                </View>
              </View>
            </View>
          ))}
        </ScrollView>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'hsl(217, 45%, 10%)', // --background
    padding: 24,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 32,
  },
  headerContent: {
    flex: 1,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: 'hsl(210, 40%, 98%)', // --foreground
    marginBottom: 8,
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 18,
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    fontWeight: '400',
  },
  monitoringStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'hsl(150, 70%, 40%)', // --success
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6, // --radius
  },
  monitoringIcon: {
    fontSize: 16,
    marginRight: 8,
  },
  monitoringText: {
    color: 'hsl(210, 40%, 98%)', // --success-foreground
    fontSize: 14,
    fontWeight: '600',
  },
  metricsContainer: {
    flexDirection: 'row',
    marginBottom: 24,
    gap: 16,
  },
  metricCard: {
    flex: 1,
    backgroundColor: 'hsl(220, 20%, 15%)', // --card
    padding: 16,
    borderRadius: 6, // --radius
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  metricIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
  },
  metricIcon: {
    fontSize: 20,
  },
  metricContent: {
    flex: 1,
  },
  metricTitle: {
    fontSize: 12,
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    marginBottom: 4,
    fontWeight: '500',
  },
  metricValue: {
    fontSize: 18,
    fontWeight: '700',
    color: 'hsl(210, 40%, 98%)', // --foreground
    letterSpacing: -0.25,
  },
  assessmentsContainer: {
    flex: 1,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: 'hsl(210, 40%, 98%)', // --foreground
    marginBottom: 20,
    letterSpacing: -0.25,
  },
  assessmentsList: {
    flex: 1,
  },
  assessmentCard: {
    backgroundColor: 'hsl(220, 20%, 15%)', // --card
    padding: 16,
    borderRadius: 6, // --radius
    marginBottom: 12,
  },
  assessmentHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  assessmentIcon: {
    fontSize: 20,
    marginRight: 16,
    marginTop: 4,
  },
  assessmentContent: {
    flex: 1,
  },
  assessmentTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  assessmentTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: 'hsl(210, 40%, 98%)', // --foreground
    flex: 1,
  },
  riskBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  riskText: {
    color: 'hsl(210, 40%, 98%)', // --foreground
    fontSize: 12,
    fontWeight: '700',
  },
  assessmentDescription: {
    fontSize: 14,
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    marginBottom: 12,
    lineHeight: 20,
  },
  aiAnalysisContainer: {
    backgroundColor: 'hsl(220, 15%, 20%, 0.5)', // --muted with opacity
    padding: 12,
    borderRadius: 6, // --radius
    marginBottom: 8,
    borderWidth: 1,
    borderColor: 'hsl(220, 15%, 25%)', // --border
  },
  aiAnalysisHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  aiAnalysisLabel: {
    fontSize: 12,
    color: 'hsl(180, 94%, 29%)', // --primary
    fontWeight: '600',
    flex: 1,
  },
  aiAnalysisIcon: {
    fontSize: 16,
    color: 'hsl(180, 94%, 29%)', // --primary
  },
  aiAnalysisText: {
    fontSize: 14,
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    lineHeight: 20,
  },
  assessmentTimestamp: {
    fontSize: 12,
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    fontWeight: '500',
  },
});
