# 📤 CSV Upload Process - Technical Deep Dive

## 🔄 **Complete Data Flow: Frontend → Backend → Dashboard**

---

## 1️⃣ **FRONTEND UPLOAD INITIATION** 

### **File Selection Methods**
```javascript
// Method 1: Drag & Drop
dropZone.addEventListener('drop', handleDrop);
dropZone.addEventListener('dragover', handleDragOver);

// Method 2: Click to Browse
dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', function(e) {
    if (e.target.files[0]) {
        handleFileUpload(e.target.files[0]);
    }
});
```

### **Upload Validation (Client-Side)**
```javascript
function handleDrop(e) {
    e.preventDefault();
    const files = e.dataTransfer.files;
    
    // Validate file type
    if (files.length > 0 && files[0].type === 'text/csv') {
        handleFileUpload(files[0]);
    } else {
        showNotification('Please upload a CSV file only.', 'error');
    }
}
```

---

## 2️⃣ **UPLOAD PROCESS EXECUTION**

### **Complete handleFileUpload() Function**
```javascript
async function handleFileUpload(file) {
    if (appState.isLoading) return; // Prevent multiple uploads
    
    try {
        // Step 1: Set loading state
        appState.isLoading = true;
        showUploadState('processing');
        updateProgress(0, 'Initializing upload...');

        // Step 2: Prepare FormData
        const formData = new FormData();
        formData.append('csvFile', file);
        console.log('📁 File prepared:', file.name, 'Size:', file.size);

        updateProgress(25, 'Uploading file...');

        // Step 3: API Request with proper headers
        const response = await fetch(`${API_BASE_URL}/upload-csv`, {
            method: 'POST',
            body: formData
            // NOTE: Don't set Content-Type - browser sets multipart/form-data automatically
        });

        updateProgress(75, 'Processing data...');

        // Step 4: Response handling
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        // Step 5: Success processing
        if (result.success) {
            updateProgress(100, 'Complete!');
            
            // Update global state
            appState.currentSession = result.sessionId;
            appState.currentDataset = result.data;
            appState.lastUpdated = new Date();
            
            // Update dashboard with new data
            await updateDashboard(result.data);
            
            // UI transitions
            showUploadState('success');
            setTimeout(() => {
                document.getElementById('upload-section').classList.add('hidden');
                document.getElementById('dashboard-main').classList.remove('hidden');
            }, 2000);
            
            showNotification('Data processed successfully!', 'success');
        } else {
            throw new Error(result.error || 'Upload failed');
        }

    } catch (error) {
        console.error('Upload error:', error);
        showNotification(`Upload failed: ${error.message}`, 'error');
        showUploadState('idle');
    } finally {
        appState.isLoading = false;
    }
}
```

---

## 3️⃣ **BACKEND PROCESSING PIPELINE**

### **Complete upload_csv() Endpoint** (`api.py`)
```python
@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    """Enhanced CSV upload and analysis endpoint"""
    session_id = None
    temp_file_path = None
    
    try:
        print("🚀 CSV Upload Started")
        
        # STEP 1: Generate unique session
        session_id = str(uuid.uuid4())
        print(f"📋 Session ID: {session_id}")
        
        # STEP 2: File validation
        if 'csvFile' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded',
                'type': 'validation_error'
            }), 400

        file = request.files['csvFile']
        print(f"📁 File received: {file.filename}")
        
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

        # STEP 3: Secure file saving
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{session_id}_{filename}"
        temp_file_path = os.path.join(tempfile.gettempdir(), unique_filename)
        
        file.save(temp_file_path)
        print(f"✅ File saved: {temp_file_path}")
        print(f"📊 File size: {os.path.getsize(temp_file_path)} bytes")

        # STEP 4: Data processing
        try:
            print("🔄 Starting CSV processing...")
            
            # Professional data processing
            processor = DataProcessor()
            df, columns_map = processor.process_csv(temp_file_path)
            print(f"✅ CSV processed: {df.shape}")

            # STEP 5: Business calculations
            print("📊 Running inventory calculations...")
            calculator = InventoryCalculations(df, columns_map)
            
            kpis = calculator.calculate_kpis()
            print(f"   ✅ KPIs calculated: {kpis}")
            
            priority_reorders = calculator.get_priority_reorders(limit=25)
            print(f"   ✅ Priority reorders: {len(priority_reorders)}")
            
            category_performance = calculator.get_category_performance()
            print(f"   ✅ Category performance: {len(category_performance)}")
            
            fast_slow_movers = calculator.get_fast_slow_movers()
            print(f"   ✅ Fast/slow movers: {len(fast_slow_movers)}")
            
            filter_options = calculator.get_filter_options()
            print(f"   ✅ Filter options generated")
            
            insights = calculator.get_inventory_insights()
            print(f"   ✅ Insights generated")
            
            print(f"✅ Calculations completed")

            # STEP 6: Chart generation
            print("📊 Generating charts...")
            chart_generator = ChartGenerator(df, columns_map)
            charts = chart_generator.generate_all_charts(priority_reorders)
            print("✅ Charts generated successfully")

            # STEP 7: Session storage
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

            # STEP 8: Comprehensive response
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
        print(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': f'Upload failed: {str(e)}',
            'type': 'upload_error'
        }), 500

    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                print(f"🧹 Cleaned up temporary file: {temp_file_path}")
            except Exception as cleanup_error:
                print(f"⚠️  Cleanup warning: {cleanup_error}")
```

