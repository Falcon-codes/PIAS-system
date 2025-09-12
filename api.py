from flask import Flask, request, jsonify, send_from_directory, send_file, render_template
from flask_cors import CORS
import os
import tempfile
import traceback
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import session
import uuid
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Enhanced Groq import with error handling
try:
    from groq import Groq
    GROQ_AVAILABLE = True
    print("✅ Groq AI integration available")
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️  Groq not available - AI features will use fallback")

# Import our enhanced analysis modules
from analysis.data_processor import DataProcessor
from analysis.calculations import InventoryCalculations
# from analysis.chart_generator import ChartGenerator
try:
    from analysis.chart_generator import ChartGenerator
except ImportError:
    from analysis.chart_generator_simple import ChartGenerator

# Initialize Flask app with enhanced configuration
app = Flask(__name__)
CORS(app, origins=["http://localhost:*", "http://127.0.0.1:*"])

# Enhanced configuration
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret-key-for-dev")
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Initialize Groq client with error handling
groq_client = None
if GROQ_AVAILABLE:
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            print("⚠️  GROQ_API_KEY not found in environment variables")
            GROQ_AVAILABLE = False
        else:
            groq_client = Groq(api_key=api_key)
            print("🤖 Groq AI client initialized successfully")
    except Exception as e:
        print(f"⚠️  Groq initialization failed: {str(e)}")
        GROQ_AVAILABLE = False

# Configuration
ALLOWED_EXTENSIONS = {'csv'}
MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25MB max file size

# Use system temp directory for cloud deployment compatibility
UPLOAD_FOLDER = tempfile.gettempdir()

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

print(f"📁 Using upload directory: {UPLOAD_FOLDER}")

# Production database storage
try:
    from database import db, get_session_data, set_session_data
    print("✅ Production database initialized")
except ImportError:
    # Fallback to in-memory storage
    print("⚠️  Using in-memory storage (development mode)")
    app_sessions = {}
    
    def get_session_data(session_id):
        return app_sessions.get(session_id, {})
    
    def set_session_data(session_id, data, filename=None):
        app_sessions[session_id] = data

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.errorhandler(413)
def too_large(e):
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum size is 25MB.',
        'type': 'file_size_error'
    }), 413

