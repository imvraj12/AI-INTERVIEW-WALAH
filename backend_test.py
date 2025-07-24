#!/usr/bin/env python3
"""
AI Interview Platform Backend API Testing
Tests all backend endpoints systematically
"""

import requests
import sys
import json
import io
from datetime import datetime
from pathlib import Path

class AIInterviewAPITester:
    def __init__(self, base_url="https://9bf3be02-0340-467f-ad5a-a30935519cfb.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.interview_id = None
        self.question_ids = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        
        # Default headers
        default_headers = {'Content-Type': 'application/json'}
        if self.token:
            default_headers['Authorization'] = f'Bearer {self.token}'
        
        # Merge with provided headers
        if headers:
            default_headers.update(headers)
        
        # Remove Content-Type for file uploads
        if files:
            default_headers.pop('Content-Type', None)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, data=data, headers=default_headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=default_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=default_headers, timeout=30)

            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}

            details = f"Status: {response.status_code}"
            if not success:
                details += f" (Expected: {expected_status})"
                if response_data:
                    details += f" Response: {json.dumps(response_data, indent=2)}"

            return self.log_test(name, success, details), response_data

        except Exception as e:
            return self.log_test(name, False, f"Error: {str(e)}"), {}

    def test_health_check(self):
        """Test health endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )
        return success

    def test_user_registration(self):
        """Test user registration"""
        self.test_timestamp = datetime.now().strftime('%H%M%S')
        self.test_email = f"test{self.test_timestamp}@example.com"
        test_user_data = {
            "name": f"Test User {self.test_timestamp}",
            "email": self.test_email,
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "api/register",
            200,
            data=test_user_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"   ✓ Token obtained: {self.token[:20]}...")
            print(f"   ✓ User ID: {self.user_id}")
        
        return success

    def test_user_login(self):
        """Test user login with existing credentials"""
        # First register a user for login test
        timestamp = datetime.now().strftime('%H%M%S')
        register_data = {
            "name": f"Login Test User {timestamp}",
            "email": f"logintest{timestamp}@example.com",
            "password": "LoginTest123!"
        }
        
        # Register user first
        reg_success, reg_response = self.run_test(
            "Pre-Login Registration",
            "POST",
            "api/register",
            200,
            data=register_data
        )
        
        if not reg_success:
            return False
        
        # Now test login
        login_data = {
            "email": register_data["email"],
            "password": register_data["password"]
        }
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "api/login",
            200,
            data=login_data
        )
        
        return success

    def create_test_pdf(self):
        """Create a simple test PDF content"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            import io
            
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            
            # Add content to PDF
            p.drawString(100, 750, "Test Resume")
            p.drawString(100, 720, "Name: John Doe")
            p.drawString(100, 690, "Experience: 5 years in Software Development")
            p.drawString(100, 660, "Skills: Python, JavaScript, React, FastAPI, MongoDB")
            p.drawString(100, 630, "Education: Computer Science Degree")
            p.drawString(100, 600, "Projects:")
            p.drawString(120, 570, "- E-commerce Platform using React and Node.js")
            p.drawString(120, 540, "- Data Analytics Dashboard with Python and MongoDB")
            p.drawString(120, 510, "- RESTful API development with FastAPI")
            
            p.save()
            buffer.seek(0)
            return buffer.getvalue()
        except ImportError:
            # Fallback: create a minimal PDF structure
            pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Resume Content) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
            return pdf_content

    def test_resume_upload(self):
        """Test resume upload functionality"""
        if not self.token:
            return self.log_test("Resume Upload", False, "No authentication token available")
        
        # Create test PDF content
        pdf_content = self.create_test_pdf()
        
        files = {
            'file': ('test_resume.pdf', io.BytesIO(pdf_content), 'application/pdf')
        }
        
        success, response = self.run_test(
            "Resume Upload",
            "POST",
            "api/upload-resume",
            200,
            files=files
        )
        
        return success

    def test_start_interview(self):
        """Test starting an interview"""
        if not self.token:
            return self.log_test("Start Interview", False, "No authentication token available")
        
        interview_data = {
            "job_role": "Software Engineer",
            "experience_level": "mid",
            "interview_type": "text"
        }
        
        success, response = self.run_test(
            "Start Interview",
            "POST",
            "api/start-interview",
            200,
            data=interview_data
        )
        
        if success and 'interview_id' in response:
            self.interview_id = response['interview_id']
            self.question_ids = [q['id'] for q in response.get('questions', [])]
            print(f"   ✓ Interview ID: {self.interview_id}")
            print(f"   ✓ Questions generated: {len(self.question_ids)}")
        
        return success

    def test_submit_response(self):
        """Test submitting interview responses"""
        if not self.token or not self.question_ids:
            return self.log_test("Submit Response", False, "No authentication token or questions available")
        
        # Submit responses to all questions
        all_success = True
        for i, question_id in enumerate(self.question_ids):
            response_data = {
                "question_id": question_id,
                "answer": f"This is my detailed answer to question {i+1}. I have extensive experience in this area and can provide specific examples of how I've handled similar situations in my previous roles."
            }
            
            success, response = self.run_test(
                f"Submit Response {i+1}/{len(self.question_ids)}",
                "POST",
                "api/submit-response",
                200,
                data=response_data
            )
            
            if not success:
                all_success = False
            
            # Check if interview is completed
            if response.get('completed'):
                print(f"   ✓ Interview completed after {i+1} responses")
                print(f"   ✓ Feedback generated: {len(response.get('feedback', ''))} characters")
                break
        
        return all_success

    def test_interview_history(self):
        """Test getting interview history"""
        if not self.token:
            return self.log_test("Interview History", False, "No authentication token available")
        
        success, response = self.run_test(
            "Interview History",
            "GET",
            "api/interview-history",
            200
        )
        
        if success:
            interviews = response.get('interviews', [])
            print(f"   ✓ Found {len(interviews)} interviews in history")
        
        return success

    def test_get_interview_details(self):
        """Test getting specific interview details"""
        if not self.token or not self.interview_id:
            return self.log_test("Get Interview Details", False, "No authentication token or interview ID available")
        
        success, response = self.run_test(
            "Get Interview Details",
            "GET",
            f"api/interview/{self.interview_id}",
            200
        )
        
        if success:
            print(f"   ✓ Interview status: {response.get('status')}")
            print(f"   ✓ Questions: {len(response.get('questions', []))}")
            print(f"   ✓ Responses: {len(response.get('responses', []))}")
        
        return success

    def test_invalid_endpoints(self):
        """Test error handling for invalid requests"""
        print("\n🔍 Testing Error Handling...")
        
        # Test invalid login
        success1, _ = self.run_test(
            "Invalid Login",
            "POST",
            "api/login",
            401,
            data={"email": "invalid@test.com", "password": "wrongpassword"}
        )
        
        # Test duplicate registration
        if self.token and hasattr(self, 'test_email'):
            # Use the same email that was registered earlier
            duplicate_data = {
                "name": "Duplicate User",
                "email": self.test_email,  # This should already exist
                "password": "TestPassword123!"
            }
            success2, _ = self.run_test(
                "Duplicate Registration",
                "POST",
                "api/register",
                400,
                data=duplicate_data
            )
        else:
            success2 = True  # Skip if no token
        
        # Test unauthorized access
        old_token = self.token
        self.token = "invalid_token"
        success3, _ = self.run_test(
            "Unauthorized Access",
            "GET",
            "api/interview-history",
            401
        )
        self.token = old_token  # Restore token
        
        return success1 and success2 and success3

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting AI Interview Platform Backend API Tests")
        print("=" * 60)
        
        # Core functionality tests
        tests = [
            self.test_health_check,
            self.test_user_registration,
            self.test_user_login,
            self.test_resume_upload,
            self.test_start_interview,
            self.test_submit_response,
            self.test_interview_history,
            self.test_get_interview_details,
            self.test_invalid_endpoints
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(test.__name__, False, f"Exception: {str(e)}")
        
        # Print final results
        print("\n" + "=" * 60)
        print(f"📊 FINAL RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! Backend API is working correctly.")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed. Check the issues above.")
            return 1

def main():
    """Main test execution"""
    tester = AIInterviewAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())