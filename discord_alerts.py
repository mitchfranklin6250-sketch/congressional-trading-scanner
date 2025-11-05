"""
Enhanced Discord Alerts with Portfolio Context
Shows politician's current holdings when alerting on their trades
"""

import json
import requests
import os
from datetime import datetime, timedelta
from collections import defaultdict
import re

class EnhancedDiscordAlerter:
    """Send trading signals with portfolio context to Discord"""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.getenv('DISCORD_WEBHOOK_URL')
        self.enabled = bool(self.webhook_url)
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
    
    def fetch_politician_portfolio(self, politician_name: str) -> dict:
        """Fetch a politician's current portfolio from recent trades"""
        print(f"  📊 Fetching {politician_name}'s portfolio...")
        
        all_trades = []
        lookback_date = datetime.now() - timedelta(days=365)
        
        # Try House Stock Watcher
        try:
            response = requests.get(
                "https://housestockwatcher.com/api/all_transactions",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for trade in data:
                    try:
                        representative = trade.get('representative', '')
                        if politician_name.lower() not in representative.lower():
                            continue
                        
                        trade_date = datetime.strptime(trade['transaction_date'], '%Y-%m-%d')
                        if trade_date < lookback_date:
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
                            continue
                        
                        all_trades.append({
                            'ticker': ticker,
                            'date': trade['transaction_date'],
                            'type': trans_type,
                            'amount': amount
                        })
                    except:
                        continue
        except:
            pass
        
        # Try Senate Stock Watcher
        try:
            response = requests.get(
                "https://senatestockwatcher.com/api/all_transactions",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for trade in data:
                    try:
                        senator = trade.get('senator', '')
                        if politician_name.lower() not in senator.lower():
                            continue
                        
                        trade_date = datetime.strptime(trade['transaction_date'], '%Y-%m-%d')
                        if trade_date < lookback_date:
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
                            continue
                        
                        all_trades.append({
                            'ticker': ticker,
                            'date': trade['transaction_date'],
                            'type': trans_type,
                            'amount': amount
                        })
                    except:
                        continue
        except:
            pass
        
        # Calculate current portfolio
        positions = defaultdict(lambda: {'buys': 0, 'sells': 0, 'net': 0})
        
        for trade in all_trades:
            ticker = trade['ticker']
            amount = trade['amount']
            
            if trade['type'] == 'BUY':
                positions[ticker]['buys'] += amount
                positions[ticker]['net'] += amount
            else:
                positions[ticker]['sells'] += amount
                positions[ticker]['net'] -= amount
        
        # Build portfolio (only positive positions)
        portfolio = []
        total_value = 0
        
        for ticker, data in positions.items():
            if data['net'] > 0:
                portfolio.append({
                    'ticker': ticker,
                    'value': data['net']
                })
                total_value += data['net']
        
        # Calculate weights
        for pos in portfolio:
            pos['weight'] = round((pos['value'] / total_value) * 100, 1) if total_value > 0 else 0
        
        # Sort by weight
        portfolio.sort(key=lambda x: x['weight'], reverse=True)
        
        return {
            'portfolio': portfolio[:10],  # Top 10
            'total_value': total_value,
            'num_positions': len(portfolio)
        }
    
    def create_enhanced_signal_embed(self, signal: dict) -> dict:
        """Create enhanced embed with portfolio context"""
        
        # Standard colors by signal type
        colors = {
            'CLUSTER': 0xFF6B6B,
            'OPTIONS_TRADE': 0x9B59B6,
            'TOP_PERFORMER': 0x3498DB,
            'LARGE_TRADE': 0xF39C12,
            'COMMITTEE_ALIGNED': 0x2ECC71
        }
        
        color = colors.get(signal['signal_type'], 0x95A5A6)
        
        # Build base embed (same as before)
        if signal['signal_type'] == 'CLUSTER':
            title = f"🚨 Cluster Signal: {signal['count']} politicians bought {signal['ticker']}"
            description = f"**Multiple congressional purchases detected**"
            
            fields = [
                {
                    "name": "Ticker",
                    "value": f"`{signal['ticker']}`",
                    "inline": True
                },
                {
                    "name": "Count",
                    "value": f"{signal['count']} politicians",
                    "inline": True
                },
                {
                    "name": "Total Amount",
                    "value": f"${signal['total_amount']:,}",
                    "inline": True
                },
                {
                    "name": "Politicians",
                    "value": "\n".join([f"• {p}" for p in signal['politicians'][:5]]),
                    "inline": False
                }
            ]
            
            if len(signal['politicians']) > 5:
                fields[-1]['value'] += f"\n... and {len(signal['politicians']) - 5} more"
        
        elif signal['signal_type'] == 'TOP_PERFORMER':
            title = f"⭐ Top Performer Trade: {signal['politician']}"
            description = f"**{signal['transaction_type'].title()} of {signal['ticker']}**"
            
            fields = [
                {
                    "name": "Ticker",
                    "value": f"`{signal['ticker']}`",
                    "inline": True
                },
                {
                    "name": "Amount",
                    "value": f"${signal['amount']:,}",
                    "inline": True
                },
                {
                    "name": "Date",
                    "value": signal['date'],
                    "inline": True
                }
            ]
            
            # ADD PORTFOLIO CONTEXT
            try:
                portfolio = self.fetch_politician_portfolio(signal['politician'])
                
                if portfolio['portfolio']:
                    portfolio_text = []
                    for i, pos in enumerate(portfolio['portfolio'][:5], 1):
                        # Highlight if this is the ticker they just traded
                        emoji = "🔥 " if pos['ticker'] == signal['ticker'] else ""
                        portfolio_text.append(
                            f"{emoji}{i}. **{pos['ticker']}** - {pos['weight']}% (${pos['value']:,.0f})"
                        )
                    
                    fields.append({
                        "name": f"📊 {signal['politician']}'s Current Portfolio",
                        "value": "\n".join(portfolio_text),
                        "inline": False
                    })
                    
                    fields.append({
                        "name": "Portfolio Stats",
                        "value": f"Total Positions: {portfolio['num_positions']} | Est. Value: ${portfolio['total_value']:,.0f}",
                        "inline": False
                    })
            except Exception as e:
                print(f"    ⚠️  Could not fetch portfolio: {e}")
        
        elif signal['signal_type'] == 'LARGE_TRADE':
            title = f"💰 Large Trade: {signal['politician']}"
            description = f"**{signal['transaction_type'].title()} of {signal['ticker']}**"
            
            fields = [
                {
                    "name": "Ticker",
                    "value": f"`{signal['ticker']}`",
                    "inline": True
                },
                {
                    "name": "Amount",
                    "value": f"${signal['amount']:,}",
                    "inline": True
                },
                {
                    "name": "Date",
                    "value": signal['date'],
                    "inline": True
                }
            ]
            
            # ADD PORTFOLIO CONTEXT for large trades too
            try:
                portfolio = self.fetch_politician_portfolio(signal['politician'])
                
                if portfolio['portfolio']:
                    portfolio_text = []
                    for i, pos in enumerate(portfolio['portfolio'][:5], 1):
                        emoji = "🔥 " if pos['ticker'] == signal['ticker'] else ""
                        portfolio_text.append(
                            f"{emoji}{i}. **{pos['ticker']}** - {pos['weight']}% (${pos['value']:,.0f})"
                        )
                    
                    fields.append({
                        "name": f"📊 {signal['politician']}'s Top Holdings",
                        "value": "\n".join(portfolio_text),
                        "inline": False
                    })
            except:
                pass
        
        elif signal['signal_type'] == 'COMMITTEE_ALIGNED':
            title = f"🏛️ Committee-Aligned Trade: {signal['politician']}"
            description = f"**{signal['ticker']} related to {signal['committee']}**"
            
            fields = [
                {
                    "name": "Ticker",
                    "value": f"`{signal['ticker']}`",
                    "inline": True
                },
                {
                    "name": "Committee",
                    "value": signal['committee'],
                    "inline": True
                },
                {
                    "name": "Amount",
                    "value": f"${signal['amount']:,}",
                    "inline": True
                }
            ]
        
        elif signal['signal_type'] == 'OPTIONS_TRADE':
            title = f"📊 Options Trade: {signal['politician']}"
            description = f"**Options activity on {signal['ticker']}**"
            
            fields = [
                {
                    "name": "Ticker",
                    "value": f"`{signal['ticker']}`",
                    "inline": True
                },
                {
                    "name": "Amount",
                    "value": f"${signal['amount']:,}",
                    "inline": True
                },
                {
                    "name": "Date",
                    "value": signal['date'],
                    "inline": True
                }
            ]
        
        else:
            title = f"📌 {signal['signal_type']}: {signal.get('politician', 'Unknown')}"
            description = f"**{signal.get('ticker', 'N/A')}**"
            fields = []
        
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "fields": fields,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "Congressional Trading Scanner with Portfolio Context"
            }
        }
        
        return embed
    
    def send_signals(self, signals: list, max_signals: int = 10):
        """Send enhanced signals to Discord"""
        
        if not self.enabled:
            print("⚠️  Discord alerts disabled (no webhook URL)")
            return
        
        if not signals:
            print("✅ No signals to send to Discord")
            return
        
        print(f"\n📤 Sending {len(signals[:max_signals])} enhanced signals to Discord...")
        
        # Send summary message first
        summary_msg = {
            "content": f"🚨 **Congressional Trading Alert**\n\n"
                      f"Found **{len(signals)}** high-priority signals\n"
                      f"Scan time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        try:
            response = requests.post(self.webhook_url, json=summary_msg)
            if response.status_code == 204:
                print("  ✅ Summary sent")
        except Exception as e:
            print(f"  ❌ Failed to send summary: {e}")
        
        # Send individual enhanced signal embeds
        sent_count = 0
        for signal in signals[:max_signals]:
            embed = self.create_enhanced_signal_embed(signal)
            payload = {"embeds": [embed]}
            
            try:
                response = requests.post(self.webhook_url, json=payload)
                
                if response.status_code == 204:
                    sent_count += 1
                else:
                    print(f"  ⚠️  Failed to send signal: {response.status_code}")
                
                import time
                time.sleep(1)  # Slower to allow portfolio fetching
                
            except Exception as e:
                print(f"  ❌ Error sending signal: {e}")
        
        print(f"  ✅ Sent {sent_count}/{len(signals[:max_signals])} enhanced signals to Discord")

def main():
    """Test enhanced Discord alerts"""
    
    print("🧪 Testing enhanced Discord alerts...")
    
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("\n⚠️  No DISCORD_WEBHOOK_URL environment variable set")
        return
    
    alerter = EnhancedDiscordAlerter(webhook_url)
    
    # Try to load signals from recent scan
    try:
        with open('signals.json', 'r') as f:
            results = json.load(f)
            signals = results.get('signals', [])
            
            if signals:
                print(f"\n📊 Found {len(signals)} signals to send")
                alerter.send_signals(signals, max_signals=5)  # Send top 5 with portfolio context
            else:
                print("\n⚠️  No signals found in signals.json")
    except FileNotFoundError:
        print("\n⚠️  signals.json not found. Run scanner first.")
    
    print("\n" + "="*60)
    print("✅ Enhanced Discord alert test complete!")
    print("="*60)

if __name__ == "__main__":
    main()