@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        'success': False,
        'error': 'Internal server error. Please try again.',
        'type': 'server_error'
    }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced API health check endpoint"""
    try:
        # Test analysis modules
        from analysis import get_package_info
        package_info = get_package_info()
        
        return jsonify({
            'status': 'healthy',
            'message': 'Predictive Inventory Analyzer API is running',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0',
            'features': {
                'csv_processing': True,
                'advanced_calculations': True,
                'professional_charts': True,
                'ai_integration': GROQ_AVAILABLE,
                'multi_format_export': True
            },
            'package_info': package_info,
            'endpoints': {
                'upload': '/api/upload-csv',
                'filter': '/api/filter-products',
                'export': '/api/export-report',
                'chat': '/api/chat',
                'columns': '/api/columns-info'
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'degraded',
            'message': 'API running with limited functionality',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 200

@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    """Enhanced CSV upload and analysis endpoint"""
    session_id = None
    temp_file_path = None
    
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Validate file upload
        if 'csvFile' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded',
                'type': 'validation_error'
            }), 400

        file = request.files['csvFile']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected',
                'type': 'validation_error'
            }), 400

        if not file or not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Please upload a CSV file.',
                'type': 'validation_error'
            }), 400

        # Save file securely using temporary directory
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{session_id}_{filename}"
        
        # Use tempfile.mktemp for better cloud compatibility
        temp_file_path = os.path.join(tempfile.gettempdir(), unique_filename)
        
        print(f"📁 Attempting to save file to: {temp_file_path}")
        print(f"📁 Upload directory permissions: {oct(os.stat(tempfile.gettempdir()).st_mode)[-3:]}")
        
        file.save(temp_file_path)
        print(f"✅ File saved successfully: {temp_file_path}")
        print(f"📊 File size: {os.path.getsize(temp_file_path)} bytes")

        # Process the CSV with enhanced error handling
        try:
            print("🔄 Starting CSV processing...")
            
            # Step 1: Process CSV
            processor = DataProcessor()
            df, columns_map = processor.process_csv(temp_file_path)
            print(f"✅ CSV processed: {df.shape}")

            # Step 2: Perform calculations
            print("📊 Running inventory calculations...")
            calculator = InventoryCalculations(df, columns_map)
            
            kpis = calculator.calculate_kpis()
            priority_reorders = calculator.get_priority_reorders(limit=25)
            category_performance = calculator.get_category_performance()
            fast_slow_movers = calculator.get_fast_slow_movers()
            filter_options = calculator.get_filter_options()
            
            # Get additional insights
            insights = calculator.get_inventory_insights()
            
            print(f"✅ Calculations completed")
            print(f"   📈 KPIs: {len(kpis)} metrics")
            print(f"   🚨 Priority reorders: {len(priority_reorders)}")
            print(f"   📊 Categories: {len(category_performance)}")

            # Step 3: Generate charts
            print("📊 Generating charts...")
            chart_generator = ChartGenerator(df, columns_map)
            charts = chart_generator.generate_all_charts(priority_reorders)
            print("✅ Charts generated successfully")

            # Step 4: Store session data
            session_data = {
                'df_json': df.to_json(),
                'columns_map': columns_map,
                'timestamp': datetime.now().isoformat(),
                'filename': filename,
                'kpis': kpis,
                'category_performance': category_performance,
                'fast_slow_movers': fast_slow_movers
            }
            set_session_data(session_id, session_data, filename)

            # Prepare comprehensive response
            response_data = {
                'success': True,
                'message': 'CSV processed successfully with professional analysis',
                'sessionId': session_id,
                'data': {
                    # Enhanced KPI data
                    'kpis': kpis,
                    
                    # Priority reorder table data
                    'reorderData': priority_reorders,
                    
                    # Professional charts (base64 encoded)
                    'charts': charts,
                    
                    # Category analysis
                    'categoryPerformance': category_performance,
                    
                    # Fast/slow movers with enhanced data
                    'movers': fast_slow_movers,
                    
                    # Enhanced filter options
                    'filterOptions': filter_options,
                    
                    # Business insights and recommendations
                    'insights': insights,
                    
                    # Processing metadata
                    'metadata': {
                        'filename': filename,
                        'processedAt': datetime.now().isoformat(),
                        'totalRows': len(df),
                        'totalColumns': len(df.columns),
                        'columnsDetected': columns_map,
                        'dataQuality': processor.get_column_info(),
                        'processingVersion': '2.0.0'
                    }
                }
            }
            
            print("🎉 Processing completed successfully!")
            return jsonify(response_data)

        except ValueError as ve:
            print(f"❌ Validation error: {str(ve)}")
            return jsonify({
                'success': False,
                'error': str(ve),
                'type': 'validation_error',
                'suggestions': [
                    'Check that your CSV has required columns: Product Name, Category, Stock, Sales',
                    'Ensure data is properly formatted',
                    'Remove any completely empty rows or columns'
                ]
            }), 400

        except Exception as pe:
            print(f"❌ Processing error: {str(pe)}")
            print(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': 'Error processing your file. Please check the format and try again.',
                'details': str(pe) if app.debug else None,
                'type': 'processing_error'
            }), 500

    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Traceback:")
        print(traceback.format_exc())
        
        # Provide detailed error information
        error_details = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'upload_dir': tempfile.gettempdir(),
            'session_id': session_id
        }
        
        return jsonify({
            'success': False,
            'error': f'Upload failed: {str(e)}',
            'details': error_details,
            'type': 'upload_error',
            'debug_info': {
                'temp_dir': tempfile.gettempdir(),
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }
        }), 500

    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                print(f"🧹 Cleaned up temporary file: {temp_file_path}")
            except Exception as cleanup_error:
                print(f"⚠️  Cleanup warning: {cleanup_error}")

@app.route('/api/filter-products', methods=['POST'])
def filter_products():
    """Enhanced product filtering with advanced criteria"""
    try:
        data = request.get_json()
        session_id = data.get('sessionId')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session ID provided. Please upload a CSV first.',
                'type': 'session_error'
            }), 400

        # Get session data
        session_data = get_session_data(session_id)
        if not session_data:
            return jsonify({
                'success': False,
                'error': 'Session expired. Please upload your CSV again.',
                'type': 'session_error'
            }), 400

        # Reconstruct dataframe
        import pandas as pd
        df = pd.read_json(session_data['df_json'])
        columns_map = session_data['columns_map']

        # Get filter parameters
        category = data.get('category')
        status = data.get('status')
        search = data.get('search', '').strip()
        abc_class = data.get('abcClass')
        
        print(f"🔍 Filtering: category={category}, status={status}, search='{search}', abc={abc_class}")

        # Apply filtering using enhanced calculations
        calculator = InventoryCalculations(df, columns_map)
        filtered_products = calculator.filter_products(
            category=category,
            status=status,
            search=search,
            abc_class=abc_class
        )

        # Calculate filtered statistics
        filtered_df = df.copy()
        
        # Apply same filters to DataFrame for stats
        if category and category not in ['All Categories', 'All']:
            filtered_df = filtered_df[filtered_df[columns_map['category']] == category]
            
        if search:
            filtered_df = filtered_df[
                filtered_df[columns_map['name']].str.contains(search, case=False, na=False)
            ]

        # Calculate filtered KPIs
        if len(filtered_df) > 0:
            filtered_calculator = InventoryCalculations(filtered_df, columns_map)
            filtered_kpis = filtered_calculator.calculate_kpis()
        else:
            filtered_kpis = {
                'totalProducts': 0,
                'criticalAlerts': 0,
                'averageTurnover': 0,
                'inventoryHealth': 0
            }

        response = {
            'success': True,
            'data': {
                'filteredProducts': filtered_products,
                'filteredCount': len(filtered_products),
                'totalCount': len(df),
                'filteredKpis': filtered_kpis,
                'appliedFilters': {
                    'category': category,
                    'status': status,
                    'search': search,
                    'abcClass': abc_class
                }
            }
        }

        print(f"✅ Filtering completed: {len(filtered_products)} products returned")
        return jsonify(response)

    except Exception as e:
        print(f"❌ Filter error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error filtering products',
            'details': str(e) if app.debug else None,
            'type': 'filter_error'
        }), 500

@app.route('/api/export-report', methods=['POST'])
def export_report():
    """Enhanced report generation and export"""
    try:
        data = request.get_json() or {}
        report_type = data.get('type', 'json').lower()
        session_id = data.get('sessionId')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session ID provided',
                'type': 'session_error'
            }), 400

        session_data = get_session_data(session_id)
        if not session_data:
            return jsonify({
                'success': False,
                'error': 'Session expired or no data available',
                'type': 'session_error'
            }), 400

        # Generate comprehensive report
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'filename': session_data.get('filename', 'unknown'),
                'report_type': report_type,
                'version': '2.0.0'
            },
            'summary': session_data.get('kpis', {}),
            'category_analysis': session_data.get('category_performance', {}),
            'inventory_insights': session_data.get('fast_slow_movers', {})
        }

        if report_type == 'json':
            # Return JSON report directly
            return jsonify({
                'success': True,
                'message': 'JSON report generated successfully',
                'data': report,
                'download_ready': True
            })
        else:
            # For other formats, return success message
            return jsonify({
                'success': True,
                'message': f'{report_type.upper()} export functionality available - comprehensive report ready',
                'download_ready': False,
                'note': 'Extended format support available in production version'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Error generating report',
            'details': str(e) if app.debug else None,
            'type': 'export_error'
        }), 500

@app.route('/api/chat', methods=['POST'])
def ai_chat():
    """Enhanced AI Assistant with Groq integration and comprehensive fallbacks"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        inventory_context = data.get('inventory_context', {})
        session_id = data.get('sessionId')

        if not message:
            return jsonify({
                'success': False,
                'error': 'No message provided',
                'type': 'validation_error'
            }), 400

        print(f"🤖 AI Chat request: '{message[:50]}...'")

        # Enhanced context building
        context_prompt = build_enhanced_inventory_context(inventory_context, message, session_id)

        # Try Groq AI first
        if GROQ_AVAILABLE and groq_client:
            try:
                print("🚀 Querying Groq AI...")
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": """You are PIAS (Predictive Inventory Analyzer System), an expert inventory management consultant AI. 
                            Provide specific, actionable advice based on the data provided. Be concise but comprehensive.
                            Focus on immediate actions, risk mitigation, and optimization opportunities.
                            Use professional terminology and provide quantified recommendations when possible."""
                        },
                        {
                            "role": "user",
                            "content": context_prompt
                        }
                    ],
                    model="mixtral-8x7b-32768",
                    temperature=0.3,
                    max_tokens=600,
                    top_p=0.9
                )

                ai_response = chat_completion.choices[0].message.content
                print("✅ Groq AI response generated")

                return jsonify({
                    'success': True,
                    'response': ai_response,
                    'timestamp': datetime.now().isoformat(),
                    'model': 'groq-mixtral-8x7b',
                    'context_used': bool(inventory_context)
                })

            except Exception as groq_error:
                print(f"⚠️  Groq AI error: {str(groq_error)}")
                # Fall through to enhanced fallback

        # Enhanced intelligent fallback system
        print("🔄 Using enhanced fallback AI system...")
        fallback_response = get_enhanced_fallback_response(message, inventory_context)

        return jsonify({
            'success': True,
            'response': fallback_response,
            'timestamp': datetime.now().isoformat(),
            'model': 'pias-fallback-v2',
            'note': 'Response generated by PIAS intelligent fallback system'
        })

    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'AI assistant temporarily unavailable',
            'details': str(e) if app.debug else None,
            'type': 'ai_error'
        }), 500

def build_enhanced_inventory_context(inventory_data, user_question, session_id=None):
    """Build comprehensive context for AI with session data"""
    
    context_parts = [
        "🎯 PIAS INVENTORY ANALYSIS CONTEXT",
        "="*50
    ]
    
    # Current metrics
    if inventory_data:
        context_parts.extend([
            "📊 CURRENT METRICS:",
            f"• Total Products: {inventory_data.get('totalProducts', 'N/A'):,}",
            f"• Critical Alerts: {inventory_data.get('criticalAlerts', 'N/A')}",
            f"• Average Turnover: {inventory_data.get('averageTurnover', 'N/A')}x",
            f"• Inventory Health: {inventory_data.get('inventoryHealth', 'N/A')}%",
            f"• Total Value: ${inventory_data.get('totalInventoryValue', 0):,.2f}"
        ])
        
        if inventory_data.get('reorderData'):
            context_parts.append(f"• Priority Reorders: {len(inventory_data.get('reorderData', []))}")
            
        if inventory_data.get('categoryPerformance'):
            top_categories = list(inventory_data.get('categoryPerformance', {}).keys())[:3]
            context_parts.append(f"• Top Categories: {', '.join(top_categories)}")
    
    # Add session-specific insights if available
    if session_id:
        session_data = get_session_data(session_id)
        if session_data and session_data.get('insights'):
            insights = session_data['insights']
            if insights.get('alerts'):
                context_parts.extend([
                    "",
                    "🚨 ALERTS:",
                    *[f"• {alert}" for alert in insights['alerts'][:3]]
                ])
            
            if insights.get('recommendations'):
                context_parts.extend([
                    "",
                    "💡 KEY RECOMMENDATIONS:",
                    *[f"• {rec}" for rec in insights['recommendations'][:3]]
                ])
    
    context_parts.extend([
        "",
        f"❓ USER QUESTION: {user_question}",
        "",
        "Please provide specific, actionable advice focusing on:",
        "1. Immediate actions needed",
        "2. Risk mitigation strategies", 
        "3. Optimization opportunities",
        "4. Quantified recommendations where possible",
        "",
        "Keep response under 200 words and be direct and actionable."
    ])
    
    return "\n".join(context_parts)

def get_enhanced_fallback_response(message, inventory_context):
    """Enhanced intelligent fallback AI system"""
    
    message_lower = message.lower()
    
    # Enhanced response mapping with context awareness
    advanced_responses = {
        # Stock management
        'restock': lambda ctx: f"""**RESTOCKING PRIORITY ANALYSIS**

