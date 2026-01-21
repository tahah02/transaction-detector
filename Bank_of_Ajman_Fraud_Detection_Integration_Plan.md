# Bank of Ajman - Fraud Detection System Integration Plan
## Step-by-Step Implementation Guide

---

## 📋 STEP 1: PRE-DEPLOYMENT PREPARATION

### 1.1 System Requirements Check
**⏱️ Time Required: 30 minutes**

**Windows Server Requirements:**
- [ ] Windows Server 2019/2022 ✅
- [ ] .NET 6.0+ Runtime installed ✅
- [ ] IIS Web Server running ✅
- [ ] SQL Server accessible ✅
- [ ] Minimum 4GB RAM available
- [ ] 10GB free disk space

**Software Installation:**
```bash
# Step 1.1.1: Install Python 3.9+
# Download from: https://www.python.org/downloads/
# ✅ Add Python to PATH during installation

# Step 1.1.2: Verify Python installation
python --version
# Expected output: Python 3.9.x or higher

# Step 1.1.3: Install pip packages
pip install --upgrade pip
pip install virtualenv
```

### 1.2 Create Backup
**⏱️ Time Required: 15 minutes**

```sql
-- Step 1.2.1: Backup existing database
BACKUP DATABASE [BankAjmanDB] 
TO DISK = 'C:\Backups\BankAjmanDB_PreFraudIntegration_' + FORMAT(GETDATE(), 'yyyyMMdd_HHmm') + '.bak'
WITH COMPRESSION, CHECKSUM;

-- Step 1.2.2: Verify backup
RESTORE VERIFYONLY 
FROM DISK = 'C:\Backups\BankAjmanDB_PreFraudIntegration_[timestamp].bak';
```

### 1.3 Create Directory Structure
**⏱️ Time Required: 5 minutes**

```bash
# Step 1.3.1: Create main directory
mkdir C:\BankAjman\FraudDetection
mkdir C:\BankAjman\Logs
mkdir C:\BankAjman\Backups

# Step 1.3.2: Set permissions
icacls C:\BankAjman /grant "IIS_IUSRS:(OI)(CI)F"
icacls C:\BankAjman /grant "Network Service:(OI)(CI)F"
```

---

## 🐍 STEP 2: PYTHON API DEPLOYMENT

### 2.1 Copy Project Files
**⏱️ Time Required: 10 minutes**

```bash
# Step 2.1.1: Copy all project files to server
# Source: Your development machine
# Destination: C:\BankAjman\FraudDetection\

# Required files:
# ├── api.py
# ├── main.py
# ├── requirements.txt
# ├── backend/
# │   ├── __init__.py
# │   ├── hybrid_decision.py
# │   ├── autoencoder.py
# │   ├── isolation_forest.py
# │   ├── rule_engine.py
# │   ├── db_service.py
# │   ├── utils.py
# │   └── model/
# │       ├── isolation_forest_model.pkl
# │       ├── feature_names.pkl
# │       ├── scaler.pkl
# │       └── autoencoder_model.h5
# └── data/
#     ├── user_stats.json
#     └── velocity_counters.json
```

### 2.2 Setup Python Environment
**⏱️ Time Required: 15 minutes**

```bash
# Step 2.2.1: Navigate to project directory
cd C:\BankAjman\FraudDetection

# Step 2.2.2: Create virtual environment
python -m venv fraud_env

# Step 2.2.3: Activate virtual environment
fraud_env\Scripts\activate

# Step 2.2.4: Install dependencies
pip install -r requirements.txt

# Step 2.2.5: Install additional Windows service packages
pip install python-windows-service
pip install pywin32
```

### 2.3 Test Python API Locally
**⏱️ Time Required: 10 minutes**

```bash
# Step 2.3.1: Test API startup
cd C:\BankAjman\FraudDetection
fraud_env\Scripts\activate
python api.py

# Step 2.3.2: Verify API is running
# Open browser: http://localhost:8001/api/health
# Expected response: {"status": "healthy", ...}

# Step 2.3.3: Test fraud detection endpoint
# Use Postman or curl to test /api/analyze-transaction
```

### 2.4 Create Windows Service
**⏱️ Time Required: 20 minutes**

