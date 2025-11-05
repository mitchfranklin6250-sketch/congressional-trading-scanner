"""
Discord Alert System for Congressional Trading Scanner
Sends beautiful formatted alerts to Discord
"""

import json
import requests
import os
from datetime import datetime

class DiscordAlerter:
    """Send trading signals to Discord"""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.getenv('DISCORD_WEBHOOK_URL')
        
        if not self.webhook_url:
            print("⚠️  No Discord webhook URL configured")
            self.enabled = False
        else:
            self.enabled = True
    
    def create_signal_embed(self, signal: dict) -> dict:
        """Create a rich embed for a signal"""
        
        # Color coding by signal type
        colors = {
            'CLUSTER': 0xFF6B6B,      # Red
            'OPTIONS_TRADE': 0x9B59B6,  # Purple
            'TOP_PERFORMER': 0x3498DB,  # Blue
            'LARGE_TRADE': 0xF39C12,    # Orange
            'COMMITTEE_ALIGNED': 0x2ECC71  # Green
        }
        
        color = colors.get(signal['signal_type'], 0x95A5A6)
        
        # Create embed based on signal type
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
                    "name": "Tracker",
                    "value": signal.get('performer_name', signal['politician']),
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
                    "name": "Reason",
                    "value": signal['reason'],
                    "inline": False
                }
            ]
        
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
                "text": "Congressional Trading Scanner"
            }
        }
        
        return embed
    
    def send_signals(self, signals: list, max_signals: int = 10):
        """Send signals to Discord"""
        
        if not self.enabled:
            print("⚠️  Discord alerts disabled (no webhook URL)")
            return
        
        if not signals:
            print("✅ No signals to send to Discord")
            return
        
        print(f"\n📤 Sending {len(signals[:max_signals])} signals to Discord...")
        
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
        
        # Send individual signal embeds
        sent_count = 0
        for signal in signals[:max_signals]:
            embed = self.create_signal_embed(signal)
            payload = {"embeds": [embed]}
            
            try:
                response = requests.post(self.webhook_url, json=payload)
                
                if response.status_code == 204:
                    sent_count += 1
                else:
                    print(f"  ⚠️  Failed to send signal: {response.status_code}")
                
                # Rate limiting - Discord allows 5 messages per 2 seconds
                import time
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ❌ Error sending signal: {e}")
        
        print(f"  ✅ Sent {sent_count}/{len(signals[:max_signals])} signals to Discord")
    
    def send_performance_report(self, report_text: str):
        """Send performance tracking report to Discord"""
        
        if not self.enabled:
            return
        
        print("\n📤 Sending performance report to Discord...")
        
        # Discord has 2000 char limit, so chunk if needed
        chunks = [report_text[i:i+1900] for i in range(0, len(report_text), 1900)]
        
        for i, chunk in enumerate(chunks):
            msg = {
                "content": f"```\n{chunk}\n```"
            }
            
            try:
                response = requests.post(self.webhook_url, json=msg)
                if response.status_code == 204:
                    print(f"  ✅ Report chunk {i+1}/{len(chunks)} sent")
                
                import time
                time.sleep(0.5)
            except Exception as e:
                print(f"  ❌ Error sending report: {e}")

def main():
    """Test Discord alerts"""
    
    print("🧪 Testing Discord alerts...")
    
    # Check for webhook URL
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("\n⚠️  No DISCORD_WEBHOOK_URL environment variable set")
        print("   Set it to test Discord alerts:")
        print("   export DISCORD_WEBHOOK_URL='your_webhook_url_here'")
        return
    
    alerter = DiscordAlerter(webhook_url)
    
    # Try to load signals from recent scan
    try:
        with open('signals.json', 'r') as f:
            results = json.load(f)
            signals = results.get('signals', [])
            
            if signals:
                print(f"\n📊 Found {len(signals)} signals to send")
                alerter.send_signals(signals)
            else:
                print("\n⚠️  No signals found in signals.json")
    except FileNotFoundError:
        print("\n⚠️  signals.json not found. Run scanner first.")
    
    print("\n" + "="*60)
    print("✅ Discord alert test complete!")
    print("="*60)

if __name__ == "__main__":
    main()