🚨 **Immediate Actions:**
• Check your Priority Reorder List - {ctx.get('criticalAlerts', 0)} items need attention
• Focus on critical status items first (stock < 7 days supply)
• Review supplier lead times for urgent items

📊 **Current Status:** {ctx.get('criticalAlerts', 0)} critical alerts out of {ctx.get('totalProducts', 0)} products

💡 **Pro Tip:** Set up automated reorder triggers at 20-day supply levels to prevent stockouts.""",

        'slow': lambda ctx: f"""**SLOW-MOVING INVENTORY OPTIMIZATION**

📉 **Current Impact:**
• Slow movers tie up valuable capital and warehouse space
• Target: Reduce inventory by 15-25% through strategic actions

🎯 **Action Plan:**
1. **Bundle Strategy** - Package slow movers with fast-moving items
2. **Promotional Campaigns** - 10-20% discounts to accelerate turnover
3. **Supplier Negotiations** - Reduce future order quantities
4. **Seasonal Clearance** - Time-based markdown strategies

⚡ **Expected Results:** 3-6 month inventory optimization cycle""",

        'fast': lambda ctx: f"""**FAST-MOVING INVENTORY OPTIMIZATION**

🚀 **Performance Indicators:**
• Fast movers drive {80 if ctx.get('averageTurnover', 0) > 4 else 60}% of your revenue
• Current turnover: {ctx.get('averageTurnover', 0):.1f}x (Target: 6-8x)

