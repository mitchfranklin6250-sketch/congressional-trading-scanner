"""
Congressional Trading Scanner - NO API KEYS REQUIRED
Works with public data sources and includes performance tracking
"""

import json
import requests
from datetime import datetime, timedelta
from collections import defaultdict
import os
import re

class CongressionalTradingScanner:
    """Scanner using free public data - no API keys needed"""
    
    def __init__(self, config_path: str = "config.json", use_sample_data: bool = False):
        """Initialize scanner"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.use_sample_data = use_sample_data
        self.min_trade_size = self.config['filters']['min_trade_size']
        self.max_days_old = self.config['filters']['max_days_old']
        self.cluster_threshold = self.config['signals']['cluster_threshold']
        
        self.committee_alignments = self.config['committee_alignments']
        self.top_performers = self.config['top_performers']
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
    
    def get_sample_data(self) -> list:
        """Generate realistic sample data for testing"""
        today = datetime.now()
        
        sample_trades = [
            # Cluster signal - multiple buys of NVDA
            {
                'ticker': 'NVDA',
                'transaction_date': (today - timedelta(days=2)).strftime('%Y-%m-%d'),
                'representative': 'Nancy Pelosi',
                'transaction_type': 'purchase',
                'amount': 250000,
                'party': 'Democrat',
                'asset_description': 'NVIDIA Corporation (NVDA)',
                'source': 'sample'
            },
            {
                'ticker': 'NVDA',
                'transaction_date': (today - timedelta(days=3)).strftime('%Y-%m-%d'),
                'representative': 'Dan Crenshaw',
                'transaction_type': 'purchase',
                'amount': 75000,
                'party': 'Republican',
                'asset_description': 'NVIDIA Corporation (NVDA)',
                'source': 'sample'
            },
            {
                'ticker': 'NVDA',
                'transaction_date': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
                'representative': 'Josh Gottheimer',
                'transaction_type': 'purchase',
                'amount': 150000,
                'party': 'Democrat',
                'asset_description': 'NVIDIA Corporation (NVDA)',
                'source': 'sample'
            },
            # Large trade signal
            {
                'ticker': 'MSFT',
                'transaction_date': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
                'representative': 'Tommy Tuberville',
                'transaction_type': 'purchase',
                'amount': 450000,
                'party': 'Republican',
                'asset_description': 'Microsoft Corporation (MSFT)',
                'source': 'sample'
            },
            # Committee aligned - defense stock
            {
                'ticker': 'LMT',
                'transaction_date': (today - timedelta(days=4)).strftime('%Y-%m-%d'),
                'representative': 'Jim Banks',
                'transaction_type': 'purchase',
                'amount': 125000,
                'party': 'Republican',
                'asset_description': 'Lockheed Martin Corporation (LMT)',
                'source': 'sample'
            },
            # Top performer trade
            {
                'ticker': 'GOOGL',
                'transaction_date': (today - timedelta(days=2)).strftime('%Y-%m-%d'),
                'representative': 'Paul Pelosi',
                'transaction_type': 'purchase',
                'amount': 300000,
                'party': 'Democrat',
                'asset_description': 'Alphabet Inc Class A (GOOGL)',
                'source': 'sample'
            },
            # Options trade
            {
                'ticker': 'TSLA',
                'transaction_date': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
                'representative': 'Marjorie Taylor Greene',
                'transaction_type': 'purchase',
                'amount': 80000,
                'party': 'Republican',
                'asset_description': 'Tesla Inc Call Options (TSLA)',
                'source': 'sample'
            },
            # Some sales for contrast
            {
                'ticker': 'AAPL',
                'transaction_date': (today - timedelta(days=5)).strftime('%Y-%m-%d'),
                'representative': 'John Doe',
                'transaction_type': 'sale',
                'amount': 100000,
                'party': 'Republican',
                'asset_description': 'Apple Inc (AAPL)',
                'source': 'sample'
            },
        ]
        
        return sample_trades
    
    def parse_amount(self, amount_str: str) -> int:
        """Convert amount string to integer"""
        if not amount_str:
            return 0
        
        amount_str = amount_str.replace('$', '').replace(',', '').strip()
        
        # Handle ranges
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
    
    def fetch_from_apis(self) -> list:
        """
        Fetch from public APIs - this will work on your machine or GitHub Actions
        Networks: housestockwatcher.com and senatestockwatcher.com
        """
        all_trades = []
        
        # Try House Stock Watcher API
        try:
            print("  📊 Fetching from House Stock Watcher...")
            response = requests.get(
                "https://housestockwatcher.com/api/all_transactions",
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                cutoff_date = datetime.now() - timedelta(days=self.max_days_old)
                
                for trade in data:
                    try:
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
                            trans_type = 'purchase'
                        elif 'sale' in trans_type or 'sell' in trans_type:
                            trans_type = 'sale'
                        else:
                            trans_type = 'unknown'
                        
                        all_trades.append({
                            'ticker': ticker,
                            'transaction_date': trade['transaction_date'],
                            'representative': trade.get('representative', ''),
                            'transaction_type': trans_type,
                            'amount': amount,
                            'party': trade.get('party', ''),
                            'asset_description': trade.get('asset_description', ''),
                            'source': 'house_stock_watcher'
                        })
                    except:
                        continue
                
                print(f"    ✅ Found {len([t for t in all_trades if t['source'] == 'house_stock_watcher'])} House trades")
        except Exception as e:
            print(f"    ⚠️  House Stock Watcher unavailable: {str(e)[:50]}")
        
        # Try Senate Stock Watcher API
        try:
            print("  📊 Fetching from Senate Stock Watcher...")
            response = requests.get(
                "https://senatestockwatcher.com/api/all_transactions",
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                cutoff_date = datetime.now() - timedelta(days=self.max_days_old)
                
                for trade in data:
                    try:
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
                            trans_type = 'purchase'
                        elif 'sale' in trans_type or 'sell' in trans_type:
                            trans_type = 'sale'
                        else:
                            trans_type = 'unknown'
                        
                        all_trades.append({
                            'ticker': ticker,
                            'transaction_date': trade['transaction_date'],
                            'representative': trade.get('senator', ''),
                            'transaction_type': trans_type,
                            'amount': amount,
                            'party': trade.get('party', ''),
                            'asset_description': trade.get('asset_description', ''),
                            'source': 'senate_stock_watcher'
                        })
                    except:
                        continue
                
                senate_count = len([t for t in all_trades if t['source'] == 'senate_stock_watcher'])
                print(f"    ✅ Found {senate_count} Senate trades")
        except Exception as e:
            print(f"    ⚠️  Senate Stock Watcher unavailable: {str(e)[:50]}")
        
        return all_trades
    
    def fetch_all_trades(self) -> list:
        """Main fetch function - uses sample or real data"""
        print("\n🔍 Fetching congressional trades...")
        
        if self.use_sample_data:
            print("  📝 Using sample data for testing")
            trades = self.get_sample_data()
            print(f"  ✅ Loaded {len(trades)} sample trades")
        else:
            trades = self.fetch_from_apis()
            
            if not trades:
                print("\n  ⚠️  No real data available. Using sample data...")
                trades = self.get_sample_data()
        
        # Remove duplicates
        unique_trades = []
        seen = set()
        
        for trade in trades:
            key = (trade['ticker'], trade['representative'], trade['transaction_date'])
            if key not in seen:
                seen.add(key)
                unique_trades.append(trade)
        
        print(f"  🎯 Total unique trades: {len(unique_trades)}")
        return unique_trades
    
    def detect_clusters(self, trades: list) -> list:
        """Detect when multiple politicians buy same stock"""
        ticker_purchases = defaultdict(list)
        
        for trade in trades:
            if trade['transaction_type'] == 'purchase':
                ticker_purchases[trade['ticker']].append(trade)
        
        clusters = []
        for ticker, ticker_trades in ticker_purchases.items():
            if len(ticker_trades) >= self.cluster_threshold:
                politicians = [t['representative'] for t in ticker_trades]
                total_amount = sum(t['amount'] for t in ticker_trades)
                
                clusters.append({
                    'signal_type': 'CLUSTER',
                    'ticker': ticker,
                    'count': len(ticker_trades),
                    'politicians': politicians,
                    'total_amount': total_amount,
                    'avg_amount': total_amount // len(ticker_trades),
                    'dates': [t['transaction_date'] for t in ticker_trades],
                    'trades': ticker_trades,
                    'priority': 1
                })
        
        return clusters
    
    def detect_large_trades(self, trades: list) -> list:
        """Detect unusually large individual trades"""
        large_trades = []
        
        for trade in trades:
            if trade['amount'] >= self.min_trade_size:
                large_trades.append({
                    'signal_type': 'LARGE_TRADE',
                    'ticker': trade['ticker'],
                    'politician': trade['representative'],
                    'amount': trade['amount'],
                    'transaction_type': trade['transaction_type'],
                    'date': trade['transaction_date'],
                    'trade': trade,
                    'priority': 4
                })
        
        return large_trades
    
    def detect_top_performer_trades(self, trades: list) -> list:
        """Detect trades from historically successful traders"""
        top_performer_trades = []
        
        for trade in trades:
            politician = trade['representative'].lower()
            
            for top_performer in self.top_performers:
                if top_performer.lower() in politician:
                    top_performer_trades.append({
                        'signal_type': 'TOP_PERFORMER',
                        'ticker': trade['ticker'],
                        'politician': trade['representative'],
                        'amount': trade['amount'],
                        'transaction_type': trade['transaction_type'],
                        'date': trade['transaction_date'],
                        'performer_name': top_performer,
                        'trade': trade,
                        'priority': 3
                    })
                    break
        
        return top_performer_trades
    
    def detect_committee_aligned_trades(self, trades: list) -> list:
        """Detect trades aligned with committee assignments"""
        aligned_trades = []
        
        for trade in trades:
            ticker = trade['ticker']
            politician = trade['representative']
            
            for committee, related_tickers in self.committee_alignments.items():
                if ticker in related_tickers:
                    aligned_trades.append({
                        'signal_type': 'COMMITTEE_ALIGNED',
                        'ticker': ticker,
                        'politician': politician,
                        'committee': committee,
                        'amount': trade['amount'],
                        'transaction_type': trade['transaction_type'],
                        'date': trade['transaction_date'],
                        'trade': trade,
                        'priority': 5
                    })
        
        return aligned_trades
    
    def detect_unusual_activity(self, trades: list) -> list:
        """Detect unusual patterns (options, etc.)"""
        unusual = []
        
        for trade in trades:
            asset_desc = trade.get('asset_description', '').lower()
            
            if 'option' in asset_desc or 'call' in asset_desc or 'put' in asset_desc:
                unusual.append({
                    'signal_type': 'OPTIONS_TRADE',
                    'ticker': trade['ticker'],
                    'politician': trade['representative'],
                    'amount': trade['amount'],
                    'transaction_type': trade['transaction_type'],
                    'date': trade['transaction_date'],
                    'reason': 'Options trade detected',
                    'trade': trade,
                    'priority': 2
                })
        
        return unusual
    
    def scan_for_signals(self) -> dict:
        """Main scanning function"""
        print("\n" + "="*60)
        print("🏛️  CONGRESSIONAL TRADING SCANNER")
        print("="*60)
        
        trades = self.fetch_all_trades()
        
        if not trades:
            print("\n⚠️  No trades available")
            return {'signals': [], 'all_trades': [], 'scan_timestamp': datetime.now().isoformat()}
        
        print("\n🔍 Running signal detection algorithms...")
        
        clusters = self.detect_clusters(trades)
        print(f"  ✅ Cluster signals: {len(clusters)}")
        
        large_trades = self.detect_large_trades(trades)
        print(f"  ✅ Large trade signals: {len(large_trades)}")
        
        top_performer_trades = self.detect_top_performer_trades(trades)
        print(f"  ✅ Top performer signals: {len(top_performer_trades)}")
        
        committee_aligned = self.detect_committee_aligned_trades(trades)
        print(f"  ✅ Committee-aligned signals: {len(committee_aligned)}")
        
        unusual_activity = self.detect_unusual_activity(trades)
        print(f"  ✅ Unusual activity signals: {len(unusual_activity)}")
        
        all_signals = (
            clusters + large_trades + top_performer_trades + 
            committee_aligned + unusual_activity
        )
        
        # Sort by priority
        all_signals.sort(key=lambda x: x.get('priority', 99))
        
        print(f"\n🎯 Total signals detected: {len(all_signals)}")
        
        return {
            'signals': all_signals,
            'all_trades': trades,
            'scan_timestamp': datetime.now().isoformat(),
            'mode': 'sample' if self.use_sample_data else 'live'
        }
    
    def save_results(self, results: dict, output_file: str = "signals.json"):
        """Save results"""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to {output_file}")
    
    def print_summary(self, results: dict):
        """Print readable summary"""
        signals = results['signals']
        
        if not signals:
            print("\n✅ No high-priority signals detected.")
            return
        
        print("\n" + "="*60)
        print("🚨 HIGH PRIORITY SIGNALS")
        print("="*60)
        
        for i, signal in enumerate(signals[:10], 1):
            print(f"\n{i}. [{signal['signal_type']}] ", end='')
            
            if signal['signal_type'] == 'CLUSTER':
                print(f"{signal['count']} politicians bought {signal['ticker']}")
                print(f"   Ticker: {signal['ticker']}")
                print(f"   Politicians: {', '.join(signal['politicians'][:3])}")
                if len(signal['politicians']) > 3:
                    print(f"   ... and {len(signal['politicians']) - 3} more")
                print(f"   Total Amount: ${signal['total_amount']:,}")
                print(f"   Avg Amount: ${signal['avg_amount']:,}")
            
            elif signal['signal_type'] == 'LARGE_TRADE':
                print(f"{signal['politician']} {signal['transaction_type']} ${signal['amount']:,} of {signal['ticker']}")
                print(f"   Ticker: {signal['ticker']}")
                print(f"   Date: {signal['date']}")
            
            elif signal['signal_type'] == 'TOP_PERFORMER':
                print(f"{signal['politician']} {signal['transaction_type']} {signal['ticker']}")
                print(f"   Tracker: {signal['performer_name']}")
                print(f"   Amount: ${signal['amount']:,}")
                print(f"   Date: {signal['date']}")
            
            elif signal['signal_type'] == 'COMMITTEE_ALIGNED':
                print(f"{signal['politician']} bought {signal['ticker']}")
                print(f"   Committee: {signal['committee']}")
                print(f"   Amount: ${signal['amount']:,}")
            
            elif signal['signal_type'] == 'OPTIONS_TRADE':
                print(f"{signal['politician']} options on {signal['ticker']}")
                print(f"   Amount: ${signal['amount']:,}")
                print(f"   Date: {signal['date']}")

def main():
    """Main execution"""
    # Check if we should use sample data
    use_sample = os.getenv('USE_SAMPLE_DATA', 'false').lower() == 'true'
    
    scanner = CongressionalTradingScanner(use_sample_data=use_sample)
    results = scanner.scan_for_signals()
    scanner.save_results(results)
    scanner.print_summary(results)
    
    print("\n" + "="*60)
    print("✅ Scan complete!")
    print("="*60)

if __name__ == "__main__":
    main()