**Step 2.4.1: Create service script**
```python
# Create file: C:\BankAjman\FraudDetection\fraud_service.py

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import subprocess

class FraudDetectionService(win32serviceutil.ServiceFramework):
    _svc_name_ = "BankAjmanFraudDetection"
    _svc_display_name_ = "Bank Ajman Fraud Detection API"
    _svc_description_ = "FastAPI service for real-time fraud detection"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.process = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        if self.process:
            self.process.terminate()

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

    def main(self):
        # Change to service directory
        os.chdir(r'C:\BankAjman\FraudDetection')
        
        # Start the FastAPI application
        cmd = [r'C:\BankAjman\FraudDetection\fraud_env\Scripts\python.exe', 'api.py']
        self.process = subprocess.Popen(cmd)
        
        # Wait for stop signal
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(FraudDetectionService)
```

**Step 2.4.2: Install Windows Service**
```bash
# Step 2.4.2.1: Install service
cd C:\BankAjman\FraudDetection
fraud_env\Scripts\python fraud_service.py install

# Step 2.4.2.2: Configure service
sc config BankAjmanFraudDetection start= auto
sc config BankAjmanFraudDetection depend= MSSQLSERVER

# Step 2.4.2.3: Start service
net start BankAjmanFraudDetection

# Step 2.4.2.4: Verify service is running
sc query BankAjmanFraudDetection
netstat -an | findstr :8001
```

---

## 🗄️ STEP 3: DATABASE SETUP

### 3.1 Create New Tables
**⏱️ Time Required: 10 minutes**

```sql
-- Step 3.1.1: Connect to SQL Server Management Studio
-- Database: [Your existing Bank database]

-- Step 3.1.2: Create fraud detection results table
CREATE TABLE FraudDetectionResults (
    Id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    TransactionId NVARCHAR(100) NOT NULL,
    CustomerId NVARCHAR(50) NOT NULL,
    AccountNumber NVARCHAR(50) NOT NULL,
    Amount DECIMAL(18,2) NOT NULL,
    Decision NVARCHAR(50) NOT NULL, -- APPROVED, REQUIRES_USER_APPROVAL
    RiskScore DECIMAL(5,4),
    Reasons NVARCHAR(MAX),
    IndividualScores NVARCHAR(MAX), -- JSON format
    ProcessingTimeMs INT,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    UserDecision NVARCHAR(50) NULL, -- APPROVED_BY_USER, REJECTED_BY_USER
    UserDecisionAt DATETIME2 NULL,
    UserDecisionBy NVARCHAR(100) NULL
);

-- Step 3.1.3: Create indexes for performance
CREATE INDEX IX_FraudDetectionResults_TransactionId 
ON FraudDetectionResults(TransactionId);

CREATE INDEX IX_FraudDetectionResults_CustomerId_CreatedAt 
ON FraudDetectionResults(CustomerId, CreatedAt DESC);

-- Step 3.1.4: Update existing transaction table
ALTER TABLE Transactions 
ADD FraudStatus NVARCHAR(50) DEFAULT 'NORMAL';

-- Step 3.1.5: Create index on new column
CREATE INDEX IX_Transactions_FraudStatus 
ON Transactions(FraudStatus);

-- Step 3.1.6: Verify table creation
SELECT name FROM sys.tables WHERE name LIKE '%Fraud%';
SELECT name FROM sys.columns WHERE object_id = OBJECT_ID('Transactions') AND name = 'FraudStatus';
```

### 3.2 Update Database Connection
**⏱️ Time Required: 5 minutes**

```python
# Step 3.2.1: Update connection string in Python
# File: C:\BankAjman\FraudDetection\backend\db_service.py

# Update connection string to match your SQL Server
CONNECTION_STRING = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=your_server;DATABASE=BankAjmanDB;Trusted_Connection=yes;"

# Step 3.2.2: Test database connection
cd C:\BankAjman\FraudDetection
fraud_env\Scripts\activate
python -c "from backend.db_service import get_db_service; db = get_db_service(); print('Connected:', db.connect())"
```

---

## 💻 STEP 4: .NET APPLICATION UPDATES

### 4.1 Install NuGet Packages
**⏱️ Time Required: 5 minutes**

```bash
# Step 4.1.1: Open your existing .NET solution in Visual Studio

# Step 4.1.2: Open Package Manager Console
# Tools > NuGet Package Manager > Package Manager Console

# Step 4.1.3: Install required packages
Install-Package Microsoft.Extensions.Http
Install-Package Newtonsoft.Json

# Step 4.1.4: Verify packages are installed
# Check packages.config or .csproj file
```

### 4.2 Add Configuration Settings
**⏱️ Time Required: 5 minutes**