---

## 4️⃣ **DATA PROCESSING MODULES**

### **DataProcessor Class** (`analysis/data_processor.py`)
```python
def process_csv(self, file_path: str) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """Main processing function"""
    try:
        # 1. Load CSV with encoding handling
        df = pd.read_csv(file_path, encoding='utf-8')
        print(f"📊 Dataset loaded: {df.shape}")
        
        # 2. Intelligent column detection
        columns_map = self.detect_columns(df)
        print(f"🎯 Column mapping: {columns_map}")
        
        # 3. Validate required columns
        is_valid, missing_cols = self.validate_required_columns(columns_map)
        if not is_valid:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
        
        # 4. Data quality analysis
        self.data_quality_report = self.analyze_data_quality(df, columns_map)
        
        # 5. Data cleaning
        df_clean = self.clean_data(df, columns_map)
        
        # 6. Final validation
        if len(df_clean) == 0:
            raise ValueError("No valid data remaining after cleaning")
        
        return df_clean, columns_map
    
    except Exception as e:
        raise Exception(f"Error processing CSV: {str(e)}")
```

### **InventoryCalculations Class** (`analysis/calculations.py`)
```python
def __init__(self, df: pd.DataFrame, columns_map: Dict[str, str]):
    self.df = df.copy()
    self.cols = columns_map
    
    # CRITICAL: Validation BEFORE preparation
    self._validate_data()  # Check columns and data types
    self._prepare_data()   # Calculate derived metrics

def calculate_kpis(self) -> Dict[str, Any]:
    """Calculate comprehensive KPI metrics"""
    
    # Basic counts
    total_products = len(self.df)
    
    # Stock status analysis
    critical_count = len(self.df[self.df['Stock_Status'] == 'CRITICAL'])
    low_count = len(self.df[self.df['Stock_Status'] == 'LOW'])
    healthy_count = len(self.df[self.df['Stock_Status'] == 'HEALTHY'])
    
    # Performance metrics
    avg_turnover = self.df['Final_Turnover'].mean()
    health_percentage = (healthy_count / total_products * 100) if total_products > 0 else 0
    
    return {
        'totalProducts': int(total_products),
        'criticalAlerts': int(critical_count),
        'averageTurnover': round(float(avg_turnover), 2),
        'inventoryHealth': round(float(health_percentage), 1),
        'lowStockItems': int(low_count),
        'healthyItems': int(healthy_count)
    }
```

---

## 5️⃣ **DASHBOARD UPDATE PROCESS**

