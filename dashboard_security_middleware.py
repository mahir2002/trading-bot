#!/usr/bin/env python3
"""
🛡️ Dashboard Security Middleware
Easy-to-integrate security middleware for existing Dash applications
to add authentication, authorization, and security features.
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from flask import Flask, request, session, redirect, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import functools
import secrets
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
import jwt
import hashlib
import hmac

# Import our secure dashboard system
from secure_dashboard_system import SecurityManager, User, SecurityConfig

logger = logging.getLogger(__name__)

class DashboardSecurityMiddleware:
    """Security middleware for existing Dash applications"""
    
    def __init__(self, app: dash.Dash, config: Dict[str, Any] = None):
        self.app = app
        self.server = app.server
        self.config = config or {}
        
        # Initialize security manager
        self.security_manager = SecurityManager(
            db_path=self.config.get('db_path', 'dashboard_security.db'),
            redis_url=self.config.get('redis_url')
        )
        
        # Security settings
        self.require_auth = self.config.get('require_authentication', True)
        self.enable_rate_limiting = self.config.get('enable_rate_limiting', True)
        self.enable_security_headers = self.config.get('enable_security_headers', True)
        self.enable_session_security = self.config.get('enable_session_security', True)
        
        # Initialize components
        self._setup_session_security()
        self._setup_login_manager()
        self._setup_rate_limiting()
        self._setup_security_headers()
        self._setup_authentication_routes()
        
        # Store original layout and callbacks
        self.original_layout = None
        self.protected_callbacks = []
        
        logger.info("🛡️ Dashboard Security Middleware initialized")
    
    def _setup_session_security(self):
        """Setup secure session configuration"""
        
        if not self.enable_session_security:
            return
        
        self.server.config.update({
            'SECRET_KEY': self.config.get('secret_key', secrets.token_urlsafe(32)),
            'SESSION_COOKIE_SECURE': True,
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'PERMANENT_SESSION_LIFETIME': timedelta(seconds=SecurityConfig.SESSION_TIMEOUT)
        })
    
    def _setup_login_manager(self):
        """Setup Flask-Login"""
        
        if not self.require_auth:
            return
        
        self.login_manager = LoginManager()
        self.login_manager.init_app(self.server)
        self.login_manager.login_view = 'login'
        self.login_manager.login_message = 'Please log in to access this page.'
        
        @self.login_manager.user_loader
        def load_user(user_id):
            return self.security_manager.get_user_by_id(user_id)
    
    def _setup_rate_limiting(self):
        """Setup rate limiting"""
        
        if not self.enable_rate_limiting:
            return
        
        self.limiter = Limiter(
            app=self.server,
            key_func=get_remote_address,
            default_limits=[SecurityConfig.DASHBOARD_RATE_LIMIT]
        )
    
    def _setup_security_headers(self):
        """Setup security headers"""
        
        if not self.enable_security_headers:
            return
        
        # Custom CSP for Dash applications
        csp = {
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline' 'unsafe-eval' https://cdn.plot.ly https://cdn.jsdelivr.net",
            'style-src': "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
            'img-src': "'self' data: https:",
            'connect-src': "'self' ws: wss:",
            'font-src': "'self' https://cdn.jsdelivr.net https://fonts.gstatic.com",
            'frame-ancestors': "'none'"
        }
        
        self.talisman = Talisman(
            self.server,
            force_https=self.config.get('force_https', False),
            strict_transport_security=True,
            content_security_policy=csp,
            referrer_policy='strict-origin-when-cross-origin'
        )
    
    def _setup_authentication_routes(self):
        """Setup authentication routes"""
        
        if not self.require_auth:
            return
        
        @self.server.route('/auth/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'POST':
                data = request.get_json() if request.is_json else request.form
                username = data.get('username', '').strip()
                password = data.get('password', '')
                
                if not username or not password:
                    return jsonify({'error': 'Username and password required'}), 400
                
                success, user, message = self.security_manager.authenticate_user(
                    username, password, request.remote_addr, request.user_agent.string
                )
                
                if success and user:
                    login_user(user, remember=False)
                    session_id = self.security_manager.create_session(
                        user.id, request.remote_addr, request.user_agent.string
                    )
                    session['session_id'] = session_id
                    
                    if request.is_json:
                        return jsonify({'success': True, 'redirect': '/'})
                    else:
                        return redirect('/')
                else:
                    if request.is_json:
                        return jsonify({'error': message}), 401
                    else:
                        return self._render_login_page(error=message)
            
            return self._render_login_page()
        
        @self.server.route('/auth/logout')
        def logout():
            if 'session_id' in session:
                self.security_manager.invalidate_session(session['session_id'])
            
            logout_user()
            session.clear()
            return redirect('/auth/login')
        
        @self.server.route('/auth/status')
        def auth_status():
            if current_user.is_authenticated:
                return jsonify({
                    'authenticated': True,
                    'user': {
                        'id': current_user.id,
                        'username': current_user.username,
                        'role': current_user.role
                    }
                })
            else:
                return jsonify({'authenticated': False})
    
    def _render_login_page(self, error=None):
        """Render login page"""
        
        error_html = f'<div class="alert alert-danger">{error}</div>' if error else ''
        
        return f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Dashboard Login</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{ 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    min-height: 100vh; 
                    display: flex; 
                    align-items: center; 
                }}
                .login-card {{ 
                    background: rgba(255, 255, 255, 0.95); 
                    border-radius: 15px; 
                    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1); 
                }}
                .login-header {{ 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; 
                    border-radius: 15px 15px 0 0; 
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="row justify-content-center">
                    <div class="col-md-6 col-lg-4">
                        <div class="card login-card">
                            <div class="card-header login-header text-center py-4">
                                <h3>🔐 Dashboard Login</h3>
                            </div>
                            <div class="card-body p-4">
                                {error_html}
                                <form method="post" action="/auth/login">
                                    <div class="mb-3">
                                        <label for="username" class="form-label">Username</label>
                                        <input type="text" class="form-control" id="username" name="username" required>
                                    </div>
                                    <div class="mb-3">
                                        <label for="password" class="form-label">Password</label>
                                        <input type="password" class="form-control" id="password" name="password" required>
                                    </div>
                                    <button type="submit" class="btn btn-primary w-100">Login</button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
    
    def protect_layout(self, layout_func: Callable = None):
        """Protect dashboard layout with authentication"""
        
        if not self.require_auth:
            return layout_func() if layout_func else self.app.layout
        
        def protected_layout():
            # Check authentication
            if not current_user.is_authenticated:
                return html.Div([
                    dbc.Container([
                        dbc.Alert([
                            html.H4("🔐 Authentication Required", className="alert-heading"),
                            html.P("Please log in to access this dashboard."),
                            html.Hr(),
                            dbc.Button("Login", href="/auth/login", color="primary", external_link=True)
                        ], color="warning")
                    ], className="mt-5")
                ])
            
            # Return original layout with security wrapper
            original_content = layout_func() if layout_func else self.app.layout
            
            return html.Div([
                # Security status bar
                self._create_security_bar(),
                
                # Original content
                original_content,
                
                # Security monitoring
                dcc.Interval(id='security-monitor-interval', interval=30000, n_intervals=0),
                dcc.Store(id='security-status-store')
            ])
        
        return protected_layout()
    
    def _create_security_bar(self):
        """Create security status bar"""
        
        return dbc.Navbar([
            dbc.NavbarBrand([
                html.I(className="fas fa-shield-alt me-2"),
                "Secured Dashboard"
            ]),
            
            dbc.Nav([
                dbc.NavItem([
                    html.Span(f"👤 {current_user.username} ({current_user.role})", 
                            className="navbar-text me-3"),
                    dbc.Button("Logout", href="/auth/logout", color="outline-light", 
                             size="sm", external_link=True)
                ])
            ], className="ms-auto")
        ], color="dark", dark=True, className="mb-3", style={'fontSize': '0.9rem'})
    
    def require_permission(self, permission: str):
        """Decorator to require specific permission for callbacks"""
        
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if self.require_auth:
                    if not current_user.is_authenticated:
                        return html.Div([
                            dbc.Alert("Authentication required", color="danger")
                        ])
                    
                    if not current_user.has_permission(permission):
                        return html.Div([
                            dbc.Alert("Insufficient permissions", color="warning")
                        ])
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def protect_callback(self, permission: str = None):
        """Decorator to protect Dash callbacks"""
        
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if self.require_auth:
                    if not current_user.is_authenticated:
                        raise dash.exceptions.PreventUpdate
                    
                    if permission and not current_user.has_permission(permission):
                        raise dash.exceptions.PreventUpdate
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def secure_api_endpoint(self, endpoint: str, methods: List[str] = ['GET'], 
                           permission: str = None):
        """Decorator to secure API endpoints"""
        
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Check authentication
                if self.require_auth:
                    auth_header = request.headers.get('Authorization')
                    if auth_header and auth_header.startswith('Bearer '):
                        # API key authentication
                        api_key = auth_header.split(' ')[1]
                        user = self.security_manager.validate_api_key(api_key)
                        
                        if not user:
                            return jsonify({'error': 'Invalid API key'}), 401
                        
                        if permission and not user.has_permission(permission):
                            return jsonify({'error': 'Insufficient permissions'}), 403
                    
                    elif not current_user.is_authenticated:
                        return jsonify({'error': 'Authentication required'}), 401
                    
                    elif permission and not current_user.has_permission(permission):
                        return jsonify({'error': 'Insufficient permissions'}), 403
                
                return func(*args, **kwargs)
            
            # Register route
            self.server.add_url_rule(endpoint, func.__name__, wrapper, methods=methods)
            return wrapper
        
        return decorator
    
    def add_security_monitoring(self):
        """Add security monitoring callbacks"""
        
        @self.app.callback(
            Output('security-status-store', 'data'),
            [Input('security-monitor-interval', 'n_intervals')]
        )
        @self.protect_callback('system_config')
        def update_security_status(n):
            """Update security monitoring data"""
            
            # Get recent security events
            import sqlite3
            
            conn = sqlite3.connect(self.security_manager.db_path)
            cursor = conn.cursor()
            
            # Failed login attempts in last hour
            cursor.execute('''
                SELECT COUNT(*) FROM security_logs 
                WHERE event_type = 'auth_failed' 
                AND timestamp > datetime('now', '-1 hour')
            ''')
            failed_logins = cursor.fetchone()[0]
            
            # Active sessions
            cursor.execute('''
                SELECT COUNT(*) FROM user_sessions 
                WHERE is_active = 1 AND expires_at > datetime('now')
            ''')
            active_sessions = cursor.fetchone()[0]
            
            # Critical events
            cursor.execute('''
                SELECT COUNT(*) FROM security_logs 
                WHERE severity = 'CRITICAL' 
                AND timestamp > datetime('now', '-24 hours')
            ''')
            critical_events = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'failed_logins': failed_logins,
                'active_sessions': active_sessions,
                'critical_events': critical_events,
                'timestamp': datetime.now().isoformat()
            }
    
    def create_user_management_interface(self):
        """Create user management interface for admins"""
        
        return html.Div([
            dbc.Card([
                dbc.CardHeader(html.H4("👥 User Management")),
                dbc.CardBody([
                    # Add user form
                    dbc.Form([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Username"),
                                dbc.Input(id="new-username", type="text", placeholder="Enter username")
                            ], width=3),
                            dbc.Col([
                                dbc.Label("Email"),
                                dbc.Input(id="new-email", type="email", placeholder="Enter email")
                            ], width=3),
                            dbc.Col([
                                dbc.Label("Password"),
                                dbc.Input(id="new-password", type="password", placeholder="Enter password")
                            ], width=3),
                            dbc.Col([
                                dbc.Label("Role"),
                                dcc.Dropdown(
                                    id="new-role",
                                    options=[
                                        {'label': 'Viewer', 'value': 'viewer'},
                                        {'label': 'Trader', 'value': 'trader'},
                                        {'label': 'Analyst', 'value': 'analyst'},
                                        {'label': 'Admin', 'value': 'admin'}
                                    ],
                                    value='viewer'
                                )
                            ], width=2),
                            dbc.Col([
                                dbc.Label("Action"),
                                dbc.Button("Add User", id="add-user-btn", color="primary", className="w-100")
                            ], width=1)
                        ], className="mb-3")
                    ]),
                    
                    # User list
                    html.Div(id="user-list"),
                    
                    # Add user result
                    html.Div(id="add-user-result")
                ])
            ])
        ])
    
    def setup_user_management_callbacks(self):
        """Setup callbacks for user management"""
        
        @self.app.callback(
            Output('add-user-result', 'children'),
            [Input('add-user-btn', 'n_clicks')],
            [State('new-username', 'value'),
             State('new-email', 'value'),
             State('new-password', 'value'),
             State('new-role', 'value')]
        )
        @self.protect_callback('manage_users')
        def add_user(n_clicks, username, email, password, role):
            if not n_clicks or not all([username, email, password, role]):
                return ""
            
            success, message = self.security_manager.create_user(username, email, password, role)
            
            if success:
                return dbc.Alert(f"✅ {message}", color="success", dismissable=True)
            else:
                return dbc.Alert(f"❌ {message}", color="danger", dismissable=True)
    
    def get_security_dashboard(self):
        """Get security monitoring dashboard"""
        
        return html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("🔐 Security Overview", className="card-title"),
                            html.Div(id="security-overview-content")
                        ])
                    ])
                ], width=12)
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("📊 Security Logs", className="card-title"),
                            html.Div(id="security-logs-content")
                        ])
                    ])
                ], width=12)
            ], className="mt-3")
        ])

def secure_existing_dashboard(app: dash.Dash, config: Dict[str, Any] = None):
    """
    Secure an existing Dash application with minimal code changes
    
    Args:
        app: Existing Dash application
        config: Security configuration options
    
    Returns:
        SecurityMiddleware instance for further customization
    """
    
    # Initialize security middleware
    security = DashboardSecurityMiddleware(app, config)
    
    # Store original layout
    original_layout = app.layout
    
    # Protect layout
    app.layout = security.protect_layout(lambda: original_layout)
    
    # Add security monitoring
    security.add_security_monitoring()
    
    logger.info("✅ Dashboard secured with authentication and security features")
    
    return security

# Example usage with existing dashboard
def example_secure_integration():
    """Example of securing an existing dashboard"""
    
    # Create existing dashboard
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    # Original layout
    app.layout = html.Div([
        html.H1("My Trading Dashboard"),
        dcc.Graph(id="example-chart"),
        html.Div(id="example-content")
    ])
    
    # Original callback
    @app.callback(
        Output('example-content', 'children'),
        [Input('example-chart', 'clickData')]
    )
    def update_content(click_data):
        return f"Chart clicked: {click_data}"
    
    # Secure the dashboard with one line
    security = secure_existing_dashboard(app, {
        'require_authentication': True,
        'enable_rate_limiting': True,
        'enable_security_headers': True
    })
    
    # Optionally add permission requirements to callbacks
    @app.callback(
        Output('admin-content', 'children'),
        [Input('admin-button', 'n_clicks')]
    )
    @security.protect_callback('admin')
    def admin_function(n_clicks):
        return "Admin only content"
    
    return app, security

if __name__ == "__main__":
    # Demo of security middleware
    app, security = example_secure_integration()
    
    print("🛡️ DASHBOARD SECURITY MIDDLEWARE DEMO")
    print("=" * 50)
    print("✅ Features enabled:")
    print("   • Authentication with login/logout")
    print("   • Role-based access control")
    print("   • Rate limiting")
    print("   • Security headers")
    print("   • Session management")
    print("   • Security monitoring")
    print("   • API key authentication")
    print("\n🌐 Dashboard URL: http://localhost:8051")
    print("🔑 Check admin_credentials.txt for login")
    
    app.run_server(host='0.0.0.0', port=8051, debug=False) 