✅ **Optimization Actions:**
1. **Stock Security** - Maintain 1.5x safety stock for top performers
2. **Supplier Partnership** - Negotiate shorter lead times
3. **Demand Forecasting** - Use 90-day rolling averages
4. **Cross-docking** - Consider direct fulfillment for highest volume items

📈 **Growth Opportunity:** Increase fast-mover stock levels by 20-30%""",

        'critical': lambda ctx: f"""**CRITICAL INVENTORY ALERT**

🚨 **URGENT - {ctx.get('criticalAlerts', 0)} Items Need Immediate Action:**

⏰ **Within 24 Hours:**
• Contact suppliers for emergency orders
• Check alternative sources
• Implement allocation controls

📋 **Within 48 Hours:**
• Review demand forecasting accuracy
• Adjust reorder points (+20% safety margin)
• Update lead time assumptions

🔧 **System Improvements:**
• Set up automated alerts at 15-day supply
• Implement daily stock monitoring for A-class items
• Consider vendor-managed inventory for critical items""",

        'health': lambda ctx: f"""**INVENTORY HEALTH ASSESSMENT**

📊 **Your Score: {ctx.get('inventoryHealth', 0):.1f}%** {get_health_grade(ctx.get('inventoryHealth', 0))}

**Breakdown:**
• Healthy Stock: {ctx.get('inventoryHealth', 0):.0f}%
• Critical/Low: {min(100-ctx.get('inventoryHealth', 0), 100):.0f}%