```json
// Step 4.2.1: Open appsettings.json
// Step 4.2.2: Add fraud detection configuration

{
  "ConnectionStrings": {
    // ... existing connection strings
  },
  "FraudDetection": {
    "ApiUrl": "http://localhost:8001/api",
    "Timeout": 30000,
    "Enabled": true,
    "MaxRetries": 3,
    "CircuitBreakerThreshold": 5
  },
  // ... rest of existing configuration
}
```

### 4.3 Create Data Models
**⏱️ Time Required: 10 minutes**

```csharp
// Step 4.3.1: Create new file: Models/FraudDetectionModels.cs

using System.ComponentModel.DataAnnotations;

namespace BankAjman.Models
{
    public class FraudDetectionResult
    {
        public string Decision { get; set; }
        public float RiskScore { get; set; }
        public float ConfidenceLevel { get; set; }
        public List<string> Reasons { get; set; } = new List<string>();
        public Dictionary<string, object> IndividualScores { get; set; } = new Dictionary<string, object>();
        public string TransactionId { get; set; }
        public int ProcessingTimeMs { get; set; }
    }

    public class ApprovalRequest
    {
        [Required]
        public string TransactionId { get; set; }
        
        [Required]
        public string PendingTransactionId { get; set; }
        
        [Required]
        public string UserDecision { get; set; } // APPROVE or REJECT
    }

    public class TransferResponse
    {
        public bool Success { get; set; }
        public bool RequiresApproval { get; set; }
        public string TransactionId { get; set; }
        public string Message { get; set; }
        public List<string> RiskReasons { get; set; } = new List<string>();
        public float RiskScore { get; set; }
        public string PendingTransactionId { get; set; }
    }
}
```

### 4.4 Create Fraud Detection Service
**⏱️ Time Required: 15 minutes**

```csharp
// Step 4.4.1: Create new file: Services/FraudDetectionService.cs

using System.Text.Json;
using BankAjman.Models;

namespace BankAjman.Services
{
    public interface IFraudDetectionService
    {
        Task<FraudDetectionResult> AnalyzeTransactionAsync(TransactionRequest request);
        Task<bool> UpdateTransactionStatusAsync(string transactionId, string userDecision, string userId);
    }

    public class FraudDetectionService : IFraudDetectionService
    {
        private readonly HttpClient _httpClient;
        private readonly ILogger<FraudDetectionService> _logger;
        private readonly IConfiguration _configuration;

        public FraudDetectionService(HttpClient httpClient, ILogger<FraudDetectionService> logger, IConfiguration configuration)
        {
            _httpClient = httpClient;
            _logger = logger;
            _configuration = configuration;
        }

        public async Task<FraudDetectionResult> AnalyzeTransactionAsync(TransactionRequest request)
        {
            try
            {
                var fraudRequest = new
                {
                    customer_id = request.CustomerId,
                    from_account_no = request.FromAccount,
                    to_account_no = request.ToAccount,
                    transaction_amount = request.Amount,
                    transfer_type = request.TransferType,
                    datetime = DateTime.Now,
                    bank_country = "UAE"
                };

                var json = JsonSerializer.Serialize(fraudRequest);
                var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");

                var response = await _httpClient.PostAsync("analyze-transaction", content);
                response.EnsureSuccessStatusCode();

                var responseJson = await response.Content.ReadAsStringAsync();
                var result = JsonSerializer.Deserialize<FraudDetectionResult>(responseJson, new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                });

                _logger.LogInformation("Fraud detection completed for transaction {TransactionId}: {Decision}", 
                    result.TransactionId, result.Decision);

                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error calling fraud detection API");
                // Fallback: Allow transaction if fraud detection fails
                return new FraudDetectionResult 
                { 
                    Decision = "APPROVED", 
                    RiskScore = 0.0f,
                    Reasons = new List<string> { "Fraud detection service unavailable" }
                };
            }
        }

        public async Task<bool> UpdateTransactionStatusAsync(string transactionId, string userDecision, string userId)
        {
            try
            {
                var updateRequest = new
                {
                    transaction_id = transactionId,
                    user_decision = userDecision,
                    decided_by = userId,
                    decided_at = DateTime.Now
                };

                var json = JsonSerializer.Serialize(updateRequest);
                var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");

                var response = await _httpClient.PostAsync("update-transaction-status", content);
                return response.IsSuccessStatusCode;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error updating transaction status");
                return false;
            }
        }
    }
}
```

### 4.5 Register Services in Startup
**⏱️ Time Required: 5 minutes**

