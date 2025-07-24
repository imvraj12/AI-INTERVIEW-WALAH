import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [currentView, setCurrentView] = useState('login');
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [interview, setInterview] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [responses, setResponses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [resumeUploaded, setResumeUploaded] = useState(false);

  // Form states
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [registerData, setRegisterData] = useState({ name: '', email: '', password: '' });
  const [interviewSetup, setInterviewSetup] = useState({
    job_role: '',
    experience_level: 'mid',
    interview_type: 'text'
  });
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [resumeFile, setResumeFile] = useState(null);

  useEffect(() => {
    if (token) {
      fetchUserData();
    }
  }, [token]);

  const fetchUserData = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/interview-history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCurrentView('dashboard');
    } catch (error) {
      console.error('Token validation failed:', error);
      localStorage.removeItem('token');
      setToken(null);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/login`, loginData);
      setToken(response.data.access_token);
      setUser(response.data.user);
      localStorage.setItem('token', response.data.access_token);
      setCurrentView('dashboard');
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Login failed. Please try again.';
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/register`, registerData);
      setToken(response.data.access_token);
      setUser(response.data.user);
      localStorage.setItem('token', response.data.access_token);
      setCurrentView('dashboard');
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Registration failed. Please try again.';
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleResumeUpload = async (e) => {
    e.preventDefault();
    if (!resumeFile) {
      alert('Please select a PDF file');
      return;
    }
    
    setLoading(true);
    const formData = new FormData();
    formData.append('file', resumeFile);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/api/upload-resume`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      alert('Resume uploaded successfully! You can now start practicing interviews.');
      setResumeFile(null);
      setResumeUploaded(true);
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Resume upload failed. Please try again.';
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const startInterview = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/start-interview`, interviewSetup, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setInterview(response.data);
      setCurrentQuestionIndex(0);
      setResponses([]);
      setCurrentAnswer('');
      setCurrentView('interview');
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to start interview. Please make sure you have uploaded a resume first.';
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!currentAnswer.trim()) {
      alert('Please provide an answer');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/submit-response`, {
        question_id: interview.questions[currentQuestionIndex].id,
        answer: currentAnswer
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setResponses([...responses, currentAnswer]);
      setCurrentAnswer('');

      if (response.data.completed) {
        setFeedback(response.data.feedback);
        setCurrentView('feedback');
      } else {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      }
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to submit answer. Please try again.';
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setCurrentView('login');
    setInterview(null);
    setFeedback(null);
  };

  const resetToStart = () => {
    setCurrentView('dashboard');
    setInterview(null);
    setFeedback(null);
    setCurrentQuestionIndex(0);
    setResponses([]);
    setCurrentAnswer('');
  };

  // Login View
  if (currentView === 'login') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <div className="mx-auto h-20 w-20 bg-indigo-600 rounded-full flex items-center justify-center mb-4">
              <span className="text-2xl">🎯</span>
            </div>
            <h2 className="text-3xl font-bold text-gray-900">AI Interview Walah</h2>
            <p className="mt-2 text-gray-600">Master your interviews with AI-powered practice</p>
          </div>
          
          <div className="bg-white rounded-lg shadow-xl p-8">
            <div className="flex mb-6">
              <button
                onClick={() => setCurrentView('login')}
                className={`flex-1 py-2 px-4 text-center rounded-l-lg ${
                  currentView === 'login' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600'
                }`}
              >
                Login
              </button>
              <button
                onClick={() => setCurrentView('register')}
                className={`flex-1 py-2 px-4 text-center rounded-r-lg ${
                  currentView === 'register' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600'
                }`}
              >
                Register
              </button>
            </div>

            <form onSubmit={handleLogin} className="space-y-4">
              <input
                type="email"
                placeholder="Email"
                value={loginData.email}
                onChange={(e) => setLoginData({...loginData, email: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                required
              />
              <input
                type="password"
                placeholder="Password"
                value={loginData.password}
                onChange={(e) => setLoginData({...loginData, password: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                required
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
              >
                {loading ? 'Logging in...' : 'Login'}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // Register View
  if (currentView === 'register') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <div className="mx-auto h-20 w-20 bg-indigo-600 rounded-full flex items-center justify-center mb-4">
              <span className="text-2xl">🎯</span>
            </div>
            <h2 className="text-3xl font-bold text-gray-900">AI Interview Walah</h2>
            <p className="mt-2 text-gray-600">Master your interviews with AI-powered practice</p>
          </div>
          
          <div className="bg-white rounded-lg shadow-xl p-8">
            <div className="flex mb-6">
              <button
                onClick={() => setCurrentView('login')}
                className={`flex-1 py-2 px-4 text-center rounded-l-lg ${
                  currentView === 'login' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600'
                }`}
              >
                Login
              </button>
              <button
                onClick={() => setCurrentView('register')}
                className={`flex-1 py-2 px-4 text-center rounded-r-lg ${
                  currentView === 'register' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600'
                }`}
              >
                Register
              </button>
            </div>

            <form onSubmit={handleRegister} className="space-y-4">
              <input
                type="text"
                placeholder="Full Name"
                value={registerData.name}
                onChange={(e) => setRegisterData({...registerData, name: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                required
              />
              <input
                type="email"
                placeholder="Email"
                value={registerData.email}
                onChange={(e) => setRegisterData({...registerData, email: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                required
              />
              <input
                type="password"
                placeholder="Password"
                value={registerData.password}
                onChange={(e) => setRegisterData({...registerData, password: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                required
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
              >
                {loading ? 'Creating Account...' : 'Create Account'}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // Dashboard View
  if (currentView === 'dashboard') {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <div className="flex items-center">
                <div className="h-10 w-10 bg-indigo-600 rounded-full flex items-center justify-center mr-3">
                  <span className="text-lg">🎯</span>
                </div>
                <h1 className="text-xl font-bold text-gray-900">AI Interview Walah</h1>
              </div>
              <button
                onClick={logout}
                className="px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Resume Upload */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload Resume</h2>
              <p className="text-gray-600 mb-4">
                Upload your resume to get personalized interview questions based on your skills and experience.
              </p>
              <form onSubmit={handleResumeUpload} className="space-y-4">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => setResumeFile(e.target.files[0])}
                    className="hidden"
                    id="resume-upload"
                  />
                  <label htmlFor="resume-upload" className="cursor-pointer">
                    <div className="text-gray-400 mb-2">
                      <svg className="mx-auto h-12 w-12" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                        <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </div>
                    <div className="text-gray-600">
                      <span className="font-medium text-indigo-600 hover:text-indigo-500">
                        Click to upload
                      </span>
                      {' '}or drag and drop
                    </div>
                    <p className="text-xs text-gray-500">PDF files only (max. 10MB)</p>
                  </label>
                  {resumeFile && (
                    <p className="mt-2 text-sm text-green-600">
                      Selected: {resumeFile.name}
                    </p>
                  )}
                </div>
                <button
                  type="submit"
                  disabled={!resumeFile || loading}
                  className="w-full py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
                >
                  {loading ? 'Uploading...' : 'Upload Resume'}
                </button>
              </form>
            </div>

            {/* Start Interview */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Start Interview Practice</h2>
              <p className="text-gray-600 mb-4">
                Configure your interview session and start practicing with AI-generated questions.
              </p>
              <form onSubmit={startInterview} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Job Role</label>
                  <input
                    type="text"
                    placeholder="e.g., Software Engineer, Data Scientist"
                    value={interviewSetup.job_role}
                    onChange={(e) => setInterviewSetup({...interviewSetup, job_role: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Experience Level</label>
                  <select
                    value={interviewSetup.experience_level}
                    onChange={(e) => setInterviewSetup({...interviewSetup, experience_level: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  >
                    <option value="entry">Entry Level (0-2 years)</option>
                    <option value="mid">Mid Level (2-5 years)</option>
                    <option value="senior">Senior Level (5+ years)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Interview Type</label>
                  <select
                    value={interviewSetup.interview_type}
                    onChange={(e) => setInterviewSetup({...interviewSetup, interview_type: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  >
                    <option value="text">Text-based Interview</option>
                    <option value="voice">Voice Interview (Coming Soon)</option>
                  </select>
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                >
                  {loading ? 'Starting Interview...' : 'Start Interview'}
                </button>
              </form>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Interview View
  if (currentView === 'interview' && interview) {
    const currentQuestion = interview.questions[currentQuestionIndex];
    const progress = ((currentQuestionIndex + 1) / interview.questions.length) * 100;

    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <h1 className="text-xl font-bold text-gray-900">Interview in Progress</h1>
              <div className="text-sm text-gray-600">
                Question {currentQuestionIndex + 1} of {interview.questions.length}
              </div>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
              <div 
                className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>
        </header>

        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white rounded-lg shadow-md p-8">
            {/* AI Avatar */}
            <div className="flex items-center mb-8">
              <div className="w-16 h-16 bg-indigo-600 rounded-full flex items-center justify-center mr-4">
                <div className="w-12 h-12 bg-indigo-500 rounded-full flex items-center justify-center animate-pulse">
                  <span className="text-white text-xl">🤖</span>
                </div>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">AI Interviewer</h3>
                <p className="text-gray-600 text-sm">Ready to assess your skills</p>
              </div>
            </div>

            {/* Question */}
            <div className="mb-8">
              <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
                <p className="text-lg text-gray-900">{currentQuestion?.question}</p>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mt-2">
                  {currentQuestion?.type}
                </span>
              </div>

              {/* Answer Input */}
              <div className="space-y-4">
                <label className="block text-sm font-medium text-gray-700">Your Answer</label>
                <textarea
                  value={currentAnswer}
                  onChange={(e) => setCurrentAnswer(e.target.value)}
                  placeholder="Type your detailed answer here..."
                  rows={8}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                />
                <div className="flex justify-between items-center">
                  <p className="text-sm text-gray-500">
                    {currentAnswer.length} characters
                  </p>
                  <button
                    onClick={submitAnswer}
                    disabled={loading || !currentAnswer.trim()}
                    className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
                  >
                    {loading ? 'Submitting...' : 
                     currentQuestionIndex === interview.questions.length - 1 ? 'Complete Interview' : 'Next Question'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Feedback View
  if (currentView === 'feedback' && feedback) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <h1 className="text-xl font-bold text-gray-900">Interview Completed!</h1>
              <button
                onClick={resetToStart}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Start New Interview
              </button>
            </div>
          </div>
        </header>

        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white rounded-lg shadow-md p-8">
            <div className="text-center mb-8">
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">🎉</span>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Congratulations!</h2>
              <p className="text-gray-600">You've successfully completed your interview practice session.</p>
            </div>

            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Feedback & Analysis</h3>
              <div className="prose prose-gray max-w-none">
                <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                  {feedback}
                </div>
              </div>
            </div>

            <div className="mt-8 flex justify-center space-x-4">
              <button
                onClick={resetToStart}
                className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Practice Again
              </button>
              <button
                onClick={() => setCurrentView('dashboard')}
                className="px-6 py-3 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return <div>Loading...</div>;
}

export default App;