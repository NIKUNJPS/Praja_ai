"""
ICIOS API Tests - Backend API Testing
Tests for: Authentication, Analytics, Civic Works, and Demo Mode APIs
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://booth-health.preview.emergentagent.com"

# Test Credentials
TEST_EMAIL = "superadmin@iciss.gov.in"
TEST_PASSWORD = "superadmin"


class TestHealthCheck:
    """Health check endpoint tests - Run first"""
    
    def test_health_endpoint(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        print(f"✅ Health check passed: {data}")


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_login_with_valid_credentials(self):
        """Test login with superadmin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        print(f"✅ Login successful: token received")
    
    def test_login_with_invalid_credentials(self):
        """Test login with wrong credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print(f"✅ Invalid credentials correctly rejected: {response.status_code}")
    
    def test_get_current_user(self):
        """Test /api/auth/me endpoint with valid token"""
        # First get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        # Get current user
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_EMAIL
        assert "role" in data
        assert "name" in data
        print(f"✅ Current user fetched: {data['name']} ({data['role']})")


class TestDashboardStats:
    """Dashboard statistics endpoint tests"""
    
    def test_dashboard_stats(self):
        """Test dashboard-stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/analytics/dashboard-stats")
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "total_citizens" in data
        assert "total_booths" in data
        assert "total_civic_works" in data
        assert "avg_health_score" in data
        assert "active_beneficiaries" in data
        assert "open_issues" in data
        assert "sentiment_trend" in data
        assert "scheme_coverage_pct" in data
        
        # Validate data values
        assert isinstance(data["total_citizens"], int)
        assert isinstance(data["total_booths"], int)
        assert data["total_citizens"] > 0  # Should have citizens
        assert data["total_booths"] > 0  # Should have booths
        
        print(f"✅ Dashboard stats: {data['total_citizens']} citizens, {data['total_booths']} booths")