```csharp
// Step 4.5.1: Open Startup.cs or Program.cs (depending on .NET version)

// Step 4.5.2: Add service registration in ConfigureServices method
public void ConfigureServices(IServiceCollection services)
{
    // ... existing service registrations

    // Add HTTP client for fraud detection
    services.AddHttpClient<IFraudDetectionService, FraudDetectionService>(client =>
    {
        var fraudConfig = Configuration.GetSection("FraudDetection");
        client.BaseAddress = new Uri(fraudConfig["ApiUrl"]);
        client.Timeout = TimeSpan.FromMilliseconds(int.Parse(fraudConfig["Timeout"]));
    });

    // ... rest of existing services
}
```

### 4.6 Update Transaction Controller
**⏱️ Time Required: 20 minutes**

```csharp
// Step 4.6.1: Open your existing TransactionController.cs

// Step 4.6.2: Add fraud detection service injection
private readonly IFraudDetectionService _fraudDetectionService;

// Update constructor
public TransactionController(
    // ... existing dependencies
    IFraudDetectionService fraudDetectionService)
{
    // ... existing assignments
    _fraudDetectionService = fraudDetectionService;
}

// Step 4.6.3: Update ProcessTransfer method
[HttpPost("transfer")]
public async Task<IActionResult> ProcessTransfer(TransferRequest request)
{
    // Existing validation
    if (!ModelState.IsValid)
        return BadRequest(ModelState);

    // Existing authentication and authorization checks
    var userId = GetCurrentUserId();
    if (!await IsAuthorizedForAccount(request.FromAccount, userId))
        return Unauthorized();

    try
    {
        // NEW: Fraud detection analysis
        var fraudResult = await _fraudDetectionService.AnalyzeTransactionAsync(request);

        if (fraudResult.Decision == "REQUIRES_USER_APPROVAL")
        {
            // Store pending transaction
            var pendingTransaction = await CreatePendingTransaction(request, fraudResult);

            return Ok(new TransferResponse
            {
                Success = false,
                RequiresApproval = true,
                TransactionId = fraudResult.TransactionId,
                Message = "Transaction requires additional approval due to security checks",
                RiskReasons = fraudResult.Reasons,
                RiskScore = fraudResult.RiskScore,
                PendingTransactionId = pendingTransaction.Id.ToString()
            });
        }

        // Continue with existing normal transaction flow
        var result = await ProcessNormalTransfer(request);
        
        // Update fraud status as normal
        await UpdateTransactionFraudStatus(result.TransactionId, "NORMAL");

        return Ok(result);
    }
    catch (Exception ex)
    {
        _logger.LogError(ex, "Error processing transfer");
        return StatusCode(500, "Internal server error");
    }
}

// Step 4.6.4: Add new approval endpoint
[HttpPost("approve-suspicious-transaction")]
public async Task<IActionResult> ApproveSuspiciousTransaction(ApprovalRequest request)
{
    var userId = GetCurrentUserId();
    
    try
    {
        if (request.UserDecision == "APPROVE")
        {
            // Process the original transaction
            var originalRequest = await GetPendingTransactionRequest(request.PendingTransactionId);
            var result = await ProcessNormalTransfer(originalRequest);
            
            // Update fraud detection status
            await _fraudDetectionService.UpdateTransactionStatusAsync(
                request.TransactionId, "APPROVED_BY_USER", userId);
            
            await UpdateTransactionFraudStatus(result.TransactionId, "APPROVED_BY_USER");

            return Ok(new { Success = true, TransactionId = result.TransactionId });
        }
        else
        {
            // Reject transaction
            await _fraudDetectionService.UpdateTransactionStatusAsync(
                request.TransactionId, "REJECTED_BY_USER", userId);
            
            await RejectPendingTransaction(request.PendingTransactionId, "REJECTED_BY_USER");

            return Ok(new { Success = true, Message = "Transaction rejected" });
        }
    }
    catch (Exception ex)
    {
        _logger.LogError(ex, "Error processing transaction approval");
        return StatusCode(500, "Internal server error");
    }
}
```

---

## 🎨 STEP 5: FRONTEND UPDATES

### 5.1 Add Fraud Approval Modal HTML
**⏱️ Time Required: 10 minutes**