🎯 **Target Ranges:**
• Excellent: 75-85% healthy
• Good: 60-75% healthy  
• Needs Work: <60% healthy

💡 **Quick Wins:**
• Focus on the critical {ctx.get('criticalAlerts', 0)} items first
• Implement ABC analysis for prioritization
• Set up weekly health monitoring reports""",

        'turnover': lambda ctx: f"""**TURNOVER RATE ANALYSIS**

📈 **Current Performance: {ctx.get('averageTurnover', 0):.2f}x annually**

**Industry Benchmarks:**
• Excellent: >6x per year
• Good: 4-6x per year
• Needs Improvement: <4x per year

🚀 **Improvement Strategies:**
1. **Demand Planning** - Use 6-month rolling forecasts
2. **Just-in-Time** - Reduce order quantities, increase frequency
3. **Product Mix** - Focus on higher-velocity items
4. **Supplier Optimization** - Negotiate shorter lead times

🎯 **90-Day Target:** Increase turnover by 15-25%""",

        'forecast': lambda ctx: f"""**DEMAND FORECASTING INSIGHTS**

🔮 **Forecasting Recommendations:**

**Based on your {ctx.get('totalProducts', 0)} products:**

📊 **Method Selection:**
• A-class items: Advanced algorithms (seasonal adjustment)
• B-class items: Moving averages (3-6 month)
• C-class items: Simple reorder points

