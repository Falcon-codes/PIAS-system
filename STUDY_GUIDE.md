# 📚 PIAS - Code Study Guide
## **Key Files You Need to Master**

---

## 🎯 **CORE FILES TO STUDY (In Priority Order)**

### **1. `api.py` - The Heart of Your Backend**
**Location**: Root directory
**What it does**: Main Flask application, handles all API endpoints

**Key sections to understand:**
```python
# Lines 1-40: Imports and app setup
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from analysis.data_processor import DataProcessor
from analysis.calculations import InventoryCalculations

app = Flask(__name__)
CORS(app, origins=["http://localhost:*", "http://127.0.0.1:*"])

# Lines 142-310: CSV Upload endpoint (THE MOST IMPORTANT)
@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    # This is where all the magic happens
    # File validation → Processing → Calculations → Response
```

### **2. `analysis/calculations.py` - Business Logic Brain**
**Location**: analysis/ folder
**What it does**: All professional inventory calculations

**Key sections to understand:**
```python
# Lines 15-22: Critical initialization order
def __init__(self, df, columns_map):
    self._validate_data()  # ALWAYS validate first
    self._prepare_data()   # Then prepare calculations

# Lines 44-116: Data preparation with all the formulas
def _prepare_data(self):
    # Annual sales calculation
    self.df['Annual_Sales'] = self.df[self.cols['sales']] * 12
    
    # Inventory turnover (professional formula)
    self.df['Inventory_Turnover'] = np.where(
        inventory_value > 0,
        self.df['COGS'] / inventory_value, 0
    )

# Lines 117-157: ABC Analysis (Revenue-based prioritization)
def _calculate_abc_analysis(self):
    # Pareto analysis: 70% A-class, 20% B-class, 10% C-class

# Lines 190-250: KPI calculations
def calculate_kpis(self):
    return {
        'totalProducts': int(total_products),
        'criticalAlerts': int(critical_count),
        'averageTurnover': round(float(avg_turnover), 2),
        'inventoryHealth': round(float(health_percentage), 1)
    }
```

### **3. `analysis/data_processor.py` - Data Intelligence**
**Location**: analysis/ folder  
**What it does**: Smart CSV processing and column detection

**Key sections to understand:**
```python
# Lines 20-49: Smart column finder
def find_column(self, keywords, columns):
    # Fuzzy matching algorithm for column detection
    # Scores columns based on keyword similarity

# Lines 51-108: Column detection logic
def detect_columns(self, df):
    column_keywords = {
        'name': ['name', 'product', 'item', 'description'],
        'category': ['category', 'type', 'class', 'group'],
        'stock': ['stock', 'inventory', 'quantity', 'qty'],
        'sales': ['sales', 'sold', 'demand', 'usage']
    }

# Lines 310-374: Main processing pipeline
def process_csv(self, file_path):
    # 1. Load CSV → 2. Detect columns → 3. Validate → 4. Clean → 5. Return
```

### **4. `templates/dashboard.html` - Frontend Brain**
**Location**: templates/ folder
**What it does**: Complete frontend application (1200+ lines!)

**Key sections to understand:**
```javascript
// Lines 466-481: App state management
let appState = {
    currentSession: null,
    currentDataset: null,
    currentKPIs: {},
    isLoading: false,
    charts: {}
};

// Lines 598-651: File upload handler (CRITICAL)
async function handleFileUpload(file) {
    const formData = new FormData();
    formData.append('csvFile', file);
    
    const response = await fetch(`${API_BASE_URL}/upload-csv`, {
        method: 'POST',
        body: formData
    });
}

// Lines 677-713: Dashboard update logic
async function updateDashboard(data) {
    updateKPICards(data.kpis);
    updateCharts(data.charts);
    updateReorderTable(data.reorderData);
}
```

---

## 🔍 **WHAT EACH FILE ACTUALLY DOES**

### **Backend Files (Python)**

#### **`api.py` (248 lines)**
```
Lines 1-83:    Setup (imports, CORS, database, Groq AI)
Lines 105-140: Health check endpoint
Lines 142-310: CSV upload endpoint (THE MAIN ONE)
Lines 366-557: Filter products endpoint
Lines 600-700: AI chat endpoint
Lines 750+:    Export and other endpoints
```

**What to study:**
- How Flask routes work (`@app.route`)
- File upload handling (`request.files['csvFile']`)
- JSON responses (`jsonify()`)
- Error handling (`try/except`)

#### **`analysis/calculations.py` (600+ lines)**
```
Lines 15-43:   Initialization and validation
Lines 44-116:  Data preparation (formulas)
Lines 117-157: ABC analysis calculation
Lines 158-188: Stock status classification  
Lines 189-250: KPI calculations
Lines 300-400: Priority reorder logic
Lines 450-550: Category performance analysis
```

**What to study:**
- Pandas DataFrame operations
- NumPy mathematical calculations
- Business formulas (EOQ, turnover, etc.)
- Data classification logic

#### **`analysis/data_processor.py` (400+ lines)**
```
Lines 20-108:  Column detection algorithms
Lines 110-133: Data validation
Lines 134-218: Data quality analysis
Lines 219-309: Data cleaning
Lines 310-375: Main processing pipeline
```

**What to study:**
- String matching algorithms
- Data validation techniques
- Pandas data cleaning
- Error handling for bad data

### **Frontend Files (HTML/JavaScript)**

#### **`templates/dashboard.html` (1200+ lines)**
```
Lines 1-52:    HTML head and styling
Lines 53-463:  HTML structure (upload, dashboard, chat)
Lines 465-551: JavaScript initialization
Lines 598-651: File upload logic
Lines 677-817: Dashboard updates
Lines 884-932: AI chat functionality
Lines 1100+:   Utility functions
```