```html
<!-- Step 5.1.1: Open your existing transaction page (e.g., Transfer.cshtml) -->
<!-- Step 5.1.2: Add modal HTML before closing </body> tag -->

<!-- Fraud Approval Modal -->
<div id="fraudApprovalModal" class="modal fade" tabindex="-1" role="dialog" style="display: none;">
    <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
            <div class="modal-header bg-warning">
                <h4 class="modal-title">
                    <i class="fas fa-exclamation-triangle"></i>
                    Security Check Required
                </h4>
            </div>
            <div class="modal-body">
                <div class="alert alert-warning">
                    <strong>⚠️ Suspicious Transaction Detected</strong><br>
                    Our security system has identified unusual patterns in this transaction.
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>Risk Assessment</h5>
                            </div>
                            <div class="card-body">
                                <div class="risk-score-container">
                                    <label>Risk Score:</label>
                                    <span id="riskScore" class="badge badge-danger risk-value">0%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>Security Concerns</h5>
                            </div>
                            <div class="card-body">
                                <ul id="riskReasons" class="list-unstyled"></ul>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4">
                    <div class="alert alert-info">
                        <strong>What would you like to do?</strong><br>
                        Please review the transaction details and security concerns above, then choose your action.
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-success btn-lg" onclick="handleApprovalDecision('APPROVE')">
                    <i class="fas fa-check"></i> Yes, Proceed with Transaction
                </button>
                <button type="button" class="btn btn-danger btn-lg" onclick="handleApprovalDecision('REJECT')">
                    <i class="fas fa-times"></i> Cancel Transaction
                </button>
            </div>
        </div>
    </div>
</div>

<!-- Loading overlay -->
<div id="loadingOverlay" class="loading-overlay" style="display: none;">
    <div class="loading-content">
        <div class="spinner-border text-primary" role="status">
            <span class="sr-only">Processing...</span>
        </div>
        <p class="mt-2">Processing your request...</p>
    </div>
</div>
```

### 5.2 Add CSS Styles
**⏱️ Time Required: 5 minutes**

```css
/* Step 5.2.1: Add to your existing CSS file or create new one */

.risk-score-container {
    text-align: center;
    padding: 20px;
}

.risk-value {
    font-size: 24px;
    padding: 10px 20px;
    border-radius: 25px;
}

.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 9999;
    display: flex;
    justify-content: center;
    align-items: center;
}

.loading-content {
    background: white;
    padding: 30px;
    border-radius: 10px;
    text-align: center;
}

.modal-lg {
    max-width: 800px;
}

#riskReasons li {
    padding: 5px 0;
    border-bottom: 1px solid #eee;
}

#riskReasons li:before {
    content: "⚠️ ";
    margin-right: 5px;
}
```

### 5.3 Update JavaScript Functions
**⏱️ Time Required: 15 minutes**

```javascript
// Step 5.3.1: Open your existing transaction JavaScript file
// Step 5.3.2: Update or add these functions

// Enhanced transaction submission
async function submitTransfer(formData) {
    try {
        showLoader();
        
        const response = await fetch('/api/transaction/transfer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (result.RequiresApproval) {
            // NEW: Show fraud approval modal
            showFraudApprovalModal(result);
        } else if (result.Success) {
            // Existing success flow
            showSuccessMessage('Transaction completed successfully');
            redirectToTransactionHistory();
        } else {
            showErrorMessage(result.Message);
        }
    } catch (error) {
        console.error('Transaction error:', error);
        showErrorMessage('Transaction failed. Please try again.');
    } finally {
        hideLoader();
    }
}

// NEW: Show fraud approval modal
function showFraudApprovalModal(data) {
    const modal = document.getElementById('fraudApprovalModal');
    
    // Populate risk score
    const riskScoreElement = document.getElementById('riskScore');
    const riskPercentage = (data.RiskScore * 100).toFixed(1);
    riskScoreElement.textContent = riskPercentage + '%';
    
    // Set risk score color based on severity
    riskScoreElement.className = 'badge risk-value ';
    if (data.RiskScore > 0.7) {
        riskScoreElement.className += 'badge-danger';
    } else if (data.RiskScore > 0.4) {
        riskScoreElement.className += 'badge-warning';
    } else {
        riskScoreElement.className += 'badge-info';
    }
    
    // Populate risk reasons
    const reasonsList = document.getElementById('riskReasons');
    reasonsList.innerHTML = data.RiskReasons
        .map(reason => `<li>${reason}</li>`)
        .join('');
    
    // Store transaction data for approval
    modal.dataset.transactionId = data.TransactionId;
    modal.dataset.pendingId = data.PendingTransactionId;
    
    // Show modal
    $('#fraudApprovalModal').modal('show');
}

// NEW: Handle user approval decision
async function handleApprovalDecision(decision) {
    const modal = document.getElementById('fraudApprovalModal');
    const transactionId = modal.dataset.transactionId;
    const pendingId = modal.dataset.pendingId;
    
    try {
        showLoader();
        
        const response = await fetch('/api/transaction/approve-suspicious-transaction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({
                TransactionId: transactionId,
                PendingTransactionId: pendingId,
                UserDecision: decision
            })
        });

        const result = await response.json();

        if (result.Success) {
            $('#fraudApprovalModal').modal('hide');
            
            if (decision === 'APPROVE') {
                showSuccessMessage('Transaction approved and completed successfully');
            } else {
                showInfoMessage('Transaction has been cancelled for security reasons');
            }
            
            // Redirect after 2 seconds
            setTimeout(() => {
                redirectToTransactionHistory();
            }, 2000);
        } else {
            showErrorMessage('Failed to process your decision. Please try again.');
        }
    } catch (error) {
        console.error('Approval error:', error);
        showErrorMessage('Error processing approval. Please try again.');
    } finally {
        hideLoader();
    }
}

// Utility functions
function showLoader() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoader() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

function showSuccessMessage(message) {
    // Use your existing success message function
    // Or implement using Bootstrap alerts/toasts
    alert('Success: ' + message);
}

function showErrorMessage(message) {
    // Use your existing error message function
    alert('Error: ' + message);
}

function showInfoMessage(message) {
    // Use your existing info message function
    alert('Info: ' + message);
}

function getAuthToken() {
    // Return your existing JWT token
    return localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
}

function redirectToTransactionHistory() {
    // Redirect to your transaction history page
    window.location.href = '/transaction/history';
}
```