class TestBoothHealth:
    """Booth Health Intelligence endpoint tests"""
    
    def test_booth_health_list(self):
        """Test booth-health endpoint"""
        response = requests.get(f"{BASE_URL}/api/analytics/booth-health?limit=10")
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "booths" in data
        assert "total_booths" in data
        assert "avg_health_score" in data
        
        booths = data["booths"]
        assert len(booths) > 0
        
        # Validate booth structure
        booth = booths[0]
        assert "booth_id" in booth
        assert "booth_name" in booth
        assert "health_score" in booth
        assert "risk_level" in booth
        assert "citizens_count" in booth
        
        # Validate health score is in valid range
        assert 0 <= booth["health_score"] <= 100
        assert booth["risk_level"] in ["Low", "Medium", "High"]
        
        print(f"✅ Booth health: {len(booths)} booths, avg score: {data['avg_health_score']}")
    
    def test_booth_health_with_filter(self):
        """Test booth-health with booth_id filter"""
        # First get a booth ID
        response = requests.get(f"{BASE_URL}/api/analytics/booth-health?limit=1")
        booths = response.json()["booths"]
        booth_id = booths[0]["booth_id"]
        
        # Query specific booth
        response = requests.get(f"{BASE_URL}/api/analytics/booth-health?booth_id={booth_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["booths"]) == 1
        assert data["booths"][0]["booth_id"] == booth_id
        print(f"✅ Booth health filter works for booth_id={booth_id}")


class TestInfluencers:
    """Top Influencers endpoint tests"""
    
    def test_top_influencers(self):
        """Test top-influencers endpoint"""
        response = requests.get(f"{BASE_URL}/api/analytics/top-influencers?limit=5")
        assert response.status_code == 200
        data = response.json()
        
        assert "influencers" in data
        assert "total" in data
        
        if len(data["influencers"]) > 0:
            influencer = data["influencers"][0]
            # Check influencer structure
            assert "id" in influencer or "citizen_id" in influencer
            assert "name" in influencer
            print(f"✅ Top influencers: {len(data['influencers'])} found")
        else:
            print("⚠️ No influencers found - may need to run influence scoring")


class TestCivicWorks:
    """Civic Works endpoint tests - Critical for Demo Mode"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_civic_works(self, auth_token):
        """Test GET civic works"""
        response = requests.get(f"{BASE_URL}/api/civic-works/", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "works" in data
        assert "total" in data
        
        print(f"✅ Civic works: {data['total']} total works")
    
    def test_create_civic_work(self, auth_token):
        """Test POST civic work creation - Critical for Demo Mode"""
        # First get a booth ID
        booth_response = requests.get(f"{BASE_URL}/api/analytics/booth-health?limit=1")
        booth = booth_response.json()["booths"][0]
        booth_id = booth["booth_id"]
        
        # Create a civic work
        response = requests.post(f"{BASE_URL}/api/civic-works/create", 
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "booth_id": booth_id,
                "title": "TEST_Demo_Civic_Work",
                "description": "Test civic work for demo mode testing",
                "category": "Road Construction",
                "budget": 250000,
                "status": "In Progress",
                "affected_streets": []
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "civic_work_id" in data
        assert "title" in data
        assert "category" in data
        assert "affected_citizens" in data
        assert "notifications_created" in data
        assert "booths_impacted" in data
        assert "execution_time_ms" in data
        
        # Validate values
        assert data["category"] == "Road Construction"
        assert data["affected_citizens"] >= 0
        assert data["execution_time_ms"] > 0
        
        print(f"✅ Civic work created: ID={data['civic_work_id']}, affected={data['affected_citizens']} citizens")
    
    def test_get_civic_work_detail(self, auth_token):
        """Test GET civic work detail"""
        # First get a civic work ID
        response = requests.get(f"{BASE_URL}/api/civic-works/", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        works = response.json()["works"]
        
        if len(works) > 0:
            work_id = works[0]["id"]
            
            # Get detail
            detail_response = requests.get(f"{BASE_URL}/api/civic-works/{work_id}", headers={
                "Authorization": f"Bearer {auth_token}"
            })
            assert detail_response.status_code == 200
            data = detail_response.json()
            
            assert "work" in data
            assert "impact" in data
            assert data["work"]["id"] == work_id
            
            print(f"✅ Civic work detail fetched for ID={work_id}")
        else:
            print("⚠️ No civic works to test detail endpoint")


class TestSentimentAndSegments:
    """Sentiment and Segmentation endpoint tests"""
    
    def test_sentiment_trends(self):
        """Test sentiment-trends endpoint"""
        response = requests.get(f"{BASE_URL}/api/analytics/sentiment-trends?days=30")
        assert response.status_code == 200
        data = response.json()
        
        assert "days" in data
        assert "total_logs" in data
        assert "sentiment_counts" in data
        assert "momentum" in data
        
        print(f"✅ Sentiment trends: {data['total_logs']} logs, momentum={data['momentum']}")
    
    def test_segment_summary(self):
        """Test segment-summary endpoint"""
        response = requests.get(f"{BASE_URL}/api/analytics/segment-summary")
        assert response.status_code == 200
        data = response.json()
        
        # Should return segment data
        assert "segment_distribution" in data or "segments" in data or "total_citizens" in data
        print(f"✅ Segment summary fetched: {data}")


class TestNotifications:
    """Notifications endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_notifications_summary(self, auth_token):
        """Test notifications summary endpoint"""
        response = requests.get(f"{BASE_URL}/api/civic-works/notifications/summary", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        print(f"✅ Notifications summary: {data}")
    
    def test_recent_notifications(self, auth_token):
        """Test recent notifications endpoint"""
        response = requests.get(f"{BASE_URL}/api/civic-works/notifications/recent?limit=10", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "notifications" in data
        assert "total" in data
        
        print(f"✅ Recent notifications: {data['total']} found")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
