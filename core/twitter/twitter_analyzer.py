"""
Comprehensive Twitter OSINT Analyzer
Extracts intelligence from Twitter profiles, tweets, and engagement patterns
"""

import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
import re


class TwitterAnalyzer:
    """
    Comprehensive Twitter/X OSINT Analysis
    
    Features:
    - User profile analysis
    - Tweet history and patterns
    - Engagement metrics (likes, retweets, replies)
    - Follower/following analysis
    - Network mapping
    - Content analysis
    - Timeline patterns
    - Exposure detection
    """
    
    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token
        self.base_url = "https://api.twitter.com/2"
        self.headers = {
            "Authorization": f"Bearer {bearer_token}"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def analyze_user(self, username: str) -> Dict[str, Any]:
        """
        Comprehensive user analysis
        
        Args:
            username: Twitter username (without @)
        
        Returns:
            Complete intelligence report
        """
        # Remove @ if provided
        username = username.lstrip('@')
        
        logger.info(f"Starting Twitter OSINT analysis for: @{username}")
        
        results = {
            "username": username,
            "analysis_timestamp": datetime.now().isoformat(),
            "profile": {},
            "tweets": {},
            "engagement": {},
            "network": {},
            "exposures": [],
            "intelligence_summary": {}
        }
        
        try:
            # Step 1: Get user profile
            user_data = self._get_user_profile(username)
            if not user_data:
                results["error"] = "User not found"
                return results
            
            user_id = user_data['id']
            results["profile"] = self._analyze_profile(user_data)
            
            # Step 2: Analyze tweets
            results["tweets"] = self._analyze_tweets(user_id, username)
            
            # Step 3: Engagement analysis
            results["engagement"] = self._analyze_engagement(results["tweets"])
            
            # Step 4: Network analysis (if quota allows)
            try:
                results["network"] = self._analyze_network(user_id)
            except Exception as e:
                logger.warning(f"Network analysis skipped: {e}")
                results["network"] = {"error": "Limited by API quota"}
            
            # Step 5: Exposure detection
            results["exposures"] = self._detect_exposures(username, results)
            
            # Step 6: Intelligence summary
            results["intelligence_summary"] = self._create_intelligence_summary(results)
            
            logger.success(f"✓ Twitter analysis completed for @{username}")
            
        except Exception as e:
            logger.error(f"Twitter analysis failed: {e}")
            results["error"] = str(e)
        
        return results
    
    def _get_user_profile(self, username: str) -> Optional[Dict]:
        """Fetch user profile data"""
        try:
            url = f"{self.base_url}/users/by/username/{username}"
            params = {
                "user.fields": "created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,verified_type,withheld"
            }
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data')
            elif response.status_code == 404:
                return None
            else:
                logger.error(f"Twitter API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to fetch user profile: {e}")
            return None
    
    def _analyze_profile(self, user_data: Dict) -> Dict[str, Any]:
        """Analyze user profile information"""
        logger.info(f"Analyzing profile for @{user_data.get('username')}")
        
        # Calculate account age
        created_at = datetime.fromisoformat(user_data['created_at'].replace('Z', '+00:00'))
        account_age_days = (datetime.now(created_at.tzinfo) - created_at).days
        
        metrics = user_data.get('public_metrics', {})
        entities = user_data.get('entities', {})
        
        # Extract URLs and mentions from description
        urls = []
        if entities.get('description', {}).get('urls'):
            urls = [url['expanded_url'] for url in entities['description']['urls']]
        
        profile = {
            "basic_info": {
                "username": user_data.get('username'),
                "name": user_data.get('name'),
                "bio": user_data.get('description'),
                "location": user_data.get('location'),
                "url": user_data.get('url'),
                "profile_image": user_data.get('profile_image_url'),
                "verified": user_data.get('verified', False),
                "verified_type": user_data.get('verified_type'),
                "protected": user_data.get('protected', False),
                "urls_in_bio": urls
            },
            "account_metrics": {
                "followers": metrics.get('followers_count', 0),
                "following": metrics.get('following_count', 0),
                "tweets": metrics.get('tweet_count', 0),
                "listed_count": metrics.get('listed_count', 0),
                "account_created": user_data.get('created_at'),
                "account_age_days": account_age_days
            },
            "account_status": {
                "verified": user_data.get('verified', False),
                "protected": user_data.get('protected', False),
                "has_pinned_tweet": user_data.get('pinned_tweet_id') is not None
            }
        }
        
        return profile
    
    def _analyze_tweets(self, user_id: str, username: str) -> Dict[str, Any]:
        """Analyze user's tweet history"""
        logger.info(f"Analyzing tweets for @{username}")
        
        try:
            url = f"{self.base_url}/users/{user_id}/tweets"
            params = {
                "max_results": 100,  # Get up to 100 recent tweets
                "tweet.fields": "created_at,public_metrics,entities,referenced_tweets,reply_settings,lang,possibly_sensitive",
                "exclude": "retweets"  # Exclude retweets for original content
            }
            
            response = self.session.get(url, params=params)
            
            if response.status_code != 200:
                return {"error": f"Failed to fetch tweets: {response.status_code}"}
            
            data = response.json()
            tweets = data.get('data', [])
            
            if not tweets:
                return {"total_tweets": 0, "message": "No tweets found or account is protected"}
            
            # Analyze tweet patterns
            hashtags = []
            mentions = []
            urls = []
            languages = {}
            hourly_pattern = [0] * 24
            daily_pattern = {}
            tweet_types = {"original": 0, "replies": 0, "quotes": 0}
            
            recent_tweets = []
            
            for tweet in tweets:
                # Time patterns
                created_at = datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00'))
                hour = created_at.hour
                day = created_at.strftime('%Y-%m-%d')
                
                hourly_pattern[hour] += 1
                daily_pattern[day] = daily_pattern.get(day, 0) + 1
                
                # Language
                lang = tweet.get('lang', 'unknown')
                languages[lang] = languages.get(lang, 0) + 1
                
                # Entities
                entities = tweet.get('entities', {})
                if entities.get('hashtags'):
                    hashtags.extend([h['tag'] for h in entities['hashtags']])
                if entities.get('mentions'):
                    mentions.extend([m['username'] for m in entities['mentions']])
                if entities.get('urls'):
                    urls.extend([u.get('expanded_url', u['url']) for u in entities['urls']])
                
                # Tweet types
                referenced = tweet.get('referenced_tweets', [])
                if referenced:
                    ref_type = referenced[0].get('type')
                    if ref_type == 'replied_to':
                        tweet_types['replies'] += 1
                    elif ref_type == 'quoted':
                        tweet_types['quotes'] += 1
                else:
                    tweet_types['original'] += 1
                
                # Store recent tweets
                metrics = tweet.get('public_metrics', {})
                recent_tweets.append({
                    "text": tweet.get('text', '')[:200],  # Truncate for response size
                    "created_at": tweet['created_at'],
                    "likes": metrics.get('like_count', 0),
                    "retweets": metrics.get('retweet_count', 0),
                    "replies": metrics.get('reply_count', 0),
                    "impressions": metrics.get('impression_count'),
                    "lang": tweet.get('lang')
                })
            
            # Most active hour
            most_active_hour = hourly_pattern.index(max(hourly_pattern)) if max(hourly_pattern) > 0 else 0
            
            # Top hashtags and mentions
            from collections import Counter
            top_hashtags = dict(Counter(hashtags).most_common(20))
            top_mentions = dict(Counter(mentions).most_common(20))
            
            return {
                "total_analyzed": len(tweets),
                "recent_tweets": recent_tweets[:20],  # Limit to 20 most recent
                "patterns": {
                    "tweet_types": tweet_types,
                    "most_active_hour": most_active_hour,
                    "hourly_distribution": hourly_pattern,
                    "daily_distribution": daily_pattern,
                    "languages": languages
                },
                "content_analysis": {
                    "top_hashtags": top_hashtags,
                    "top_mentions": top_mentions,
                    "unique_hashtags": len(set(hashtags)),
                    "unique_mentions": len(set(mentions)),
                    "external_links": len(urls)
                }
            }
            
        except Exception as e:
            logger.error(f"Tweet analysis failed: {e}")
            return {"error": str(e)}
    
    def _analyze_engagement(self, tweets_data: Dict) -> Dict[str, Any]:
        """Analyze engagement metrics"""
        recent_tweets = tweets_data.get('recent_tweets', [])
        
        if not recent_tweets:
            return {"message": "No tweets to analyze"}
        
        total_likes = sum(t.get('likes', 0) for t in recent_tweets)
        total_retweets = sum(t.get('retweets', 0) for t in recent_tweets)
        total_replies = sum(t.get('replies', 0) for t in recent_tweets)
        
        avg_likes = total_likes / len(recent_tweets) if recent_tweets else 0
        avg_retweets = total_retweets / len(recent_tweets) if recent_tweets else 0
        avg_replies = total_replies / len(recent_tweets) if recent_tweets else 0
        
        # Find most engaging tweet
        most_liked = max(recent_tweets, key=lambda x: x.get('likes', 0)) if recent_tweets else None
        most_retweeted = max(recent_tweets, key=lambda x: x.get('retweets', 0)) if recent_tweets else None
        
        return {
            "totals": {
                "likes": total_likes,
                "retweets": total_retweets,
                "replies": total_replies
            },
            "averages": {
                "likes_per_tweet": round(avg_likes, 2),
                "retweets_per_tweet": round(avg_retweets, 2),
                "replies_per_tweet": round(avg_replies, 2)
            },
            "top_performing": {
                "most_liked": {
                    "text": most_liked.get('text', '')[:100] if most_liked else None,
                    "likes": most_liked.get('likes', 0) if most_liked else 0
                },
                "most_retweeted": {
                    "text": most_retweeted.get('text', '')[:100] if most_retweeted else None,
                    "retweets": most_retweeted.get('retweets', 0) if most_retweeted else 0
                }
            }
        }
    
    def _analyze_network(self, user_id: str) -> Dict[str, Any]:
        """Analyze follower/following network (may hit rate limits)"""
        network = {
            "followers_sample": [],
            "following_sample": [],
            "note": "Limited to samples due to API quotas"
        }
        
        # Note: Getting full follower lists requires elevated access
        # This is a basic implementation that may not work with basic tier
        
        return network
    
    def _detect_exposures(self, username: str, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect potential exposure risks"""
        logger.info(f"Detecting exposures for @{username}")
        
        exposures = []
        profile = results.get("profile", {})
        basic_info = profile.get("basic_info", {})
        tweets = results.get("tweets", {})
        
        # Location exposure
        if basic_info.get("location"):
            exposures.append({
                "type": "Location Disclosure",
                "severity": "MEDIUM",
                "description": "Geographical location visible in profile",
                "value": basic_info["location"],
                "recommendation": "Consider removing precise location data"
            })
        
        # URL exposure
        urls_in_bio = basic_info.get("urls_in_bio", [])
        if urls_in_bio:
            exposures.append({
                "type": "External Links",
                "severity": "LOW",
                "description": f"{len(urls_in_bio)} external link(s) in bio",
                "value": ", ".join(urls_in_bio[:3]),
                "recommendation": "Review if all links should be public"
            })
        
        # Protected account check
        if not basic_info.get("protected"):
            exposures.append({
                "type": "Public Account",
                "severity": "LOW",
                "description": "Account tweets are publicly visible",
                "value": "All tweets accessible without approval",
                "recommendation": "Consider enabling protected mode for privacy"
            })
        
        # High tweet count
        tweet_count = profile.get("account_metrics", {}).get("tweets", 0)
        if tweet_count > 10000:
            exposures.append({
                "type": "Extensive Tweet History",
                "severity": "MEDIUM",
                "description": "Large volume of public tweets",
                "value": f"{tweet_count} total tweets",
                "recommendation": "Review old tweets for sensitive information"
            })
        
        # Frequent mentions exposure
        top_mentions = tweets.get("content_analysis", {}).get("top_mentions", {})
        if top_mentions and len(top_mentions) > 10:
            exposures.append({
                "type": "Network Exposure",
                "severity": "LOW",
                "description": "Frequent interactions reveal social network",
                "value": f"Mentions {len(top_mentions)} different accounts regularly",
                "recommendation": "Be aware of revealed associations"
            })
        
        return exposures
    
    def _create_intelligence_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create executive intelligence summary"""
        profile = results.get("profile", {})
        tweets = results.get("tweets", {})
        engagement = results.get("engagement", {})
        
        metrics = profile.get("account_metrics", {})
        patterns = tweets.get("patterns", {})
        
        return {
            "account_type": self._determine_account_type(profile, tweets),
            "activity_level": self._categorize_activity(tweets),
            "engagement_rate": self._calculate_engagement_rate(metrics, engagement),
            "primary_language": self._get_primary_language(patterns),
            "most_active_time": patterns.get("most_active_hour", 0),
            "follower_ratio": self._calculate_follower_ratio(metrics),
            "content_focus": self._analyze_content_focus(tweets),
            "exposure_risk": self._calculate_exposure_risk(results.get("exposures", [])),
            "key_findings": self._extract_key_findings(results)
        }
    
    def _determine_account_type(self, profile: Dict, tweets: Dict) -> str:
        """Determine account type"""
        metrics = profile.get("account_metrics", {})
        verified = profile.get("account_status", {}).get("verified", False)
        followers = metrics.get("followers", 0)
        
        if verified:
            return "Verified Account"
        elif followers > 100000:
            return "Influencer"
        elif followers > 10000:
            return "Popular Account"
        elif followers > 1000:
            return "Active User"
        else:
            return "Regular User"
    
    def _categorize_activity(self, tweets: Dict) -> str:
        """Categorize posting activity"""
        total = tweets.get("total_analyzed", 0)
        
        if total >= 80:
            return "Very Active"
        elif total >= 50:
            return "Active"
        elif total >= 20:
            return "Moderate"
        elif total > 0:
            return "Low"
        else:
            return "Minimal/Protected"
    
    def _calculate_engagement_rate(self, metrics: Dict, engagement: Dict) -> str:
        """Calculate engagement rate"""
        followers = metrics.get("followers", 1)
        avg_engagement = engagement.get("averages", {})
        avg_likes = avg_engagement.get("likes_per_tweet", 0)
        
        if followers == 0:
            return "N/A"
        
        rate = (avg_likes / followers) * 100 if followers > 0 else 0
        
        if rate > 10:
            return "Very High"
        elif rate > 5:
            return "High"
        elif rate > 1:
            return "Moderate"
        else:
            return "Low"
    
    def _get_primary_language(self, patterns: Dict) -> str:
        """Get primary language"""
        languages = patterns.get("languages", {})
        if not languages:
            return "Unknown"
        return max(languages.items(), key=lambda x: x[1])[0] if languages else "Unknown"
    
    def _calculate_follower_ratio(self, metrics: Dict) -> float:
        """Calculate follower to following ratio"""
        followers = metrics.get("followers", 0)
        following = metrics.get("following", 1)
        return round(followers / following, 2) if following > 0 else 0
    
    def _analyze_content_focus(self, tweets: Dict) -> str:
        """Analyze content focus"""
        tweet_types = tweets.get("patterns", {}).get("tweet_types", {})
        original = tweet_types.get("original", 0)
        replies = tweet_types.get("replies", 0)
        
        if replies > original * 2:
            return "Conversational (mostly replies)"
        elif original > replies * 2:
            return "Content Creator (original posts)"
        else:
            return "Balanced (mixed content)"
    
    def _calculate_exposure_risk(self, exposures: List) -> str:
        """Calculate overall exposure risk"""
        if not exposures:
            return "LOW"
        
        severity_levels = [e.get("severity", "LOW") for e in exposures]
        
        if "CRITICAL" in severity_levels:
            return "CRITICAL"
        elif "HIGH" in severity_levels:
            return "HIGH"
        elif "MEDIUM" in severity_levels:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _extract_key_findings(self, results: Dict) -> List[str]:
        """Extract key intelligence findings"""
        findings = []
        
        profile = results.get("profile", {})
        metrics = profile.get("account_metrics", {})
        tweets = results.get("tweets", {})
        
        # Account age
        account_age = metrics.get("account_age_days", 0)
        findings.append(f"Account age: {account_age // 365} years, {account_age % 365} days")
        
        # Follower count
        followers = metrics.get("followers", 0)
        if followers > 10000:
            findings.append(f"Large following: {followers:,} followers")
        
        # Tweet volume
        total_tweets = metrics.get("tweets", 0)
        if total_tweets > 1000:
            findings.append(f"Prolific tweeter: {total_tweets:,} total tweets")
        
        # Verified status
        if profile.get("account_status", {}).get("verified"):
            findings.append("Verified account")
        
        # Top hashtags
        top_hashtags = tweets.get("content_analysis", {}).get("top_hashtags", {})
        if top_hashtags:
            top_3 = list(top_hashtags.keys())[:3]
            findings.append(f"Top topics: #{', #'.join(top_3)}")
        
        return findings
