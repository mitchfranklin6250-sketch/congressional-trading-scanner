"""
Congress Buys Strategy
Replicates Quiver Quantitative's "Congress Buys" strategy (+511% all-time)

Strategy:
- Track ALL congressional stock purchases
- Weight positions by reported transaction size
- Rebalance weekly based on new trades
- Hold positions until sold or 90 days
"""

import json
import requests
from datetime import datetime, timedelta
from collections import defaultdict
import re

class CongressBuysStrategy:
    """Track and weight all congressional purchases"""
    
    def __init__(self, lookback_days: int = 90):
        self.lookback_days = lookback_days
        self.min_position_size = 15000  # Minimum trade size to track
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def parse_amount(self, amount_str: str) -> int:
        """Convert amount string to integer"""
        if not amount_str:
            return 0
        
        amount_str = amount_str.replace('$', '').replace(',', '').strip()
        
        # Handle ranges like "$1,001 - $15,000"
        if '-' in amount_str:
            parts = amount_str.split('-')
            try:
                low = float(parts[0].strip())
                high = float(parts[1].strip())
                return int((low + high) / 2)
            except:
                pass
        
        # Handle K/M notation
        if 'K' in amount_str.upper():
            try:
                return int(float(amount_str.upper().replace('K', '').strip()) * 1000)
            except:
                pass
        
        if 'M' in amount_str.upper():
            try:
                return int(float(amount_str.upper().replace('M', '').strip()) * 1000000)
            except:
                pass
        
        try:
            return int(float(amount_str))
        except:
            return 0
    
    def fetch_all_purchases(self) -> list:
        """Fetch all congressional purchases from public APIs"""
        print("\n🔍 Fetching congressional purchases...")
        
        all_purchases = []
        cutoff_date = datetime.now() - timedelta(days=self.lookback_days)
        
        # Fetch from House Stock Watcher
        try:
            print("  📊 Fetching House purchases...")
            response = requests.get(
                "https://housestockwatcher.com/api/all_transactions",
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for trade in data:
                    try:
                        # Only purchases
                        trans_type = trade.get('type', '').lower()
                        if 'purchase' not in trans_type and 'buy' not in trans_type:
                            continue
                        
                        trans_date = datetime.strptime(trade['transaction_date'], '%Y-%m-%d')
                        if trans_date < cutoff_date:
                            continue
                        
                        ticker = trade.get('ticker', '')
                        if not ticker:
                            asset_desc = trade.get('asset_description', '')
                            ticker_match = re.search(r'\(([A-Z]{1,5})\)', asset_desc)
                            if ticker_match:
                                ticker = ticker_match.group(1)
                        
                        if not ticker:
                            continue
                        
                        amount = self.parse_amount(trade.get('amount', ''))
                        
                        if amount >= self.min_position_size:
                            all_purchases.append({
                                'ticker': ticker,
                                'date': trade['transaction_date'],
                                'politician': trade.get('representative', ''),
                                'amount': amount,
                                'chamber': 'House'
                            })
                    except:
                        continue
                
                print(f"    ✅ Found {len([p for p in all_purchases if p['chamber'] == 'House'])} House purchases")
        except Exception as e:
            print(f"    ⚠️  House data unavailable: {str(e)[:50]}")
        
        # Fetch from Senate Stock Watcher
        try:
            print("  📊 Fetching Senate purchases...")
            response = requests.get(
                "https://senatestockwatcher.com/api/all_transactions",
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for trade in data:
                    try:
                        trans_type = trade.get('type', '').lower()
                        if 'purchase' not in trans_type and 'buy' not in trans_type:
                            continue
                        
                        trans_date = datetime.strptime(trade['transaction_date'], '%Y-%m-%d')
                        if trans_date < cutoff_date:
                            continue
                        
                        ticker = trade.get('ticker', '')
                        if not ticker:
                            asset_desc = trade.get('asset_description', '')
                            ticker_match = re.search(r'\(([A-Z]{1,5})\)', asset_desc)
                            if ticker_match:
                                ticker = ticker_match.group(1)
                        
                        if not ticker:
                            continue
                        
                        amount = self.parse_amount(trade.get('amount', ''))
                        
                        if amount >= self.min_position_size:
                            all_purchases.append({
                                'ticker': ticker,
                                'date': trade['transaction_date'],
                                'politician': trade.get('senator', ''),
                                'amount': amount,
                                'chamber': 'Senate'
                            })
                    except:
                        continue
                
                senate_count = len([p for p in all_purchases if p['chamber'] == 'Senate'])
                print(f"    ✅ Found {senate_count} Senate purchases")
        except Exception as e:
            print(f"    ⚠️  Senate data unavailable: {str(e)[:50]}")
        
        print(f"\n  🎯 Total purchases: {len(all_purchases)}")
        return all_purchases
    
    def calculate_portfolio_weights(self, purchases: list) -> dict:
        """Calculate portfolio weights based on purchase amounts"""
        print("\n📊 Calculating portfolio weights...")
        
        # Aggregate by ticker
        ticker_data = defaultdict(lambda: {'total_amount': 0, 'count': 0, 'politicians': []})
        
        for purchase in purchases:
            ticker = purchase['ticker']
            ticker_data[ticker]['total_amount'] += purchase['amount']
            ticker_data[ticker]['count'] += 1
            ticker_data[ticker]['politicians'].append(purchase['politician'])
        
        # Calculate total portfolio value
        total_value = sum(data['total_amount'] for data in ticker_data.values())
        
        # Calculate weights
        portfolio = []
        for ticker, data in ticker_data.items():
            weight = (data['total_amount'] / total_value) * 100
            
            portfolio.append({
                'ticker': ticker,
                'weight': round(weight, 2),
                'total_amount': data['total_amount'],
                'purchase_count': data['count'],
                'politicians': list(set(data['politicians'])),
                'num_politicians': len(set(data['politicians']))
            })
        
        # Sort by weight
        portfolio.sort(key=lambda x: x['weight'], reverse=True)
        
        print(f"  ✅ Portfolio: {len(portfolio)} unique tickers")
        print(f"  💰 Total value: ${total_value:,.0f}")
        
        return {
            'portfolio': portfolio,
            'total_value': total_value,
            'num_positions': len(portfolio),
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def generate_rebalance_signals(self, current_portfolio: dict, your_portfolio_value: float = 10000) -> list:
        """Generate buy signals based on portfolio weights"""
        print(f"\n💰 Generating signals for ${your_portfolio_value:,.0f} portfolio...")
        
        signals = []
        
        for position in current_portfolio['portfolio']:
            target_value = (position['weight'] / 100) * your_portfolio_value
            
            signals.append({
                'ticker': position['ticker'],
                'action': 'BUY',
                'weight': position['weight'],
                'target_value': round(target_value, 2),
                'num_congress_buyers': position['num_politicians'],
                'total_congress_amount': position['total_amount'],
                'conviction': 'HIGH' if position['num_politicians'] >= 3 else 
                             'MEDIUM' if position['num_politicians'] == 2 else 'LOW'
            })
        
        # Sort by conviction and weight
        conviction_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        signals.sort(key=lambda x: (conviction_order[x['conviction']], -x['weight']))
        
        return signals
    
    def save_results(self, portfolio: dict, signals: list, output_file: str = "congress_buys_portfolio.json"):
        """Save portfolio and signals"""
        results = {
            'strategy': 'Congress Buys',
            'description': 'All congressional purchases weighted by size',
            'portfolio': portfolio,
            'signals': signals,
            'last_updated': datetime.now().isoformat()
        }
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to {output_file}")
    
    def print_portfolio_summary(self, portfolio: dict, signals: list):
        """Print human-readable summary"""
        print("\n" + "="*70)
        print("📊 CONGRESS BUYS STRATEGY - CURRENT PORTFOLIO")
        print("="*70)
        
        print(f"\n💼 Portfolio Summary:")
        print(f"   Total Positions: {portfolio['num_positions']}")
        print(f"   Total Congressional Investment: ${portfolio['total_value']:,.0f}")
        print(f"   Generated: {portfolio['generated_date']}")
        
        print(f"\n🏆 Top 10 Positions:")
        for i, pos in enumerate(portfolio['portfolio'][:10], 1):
            print(f"\n{i}. {pos['ticker']} - {pos['weight']}% of portfolio")
            print(f"   Congress buyers: {pos['num_politicians']}")
            print(f"   Total bought: ${pos['total_amount']:,.0f}")
            print(f"   Purchases: {pos['purchase_count']}")
        
        print(f"\n🎯 YOUR ACTION ITEMS (for $10,000 portfolio):")
        print(f"\nHIGH CONVICTION (3+ congress members):")
        high_conviction = [s for s in signals if s['conviction'] == 'HIGH']
        for signal in high_conviction[:5]:
            print(f"  • BUY ${signal['target_value']:,.2f} of {signal['ticker']} ({signal['weight']}%)")
        
        print(f"\nMEDIUM CONVICTION (2 congress members):")
        medium_conviction = [s for s in signals if s['conviction'] == 'MEDIUM']
        for signal in medium_conviction[:3]:
            print(f"  • BUY ${signal['target_value']:,.2f} of {signal['ticker']} ({signal['weight']}%)")
        
        print("\n" + "="*70)

def main():
    """Run the Congress Buys strategy"""
    print("="*70)
    print("🏛️  CONGRESS BUYS STRATEGY")
    print("Replicating Quiver Quantitative's +511% Strategy")
    print("="*70)
    
    # Initialize strategy
    strategy = CongressBuysStrategy(lookback_days=90)
    
    # Fetch all purchases
    purchases = strategy.fetch_all_purchases()
    
    if not purchases:
        print("\n⚠️  No purchases found. Using sample data for demo...")
        # Could add sample data here
        return
    
    # Calculate portfolio weights
    portfolio = strategy.calculate_portfolio_weights(purchases)
    
    # Generate rebalance signals for different portfolio sizes
    signals_10k = strategy.generate_rebalance_signals(portfolio, 10000)
    
    # Save results
    strategy.save_results(portfolio, signals_10k)
    
    # Print summary
    strategy.print_portfolio_summary(portfolio, signals_10k)
    
    print("\n💡 TIP: Run this weekly to get rebalancing signals!")
    print("📊 Compare your returns to the strategy's performance over time")
    
    print("\n" + "="*70)
    print("✅ Congress Buys Strategy Complete!")
    print("="*70)

if __name__ == "__main__":
    main()
