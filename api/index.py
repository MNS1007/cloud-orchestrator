from http.server import BaseHTTPRequestHandler
import json
import os
import sys

# Add the cloud_orchestrator directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'cloud_orchestrator'))

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>Cloud Orchestrator - ADK Web Agents</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        .input-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
        }
        textarea {
            width: 100%;
            height: 120px;
            padding: 15px;
            border: none;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.9);
            color: #333;
            font-size: 16px;
            resize: vertical;
        }
        button {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 18px;
            cursor: pointer;
            transition: transform 0.2s;
            width: 100%;
        }
        button:hover {
            transform: translateY(-2px);
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .result {
            margin-top: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            max-height: 400px;
            overflow-y: auto;
        }
        .loading {
            text-align: center;
            padding: 20px;
        }
        .spinner {
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-top: 4px solid white;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Cloud Orchestrator</h1>
        <p style="text-align: center; margin-bottom: 30px; font-size: 18px;">
            Deploy and manage your Google Cloud infrastructure with AI-powered agents
        </p>
        
        <div class="input-group">
            <label for="prompt">Describe your infrastructure request:</label>
            <textarea id="prompt" placeholder="Example: Set up a real-time data pipeline from Pub/Sub through Dataflow into BigQuery with monitoring and alerting...">Set up a real-time data pipeline from Pub/Sub through Dataflow into BigQuery</textarea>
        </div>
        
        <button onclick="submitRequest()" id="submitBtn">🤖 Generate Infrastructure Plan</button>
        
        <div id="result" class="result" style="display: none;"></div>
    </div>

    <script>
        async function submitRequest() {
            const prompt = document.getElementById('prompt').value;
            const submitBtn = document.getElementById('submitBtn');
            const result = document.getElementById('result');
            
            if (!prompt.trim()) {
                alert('Please enter a request');
                return;
            }
            
            submitBtn.disabled = true;
            submitBtn.textContent = '🔄 Processing...';
            result.style.display = 'block';
            result.innerHTML = '<div class="loading"><div class="spinner"></div>Generating your infrastructure plan...</div>';
            
            try {
                const response = await fetch('/api/process', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ prompt: prompt })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    result.innerHTML = data.result;
                } else {
                    result.innerHTML = '❌ Error: ' + data.error;
                }
            } catch (error) {
                result.innerHTML = '❌ Network error: ' + error.message;
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = '🤖 Generate Infrastructure Plan';
            }
        }
        
        // Allow Enter key to submit
        document.getElementById('prompt').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && e.ctrlKey) {
                submitRequest();
            }
        });
    </script>
</body>
</html>
        """
        
        self.wfile.write(html.encode())
    
    def do_POST(self):
        if self.path == '/api/process':
            self.handle_process_request()
        else:
            self.send_error(404)
    
    def handle_process_request(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            prompt = data.get('prompt', '')
            
            # Process the request using ADK
            result = self.process_with_adk(prompt)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'success': True,
                'result': result
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'success': False,
                'error': str(e)
            }
            
            self.wfile.write(json.dumps(response).encode())
    
    def process_with_adk(self, prompt):
        """Process the request using ADK web agents"""
        try:
            # For now, return a simple response to test the deployment
            return f"""✅ **Infrastructure Plan Generated Successfully!**

📋 **Request:** {prompt}

🔄 **Execution Flow:**
1. **IAM** - Create service account for data pipeline
2. **Pub/Sub** - Create topic for event ingestion
3. **Dataflow** - Launch streaming job to process events
4. **BigQuery** - Create dataset for analytics
5. **BigQuery** - Create table for processed data

📊 **Summary:**
• Total steps: 5
• Services involved: 4
• Execution order: IAM → Pub/Sub → Dataflow → BigQuery

💡 **Next Steps:**
1. Review the generated plan above
2. Execute the tool calls in order
3. Monitor the deployment progress

🎉 **Deployment Status:** Ready to deploy!"""
            
        except Exception as e:
            return f"❌ Error processing request: {str(e)}" 