**What to study:**
- Modern JavaScript (async/await, fetch)
- DOM manipulation
- Event handling
- State management
- AJAX requests

---

## 🔐 **AUTHENTICATION & SECURITY (Current State)**

### **Login/Signup (Templates Only)**
Your `templates/login.html` and `templates/signup.html` are **UI templates only**. They don't connect to backend yet.

**To understand the current auth system:**
```python
# In api.py - NO USER AUTHENTICATION YET
# Sessions are only for CSV uploads:
session_id = str(uuid.uuid4())  # Temporary ID per upload
app_sessions[session_id] = data  # In-memory storage

# To add real auth, you'd need:
# 1. User model in database.py
# 2. Password hashing (bcrypt)
# 3. Login/signup endpoints
# 4. Session management
```

### **Current Security Features**
```python
# File upload security (api.py lines 85-87, 169-174)
ALLOWED_EXTENSIONS = {'csv'}
def allowed_file(filename):
    return filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Secure filename handling (line 177)
filename = secure_filename(file.filename)

# Environment variables (.env file)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")
```

---

## 🗄️ **DATABASE SYSTEM**

### **Current Setup (Development)**
```python
# api.py lines 77-83: In-memory storage
app_sessions = {}

def get_session_data(session_id):
    return app_sessions.get(session_id, {})

def set_session_data(session_id, data, filename=None):
    app_sessions[session_id] = data
```

### **Production Ready (`database.py`)**
Your `database.py` file has production database code but it's not active yet.

**To understand your database:**
1. **Current**: Dictionary in memory (lost when server restarts)
2. **Production**: PostgreSQL/SQLite ready via `database.py`
3. **Sessions**: UUID-based, temporary, for CSV uploads only
4. **Users**: No user storage yet (templates ready)

---

## 🤖 **AI INTEGRATION (GROQ)**

### **Setup Code (`api.py` lines 16-56)**
```python
try:
    from groq import Groq
    GROQ_AVAILABLE = True
    groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
except ImportError:
    GROQ_AVAILABLE = False
    # System works without AI
```

### **Chat Endpoint (`api.py` lines 600+)**
```python
@app.route('/api/chat', methods=['POST'])
def chat():
    # Gets inventory context from frontend
    # Sends to Groq AI
    # Returns intelligent response
```

### **Frontend Chat (`dashboard.html` lines 884-932)**
```javascript
async function sendChatMessage() {
    const inventoryContext = {
        ...appState.currentKPIs,
        reorderData: appState.currentReorderData
    };
    
    // Send context + user message to AI
}
```

---

## 📊 **CORE CALCULATIONS EXPLAINED**

### **ABC Analysis** (`calculations.py` lines 117-157)
```python
# Revenue-based product classification
df_sorted['Revenue_Impact'] = df_sorted['Annual_Sales'] * unit_cost
cumulative_percent = (cumulative_value / total_value) * 100

# A-class: Top 70% revenue, B-class: Next 20%, C-class: Bottom 10%
conditions = [
    cumulative_percent <= 70,  # A
    cumulative_percent <= 90,  # B
    cumulative_percent <= 100  # C
]
```

### **Inventory Turnover** (`calculations.py` lines 60-77)
```python
# Professional formula: COGS ÷ Average Inventory Value
self.df['Inventory_Turnover'] = np.where(
    inventory_value > 0,
    self.df['COGS'] / inventory_value,
    0
)
```

### **Days of Supply** (`calculations.py` lines 79-84)
```python
# How many days current stock will last
self.df['Days_of_Supply'] = np.where(
    self.df[self.cols['sales']] > 0,
    (self.df[self.cols['stock']] / self.df[self.cols['sales']]) * 30,
    365  # High days if no sales
)
```

### **Economic Order Quantity (EOQ)** (`calculations.py` lines 96-106)
```python
# Optimal order quantity formula
self.df['EOQ'] = np.sqrt(
    (2 * annual_demand * ordering_cost) / np.maximum(holding_cost, 1)
)
```

---

## 🎯 **STUDY PLAN (Priority Order)**

### **Week 1: Core Understanding**
1. **`api.py`** - Focus on upload endpoint (lines 142-310)
2. **`templates/dashboard.html`** - Focus on upload handler (lines 598-651)
3. **Run the system** - Upload a CSV and trace the code flow

### **Week 2: Business Logic**
1. **`analysis/calculations.py`** - Study all formulas
2. **`analysis/data_processor.py`** - Understand data cleaning
3. **Test with different CSV files** - See how calculations change

### **Week 3: Advanced Features**
1. **AI integration** - Chat functionality
2. **Frontend state management** - How data flows
3. **Error handling** - How system recovers from problems

### **Week 4: Architecture**
1. **Database system** - Current vs production
2. **Security implementation** - File upload protection
3. **Deployment configuration** - How it runs in production

---

## 🔥 **MOST CRITICAL CODE SECTIONS**

### **1. Upload Pipeline** (`api.py` lines 142-310)
```python
@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    # File validation
    # Data processing  
    # Business calculations
    # Chart generation
    # Response building
```

### **2. Data Validation** (`calculations.py` lines 23-42)
```python
def _validate_data(self):
    # Ensures required columns exist
    # Converts data types
    # Fills missing values
```

### **3. Frontend State Management** (`dashboard.html` lines 466-481)
```javascript
let appState = {
    currentSession: null,    // Links to backend session
    currentDataset: null,    // Processed data
    currentKPIs: {},        // Dashboard metrics
    isLoading: false        // UI state
};
```

---

These are the **EXACT files and line numbers** you need to study to understand your entire PIAS system. Start with the upload pipeline (`api.py` + `dashboard.html`) and then dive into the business calculations (`calculations.py`)! 🚀