⚡ **Quick Implementation:**
1. Start with 90-day rolling averages
2. Adjust for seasonality (+/-20%)
3. Review accuracy monthly
4. Refine parameters quarterly

🎯 **Expected Accuracy:** 70-85% improvement in 3-6 months"""
    }
    
    # Context-aware response generation
    for keyword, response_func in advanced_responses.items():
        if keyword in message_lower:
            try:
                return response_func(inventory_context)
            except:
                # Fallback to simple response
                break
    
    # General analysis responses
    general_responses = {
        'summary': f"""**INVENTORY OVERVIEW SUMMARY**

📊 **Key Metrics:**
• Total Products: {inventory_context.get('totalProducts', 0):,}
• Health Score: {inventory_context.get('inventoryHealth', 0):.1f}%
• Turnover Rate: {inventory_context.get('averageTurnover', 0):.1f}x
• Critical Items: {inventory_context.get('criticalAlerts', 0)}

🎯 **Priority Actions:**
1. Address {inventory_context.get('criticalAlerts', 0)} critical stock issues
2. Optimize turnover rate (target: 4-6x)
3. Improve inventory health score to 75%+

💡 **Next Steps:** Focus on critical alerts first, then optimize fast-movers.""",

        'abc': """**ABC ANALYSIS RECOMMENDATIONS**

🏆 **A-Class Items (20% of products, 80% of value):**
• Tight inventory control
• Daily monitoring
• Multiple suppliers
• 1-2 week safety stock

📊 **B-Class Items (30% of products, 15% of value):**
• Periodic review (weekly)
• Economic order quantities
• 2-4 week safety stock

📋 **C-Class Items (50% of products, 5% of value):**
• Simple reorder systems  
• Bulk purchasing
• 4-8 week safety stock

Start with A-class optimization for maximum impact."""
    }
    
    # Return appropriate response
    for keyword in general_responses:
        if keyword in message_lower:
            return general_responses[keyword]
    
    # Ultimate fallback with helpful suggestions
    return f"""**PIAS INVENTORY ASSISTANT**

I can help analyze your inventory data! Here are some specific areas I can assist with:

🔍 **Available Analysis:**
• **"Show restock priorities"** - Get immediate reorder recommendations
• **"Analyze slow movers"** - Identify optimization opportunities  
• **"Check inventory health"** - Overall system assessment
• **"Turnover analysis"** - Performance benchmarking
• **"ABC classification"** - Priority-based management

📊 **Your Current Status:**
• {inventory_context.get('totalProducts', 0):,} products monitored
• {inventory_context.get('criticalAlerts', 0)} items need attention
• {inventory_context.get('inventoryHealth', 0):.1f}% health score

