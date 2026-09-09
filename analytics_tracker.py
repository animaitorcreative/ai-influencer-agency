"""
Analytics Tracker for AI Influencer Agency
Tracks engagement metrics, performance data, and revenue projections.

Usage:
    from analytics_tracker import AnalyticsTracker
    
    tracker = AnalyticsTracker()
    results = tracker.generate_performance_report()
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict

# Import our modules
os.environ["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
import character_creator


class EngagementMetric:
    """Tracks engagement metrics for influencer posts."""
    
    def __init__(self, character_id: str):
        self.character_id = character_id
        self.posts = []
        self.metrics = {
            "total_posts": 0,
            "total_likes": 0,
            "total_shares": 0,
            "total_saves": 0,
            "average_engagement_rate": 0.0,
            "top_performing_post": None,
            "revenue_tracked": 0.0,
            "post_history": []
        }
        
    def log_post(self, caption: str, image_url: str, 
                  likes: int = 0, shares: int = 0, saves: int = 0,
                  revenue: float = 0.0):
        """Log a new post with engagement data."""
        post_data = {
            "timestamp": datetime.now().isoformat(),
            "caption": caption[:100] + ("..." if len(caption) > 100 else ""),
            "image_url": image_url,
            "likes": likes,
            "shares": shares,
            "saves": saves,
            "revenue": revenue,
            "engagement_rate": (likes + shares + saves) / 100 if (likes + shares + saves) > 0 else 0.0
        }
        
        self.posts.append(post_data)
        self.metrics["total_posts"] += 1
        self.metrics["total_likes"] += likes
        self.metrics["total_shares"] += shares
        self.metrics["total_saves"] += saves
        self.metrics["revenue_tracked"] += revenue
        
        # Update top performing post
        if not self.metrics["top_performing_post"]:
            self.metrics["top_performing_post"] = post_data
        else:
            current_total = (self.metrics["top_performing_post"]["likes"] + 
                           self.metrics["top_performing_post"]["shares"])
            new_total = likes + shares
            if new_total > current_total:
                self.metrics["top_performing_post"] = post_data
                
    def get_engagement_rate(self) -> float:
        """Calculate average engagement rate."""
        if self.metrics["total_posts"] == 0:
            return 0.0
        total_engagement = self.metrics["total_likes"] + self.metrics["total_shares"] + self.metrics["total_saves"]
        return (total_engagement / self.metrics["total_posts"]) * 100
    
    def get_top_performing_post(self) -> Dict:
        """Get the best performing post."""
        return self.metrics.get("top_performing_post", {})
    
    def get_revenue_summary(self) -> float:
        """Get total tracked revenue."""
        return self.metrics["revenue_tracked"]


class AnalyticsTracker:
    """Comprehensive analytics tracking for the influencer agency."""
    
    def __init__(self):
        self.tracker_dir = "./agency/analytics"
        os.makedirs(self.tracker_dir, exist_ok=True)
        
        # Initialize trackers for each character
        self.trackers = {}
        self.load_tracked_characters()
        
    def load_tracked_characters(self):
        """Load tracked characters from history files."""
        try:
            history_files = [f for f in os.listdir(self.tracker_dir) if f.endswith(".json")]
            
            for file in history_files:
                filepath = os.path.join(self.tracker_dir, file)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    
                character_id = data.get("character_id")
                if character_id and character_id not in self.trackers:
                    self.trackers[character_id] = EngagementMetric(character_id)
                    # Restore history
                    for post_data in data.get("posts", []):
                        self.trackers[character_id].log_post(
                            caption=post_data.get("caption", ""),
                            image_url=post_data.get("image_url", ""),
                            likes=post_data.get("likes", 0),
                            shares=post_data.get("shares", 0),
                            saves=post_data.get("saves", 0)
                        )
        except Exception as e:
            print(f"⚠️ Error loading analytics history: {e}")
            
    def save_tracker(self, character_id: str):
        """Save tracker data to file."""
        if character_id not in self.trackers:
            return
            
        tracker = self.trackers[character_id]
        filepath = os.path.join(self.tracker_dir, f"{character_id}.json")
        
        with open(filepath, 'w') as f:
            json.dump({
                "character_id": character_id,
                "total_posts": tracker.metrics["total_posts"],
                "posts": tracker.posts[-10:],  # Keep last 10 posts for memory
                "revenue_tracked": tracker.metrics["revenue_tracked"]
            }, f)
            
    def log_engagement(self, character_id: str, caption: str, image_url: str, 
                       likes: int = 0, shares: int = 0, saves: int = 0, revenue: float = 0.0):
        """Log engagement data for a character."""
        if character_id not in self.trackers:
            # Create new tracker
            bib = character_creator.get_character_bible(character_id)
            if bib:
                self.tracker_dir = os.path.join(self.tracker_dir, "by_character", character_id)
                os.makedirs(self.tracker_dir, exist_ok=True)
            self.trackers[character_id] = EngagementMetric(character_id)
            
        self.trackers[character_id].log_post(
            caption=caption,
            image_url=image_url,
            likes=likes,
            shares=shares,
            saves=saves,
            revenue=revenue
        )
        
        # Save tracker data
        self.save_tracker(character_id)
        
    def get_performance_report(self, character_id: str) -> Dict:
        """Generate a performance report for a character."""
        if character_id not in self.trackers:
            return {"error": f"Character {character_id} not tracked"}
            
        tracker = self.trackers[character_id]
        
        report = {
            "character_id": character_id,
            "total_posts": tracker.metrics["total_posts"],
            "total_likes": tracker.metrics["total_likes"],
            "total_shares": tracker.metrics["total_shares"],
            "total_saves": tracker.metrics["total_saves"],
            "average_engagement_rate": round(tracker.get_engagement_rate(), 2),
            "total_revenue_tracked": tracker.get_revenue_summary(),
            "top_performing_post": tracker.get_top_performing_post() if tracker.get_top_performing_post() else None,
            "posts_history": tracker.posts[-5:],  # Last 5 posts
            "generated_at": datetime.now().isoformat()
        }
        
        return report
    
    def get_all_performance_reports(self) -> Dict:
        """Get performance reports for all tracked characters."""
        reports = {}
        for char_id, tracker in self.trackers.items():
            reports[char_id] = self.get_performance_report(char_id)
        return reports


class RevenueProjections:
    """Revenue projections based on engagement metrics and pricing tiers."""
    
    PRICING_TIERS = {
        "standard": {"rate_per_post": 100, "min_posts": 5},
        "premium": {"rate_per_post": 500, "min_posts": 20},
        "enterprise": {"rate_per_post": 2000, "min_posts": 50}
    }
    
    def __init__(self):
        self.tracker = AnalyticsTracker()
        
    def estimate_monthly_revenue(self, character_id: str) -> Dict:
        """Estimate monthly revenue based on engagement."""
        report = self.tracker.get_performance_report(character_id)
        
        if "error" in report:
            return {"error": report["error"]}
            
        total_posts = report["total_posts"]
        avg_engagement = report["average_engagement_rate"]
        revenue_tracked = report["total_revenue_tracked"]
        
        # Estimate potential revenue based on engagement and historical data
        estimated_monthly = self._calculate_estimated_monthly(revenue_tracked, total_posts)
        
        return {
            "character_id": character_id,
            "estimated_monthly_revenue": round(estimated_monthly, 2),
            "posts_history": report["total_posts"],
            "revenue_tracked_to_date": revenue_tracked,
            "growth_trajectory": self._calculate_growth_trajectory(report),
            "recommended_tier": self._recommend_pricing_tier(avg_engagement)
        }
    
    def _calculate_estimated_monthly(self, current_revenue: float, total_posts: int) -> float:
        """Estimate monthly revenue based on trend."""
        if total_posts == 0:
            return 100.0  # Base estimate
            
        # Simple linear projection - in production, this would be more sophisticated
        posts_per_month = total_posts / max(1, int(datetime.now().strftime("%m")))
        revenue_per_post = current_revenue / max(total_posts, 1)
        
        return round(revenue_per_post * posts_per_month * 30, 2)
    
    def _calculate_growth_trajectory(self, report: Dict) -> str:
        """Calculate growth trajectory based on recent posts."""
        if len(report.get("posts_history", [])) < 2:
            return "insufficient_data"
            
        # Compare last 2 posts for trend
        last_two = report["posts_history"][-2:]
        
        if not last_two or not all(isinstance(p, dict) for p in last_two):
            return "insufficient_data"
            
        try:
            recent_engagement = sum(p.get("likes", 0) + p.get("shares", 0) 
                                   for p in last_two)
            if recent_engagement == 0:
                return "no_recent_engagement"
                
            # Simplified trend detection
            return "growing" if len(last_two) > 2 else "neutral"
        except Exception:
            return "insufficient_data"
    
    def _recommend_pricing_tier(self, avg_engagement_rate: float) -> str:
        """Recommend pricing tier based on engagement rate."""
        if avg_engagement_rate >= 5.0:
            return "enterprise"
        elif avg_engagement_rate >= 2.0:
            return "premium"
        else:
            return "standard"


def main():
    """Test the analytics tracker."""
    from datetime import datetime
    
    tracker = AnalyticsTracker()
    
    # Create a test character and log some engagement
    bib = CharacterCreator.create_character("Test_Influencer", "Tech & AI")
    
    # Simulate posting
    for i in range(5):
        post_id = f"post_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"
        
        tracker.log_engagement(bib.character_id, 
                              f"Test post {i+1} from Test_Influencer",
                              f"https://example.com/test_{i}.jpg",
                              likes=50 + i*10,  # Simulating growth
                              shares=i*2,
                              saves=2,
                              revenue=(i+1) * 100.0)  # $100 per post
        
        print(f"✓ Logged post {post_id} with ${(i+1)*100:.2f}")
        
    # Generate report
    report = tracker.get_performance_report(bib.character_id)
    
    revenue_proj = RevenueProjections()
    projection = revenue_proj.estimate_monthly_revenue(bib.character_id)
    
    print(f"\n📊 Performance Report for {bib.name}:")
    print(f"   Total Posts: {report['total_posts']}")
    print(f"   Total Likes: {report['total_likes']}")
    print(f"   Average Engagement Rate: {report['average_engagement_rate']:.2f}%")
    print(f"   Revenue Tracked: ${report['total_revenue_tracked']:.2f}")
    
    print(f"\n💰 Monthly Revenue Projection: ${projection['estimated_monthly_revenue']:.2f}")
    print(f"   Recommended Tier: {projection['recommended_tier'].upper()}")

if __name__ == "__main__":
    main()
