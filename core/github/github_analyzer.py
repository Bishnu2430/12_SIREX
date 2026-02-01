"""
Comprehensive GitHub OSINT Analyzer
Extracts intelligence from GitHub profiles, repositories, and activity patterns
"""

import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
import re


class GitHubAnalyzer:
    """
    Comprehensive GitHub OSINT Analysis
    
    Features:
    - User profile analysis
    - Repository intelligence
    - Activity patterns and timing
    - Network analysis (followers, following, orgs)
    - Exposure detection (emails, secrets, personal data)
    - Contribution patterns
    """
    
    def __init__(self, access_token: str):
        self.token = access_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def analyze_user(self, username: str) -> Dict[str, Any]:
        """
        Comprehensive user analysis
        
        Returns:
            Complete intelligence report on GitHub user
        """
        logger.info(f"Starting GitHub OSINT analysis for: {username}")
        
        results = {
            "username": username,
            "analysis_timestamp": datetime.now().isoformat(),
            "profile": {},
            "repositories": {},
            "activity": {},
            "network": {},
            "exposures": [],
            "intelligence_summary": {}
        }
        
        try:
            # Step 1: Profile analysis
            results["profile"] = self._analyze_profile(username)
            
            # Step 2: Repository analysis
            results["repositories"] = self._analyze_repositories(username)
            
            # Step 3: Activity patterns
            results["activity"] = self._analyze_activity(username)
            
            # Step 4: Network analysis
            results["network"] = self._analyze_network(username)
            
            # Step 5: Exposure detection
            results["exposures"] = self._detect_exposures(username, results)
            
            # Step 6: Intelligence summary
            results["intelligence_summary"] = self._create_intelligence_summary(results)
            
            logger.success(f"✓ GitHub analysis completed for {username}")
            
        except Exception as e:
            logger.error(f"GitHub analysis failed: {e}")
            results["error"] = str(e)
        
        return results
    
    def _analyze_profile(self, username: str) -> Dict[str, Any]:
        """Analyze user profile information"""
        logger.info(f"Analyzing profile for {username}")
        
        response = self.session.get(f"{self.base_url}/users/{username}")
        
        if response.status_code != 200:
            raise Exception(f"User not found or API error: {response.status_code}")
        
        user = response.json()
        
        # Calculate account age
        created_at = datetime.fromisoformat(user['created_at'].replace('Z', '+00:00'))
        account_age_days = (datetime.now(created_at.tzinfo) - created_at).days
        
        profile = {
            "basic_info": {
                "username": user['login'],
                "name": user.get('name'),
                "bio": user.get('bio'),
                "company": user.get('company'),
                "location": user.get('location'),
                "email": user.get('email'),
                "blog": user.get('blog'),
                "twitter_username": user.get('twitter_username'),
                "avatar_url": user.get('avatar_url')
            },
            "account_metrics": {
                "public_repos": user['public_repos'],
                "public_gists": user['public_gists'],
                "followers": user['followers'],
                "following": user['following'],
                "account_created": user['created_at'],
                "last_updated": user['updated_at'],
                "account_age_days": account_age_days,
                "hireable": user.get('hireable')
            },
            "urls": {
                "profile_url": user['html_url'],
                "api_url": user['url'],
                "repos_url": user['repos_url'],
                "events_url": user['events_url']
            }
        }
        
        return profile
    
    def _analyze_repositories(self, username: str) -> Dict[str, Any]:
        """Analyze user's repositories"""
        logger.info(f"Analyzing repositories for {username}")
        
        repos = []
        page = 1
        
        while True:
            response = self.session.get(
                f"{self.base_url}/users/{username}/repos",
                params={"per_page": 100, "page": page, "sort": "updated"}
            )
            
            if response.status_code != 200:
                break
            
            page_repos = response.json()
            if not page_repos:
                break
            
            repos.extend(page_repos)
            page += 1
            
            if len(page_repos) < 100:
                break
        
        # Analyze repo data
        languages = {}
        topics = []
        total_stars = 0
        total_forks = 0
        total_watchers = 0
        
        repo_list = []
        
        for repo in repos:
            repo_data = {
                "name": repo['name'],
                "full_name": repo['full_name'],
                "description": repo.get('description'),
                "url": repo['html_url'],
                "is_fork": repo['fork'],
                "is_private": repo['private'],
                "language": repo.get('language'),
                "stars": repo['stargazers_count'],
                "forks": repo['forks_count'],
                "watchers": repo['watchers_count'],
                "size_kb": repo['size'],
                "created_at": repo['created_at'],
                "updated_at": repo['updated_at'],
                "pushed_at": repo.get('pushed_at'),
                "topics": repo.get('topics', []),
                "license": repo.get('license', {}).get('name') if repo.get('license') else None
            }
            
            repo_list.append(repo_data)
            
            # Aggregate stats
            if repo['language']:
                languages[repo['language']] = languages.get(repo['language'], 0) + 1
            
            total_stars += repo['stargazers_count']
            total_forks += repo['forks_count']
            total_watchers += repo['watchers_count']
            
            topics.extend(repo.get('topics', []))
        
        # Sort languages by frequency
        sorted_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        
        # Unique topics
        unique_topics = list(set(topics))
        
        return {
            "total_repositories": len(repos),
            "repositories": repo_list[:50],  # Limit to top 50 for response size
            "statistics": {
                "total_stars": total_stars,
                "total_forks": total_forks,
                "total_watchers": total_watchers,
                "languages": dict(sorted_languages),
                "primary_language": sorted_languages[0][0] if sorted_languages else None,
                "topics": unique_topics[:20]
            }
        }
    
    def _analyze_activity(self, username: str) -> Dict[str, Any]:
        """Analyze user activity patterns"""
        logger.info(f"Analyzing activity for {username}")
        
        # Get recent events
        response = self.session.get(
            f"{self.base_url}/users/{username}/events/public",
            params={"per_page": 100}
        )
        
        if response.status_code != 200:
            return {"error": "Could not fetch events"}
        
        events = response.json()
        
        # Analyze patterns
        event_types = {}
        hourly_activity = [0] * 24
        daily_activity = {}
        recent_activity = []
        
        for event in events:
            event_type = event['type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
            
            # Parse timestamp
            created_at = datetime.fromisoformat(event['created_at'].replace('Z', '+00:00'))
            hour = created_at.hour
            day = created_at.strftime('%Y-%m-%d')
            
            hourly_activity[hour] += 1
            daily_activity[day] = daily_activity.get(day, 0) + 1
            
            # Recent activity summary
            recent_activity.append({
                "type": event_type,
                "repo": event.get('repo', {}).get('name'),
                "created_at": event['created_at']
            })
        
        # Find most active hours
        most_active_hour = hourly_activity.index(max(hourly_activity))
        
        return {
            "recent_events_count": len(events),
            "event_types": event_types,
            "activity_patterns": {
                "most_active_hour": most_active_hour,
                "hourly_distribution": hourly_activity,
                "daily_distribution": daily_activity
            },
            "recent_activity": recent_activity[:20]
        }
    
    def _analyze_network(self, username: str) -> Dict[str, Any]:
        """Analyze user's network (followers, following, orgs)"""
        logger.info(f"Analyzing network for {username}")
        
        network = {
            "followers": [],
            "following": [],
            "organizations": []
        }
        
        # Get followers (limit to 100)
        response = self.session.get(
            f"{self.base_url}/users/{username}/followers",
            params={"per_page": 100}
        )
        
        if response.status_code == 200:
            followers = response.json()
            network["followers"] = [
                {
                    "username": f['login'],
                    "profile_url": f['html_url'],
                    "avatar_url": f['avatar_url']
                }
                for f in followers
            ]
        
        # Get following (limit to 100)
        response = self.session.get(
            f"{self.base_url}/users/{username}/following",
            params={"per_page": 100}
        )
        
        if response.status_code == 200:
            following = response.json()
            network["following"] = [
                {
                    "username": f['login'],
                    "profile_url": f['html_url'],
                    "avatar_url": f['avatar_url']
                }
                for f in following
            ]
        
        # Get organizations
        response = self.session.get(f"{self.base_url}/users/{username}/orgs")
        
        if response.status_code == 200:
            orgs = response.json()
            network["organizations"] = [
                {
                    "name": org['login'],
                    "url": org.get('url'),
                    "avatar_url": org.get('avatar_url')
                }
                for org in orgs
            ]
        
        network["statistics"] = {
            "followers_count": len(network["followers"]),
            "following_count": len(network["following"]),
            "organizations_count": len(network["organizations"])
        }
        
        return network
    
    def _detect_exposures(self, username: str, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect potential exposure risks"""
        logger.info(f"Detecting exposures for {username}")
        
        exposures = []
        profile = results.get("profile", {})
        
        # Email exposure
        if profile.get("basic_info", {}).get("email"):
            exposures.append({
                "type": "Email Exposure",
                "severity": "MEDIUM",
                "description": "Email address publicly visible",
                "value": profile["basic_info"]["email"],
                "recommendation": "Consider hiding email in GitHub settings"
            })
        
        # Location exposure
        if profile.get("basic_info", {}).get("location"):
            exposures.append({
                "type": "Location Exposure",
                "severity": "LOW",
                "description": "Geographical location disclosed",
                "value": profile["basic_info"]["location"],
                "recommendation": "Assess if location data is necessary"
            })
        
        # Company exposure
        if profile.get("basic_info", {}).get("company"):
            exposures.append({
                "type": "Organization Affiliation",
                "severity": "MEDIUM",
                "description": "Company/organization affiliation visible",
                "value": profile["basic_info"]["company"],
                "recommendation": "Review if company disclosure is intended"
            })
        
        # Social links exposure
        if profile.get("basic_info", {}).get("twitter_username"):
            exposures.append({
                "type": "Social Media Linkage",
                "severity": "LOW",
                "description": "Twitter account linked",
                "value": profile["basic_info"]["twitter_username"],
                "recommendation": "Cross-platform tracking possible"
            })
        
        # High activity exposure
        repos_count = results.get("repositories", {}).get("total_repositories", 0)
        if repos_count > 50:
            exposures.append({
                "type": "Activity Pattern Exposure",
                "severity": "LOW",
                "description": "Extensive public activity visible",
                "value": f"{repos_count} public repositories",
                "recommendation": "Review if all repos should be public"
            })
        
        return exposures
    
    def _create_intelligence_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create executive intelligence summary"""
        profile = results.get("profile", {})
        repos = results.get("repositories", {})
        activity = results.get("activity", {})
        network = results.get("network", {})
        exposures = results.get("exposures", [])
        
        return {
            "user_type": self._determine_user_type(profile, repos),
            "tech_stack": repos.get("statistics", {}).get("languages", {}),
            "primary_language": repos.get("statistics", {}).get("primary_language"),
            "activity_level": self._categorize_activity(activity),
            "network_size": network.get("statistics", {}).get("followers_count", 0),
            "total_stars": repos.get("statistics", {}).get("total_stars", 0),
            "exposure_risk": self._calculate_exposure_risk(exposures),
            "key_findings": self._extract_key_findings(results)
        }
    
    def _determine_user_type(self, profile: Dict, repos: Dict) -> str:
        """Determine user type based on activity"""
        repo_count = repos.get("total_repositories", 0)
        followers = profile.get("account_metrics", {}).get("followers", 0)
        
        if repo_count > 100:
            return "Very Active Developer"
        elif repo_count > 50:
            return "Active Developer"
        elif repo_count > 10:
            return "Regular Developer"
        elif followers > 1000:
            return "Influencer/Thought Leader"
        else:
            return "Casual User"
    
    def _categorize_activity(self, activity: Dict) -> str:
        """Categorize activity level"""
        events = activity.get("recent_events_count", 0)
        
        if events > 80:
            return "Very High"
        elif events > 50:
            return "High"
        elif events > 20:
            return "Moderate"
        elif events > 5:
            return "Low"
        else:
            return "Minimal"
    
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
        repos = results.get("repositories", {})
        network = results.get("network", {})
        
        # Account age
        account_age = profile.get("account_metrics", {}).get("account_age_days", 0)
        findings.append(f"Account age: {account_age // 365} years, {account_age % 365} days")
        
        # Primary tech
        primary_lang = repos.get("statistics", {}).get("primary_language")
        if primary_lang:
            findings.append(f"Primary technology: {primary_lang}")
        
        # Network size
        followers = network.get("statistics", {}).get("followers_count", 0)
        if followers > 100:
            findings.append(f"Significant following: {followers} followers")
        
        # Organizations
        orgs_count = network.get("statistics", {}).get("organizations_count", 0)
        if orgs_count > 0:
            findings.append(f"Member of {orgs_count} organization(s)")
        
        # Stars
        total_stars = repos.get("statistics", {}).get("total_stars", 0)
        if total_stars > 100:
            findings.append(f"Popular projects: {total_stars} total stars")
        
        return findings