---

## 🚀 STEP 6: BUILD AND DEPLOY

### 6.1 Build .NET Application
**⏱️ Time Required: 10 minutes**

```bash
# Step 6.1.1: Open Command Prompt in your .NET solution directory
cd C:\YourBankingSolution

# Step 6.1.2: Restore NuGet packages
dotnet restore

# Step 6.1.3: Build solution
dotnet build -c Release

# Step 6.1.4: Publish application
dotnet publish -c Release -o C:\inetpub\wwwroot\BankAjman

# Step 6.1.5: Verify build success
# Check for any build errors in output
```

### 6.2 Deploy to IIS
**⏱️ Time Required: 10 minutes**

```bash
# Step 6.2.1: Stop IIS application pool
# Open IIS Manager
# Navigate to Application Pools
# Right-click your application pool > Stop

# Step 6.2.2: Copy files to IIS directory
# Files should be copied to: C:\inetpub\wwwroot\BankAjman
# Ensure all new files are included

# Step 6.2.3: Update web.config (if needed)
# Verify connection strings
# Check fraud detection configuration

# Step 6.2.4: Start IIS application pool
# Right-click your application pool > Start

# Step 6.2.5: Test application
# Open browser: https://yourbankdomain.com
# Verify login works
# Test existing functionality
```

---

## 🧪 STEP 7: INTEGRATION TESTING

### 7.1 Test Python API
**⏱️ Time Required: 15 minutes**

```bash
# Step 7.1.1: Test health endpoint
curl http://localhost:8001/api/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2024-01-XX...",
#   "database": "connected",
#   "models": {...}
# }

# Step 7.1.2: Test fraud detection endpoint
# Use Postman or create test script
```

**Test Data for Postman:**
```json
{
  "customer_id": "TEST001",
  "from_account_no": "1234567890",
  "to_account_no": "0987654321",
  "transaction_amount": 50000.00,
  "transfer_type": "S",
  "datetime": "2024-01-15T14:30:00",
  "bank_country": "UAE"
}
```

### 7.2 Test .NET Integration
**⏱️ Time Required: 20 minutes**

```csharp
// Step 7.2.1: Test normal transaction (should be approved)
// Amount: 1000 AED
// Transfer type: "I" (internal)
// Expected: Direct approval

// Step 7.2.2: Test suspicious transaction (should require approval)
// Amount: 100000 AED
// Transfer type: "S" (SWIFT)
// Expected: User approval modal

// Step 7.2.3: Test user approval flow
// 1. Submit suspicious transaction
// 2. Verify modal appears
// 3. Click "Approve"
// 4. Verify transaction completes

// Step 7.2.4: Test user rejection flow
// 1. Submit suspicious transaction
// 2. Verify modal appears
// 3. Click "Reject"
// 4. Verify transaction is cancelled
```

