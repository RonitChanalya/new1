# Honeypot Intelligence Network Test Script
# Tests the honeypot system using PowerShell

Write-Host "HONEYPOT INTELLIGENCE NETWORK TEST" -ForegroundColor Green
Write-Host "=" * 50

# Test 1: System Health
Write-Host "`n1. TESTING SYSTEM HEALTH" -ForegroundColor Yellow
Write-Host "-" * 30
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method GET
    Write-Host "SUCCESS: System is running" -ForegroundColor Green
    Write-Host "Status: $($health.status)" -ForegroundColor Cyan
} catch {
    Write-Host "ERROR: System health check failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 2: Deploy Honeypots
Write-Host "`n2. DEPLOYING HONEYPOTS" -ForegroundColor Yellow
Write-Host "-" * 30
$headers = @{ 'x-api-key' = '5ac00dc6a40ea9ddbe0e341bbd3537b1' }
$honeypotTypes = @("fake_ml_endpoint", "fake_crypto_service", "fake_admin_panel")

foreach ($type in $honeypotTypes) {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/honeypot/deploy?honeypot_type=$type" -Method POST -Headers $headers
        Write-Host "SUCCESS: Deployed $type" -ForegroundColor Green
        Write-Host "  ID: $($response.honeypot_id)" -ForegroundColor Cyan
    } catch {
        Write-Host "ERROR: Failed to deploy $type" -ForegroundColor Red
    }
}

# Test 3: Fake ML Endpoint
Write-Host "`n3. TESTING FAKE ML ENDPOINT" -ForegroundColor Yellow
Write-Host "-" * 30
$attackVector = @(25000, 0.05, 15, 1.0)
Write-Host "Attack Vector: $attackVector" -ForegroundColor Cyan

$mlPayload = @{
    token = "test_attacker"
    vector = $attackVector
    timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
} | ConvertTo-Json

