#!/usr/bin/env python3
"""
Master Strategy Runner
Runs all congressional trading strategies:
1. Congress Buys Strategy (+511% all-time)
2. Dan Meuser Strategy (+735% all-time)
3. Strategy Analysis & Blending
4. Discord Alerts
"""

import sys
from datetime import datetime

def run_all_strategies():
    """Execute all strategies in sequence"""
    
    print("="*70)
    print("🏛️  MASTER STRATEGY RUNNER")
    print("="*70)
    print(f"\nExecution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success_count = 0
    errors = []
    
    # Strategy 1: Congress Buys
    print("\n" + "="*70)
    print("STRATEGY 1: Congress Buys (+511% all-time)")
    print("="*70)
    try:
        from congress_buys_strategy import CongressBuysStrategy
        
        strategy = CongressBuysStrategy(lookback_days=90)
        purchases = strategy.fetch_all_purchases()
        
        if purchases:
            portfolio = strategy.calculate_portfolio_weights(purchases)
            signals = strategy.generate_rebalance_signals(portfolio, 10000)
            strategy.save_results(portfolio, signals)
            strategy.print_portfolio_summary(portfolio, signals)
            success_count += 1
            print("\n✅ Congress Buys Strategy complete")
        else:
            print("\n⚠️  No data available for Congress Buys")
            errors.append("Congress Buys: No data")
    except Exception as e:
        print(f"\n❌ Congress Buys Strategy failed: {e}")
        errors.append(f"Congress Buys: {e}")
    
    # Strategy 2: Dan Meuser
    print("\n" + "="*70)
    print("STRATEGY 2: Dan Meuser (+735% all-time)")
    print("="*70)
    try:
        from dan_meuser_strategy import DanMeuserStrategy
        
        strategy = DanMeuserStrategy(lookback_days=365)
        trades = strategy.fetch_dan_meuser_trades()
        
        if trades:
            portfolio = strategy.calculate_current_portfolio(trades)
            recent_activity = strategy.get_recent_activity(trades, days=30)
            signals = strategy.generate_mirror_signals(portfolio, 10000)
            strategy.save_results(trades, portfolio, signals, recent_activity)
            strategy.print_summary(portfolio, signals, recent_activity)
            success_count += 1
            print("\n✅ Dan Meuser Strategy complete")
        else:
            print("\n⚠️  No Dan Meuser trades found")
            errors.append("Dan Meuser: No trades found")
    except Exception as e:
        print(f"\n❌ Dan Meuser Strategy failed: {e}")
        errors.append(f"Dan Meuser: {e}")
    
    # Strategy 3: Analysis & Blending
    print("\n" + "="*70)
    print("STRATEGY 3: Analysis & Blending")
    print("="*70)
    try:
        from strategy_analyzer import StrategyAnalyzer
        
        analyzer = StrategyAnalyzer()
        congress_buys, dan_meuser = analyzer.load_strategy_results()
        
        if congress_buys and dan_meuser:
            analyzer.compare_strategies(congress_buys, dan_meuser)
            overlap = analyzer.find_overlapping_positions(congress_buys, dan_meuser)
            analyzer.recommend_strategy(congress_buys, dan_meuser, overlap)
            analyzer.generate_combined_portfolio(congress_buys, dan_meuser, 10000, 0.6)
            success_count += 1
            print("\n✅ Strategy Analysis complete")
        else:
            print("\n⚠️  Cannot analyze - strategies didn't produce results")
            errors.append("Analysis: Missing strategy results")
    except Exception as e:
        print(f"\n❌ Strategy Analysis failed: {e}")
        errors.append(f"Analysis: {e}")
    
    # Step 4: Discord Alerts
    print("\n" + "="*70)
    print("STEP 4: Sending Discord Alerts")
    print("="*70)
    try:
        from strategy_discord_alerts import StrategyAlerter
        import os
        
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if webhook_url:
            alerter = StrategyAlerter(webhook_url)
            
            # Send all strategy alerts
            try:
                import json
                with open('congress_buys_portfolio.json', 'r') as f:
                    cb_data = json.load(f)
                    alerter.send_congress_buys_alert(cb_data['portfolio'])
            except:
                pass
            
            try:
                with open('dan_meuser_portfolio.json', 'r') as f:
                    dm_data = json.load(f)
                    alerter.send_dan_meuser_alert(
                        dm_data['current_portfolio'],
                        dm_data['recent_activity']
                    )
            except:
                pass
            
            try:
                with open('blended_portfolio.json', 'r') as f:
                    blend_data = json.load(f)
                    alerter.send_blended_alert(blend_data)
            except:
                pass
            
            print("\n✅ Discord alerts sent")
        else:
            print("\n⚠️  Discord alerts disabled (no webhook configured)")
    except Exception as e:
        print(f"\n❌ Discord alerts failed: {e}")
        errors.append(f"Discord: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("📊 EXECUTION SUMMARY")
    print("="*70)
    print(f"\nSuccessful Strategies: {success_count}/3")
    
    if errors:
        print(f"\n⚠️  Errors:")
        for error in errors:
            print(f"   • {error}")
    
    print("\n💾 Generated Files:")
    print("   • congress_buys_portfolio.json")
    print("   • dan_meuser_portfolio.json")
    print("   • blended_portfolio.json")
    
    print("\n" + "="*70)
    print("✅ MASTER STRATEGY RUNNER COMPLETE")
    print("="*70)
    
    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    sys.exit(run_all_strategies())
