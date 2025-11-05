#!/usr/bin/env python3
"""
Master Automation Script - Runs complete congressional trading pipeline
1. Scan for new trades
2. Detect signals
3. Update performance tracking
4. Send Discord alerts
"""

import sys
import json
from datetime import datetime
from congressional_scanner import CongressionalTradingScanner
from performance_tracker import PerformanceTracker
from discord_alerts import DiscordAlerter

def main():
    print("="*70)
    print("🏛️  CONGRESSIONAL TRADING AUTOMATION PIPELINE")
    print("="*70)
    print(f"\nExecution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ===== STEP 1: SCAN FOR TRADES =====
    print("\n" + "="*70)
    print("STEP 1: Scanning for Congressional Trades")
    print("="*70)
    
    try:
        scanner = CongressionalTradingScanner()
        results = scanner.scan_for_signals()
        scanner.save_results(results)
        scanner.print_summary(results)
        
        signals = results['signals']
        print(f"\n✅ Scanning complete - {len(signals)} signals detected")
        
    except Exception as e:
        print(f"\n❌ Error in scanning: {e}")
        signals = []
        results = {'signals': [], 'all_trades': []}
    
    # ===== STEP 2: UPDATE PERFORMANCE TRACKING =====
    print("\n" + "="*70)
    print("STEP 2: Updating Performance Tracking")
    print("="*70)
    
    try:
        tracker = PerformanceTracker()
        
        # Add new signals to tracking
        for signal in signals[:5]:  # Track top 5 signals
            if signal.get('ticker'):
                # In production, would get real entry price
                # For now, mark for tracking
                print(f"  📊 Marking {signal['ticker']} for tracking")
        
        # Update existing tracked positions
        if tracker.history['tracked_signals']:
            tracker.update_tracked_signals()
            tracker.save_history()
            
            # Generate performance report
            report = tracker.generate_performance_report()
            
            print("\n✅ Performance tracking updated")
        else:
            report = None
            print("\n📝 No positions currently tracked")
            
    except Exception as e:
        print(f"\n❌ Error in performance tracking: {e}")
        report = None
    
    # ===== STEP 3: SEND DISCORD ALERTS =====
    print("\n" + "="*70)
    print("STEP 3: Sending Discord Alerts")
    print("="*70)
    
    try:
        alerter = DiscordAlerter()
        
        if alerter.enabled:
            # Send signal alerts
            alerter.send_signals(signals, max_signals=10)
            
            # Send performance report if available
            if report:
                alerter.send_performance_report(report)
            
            print("\n✅ Discord alerts sent")
        else:
            print("\n⚠️  Discord alerts disabled (no webhook configured)")
            
    except Exception as e:
        print(f"\n❌ Error sending alerts: {e}")
    
    # ===== SUMMARY =====
    print("\n" + "="*70)
    print("📊 PIPELINE SUMMARY")
    print("="*70)
    print(f"\nSignals Detected: {len(signals)}")
    print(f"Scan Mode: {results.get('mode', 'unknown')}")
    
    if signals:
        print(f"\nTop Signal: {signals[0]['signal_type']} - {signals[0]['ticker']}")
    
    print("\n" + "="*70)
    print("✅ PIPELINE COMPLETE")
    print("="*70)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