try {
    $mlResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/ml/fake-score" -Method POST -Body $mlPayload -ContentType 'application/json'
    Write-Host "SUCCESS: Fake ML response received" -ForegroundColor Green
    Write-Host "  Risk Score: $($mlResponse.risk)" -ForegroundColor Cyan
    Write-Host "  Action: $($mlResponse.action)" -ForegroundColor Cyan
    Write-Host "  Model Version: $($mlResponse.model_version)" -ForegroundColor Cyan
    Write-Host "  Mode: $($mlResponse.mode)" -ForegroundColor Cyan
    
    if ($mlResponse.mode -eq "honeypot") {
        Write-Host "  HONEYPOT DETECTED - Deception working!" -ForegroundColor Magenta
    }
} catch {
    Write-Host "ERROR: Fake ML endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Fake Crypto Endpoint
Write-Host "`n4. TESTING FAKE CRYPTO ENDPOINT" -ForegroundColor Yellow
Write-Host "-" * 30
$cryptoVector = @(15000, 0.1, 10, 1.0)
Write-Host "Crypto Vector: $cryptoVector" -ForegroundColor Cyan

$cryptoPayload = @{
    token = "crypto_attacker"
    vector = $cryptoVector
    client_capabilities = @{
        protocols = @("aes256", "chacha20_poly1305", "hybrid_pqc_aes256")
        supports_pqc = $true
        supports_hybrid = $true
    }
    timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
} | ConvertTo-Json

try {
    $cryptoResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/ml/fake-crypto" -Method POST -Body $cryptoPayload -ContentType 'application/json'
    Write-Host "SUCCESS: Fake crypto response received" -ForegroundColor Green
    Write-Host "  Risk: $($cryptoResponse.risk)" -ForegroundColor Cyan
    
    if ($cryptoResponse.crypto_recommendation) {
        $rec = $cryptoResponse.crypto_recommendation
        Write-Host "  Protocol: $($rec.recommended_protocol)" -ForegroundColor Cyan
        Write-Host "  Strength: $($rec.crypto_strength)" -ForegroundColor Cyan
        Write-Host "  PQC Required: $($rec.pqc_required)" -ForegroundColor Cyan
    }
    
    if ($cryptoResponse.honeypot_indicators) {
        $indicators = $cryptoResponse.honeypot_indicators
        Write-Host "  Decoy Crypto: $($indicators.decoy_crypto)" -ForegroundColor Magenta
        Write-Host "  Fake Negotiation: $($indicators.fake_negotiation)" -ForegroundColor Magenta
    }
} catch {
    Write-Host "ERROR: Fake crypto endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Fake Admin Endpoint
Write-Host "`n5. TESTING FAKE ADMIN ENDPOINT" -ForegroundColor Yellow
Write-Host "-" * 30
try {
    $adminResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/fake-health" -Method GET
    Write-Host "SUCCESS: Fake admin response received" -ForegroundColor Green
    Write-Host "  Status: $($adminResponse.status)" -ForegroundColor Cyan
    
    if ($adminResponse.fake_metrics) {
        $metrics = $adminResponse.fake_metrics
        Write-Host "  CPU: $($metrics.cpu)%" -ForegroundColor Cyan
        Write-Host "  Memory: $($metrics.memory)%" -ForegroundColor Cyan
    }
    
    if ($adminResponse.honeypot_data) {
        $honeypotData = $adminResponse.honeypot_data
        Write-Host "  Fake Alerts: $($honeypotData.fake_alerts)" -ForegroundColor Magenta
        Write-Host "  Fake Models: $($honeypotData.fake_models)" -ForegroundColor Magenta
        Write-Host "  Decoy Status: $($honeypotData.decoy_status)" -ForegroundColor Magenta
    }
} catch {
    Write-Host "ERROR: Fake admin endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 6: Intelligence Report
Write-Host "`n6. TESTING INTELLIGENCE REPORT" -ForegroundColor Yellow
Write-Host "-" * 30
try {
    $intelResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/honeypot/intelligence" -Method GET -Headers $headers
    Write-Host "SUCCESS: Intelligence report received" -ForegroundColor Green
    Write-Host "  Active Honeypots: $($intelResponse.active_honeypots)" -ForegroundColor Cyan
    Write-Host "  Total Interactions: $($intelResponse.total_interactions)" -ForegroundColor Cyan
    Write-Host "  Attacker Profiles: $($intelResponse.attacker_profiles)" -ForegroundColor Cyan
    Write-Host "  High Threat Attackers: $($intelResponse.high_threat_attackers)" -ForegroundColor Cyan
    Write-Host "  Intelligence Data Points: $($intelResponse.intelligence_data_points)" -ForegroundColor Cyan
    Write-Host "  Monitoring Status: $($intelResponse.monitoring_status)" -ForegroundColor Cyan
    
    if ($intelResponse.threat_summary) {
        $summary = $intelResponse.threat_summary
        Write-Host "`n  Threat Summary:" -ForegroundColor Yellow
        Write-Host "    Total Attackers: $($summary.total_attackers)" -ForegroundColor Cyan
        
        if ($summary.threat_distribution) {
            $dist = $summary.threat_distribution
            Write-Host "    Threat Distribution:" -ForegroundColor Yellow
            Write-Host "      Critical: $($dist.critical)" -ForegroundColor Red
            Write-Host "      High: $($dist.high)" -ForegroundColor Red
            Write-Host "      Medium: $($dist.medium)" -ForegroundColor Yellow
            Write-Host "      Low: $($dist.low)" -ForegroundColor Green
        }
        
        if ($summary.recommendations) {
            Write-Host "    Security Recommendations:" -ForegroundColor Yellow
            foreach ($rec in $summary.recommendations) {
                Write-Host "      - $rec" -ForegroundColor Cyan
            }
        }
    }
} catch {
    Write-Host "ERROR: Intelligence report failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Final Summary
Write-Host "`n" + "=" * 50 -ForegroundColor Green
Write-Host "HONEYPOT INTELLIGENCE TEST COMPLETE" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green
Write-Host "The honeypot intelligence network provides:" -ForegroundColor White
Write-Host "1. DECEPTION: Fake responses confuse attackers" -ForegroundColor Cyan
Write-Host "2. INTELLIGENCE: Gathers data on attack patterns" -ForegroundColor Cyan
Write-Host "3. PROFILING: Creates attacker behavioral profiles" -ForegroundColor Cyan
Write-Host "4. COUNTER-INTELLIGENCE: Uses intelligence to improve defenses" -ForegroundColor Cyan
Write-Host "5. MILITARY-GRADE: Suitable for high-security environments" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Green
