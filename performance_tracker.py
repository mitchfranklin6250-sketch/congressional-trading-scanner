"""
Performance Tracker - Track which signals and politicians actually work
This is the Quiver Quantitative premium feature
"""

import json
import requests
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

class PerformanceTracker:
    """Track historical performance of signals and politicians"""
    
    def __init__(self, signals_file: str = "signals.json", 
                 history_file: str = "signal_history.json"):
        self.signals_file = signals_file
        self.history_file = history_file
        
        # Load historical data
        try:
            with open(history_file, 'r') as f:
                self.history = json.load(f)
        except FileNotFoundError:
            self.history = {
                'tracked_signals': [],
                'politician_performance': {},
                'signal_type_performance': {},
                'ticker_performance': {}
            }
    
    def get_stock_price(self, ticker: str, date: str = None) -> float:
        """
        Get stock price for a ticker (uses Yahoo Finance public API)
        If date is provided, gets historical price. Otherwise gets current price.
        """
        try:
            if date:
                # Get historical price
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                # For demo, return mock data - you can integrate real API
                # Using Alpha Vantage free API or Yahoo Finance
                pass
            
            # Get current price from Yahoo Finance
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            params = {'interval': '1d', 'range': '1d'}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                current_price = data['chart']['result'][0]['meta']['regularMarketPrice']
                return current_price
            
            return None
            
        except Exception as e:
            print(f"    ⚠️  Could not fetch price for {ticker}: {str(e)[:50]}")
            return None
    
    def add_signal_to_history(self, signal: dict, entry_price: float = None):
        """Add a new signal to tracking history"""
        
        # Create tracking record
        tracking_record = {
            'signal_id': f"{signal['ticker']}_{signal.get('politician', 'cluster')}_{datetime.now().strftime('%Y%m%d')}",
            'ticker': signal['ticker'],
            'signal_type': signal['signal_type'],
            'politician': signal.get('politician', signal.get('politicians', ['Unknown'])[0]),
            'entry_date': datetime.now().strftime('%Y-%m-%d'),
            'entry_price': entry_price,
            'amount': signal.get('amount', 0),
            'status': 'tracking',
            'days_tracked': 0
        }
        
        self.history['tracked_signals'].append(tracking_record)
        print(f"  ✅ Now tracking: {signal['ticker']} ({signal['signal_type']})")
    
    def update_tracked_signals(self):
        """Update performance of all tracked signals"""
        print("\n📊 Updating tracked signal performance...")
        
        updated_count = 0
        
        for signal in self.history['tracked_signals']:
            if signal['status'] != 'tracking':
                continue
            
            ticker = signal['ticker']
            entry_price = signal.get('entry_price')
            
            if not entry_price:
                continue
            
            # Get current price
            current_price = self.get_stock_price(ticker)
            
            if current_price:
                # Calculate return
                returns = ((current_price - entry_price) / entry_price) * 100
                
                # Update signal
                signal['current_price'] = current_price
                signal['return_pct'] = round(returns, 2)
                signal['days_tracked'] = (
                    datetime.now() - datetime.strptime(signal['entry_date'], '%Y-%m-%d')
                ).days
                
                updated_count += 1
                
                # Check if we should close the position (30 days or >20% gain)
                if signal['days_tracked'] >= 30 or returns > 20:
                    signal['status'] = 'closed'
                    signal['exit_date'] = datetime.now().strftime('%Y-%m-%d')
                    signal['exit_price'] = current_price
        
        print(f"  ✅ Updated {updated_count} tracked signals")
        
        # Calculate aggregate stats
        self.calculate_aggregate_stats()
    
    def calculate_aggregate_stats(self):
        """Calculate performance stats by politician, signal type, etc."""
        
        # Reset stats
        politician_returns = defaultdict(list)
        signal_type_returns = defaultdict(list)
        ticker_returns = defaultdict(list)
        
        # Aggregate returns
        for signal in self.history['tracked_signals']:
            if 'return_pct' in signal:
                returns = signal['return_pct']
                
                politician_returns[signal['politician']].append(returns)
                signal_type_returns[signal['signal_type']].append(returns)
                ticker_returns[signal['ticker']].append(returns)
        
        # Calculate stats for politicians
        self.history['politician_performance'] = {}
        for politician, returns in politician_returns.items():
            if returns:
                self.history['politician_performance'][politician] = {
                    'avg_return': round(statistics.mean(returns), 2),
                    'win_rate': round(len([r for r in returns if r > 0]) / len(returns) * 100, 1),
                    'total_signals': len(returns),
                    'best_return': round(max(returns), 2),
                    'worst_return': round(min(returns), 2)
                }
        
        # Calculate stats for signal types
        self.history['signal_type_performance'] = {}
        for sig_type, returns in signal_type_returns.items():
            if returns:
                self.history['signal_type_performance'][sig_type] = {
                    'avg_return': round(statistics.mean(returns), 2),
                    'win_rate': round(len([r for r in returns if r > 0]) / len(returns) * 100, 1),
                    'total_signals': len(returns)
                }
        
        # Calculate stats for tickers
        self.history['ticker_performance'] = {}
        for ticker, returns in ticker_returns.items():
            if returns:
                self.history['ticker_performance'][ticker] = {
                    'avg_return': round(statistics.mean(returns), 2),
                    'times_signaled': len(returns)
                }
    
    def save_history(self):
        """Save tracking history"""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2, default=str)
        print(f"\n💾 Performance history saved to {self.history_file}")
    
    def generate_performance_report(self) -> str:
        """Generate detailed performance report"""
        
        report = []
        report.append("\n" + "="*60)
        report.append("📊 PERFORMANCE TRACKING REPORT")
        report.append("="*60)
        
        # Overall stats
        active_signals = len([s for s in self.history['tracked_signals'] if s['status'] == 'tracking'])
        closed_signals = len([s for s in self.history['tracked_signals'] if s['status'] == 'closed'])
        
        report.append(f"\n📈 Portfolio Overview:")
        report.append(f"   Active Signals: {active_signals}")
        report.append(f"   Closed Signals: {closed_signals}")
        report.append(f"   Total Tracked: {len(self.history['tracked_signals'])}")
        
        # Top performing politicians
        if self.history['politician_performance']:
            report.append(f"\n👤 Top Performing Politicians:")
            
            sorted_politicians = sorted(
                self.history['politician_performance'].items(),
                key=lambda x: x[1]['avg_return'],
                reverse=True
            )[:5]
            
            for i, (politician, stats) in enumerate(sorted_politicians, 1):
                report.append(f"\n{i}. {politician}")
                report.append(f"   Avg Return: {stats['avg_return']:+.2f}%")
                report.append(f"   Win Rate: {stats['win_rate']:.1f}%")
                report.append(f"   Total Signals: {stats['total_signals']}")
        
        # Signal type performance
        if self.history['signal_type_performance']:
            report.append(f"\n🎯 Signal Type Performance:")
            
            sorted_signals = sorted(
                self.history['signal_type_performance'].items(),
                key=lambda x: x[1]['avg_return'],
                reverse=True
            )
            
            for sig_type, stats in sorted_signals:
                report.append(f"\n{sig_type}:")
                report.append(f"   Avg Return: {stats['avg_return']:+.2f}%")
                report.append(f"   Win Rate: {stats['win_rate']:.1f}%")
                report.append(f"   Total: {stats['total_signals']}")
        
        # Currently tracking
        active = [s for s in self.history['tracked_signals'] if s['status'] == 'tracking']
        if active:
            report.append(f"\n📊 Currently Tracking ({len(active)} signals):")
            
            # Sort by return
            active.sort(key=lambda x: x.get('return_pct', 0), reverse=True)
            
            for signal in active[:5]:
                report.append(f"\n• {signal['ticker']} - {signal['politician']}")
                if 'return_pct' in signal:
                    report.append(f"   Return: {signal['return_pct']:+.2f}%")
                    report.append(f"   Days: {signal['days_tracked']}")
                    report.append(f"   Entry: ${signal['entry_price']:.2f}")
                    report.append(f"   Current: ${signal['current_price']:.2f}")
        
        # Best closed trades
        closed = [s for s in self.history['tracked_signals'] if s['status'] == 'closed']
        if closed:
            report.append(f"\n🏆 Best Closed Trades:")
            
            closed.sort(key=lambda x: x.get('return_pct', 0), reverse=True)
            
            for signal in closed[:3]:
                report.append(f"\n• {signal['ticker']} - {signal['politician']}")
                report.append(f"   Return: {signal['return_pct']:+.2f}%")
                report.append(f"   Entry: ${signal['entry_price']:.2f} → Exit: ${signal['exit_price']:.2f}")
                report.append(f"   Days Held: {signal['days_tracked']}")
        
        report.append("\n" + "="*60)
        
        return "\n".join(report)
    
    def print_performance_report(self):
        """Print performance report"""
        print(self.generate_performance_report())

def main():
    """Demo/test the performance tracker"""
    
    print("🚀 Performance Tracker Demo")
    
    # Initialize tracker
    tracker = PerformanceTracker()
    
    # Load recent signals if available
    try:
        with open('signals.json', 'r') as f:
            scan_results = json.load(f)
            signals = scan_results.get('signals', [])
            
            if signals:
                print(f"\n📊 Found {len(signals)} signals from recent scan")
                print("   (In production, would start tracking these with entry prices)")
    except FileNotFoundError:
        print("\n⚠️  No signals.json found. Run scanner first.")
    
    # Update any existing tracked signals
    if tracker.history['tracked_signals']:
        tracker.update_tracked_signals()
        tracker.save_history()
    else:
        print("\n📝 No signals currently being tracked.")
        print("   Run scanner and tracker together to start tracking performance.")
    
    # Generate report
    tracker.print_performance_report()
    
    print("\n" + "="*60)
    print("✅ Performance tracking complete!")
    print("="*60)

if __name__ == "__main__":
    main()
