"""
Strategy Analyzer
Compare Congress Buys vs Dan Meuser strategies
Helps you decide which to follow or how to blend both
"""

import json
from datetime import datetime

class StrategyAnalyzer:
    """Compare and analyze multiple congressional trading strategies"""
    
    def load_strategy_results(self):
        """Load results from both strategies"""
        
        congress_buys = None
        dan_meuser = None
        
        try:
            with open('congress_buys_portfolio.json', 'r') as f:
                congress_buys = json.load(f)
        except FileNotFoundError:
            print("⚠️  Congress Buys results not found. Run congress_buys_strategy.py first.")
        
        try:
            with open('dan_meuser_portfolio.json', 'r') as f:
                dan_meuser = json.load(f)
        except FileNotFoundError:
            print("⚠️  Dan Meuser results not found. Run dan_meuser_strategy.py first.")
        
        return congress_buys, dan_meuser
    
    def compare_strategies(self, congress_buys: dict, dan_meuser: dict):
        """Compare key metrics between strategies"""
        
        print("\n" + "="*70)
        print("📊 STRATEGY COMPARISON")
        print("="*70)
        
        # Performance comparison
        print("\n📈 Historical Performance:")
        print(f"{'Strategy':<25} {'All-Time':<15} {'CAGR':<15} {'1-Year':<15}")
        print("-" * 70)
        print(f"{'Congress Buys':<25} {'+511.03%':<15} {'38.19%':<15} {'39.79%':<15}")
        print(f"{'Dan Meuser':<25} {'+735.85%':<15} {'40.42%':<15} {'33.84%':<15}")
        
        # Portfolio characteristics
        if congress_buys and dan_meuser:
            print("\n💼 Current Portfolio Characteristics:")
            print(f"{'Strategy':<25} {'Positions':<15} {'Total Value':<20}")
            print("-" * 70)
            
            cb_positions = congress_buys['portfolio']['num_positions']
            cb_value = congress_buys['portfolio']['total_value']
            print(f"{'Congress Buys':<25} {cb_positions:<15} ${cb_value:>18,.0f}")
            
            dm_positions = dan_meuser['current_portfolio']['num_positions']
            dm_value = dan_meuser['current_portfolio']['total_value']
            print(f"{'Dan Meuser':<25} {dm_positions:<15} ${dm_value:>18,.0f}")
            
            # Diversification
            print(f"\n📊 Diversification:")
            print(f"   Congress Buys: {cb_positions} stocks (HIGH diversification)")
            print(f"   Dan Meuser: {dm_positions} stocks ({'HIGH' if dm_positions > 15 else 'MEDIUM' if dm_positions > 8 else 'LOW'} diversification)")
    
    def find_overlapping_positions(self, congress_buys: dict, dan_meuser: dict):
        """Find stocks that appear in both strategies"""
        
        if not (congress_buys and dan_meuser):
            return []
        
        cb_tickers = {pos['ticker'] for pos in congress_buys['portfolio']['portfolio']}
        dm_tickers = {pos['ticker'] for pos in dan_meuser['current_portfolio']['portfolio']}
        
        overlap = cb_tickers.intersection(dm_tickers)
        
        print(f"\n🎯 Overlapping Positions ({len(overlap)} stocks):")
        
        if overlap:
            print("   These stocks appear in BOTH strategies (highest conviction):")
            
            overlap_details = []
            for ticker in overlap:
                cb_pos = next((p for p in congress_buys['portfolio']['portfolio'] if p['ticker'] == ticker), None)
                dm_pos = next((p for p in dan_meuser['current_portfolio']['portfolio'] if p['ticker'] == ticker), None)
                
                if cb_pos and dm_pos:
                    overlap_details.append({
                        'ticker': ticker,
                        'congress_weight': cb_pos['weight'],
                        'dan_weight': dm_pos['weight'],
                        'congress_buyers': cb_pos['num_politicians']
                    })
            
            # Sort by combined weight
            overlap_details.sort(key=lambda x: x['congress_weight'] + x['dan_weight'], reverse=True)
            
            for detail in overlap_details[:5]:
                print(f"   • {detail['ticker']}: Congress {detail['congress_weight']}%, Dan {detail['dan_weight']}% ({detail['congress_buyers']} buyers)")
        else:
            print("   No overlapping positions")
        
        return list(overlap)
    
    def recommend_strategy(self, congress_buys: dict, dan_meuser: dict, overlap: list):
        """Provide personalized recommendation"""
        
        print("\n" + "="*70)
        print("💡 RECOMMENDATION")
        print("="*70)
        
        print("\n🎯 Best Strategy For You:")
        
        print("\n✅ Choose CONGRESS BUYS if:")
        print("   • You want maximum diversification")
        print("   • You prefer crowd wisdom (many politicians)")
        print("   • You're risk-averse")
        print("   • You want to track the entire Congress")
        print("   • Performance: +511% all-time, 38.19% CAGR")
        
        print("\n✅ Choose DAN MEUSER if:")
        print("   • You want concentrated positions")
        print("   • You trust one top performer")
        print("   • You can handle more volatility")
        print("   • You want simpler portfolio management")
        print("   • Performance: +735% all-time, 40.42% CAGR")
        
        print("\n🔥 OPTIMAL STRATEGY (RECOMMENDED):")
        print("   Blend both strategies for best risk/return:")
        print("   • 60% Congress Buys (diversification)")
        print("   • 40% Dan Meuser (alpha generation)")
        print("   • Focus extra on overlapping positions (double conviction)")
        
        if overlap:
            print(f"\n   💎 HIGHEST CONVICTION: Overweight these {len(overlap)} stocks:")
            print(f"   {', '.join(overlap[:10])}")
    
    def generate_combined_portfolio(self, congress_buys: dict, dan_meuser: dict, 
                                    portfolio_value: float = 10000,
                                    congress_allocation: float = 0.6):
        """Generate a blended portfolio"""
        
        print("\n" + "="*70)
        print(f"💰 BLENDED PORTFOLIO (${portfolio_value:,.0f})")
        print("="*70)
        
        congress_value = portfolio_value * congress_allocation
        dan_value = portfolio_value * (1 - congress_allocation)
        
        print(f"\nAllocation:")
        print(f"   Congress Buys: ${congress_value:,.0f} ({congress_allocation*100:.0f}%)")
        print(f"   Dan Meuser: ${dan_value:,.0f} ({(1-congress_allocation)*100:.0f}%)")
        
        # Build combined positions
        combined = {}
        
        # Add Congress Buys positions
        if congress_buys:
            for pos in congress_buys['portfolio']['portfolio']:
                ticker = pos['ticker']
                value = (pos['weight'] / 100) * congress_value
                combined[ticker] = combined.get(ticker, 0) + value
        
        # Add Dan Meuser positions
        if dan_meuser:
            for pos in dan_meuser['current_portfolio']['portfolio']:
                ticker = pos['ticker']
                value = (pos['weight'] / 100) * dan_value
                combined[ticker] = combined.get(ticker, 0) + value
        
        # Sort by value
        combined_list = [{'ticker': k, 'value': v} for k, v in combined.items()]
        combined_list.sort(key=lambda x: x['value'], reverse=True)
        
        print(f"\n🎯 Top 15 Positions in Blended Portfolio:")
        for i, pos in enumerate(combined_list[:15], 1):
            weight = (pos['value'] / portfolio_value) * 100
            print(f"{i:2}. {pos['ticker']:<6} ${pos['value']:>8,.2f} ({weight:>5.2f}%)")
        
        # Save combined portfolio
        results = {
            'strategy': 'Blended Congress + Dan Meuser',
            'total_value': portfolio_value,
            'congress_allocation': congress_allocation,
            'dan_allocation': 1 - congress_allocation,
            'positions': combined_list,
            'generated': datetime.now().isoformat()
        }
        
        with open('blended_portfolio.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Blended portfolio saved to blended_portfolio.json")

def main():
    """Run strategy comparison"""
    
    print("="*70)
    print("🔬 STRATEGY ANALYZER")
    print("Compare Congress Buys vs Dan Meuser Strategies")
    print("="*70)
    
    analyzer = StrategyAnalyzer()
    
    # Load results
    congress_buys, dan_meuser = analyzer.load_strategy_results()
    
    if not (congress_buys or dan_meuser):
        print("\n❌ No strategy results found!")
        print("\nPlease run these first:")
        print("   1. python congress_buys_strategy.py")
        print("   2. python dan_meuser_strategy.py")
        return
    
    # Compare strategies
    if congress_buys and dan_meuser:
        analyzer.compare_strategies(congress_buys, dan_meuser)
        
        # Find overlaps
        overlap = analyzer.find_overlapping_positions(congress_buys, dan_meuser)
        
        # Recommend
        analyzer.recommend_strategy(congress_buys, dan_meuser, overlap)
        
        # Generate blended portfolio
        analyzer.generate_combined_portfolio(congress_buys, dan_meuser, 10000, 0.6)
    
    print("\n" + "="*70)
    print("✅ Analysis Complete!")
    print("="*70)
    
    print("\n📚 Next Steps:")
    print("   1. Review the blended portfolio recommendations")
    print("   2. Set up Discord alerts for both strategies")
    print("   3. Rebalance weekly as new trades come in")
    print("   4. Track your performance vs the strategies")

if __name__ == "__main__":
    main()