### **Frontend Dashboard Update** (`templates/dashboard.html`)
```javascript
async function updateDashboard(data) {
    try {
        console.log('📊 Updating dashboard with data:', data);

        // 1. Update KPI cards
        if (data.kpis) {
            updateKPICards(data.kpis);
            appState.currentKPIs = data.kpis;
        }

        // 2. Update charts
        if (data.charts) {
            await updateCharts(data.charts);
            appState.charts = data.charts;
        }

        // 3. Update reorder table
        if (data.reorderData) {
            updateReorderTable(data.reorderData);
            appState.currentReorderData = data.reorderData;
        }

        // 4. Update filter options
        if (data.filterOptions) {
            updateFilterOptions(data.filterOptions);
            appState.filterOptions = data.filterOptions;
        }

        // 5. Update metadata display
        if (data.metadata) {
            document.getElementById('dashboard-subtitle').textContent = 
                `Processed ${data.metadata.totalRows} products from ${data.metadata.filename}`;
        }

        updateTimestamps();
        console.log('✅ Dashboard updated successfully');
        
    } catch (error) {
        console.error('❌ Dashboard update error:', error);
        showNotification('Dashboard update error', 'error');
    }
}

function updateKPICards(kpis) {
    const updates = {
        'total-products': kpis.totalProducts?.toLocaleString() || '0',
        'critical-alerts': kpis.criticalAlerts || '0', 
        'avg-turnover': `${kpis.averageTurnover || 0}x`,
        'inventory-health': `${kpis.inventoryHealth || 0}%`
    };

    Object.entries(updates).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
}

function updateReorderTable(reorderData) {
    const tableBody = document.getElementById('reorder-table-body');

    if (!reorderData || reorderData.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="3" class="px-4 py-8 text-center text-gray-500">
                    <i class="fas fa-check-circle text-3xl mb-2 text-green-500"></i>
                    <p>No urgent reorders needed!</p>
                </td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = '';

    reorderData.slice(0, 10).forEach((item) => {
        const row = document.createElement('tr');
        const productName = item.product || item.name || 'Unknown Product';
        const currentStock = item.currentStock || item.current_stock || 0;
        const status = item.status || item.urgency || 'Unknown';
        const statusClass = status.toLowerCase();

        row.innerHTML = `
            <td class="px-4 py-3">
                <span class="font-medium text-gray-900">${productName}</span>
            </td>
            <td class="px-4 py-3">${currentStock}</td>
            <td class="px-4 py-3">
                <span class="status ${statusClass}">${status}</span>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
}
```

---

## 6️⃣ **ERROR HANDLING & RECOVERY**

### **Frontend Error Handling**
```javascript
// Comprehensive error handling in upload
catch (error) {
    console.error('Upload error:', error);
    
    // Determine error type and show appropriate message
    if (error.message.includes('400')) {
        showNotification('Invalid file format. Please check your CSV file.', 'error');
    } else if (error.message.includes('500')) {
        showNotification('Server processing error. Please try again.', 'error');
    } else if (error.message.includes('502')) {
        showNotification('Server timeout. File may be too large or complex.', 'error');
    } else {
        showNotification(`Upload failed: ${error.message}`, 'error');
    }
    
    showUploadState('idle');
} finally {
    appState.isLoading = false;
}
```

### **Backend Error Types**
```python
# Validation errors (400)
return jsonify({
    'success': False,
    'error': 'Missing required columns: Product Name, Category',
    'type': 'validation_error',
    'suggestions': ['Check column names', 'Ensure data format']
}), 400

# Processing errors (500)
return jsonify({
    'success': False,
    'error': 'Error processing your file',
    'type': 'processing_error',
    'details': str(error) if app.debug else None
}), 500

# File errors (413)
return jsonify({
    'success': False,
    'error': 'File too large. Maximum size is 25MB.',
    'type': 'file_size_error'
}), 413
```

---

## 7️⃣ **SESSION MANAGEMENT**

### **Session Storage System**
```python
# In-memory storage (development)
app_sessions = {}

def get_session_data(session_id):
    return app_sessions.get(session_id, {})

def set_session_data(session_id, data, filename=None):
    app_sessions[session_id] = data

# Session data structure
session_data = {
    'df_json': df.to_json(),           # Processed data
    'columns_map': columns_map,        # Column mappings
    'timestamp': datetime.now().isoformat(),
    'filename': filename,              # Original filename
    'kpis': kpis,                     # Calculated KPIs
    'category_performance': category_data,
    'fast_slow_movers': movers_data
}
```

### **Frontend Session Usage**
```javascript
// Global session state
appState.currentSession = result.sessionId;

// Use session for filtering
const filters = {
    sessionId: appState.currentSession,
    category: selectedCategory,
    search: searchTerm
};

// Session-based API calls
fetch(`/api/filter-products`, {
    method: 'POST',
    body: JSON.stringify(filters)
});
```

---

## 🔧 **DEBUGGING THE 502 ERROR**

### **Likely Causes of Current 502 Error:**
1. **Gunicorn Timeout**: Complex calculations taking > 30 seconds
2. **Memory Overflow**: Large CSV files consuming too much RAM  
3. **Chart Generation**: Matplotlib operations timing out
4. **Import Errors**: Missing dependencies in production

### **Debug Steps:**
1. **Check server logs** for specific error messages
2. **Test with small CSV** (< 100 rows) to isolate issue
3. **Monitor memory usage** during processing
4. **Verify all dependencies** are installed in production

### **Quick Fixes:**
```python
# Increase timeout in gunicorn_config.py
timeout = 60  # Instead of 30

# Add memory limits to calculations
def calculate_kpis(self):
    if len(self.df) > 10000:  # Large dataset
        return self._calculate_kpis_light()  # Simplified version
    else:
        return self._calculate_kpis_full()   # Full analysis
```

---

This comprehensive flow shows exactly how your CSV upload works from frontend click to dashboard display, including all the professional business logic and error handling that makes PIAS a production-ready inventory management system.