💡 **Try asking:** "What needs restocking?" or "How can I improve turnover?"
"""

def get_health_grade(health_score):
    """Get letter grade for inventory health"""
    if health_score >= 85:
        return "🟢 A (Excellent)"
    elif health_score >= 75:
        return "🟡 B (Good)"
    elif health_score >= 60:
        return "🟠 C (Fair)"
    else:
        return "🔴 D (Needs Work)"

@app.route('/api/columns-info', methods=['POST'])
def get_columns_info():
    """Enhanced CSV column analysis endpoint"""
    temp_file_path = None
    
    try:
        if 'csvFile' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded',
                'type': 'validation_error'
            }), 400

        file = request.files['csvFile']

        if not file or not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Please upload a CSV file.',
                'type': 'validation_error'
            }), 400

        # Save file temporarily
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_preview_{filename}"
        temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(temp_file_path)

        try:
            # Use DataProcessor for enhanced analysis
            processor = DataProcessor()
            
            # Quick validation
            validation_result = processor.validate_csv_format(temp_file_path)
            
            if not validation_result['valid']:
                return jsonify({
                    'success': False,
                    'error': validation_result['error'],
                    'type': 'format_error',
                    'details': validation_result['details']
                }), 400

            # Read full file for detailed analysis
            import pandas as pd
            df = pd.read_csv(temp_file_path)
            
            columns_map = processor.detect_columns(df)
            is_valid, missing_cols = processor.validate_required_columns(columns_map)
            
            # Get data quality preview
            quality_preview = processor.analyze_data_quality(df.head(100), columns_map)  # Preview only

            return jsonify({
                'success': True,
                'data': {
                    'filename': filename,
                    'totalColumns': len(df.columns),
                    'totalRows': len(df),
                    'allColumns': list(df.columns),
                    'detectedColumns': columns_map,
                    'isValid': is_valid,
                    'missingColumns': missing_cols,
                    'preview': df.head(5).to_dict('records'),
                    'dataQuality': quality_preview,
                    'recommendations': quality_preview.get('recommendations', [])
                }
            })

        finally:
            # Clean up
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    except Exception as e:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass
                
        return jsonify({
            'success': False,
            'error': 'Error analyzing CSV structure',
            'details': str(e) if app.debug else None,
            'type': 'analysis_error'
        }), 500

# Serve static files (for development)
@app.route('/static/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('static', filename)

@app.route('/')
def landing_page():
    """Serve the landing page"""
    try:
        return render_template('landing.html')
    except Exception as e:
        print(f"Landing page error: {e}")
        # Fallback response if template not found
        return """
        <h1>PIAS - Predictive Inventory Analyzer System</h1>
        <h2>Version 2.0.0 - Professional Edition</h2>
        <p>Welcome to PIAS! Transform your inventory management with AI-powered analytics.</p>
        <div style="margin: 20px 0;">
            <a href="/login" style="background: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; margin-right: 10px;">Login</a>
            <a href="/signup" style="background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px;">Sign Up</a>
        </div>
        """       

@app.route('/login')
def login_page():
    """Serve the login page"""
    try:
        return render_template('login.html')
    except Exception as e:
        print(f"Login page error: {e}")
        return f"<h1>Login Page</h1><p>Error: {e}</p><a href='/'>Back to Home</a>"

@app.route('/signup')
def signup_page():
    """Serve the signup page"""
    try:
        return render_template('signup.html')
    except Exception as e:
        print(f"Signup page error: {e}")
        return f"<h1>Signup Page</h1><p>Error: {e}</p><a href='/'>Back to Home</a>"

@app.route('/dashboard')
def dashboard_page():
    """Serve the enhanced dashboard (protected route)"""
    try:
        return render_template('dashboard.html')
    except Exception as e:
        print(f"Dashboard error: {e}")
        # Fallback response if template not found
        return """
        <h1>Predictive Inventory Analyzer System (PIAS) Dashboard</h1>
        <h2>Version 2.0.0 - Professional Edition</h2>
        <p>Dashboard is loading...</p>
        <div id="dashboard-container">
            <p>Please upload a CSV file to begin analysis.</p>
        </div>
        <script>window.location.href = '/';</script>
        """

# Debug endpoint to test uploads
@app.route('/api/debug-upload', methods=['POST'])
def debug_upload():
    """Debug endpoint to test file upload functionality step by step"""
    try:
        print("🔍 Debug upload started...")
        
        # Step 1: Check if file is in request
        print(f"📝 Request files: {list(request.files.keys())}")
        print(f"📝 Request form: {list(request.form.keys())}")
        
        if 'csvFile' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No csvFile in request.files',
                'debug': {
                    'files_keys': list(request.files.keys()),
                    'form_keys': list(request.form.keys())
                }
            }), 400
        
        file = request.files['csvFile']
        print(f"📁 File object: {file}")
        print(f"📁 Filename: {file.filename}")
        print(f"📁 Content type: {file.content_type}")
        
        # Step 2: Test temp directory
        temp_dir = tempfile.gettempdir()
        print(f"📁 Temp directory: {temp_dir}")
        print(f"📁 Temp dir exists: {os.path.exists(temp_dir)}")
        print(f"📁 Temp dir writable: {os.access(temp_dir, os.W_OK)}")
        
        # Step 3: Test file save
        test_filename = f"debug_test_{uuid.uuid4()}.csv"
        test_path = os.path.join(temp_dir, test_filename)
        print(f"📁 Test path: {test_path}")
        
        file.save(test_path)
        print(f"✅ File saved successfully")
        
        # Step 4: Test file read
        file_size = os.path.getsize(test_path)
        print(f"📊 File size: {file_size} bytes")
        
        # Step 5: Test pandas read
        import pandas as pd
        df = pd.read_csv(test_path)
        print(f"📊 DataFrame shape: {df.shape}")
        print(f"📊 DataFrame columns: {list(df.columns)}")
        
        # Cleanup
        os.remove(test_path)
        print(f"🧹 Test file cleaned up")
        
        return jsonify({
            'success': True,
            'debug': {
                'temp_dir': temp_dir,
                'file_size': file_size,
                'df_shape': df.shape,
                'df_columns': list(df.columns),
                'message': 'All tests passed!'
            }
        })
        
    except Exception as e:
        print(f"❌ Debug error: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        print(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc()
        }), 500

# Authentication API endpoints
@app.route('/api/login', methods=['POST'])
def api_login():
    """Handle login API requests"""
    try:
        data = request.get_json()
        email = data.get('email', '')
        password = data.get('password', '')
        
        # Demo authentication
        if email == 'demo@pias.com' and password == 'demo123':
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'email': email,
                    'name': 'Demo User',
                    'role': 'admin'
                },
                'token': 'demo_token_' + str(uuid.uuid4())
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid credentials'
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Login failed',
            'details': str(e)
        }), 500

@app.route('/api/signup', methods=['POST'])
def api_signup():
    """Handle signup API requests"""
    try:
        data = request.get_json()
        email = data.get('email', '')
        name = data.get('name', '')
        password = data.get('password', '')
        
        # Basic validation
        if not email or not name or not password:
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
            
        # For demo purposes, always succeed
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'user': {
                'email': email,
                'name': name,
                'role': 'user'
            },
            'token': 'demo_token_' + str(uuid.uuid4())
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Signup failed',
            'details': str(e)
        }), 500

# Production vs Development configuration
def create_app():
    """Application factory for production deployment"""
    # Clean up expired sessions on startup
    try:
        if 'db' in globals():
            db.cleanup_expired_sessions()
    except Exception as e:
        print(f"Session cleanup warning: {e}")
    
    return app

if __name__ == '__main__':
    # Development server
    print("="*80)
    print("🚀 PREDICTIVE INVENTORY ANALYZER SYSTEM (PIAS) v2.0")
    print("="*80)
    print("🌐 Server starting at: http://localhost:5000")
    print("🔍 API Health Check: http://localhost:5000/api/health")  
    print("📋 Dashboard: http://localhost:5000")
    print("📁 Upload endpoint: POST /api/upload-csv")
    print("🤖 AI Chat endpoint: POST /api/chat")
    print("📊 Enhanced Features:")
    print("   ✅ Professional inventory calculations")
    print("   ✅ Advanced chart generation") 
    print("   ✅ AI-powered insights")
    print("   ✅ Comprehensive reporting")
    print("   ✅ Enhanced error handling")
    print("   ✅ Production database ready")
    print("="*80)
    print("🎯 Ready for professional inventory analysis!")
    print("="*80)

    # Development mode
    is_production = os.environ.get('FLASK_ENV') == 'production'
    
    if is_production:
        print("🔧 Production mode - use Gunicorn for serving")
    else:
        print("🔧 Development mode")
        # Run the enhanced app in development
        app.run(
            debug=True, 
            host='0.0.0.0', 
            port=int(os.environ.get('PORT', 5000)),
            threaded=True,
            use_reloader=False  # Disable reloader for cloud compatibility
        )

# For Gunicorn
application = create_app()
