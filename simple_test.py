#!/usr/bin/env python3
"""
Simple test to check how open_dag_page opens the browser.
"""

import os
import sys
import json
import webbrowser

def open_dag_page(parsed_response, filename="dag_visualization.html"):
    """
    Generate an HTML page rendering the DAG or tool calls via Cytoscape and open it in a browser.
    Returns success or error message.
    """
    try:
        # Check if input is tool calls (list of dicts) or DAG (dict of lists)
        if isinstance(parsed_response, list):
            # Handle tool calls
            tool_calls = parsed_response
            elements = []
            seen = set()
            
            # Create nodes for each tool call
            for i, tool_call in enumerate(tool_calls):
                action = tool_call.get("action", "unknown")
                service = action.split('.')[0].replace('_', ' ').title()
                node_id = f"step_{i+1}"
                
                elements.append({
                    "data": {
                        "id": node_id,
                        "label": f"{i+1}. {service}\n{action}",
                        "service": service,
                        "action": action
                    }
                })
                seen.add(node_id)
            
            # Create edges connecting sequential steps
            for i in range(len(tool_calls) - 1):
                elements.append({
                    "data": {
                        "source": f"step_{i+1}",
                        "target": f"step_{i+2}",
                        "label": "→"
                    }
                })
            
            title = "Tool Execution Flow"
            
        else:
            # Handle DAG (original functionality)
            dag = parsed_response
            elements = []
            seen = set()
            for src, targets in dag.items():
                if src not in seen:
                    elements.append({"data": {"id": src}})
                    seen.add(src)
                for tgt in targets:
                    if tgt not in seen:
                        elements.append({"data": {"id": tgt}})
                        seen.add(tgt)
                    elements.append({"data": {"source": src, "target": tgt}})
            
            title = "GCP Service DAG"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8'>
    <title>{title}</title>
    <script src='https://unpkg.com/cytoscape/dist/cytoscape.min.js'></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        #cy {{
            width: 100%;
            height: 600px;
            border: 2px solid #ddd;
            border-radius: 8px;
            background-color: white;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
            color: #333;
        }}
        .info {{
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
    </div>
    
    <div class="info">
        <p><strong>Total Steps:</strong> {len([e for e in elements if 'source' not in e['data']])}</p>
        <p><strong>Generated:</strong> {filename}</p>
    </div>
    
    <div id='cy'></div>
    
    <script>
        var elems = {json.dumps(elements)};
        var cy = cytoscape({{
            container: document.getElementById('cy'),
            elements: elems,
            layout: {{
                name: 'breadthfirst',
                directed: true,
                padding: 20,
                spacingFactor: 1.5
            }},
            style: [
                {{
                    selector: 'node',
                    style: {{
                        'content': 'data(label)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'shape': 'roundrectangle',
                        'background-color': '#4285f4',
                        'color': 'white',
                        'width': '180px',
                        'height': '80px',
                        'padding': '10px',
                        'font-size': '12px',
                        'font-weight': 'bold',
                        'border-width': 2,
                        'border-color': '#1a73e8'
                    }}
                }},
                {{
                    selector: 'edge',
                    style: {{
                        'curve-style': 'bezier',
                        'target-arrow-shape': 'triangle',
                        'target-arrow-color': '#666',
                        'line-color': '#666',
                        'width': 3,
                        'label': 'data(label)',
                        'font-size': '14px',
                        'font-weight': 'bold',
                        'color': '#666'
                    }}
                }}
            ]
        }});
        
        // Add hover effects
        cy.on('mouseover', 'node', function(e) {{
            e.target.style('background-color', '#34a853');
            e.target.style('border-color', '#137333');
        }});
        
        cy.on('mouseout', 'node', function(e) {{
            e.target.style('background-color', '#4285f4');
            e.target.style('border-color', '#1a73e8');
        }});
    </script>
</body>
</html>"""
        
        # Get absolute path for the file
        abs_path = os.path.abspath(filename)
        
        # Write the HTML file
        with open(filename, 'w') as f:
            f.write(html)
        
        # Try to open in browser with multiple fallback methods
        browser_opened = False
        file_url = f"file://{abs_path}"
        
        try:
            # Method 1: Try webbrowser.open_new_tab
            print(f"Trying webbrowser.open_new_tab({file_url})")
            webbrowser.open_new_tab(file_url)
            browser_opened = True
            print("✅ Method 1 succeeded!")
        except Exception as e1:
            print(f"❌ Method 1 failed: {e1}")
            try:
                # Method 2: Try webbrowser.open with new=2
                print(f"Trying webbrowser.open({file_url}, new=2)")
                webbrowser.open(file_url, new=2)
                browser_opened = True
                print("✅ Method 2 succeeded!")
            except Exception as e2:
                print(f"❌ Method 2 failed: {e2}")
                try:
                    # Method 3: Try webbrowser.open with new=1
                    print(f"Trying webbrowser.open({file_url}, new=1)")
                    webbrowser.open(file_url, new=1)
                    browser_opened = True
                    print("✅ Method 3 succeeded!")
                except Exception as e3:
                    print(f"❌ Method 3 failed: {e3}")
                    # Method 4: Try webbrowser.open without new parameter
                    try:
                        print(f"Trying webbrowser.open({file_url})")
                        webbrowser.open(file_url)
                        browser_opened = True
                        print("✅ Method 4 succeeded!")
                    except Exception as e4:
                        print(f"❌ Method 4 failed: {e4}")
        
        if browser_opened:
            return {
                "status": "success", 
                "message": f"✅ Successfully opened {filename} in browser\n📁 File location: {abs_path}"
            }
        else:
            return {
                "status": "warning", 
                "message": f"⚠️ HTML file created successfully but couldn't open browser automatically.\n📁 Please manually open: {abs_path}\n🔗 Or copy this URL: {file_url}"
            }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"❌ Failed to create visualization: {str(e)}\n💡 Check file permissions and disk space."
        }

def test_open_dag():
    """Test the open_dag_page function with sample tool calls."""
    
    print("🧪 Testing open_dag_page function")
    print("=" * 40)
    
    # Sample tool calls
    sample_tool_calls = [
        {
            "action": "iam.create_sa",
            "params": {"project_id": "test-project", "display_name": "Analytics SA"}
        },
        {
            "action": "pubsub.create_topic",
            "params": {"project_id": "test-project", "topic_id": "events"}
        },
        {
            "action": "dataflow.launch_flex_template",
            "params": {
                "project_id": "test-project",
                "region": "us-central1",
                "job_name": "stream-processor"
            }
        },
        {
            "action": "bigquery.create_dataset",
            "params": {"project_id": "test-project", "dataset_id": "analytics"}
        },
        {
            "action": "bigquery.create_table",
            "params": {
                "project_id": "test-project",
                "dataset_id": "analytics",
                "table_id": "events"
            }
        }
    ]
    
    print(f"📋 Testing with {len(sample_tool_calls)} tool calls:")
    for i, tool_call in enumerate(sample_tool_calls, 1):
        action = tool_call.get("action", "unknown")
        service = action.split('.')[0].replace('_', ' ').title()
        print(f"  {i}. {service} - {action}")
    
    print("\n🔄 Calling open_dag_page...")
    
    # Test the function
    result = open_dag_page(sample_tool_calls, "test_visualization.html")
    
    print(f"\n📊 Result:")
    print(f"  Status: {result.get('status', 'unknown')}")
    print(f"  Message: {result.get('message', 'No message')}")
    
    if result.get('status') == 'success':
        print("✅ Visualization created and opened successfully!")
    elif result.get('status') == 'warning':
        print("⚠️ Visualization created but browser couldn't be opened automatically.")
        print("   Check the file path in the message above.")
    else:
        print("❌ Failed to create visualization.")
        print("   Check the error message above.")
    
    return result

if __name__ == "__main__":
    print("🚀 Starting open_dag_page test")
    
    try:
        result = test_open_dag()
        print(f"\n🎉 Test completed with status: {result.get('status', 'unknown')}")
            
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc() 