### 7.3 Database Verification
**⏱️ Time Required: 10 minutes**

```sql
-- Step 7.3.1: Check fraud detection results
SELECT TOP 10 * FROM FraudDetectionResults 
ORDER BY CreatedAt DESC;

-- Step 7.3.2: Check transaction fraud status
SELECT TOP 10 TransactionId, Amount, FraudStatus 
FROM Transactions 
WHERE FraudStatus IS NOT NULL
ORDER BY CreatedDate DESC;

-- Step 7.3.3: Verify user decisions
SELECT 
    TransactionId,
    Decision,
    UserDecision,
    UserDecisionBy,
    UserDecisionAt
FROM FraudDetectionResults 
WHERE UserDecision IS NOT NULL;
```

---

## 📊 STEP 8: MONITORING SETUP

### 8.1 Setup Logging
**⏱️ Time Required: 10 minutes**

```python
# Step 8.1.1: Update Python API logging
# File: C:\BankAjman\FraudDetection\api.py

import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('C:/BankAjman/Logs/fraud_detection.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Add logging to endpoints
@app.post("/api/analyze-transaction", response_model=TransactionResponse)
def analyze_transaction(request: TransactionRequest):
    logger.info(f"Fraud analysis started for customer {request.customer_id}, amount {request.transaction_amount}")
    
    # ... existing code ...
    
    logger.info(f"Fraud analysis completed: {decision}, risk score: {result.get('risk_score', 0)}")
    return response
```

### 8.2 Setup Performance Monitoring
**⏱️ Time Required: 5 minutes**

```sql
-- Step 8.2.1: Create monitoring queries

-- Daily fraud detection statistics
SELECT 
    CAST(CreatedAt AS DATE) as Date,
    COUNT(*) as TotalAnalyzed,
    SUM(CASE WHEN Decision = 'REQUIRES_USER_APPROVAL' THEN 1 ELSE 0 END) as RequiredApproval,
    SUM(CASE WHEN UserDecision = 'APPROVED_BY_USER' THEN 1 ELSE 0 END) as UserApproved,
    SUM(CASE WHEN UserDecision = 'REJECTED_BY_USER' THEN 1 ELSE 0 END) as UserRejected,
    AVG(ProcessingTimeMs) as AvgProcessingTime
FROM FraudDetectionResults 
WHERE CreatedAt >= DATEADD(day, -7, GETDATE())
GROUP BY CAST(CreatedAt AS DATE)
ORDER BY Date DESC;

-- High risk transactions
SELECT 
    TransactionId,
    CustomerId,
    Amount,
    RiskScore,
    Decision,
    CreatedAt
FROM FraudDetectionResults 
WHERE RiskScore > 0.7
ORDER BY CreatedAt DESC;
```

---

## ✅ STEP 9: FINAL VERIFICATION

### 9.1 Complete System Test
**⏱️ Time Required: 30 minutes**

**Test Scenario 1: Normal Transaction**
- [ ] Login to banking application
- [ ] Navigate to transfer page
- [ ] Enter normal transaction (Amount: 1000 AED)
- [ ] Submit transaction
- [ ] ✅ Should complete without approval modal
- [ ] ✅ Check database: FraudStatus = 'NORMAL'

**Test Scenario 2: Suspicious Transaction**
- [ ] Login to banking application
- [ ] Navigate to transfer page
- [ ] Enter suspicious transaction (Amount: 50000 AED, Type: SWIFT)
- [ ] Submit transaction
- [ ] ✅ Should show approval modal
- [ ] ✅ Modal should display risk score and reasons
- [ ] Click "Approve"
- [ ] ✅ Transaction should complete
- [ ] ✅ Check database: FraudStatus = 'APPROVED_BY_USER'

**Test Scenario 3: Transaction Rejection**
- [ ] Submit suspicious transaction
- [ ] ✅ Approval modal appears
- [ ] Click "Reject"
- [ ] ✅ Transaction should be cancelled
- [ ] ✅ Check database: UserDecision = 'REJECTED_BY_USER'

### 9.2 Performance Verification
**⏱️ Time Required: 10 minutes**

```bash
# Step 9.2.1: Check API response times
# Use browser developer tools or Postman
# Fraud detection should respond within 2-3 seconds

# Step 9.2.2: Check service status
sc query BankAjmanFraudDetection
# Status should be: RUNNING

# Step 9.2.3: Check logs
type C:\BankAjman\Logs\fraud_detection.log
# Should show recent activity without errors
```

