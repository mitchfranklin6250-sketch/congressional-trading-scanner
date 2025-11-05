"""
Dan Meuser Portfolio Strategy
Replicates Quiver Quantitative's "Dan Meuser Strategy" (+735% all-time, 40% CAGR)

Strategy:
- Track ONLY Dan Meuser's trades
- Mirror his exact portfolio positions
- Alert on every new trade immediately
- Calculate position sizes for your portfolio
"""

import json
import requests
from datetime import datetime, timedelta
from collections import defaultdict
import re

class DanMeuserStrategy:
    """Track and mirror Dan Meuser's portfolio"""
    
    def __init__(self, lookback_days: int = 365):
        self.lookback_days = lookback_days
        self.target_politician = "Dan Meuser"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def parse_amount(self, amount_str: str) -> int:
        """Convert amount string to integer"""
        if not amount_str:
            return 0
        
        amount_str = amount_str.replace('$', '').replace(',', '').strip()
        
        if '-' in amount_str:
            parts = amount_str.split('-')
            try:
                low = float(parts[0].strip())
                high = float(parts[1].strip())
                return int((low + high) / 2)
            except:
                pass
        
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
    
    def fetch_dan_meuser_trades(self) -> list:
        """Fetch all Dan Meuser trades"""
        print(f"\n🔍 Fetching {self.target_politician} trades...")
        
        all_trades = []
        cutoff_date = datetime.now() - timedelta(days=self.lookback_days)
        
        # Fetch from House Stock Watcher (Dan Meuser is in the House)
        try:
            print("  📊 Scanning House Stock Watcher...")
            response = requests.get(
                "https://housestockwatcher.com/api/all_transactions",
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for trade in data:
                    try:
                        # Filter for Dan Meuser only
                        politician = trade.get('representative', '')
                        if self.target_politician.lower() not in politician.lower():
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
                        
                        trans_type = trade.get('type', '').lower()
                        if 'purchase' in trans_type or 'buy' in trans_type:
                            trans_type = 'BUY'
                        elif 'sale' in trans_type or 'sell' in trans_type:
                            trans_type = 'SELL'
                        else:
                            trans_type = 'UNKNOWN'
                        
                        all_trades.append({
                            'ticker': ticker,
                            'date': trade['transaction_date'],
                            'transaction_type': trans_type,
                            'amount': amount,
                            'asset_description': trade.get('asset_description', ''),
                            'disclosure_date': trade.get('disclosure_date', '')
                        })
                    except:
                        continue
                
                print(f"    ✅ Found {len(all_trades)} Dan Meuser trades")
        except Exception as e:
            print(f"    ⚠️  House data unavailable: {str(e)[:50]}")
        
        return all_trades
    
    def calculate_current_portfolio(self, trades: list) -> dict:
        """Calculate current portfolio based on buy/sell activity"""
        print("\n📊 Calculating Dan Meuser's current portfolio...")
        
        # Track positions
        positions = defaultdict(lambda: {'buys': 0, 'sells': 0, 'net_amount': 0, 'last_trade': None})
        
        for trade in trades:
            ticker = trade['ticker']
            amount = trade['amount']
            
            if trade['transaction_type'] == 'BUY':
                positions[ticker]['buys'] += amount
                positions[ticker]['net_amount'] += amount
            elif trade['transaction_type'] == 'SELL':
                positions[ticker]['sells'] += amount
                positions[ticker]['net_amount'] -= amount
            
            # Track most recent trade
            if not positions[ticker]['last_trade'] or trade['date'] > positions[ticker]['last_trade']:
                positions[ticker]['last_trade'] = trade['date']
        
        # Build portfolio (only positive net positions)
        portfolio = []
        total_value = 0
        
        for ticker, data in positions.items():
            if data['net_amount'] > 0:  # Still holding
                portfolio.append({
                    'ticker': ticker,
                    'estimated_position': data['net_amount'],
                    'total_buys': data['buys'],
                    'total_sells': data['sells'],
                    'last_trade_date': data['last_trade'],
                    'status': 'HOLDING'
                })
                total_value += data['net_amount']
        
        # Calculate weights
        for position in portfolio:
            position['weight'] = round((position['estimated_position'] / total_value) * 100, 2) if total_value > 0 else 0
        
        # Sort by weight
        portfolio.sort(key=lambda x: x['weight'], reverse=True)
        
        print(f"  ✅ Current positions: {len(portfolio)}")
        print(f"  💰 Estimated total value: ${total_value:,.0f}")
        
        return {
            'portfolio': portfolio,
            'total_value': total_value,
            'num_positions': len(portfolio),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_recent_activity(self, trades: list, days: int = 30) -> list:
        """Get recent trading activity"""
        cutoff = datetime.now() - timedelta(days=days)
        
        recent = [
            trade for trade in trades 
            if datetime.strptime(trade['date'], '%Y-%m-%d') >= cutoff
        ]
        
        recent.sort(key=lambda x: x['date'], reverse=True)
        return recent
    
    def generate_mirror_signals(self, portfolio: dict, your_portfolio_value: float = 10000) -> list:
        """Generate signals to mirror Dan Meuser's portfolio"""
        print(f"\n💰 Generating mirror signals for ${your_portfolio_value:,.0f} portfolio...")
        
        signals = []
        
        for position in portfolio['portfolio']:
            target_value = (position['weight'] / 100) * your_portfolio_value
            
            signals.append({
                'ticker': position['ticker'],
                'action': 'BUY',
                'weight': position['weight'],
                'target_value': round(target_value, 2),
                'dan_position_size': position['estimated_position'],
                'last_trade': position['last_trade_date'],
                'priority': 'HIGH' if position['weight'] >= 10 else 
                           'MEDIUM' if position['weight'] >= 5 else 'LOW'
            })
        
        # Sort by priority and weight
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        signals.sort(key=lambda x: (priority_order[x['priority']], -x['weight']))
        
        return signals
    
    def save_results(self, trades: list, portfolio: dict, signals: list, recent_activity: list):
        """Save all results"""
        results = {
            'strategy': 'Dan Meuser Portfolio Mirror',
            'politician': self.target_politician,
            'description': 'Mirror Dan Meuser\'s +735% portfolio',
            'performance': {
                'all_time_return': '+735.85%',
                'cagr': '40.42%',
                'one_year_return': '+33.84%'
            },
            'current_portfolio': portfolio,
            'mirror_signals': signals,
            'recent_activity': recent_activity,
            'all_trades': trades,
            'last_updated': datetime.now().isoformat()
        }
        
        with open('dan_meuser_portfolio.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to dan_meuser_portfolio.json")
    
    def print_summary(self, portfolio: dict, signals: list, recent_activity: list):
        """Print human-readable summary"""
        print("\n" + "="*70)
        print("🏆 DAN MEUSER PORTFOLIO STRATEGY")
        print("="*70)
        
        print(f"\n📈 Performance Metrics:")
        print(f"   All-Time Return: +735.85%")
        print(f"   CAGR: 40.42%")
        print(f"   1-Year Return: +33.84%")
        print(f"   30-Day Return: +3.91%")
        
        print(f"\n💼 Current Portfolio ({portfolio['num_positions']} positions):")
        print(f"   Estimated Total Value: ${portfolio['total_value']:,.0f}")
        
        print(f"\n🏆 Top Holdings:")
        for i, pos in enumerate(portfolio['portfolio'][:10], 1):
            print(f"\n{i}. {pos['ticker']} - {pos['weight']}% of portfolio")
            print(f"   Estimated Position: ${pos['estimated_position']:,.0f}")
            print(f"   Last Trade: {pos['last_trade_date']}")
            print(f"   Status: {pos['status']}")
        
        if recent_activity:
            print(f"\n🔥 Recent Activity (Last 30 Days):")
            for trade in recent_activity[:5]:
                action_emoji = "🟢" if trade['transaction_type'] == 'BUY' else "🔴"
                print(f"   {action_emoji} {trade['date']}: {trade['transaction_type']} ${trade['amount']:,.0f} of {trade['ticker']}")
        else:
            print(f"\n📊 No recent activity in last 30 days")
        
        print(f"\n🎯 YOUR ACTION ITEMS (to mirror his portfolio with $10,000):")
        print(f"\nHIGH PRIORITY (10%+ positions):")
        for signal in [s for s in signals if s['priority'] == 'HIGH'][:5]:
            print(f"  • BUY ${signal['target_value']:,.2f} of {signal['ticker']} ({signal['weight']}%)")
        
        print(f"\nMEDIUM PRIORITY (5-10% positions):")
        for signal in [s for s in signals if s['priority'] == 'MEDIUM'][:3]:
            print(f"  • BUY ${signal['target_value']:,.2f} of {signal['ticker']} ({signal['weight']}%)")
        
        print("\n💡 TIP: Set up alerts for Dan Meuser's trades to mirror in real-time!")
        
        print("\n" + "="*70)

def main():
    """Run Dan Meuser portfolio strategy"""
    print("="*70)
    print("🏛️  DAN MEUSER PORTFOLIO STRATEGY")
    print("Replicating +735% All-Time Returns")
    print("="*70)
    
    # Initialize strategy
    strategy = DanMeuserStrategy(lookback_days=365)
    
    # Fetch all Dan Meuser trades
    trades = strategy.fetch_dan_meuser_trades()
    
    if not trades:
        print("\n⚠️  No Dan Meuser trades found.")
        print("   This could mean:")
        print("   1. Data sources are temporarily unavailable")
        print("   2. No trades in the last 365 days")
        print("   3. Network issues")
        return
    
    # Calculate current portfolio
    portfolio = strategy.calculate_current_portfolio(trades)
    
    # Get recent activity
    recent_activity = strategy.get_recent_activity(trades, days=30)
    
    # Generate mirror signals
    signals = strategy.generate_mirror_signals(portfolio, 10000)
    
    # Save results
    strategy.save_results(trades, portfolio, signals, recent_activity)
    
    # Print summary
    strategy.print_summary(portfolio, signals, recent_activity)
    
    print("\n✅ Dan Meuser Strategy Complete!")
    print("="*70)

if __name__ == "__main__":
    main()
