"""
Enhanced Discord Alerts for Strategy Updates
Sends alerts for Congress Buys and Dan Meuser strategies
"""

import json
import requests
import os
from datetime import datetime

class StrategyAlerter:
    """Send strategy updates to Discord"""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.getenv('DISCORD_WEBHOOK_URL')
        self.enabled = bool(self.webhook_url)
    
    def send_congress_buys_alert(self, portfolio: dict):
        """Send Congress Buys portfolio update"""
        
        if not self.enabled:
            return
        
        print("\n📤 Sending Congress Buys update to Discord...")
        
        # Summary message
        summary = {
            "content": f"📊 **Congress Buys Strategy Update**\n\n"
                      f"✅ Portfolio: {portfolio['num_positions']} positions\n"
                      f"💰 Total Congressional Investment: ${portfolio['total_value']:,.0f}\n"
                      f"📈 Historical Return: +511% all-time"
        }
        
        try:
            response = requests.post(self.webhook_url, json=summary)
            if response.status_code == 204:
                print("  ✅ Summary sent")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            return
        
        # Top positions embed
        top_positions = portfolio['portfolio'][:5]
        
        fields = []
        for i, pos in enumerate(top_positions, 1):
            fields.append({
                "name": f"{i}. {pos['ticker']} ({pos['weight']}%)",
                "value": f"${pos['total_amount']:,.0f} from {pos['num_politicians']} members",
                "inline": False
            })
        
        embed = {
            "title": "🏆 Top 5 Congressional Picks",
            "description": "Highest conviction stocks (most congressional buyers)",
            "color": 0x2ECC71,
            "fields": fields,
            "footer": {
                "text": f"Last updated: {portfolio['generated_date']}"
            }
        }
        
        try:
            response = requests.post(self.webhook_url, json={"embeds": [embed]})
            if response.status_code == 204:
                print("  ✅ Top positions sent")
            
            import time
            time.sleep(0.5)
        except Exception as e:
            print(f"  ❌ Failed: {e}")
    
    def send_dan_meuser_alert(self, portfolio: dict, recent_activity: list):
        """Send Dan Meuser portfolio update"""
        
        if not self.enabled:
            return
        
        print("\n📤 Sending Dan Meuser update to Discord...")
        
        # Summary with performance
        summary = {
            "content": f"🏆 **Dan Meuser Portfolio Update**\n\n"
                      f"📈 All-Time Return: +735.85% | CAGR: 40.42%\n"
                      f"💼 Current Portfolio: {portfolio['num_positions']} positions\n"
                      f"💰 Estimated Value: ${portfolio['total_value']:,.0f}"
        }
        
        try:
            response = requests.post(self.webhook_url, json=summary)
            if response.status_code == 204:
                print("  ✅ Summary sent")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            return
        
        import time
        time.sleep(0.5)
        
        # Recent activity (if any)
        if recent_activity:
            activity_text = []
            for trade in recent_activity[:3]:
                emoji = "🟢" if trade['transaction_type'] == 'BUY' else "🔴"
                activity_text.append(
                    f"{emoji} {trade['date']}: **{trade['transaction_type']}** "
                    f"${trade['amount']:,.0f} of **{trade['ticker']}**"
                )
            
            activity_embed = {
                "title": "🔥 Recent Activity (Last 30 Days)",
                "description": "\n".join(activity_text) if activity_text else "No recent activity",
                "color": 0x3498DB
            }
            
            try:
                response = requests.post(self.webhook_url, json={"embeds": [activity_embed]})
                if response.status_code == 204:
                    print("  ✅ Recent activity sent")
                time.sleep(0.5)
            except Exception as e:
                print(f"  ❌ Failed: {e}")
        
        # Top holdings
        top_holdings = portfolio['portfolio'][:5]
        
        fields = []
        for i, pos in enumerate(top_holdings, 1):
            fields.append({
                "name": f"{i}. {pos['ticker']} ({pos['weight']}%)",
                "value": f"Position: ${pos['estimated_position']:,.0f}\nLast trade: {pos['last_trade_date']}",
                "inline": False
            })
        
        holdings_embed = {
            "title": "💎 Top 5 Holdings",
            "description": "Dan Meuser's largest positions",
            "color": 0xF39C12,
            "fields": fields
        }
        
        try:
            response = requests.post(self.webhook_url, json={"embeds": [holdings_embed]})
            if response.status_code == 204:
                print("  ✅ Top holdings sent")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
    
    def send_blended_alert(self, blended_portfolio: dict):
        """Send blended portfolio alert"""
        
        if not self.enabled:
            return
        
        print("\n📤 Sending blended portfolio to Discord...")
        
        summary = {
            "content": f"🎯 **Blended Portfolio Strategy**\n\n"
                      f"💰 Total Value: ${blended_portfolio['total_value']:,.0f}\n"
                      f"📊 60% Congress Buys + 40% Dan Meuser\n"
                      f"🎯 {len(blended_portfolio['positions'])} total positions"
        }
        
        try:
            response = requests.post(self.webhook_url, json=summary)
            if response.status_code == 204:
                print("  ✅ Blended summary sent")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            return
        
        import time
        time.sleep(0.5)
        
        # Top positions
        top_positions = blended_portfolio['positions'][:10]
        
        fields = []
        for i, pos in enumerate(top_positions, 1):
            weight = (pos['value'] / blended_portfolio['total_value']) * 100
            fields.append({
                "name": f"{i}. {pos['ticker']}",
                "value": f"${pos['value']:,.2f} ({weight:.1f}%)",
                "inline": True
            })
        
        embed = {
            "title": "🏆 Top 10 Blended Positions",
            "description": "Optimal risk/return combination",
            "color": 0x9B59B6,
            "fields": fields
        }
        
        try:
            response = requests.post(self.webhook_url, json={"embeds": [embed]})
            if response.status_code == 204:
                print("  ✅ Top positions sent")
        except Exception as e:
            print(f"  ❌ Failed: {e}")

def main():
    """Test strategy alerts"""
    
    print("🧪 Testing strategy Discord alerts...")
    
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("\n⚠️  No DISCORD_WEBHOOK_URL set")
        return
    
    alerter = StrategyAlerter(webhook_url)
    
    # Try to send Congress Buys alert
    try:
        with open('congress_buys_portfolio.json', 'r') as f:
            congress_data = json.load(f)
            alerter.send_congress_buys_alert(congress_data['portfolio'])
    except FileNotFoundError:
        print("⚠️  congress_buys_portfolio.json not found")
    
    # Try to send Dan Meuser alert
    try:
        with open('dan_meuser_portfolio.json', 'r') as f:
            dan_data = json.load(f)
            alerter.send_dan_meuser_alert(
                dan_data['current_portfolio'],
                dan_data['recent_activity']
            )
    except FileNotFoundError:
        print("⚠️  dan_meuser_portfolio.json not found")
    
    # Try to send blended alert
    try:
        with open('blended_portfolio.json', 'r') as f:
            blended_data = json.load(f)
            alerter.send_blended_alert(blended_data)
    except FileNotFoundError:
        print("⚠️  blended_portfolio.json not found")
    
    print("\n✅ Strategy alerts complete!")

if __name__ == "__main__":
    main()