### 9.3 Security Verification
**⏱️ Time Required: 5 minutes**

- [ ] ✅ HTTPS is enforced
- [ ] ✅ JWT tokens are validated
- [ ] ✅ Database connections are secure
- [ ] ✅ API endpoints require authentication
- [ ] ✅ Sensitive data is not logged

---

## 🎯 SUCCESS CRITERIA CHECKLIST

### Technical Requirements
- [ ] ✅ Python API service running on port 8001
- [ ] ✅ .NET application successfully calling fraud API
- [ ] ✅ Database tables created and populated
- [ ] ✅ User approval modal working correctly
- [ ] ✅ Transaction status updates working
- [ ] ✅ All existing functionality preserved

### Performance Requirements
- [ ] ✅ API response time < 3 seconds
- [ ] ✅ No impact on normal transaction flow
- [ ] ✅ Service automatically starts with Windows
- [ ] ✅ Error handling and fallback working

### Business Requirements
- [ ] ✅ Suspicious transactions require user approval
- [ ] ✅ Normal transactions process automatically
- [ ] ✅ Complete audit trail maintained
- [ ] ✅ User-friendly approval interface

---

## 🚨 TROUBLESHOOTING GUIDE

### Common Issues and Solutions

**Issue 1: Python Service Won't Start**
```bash
# Check Python installation
python --version

# Check service logs
type C:\BankAjman\Logs\fraud_detection.log

# Manually test API
cd C:\BankAjman\FraudDetection
fraud_env\Scripts\activate
python api.py

# Check port availability
netstat -an | findstr :8001
```

**Issue 2: .NET Can't Connect to Python API**
```csharp
// Test HTTP connectivity
var client = new HttpClient();
var response = await client.GetAsync("http://localhost:8001/api/health");
Console.WriteLine(response.StatusCode);

// Check firewall settings
// Verify fraud detection configuration in appsettings.json
```

**Issue 3: Database Connection Issues**
```sql
-- Test database connectivity
SELECT @@SERVERNAME, DB_NAME();

-- Check table existence
SELECT name FROM sys.tables WHERE name LIKE '%Fraud%';

-- Verify permissions
SELECT 
    dp.name AS principal_name,
    dp.type_desc AS principal_type_desc,
    o.name AS object_name,
    p.permission_name,
    p.state_desc AS permission_state_desc
FROM sys.database_permissions p
LEFT JOIN sys.objects o ON p.major_id = o.object_id
LEFT JOIN sys.database_principals dp ON p.grantee_principal_id = dp.principal_id
WHERE o.name LIKE '%Fraud%';
```

**Issue 4: Frontend Modal Not Appearing**
```javascript
// Check browser console for errors
console.log('Testing fraud modal');

// Verify jQuery/Bootstrap is loaded
console.log(typeof $);
console.log(typeof Bootstrap);

// Test modal manually
$('#fraudApprovalModal').modal('show');
```

---

## 📞 SUPPORT INFORMATION

### Emergency Rollback
If critical issues occur, follow these steps:

1. **Disable Fraud Detection**
```json
// In appsettings.json
{
  "FraudDetection": {
    "Enabled": false
  }
}
```

2. **Stop Python Service**
```bash
net stop BankAjmanFraudDetection
```

3. **Restore Database** (if needed)
```sql
RESTORE DATABASE [BankAjmanDB] 
FROM DISK = 'C:\Backups\BankAjmanDB_PreFraudIntegration_[timestamp].bak'
WITH REPLACE;
```

### Contact Information
- **Technical Lead**: [Your Contact]
- **Database Admin**: [DBA Contact]
- **System Admin**: [SysAdmin Contact]

---

## 📋 POST-DEPLOYMENT CHECKLIST

### Day 1 After Deployment
- [ ] Monitor fraud detection logs
- [ ] Check system performance
- [ ] Verify transaction processing
- [ ] Review user feedback

### Week 1 After Deployment
- [ ] Analyze fraud detection statistics
- [ ] Review false positive rates
- [ ] Optimize detection thresholds
- [ ] Train support staff

### Month 1 After Deployment
- [ ] Performance optimization
- [ ] Model retraining (if needed)
- [ ] Business impact assessment
- [ ] Documentation updates

---

**🎉 CONGRATULATIONS!**

Your Bank of Ajman fraud detection system is now successfully integrated and operational!

**Total Implementation Time**: 2-3 days
**Business Impact**: Enhanced security with minimal user disruption
**Technical Achievement**: Seamless integration of AI/ML with existing banking infrastructure