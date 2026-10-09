from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from PIL import Image
import subprocess
import tempfile
import os
import base64
import time
import sys
import io
import socket
import zipfile

app = Flask(__name__)

# FIX: ChromeDriver ek baar download karo — service globally cache karo
CHROME_SERVICE = None

def get_chrome_service():
    global CHROME_SERVICE
    if CHROME_SERVICE is None:
        print("Downloading/caching ChromeDriver...")
        driver_path = ChromeDriverManager().install()
        CHROME_SERVICE = Service(driver_path)
        print(f"ChromeDriver cached: {driver_path}")
    return CHROME_SERVICE

def kill_port(port):
    try:
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True, text=True
        )
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.strip().split()
                if parts:
                    pid = parts[-1]
                    subprocess.run(
                        ['taskkill', '/F', '/PID', pid],
                        capture_output=True
                    )
                    print(f"Killed PID {pid} on port {port}")
                    time.sleep(1)
    except Exception as e:
        print(f"Port cleanup note: {e}")

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def wait_for_port(port, timeout=30):
    """Port available hone tak wait karo"""
    start = time.time()
    while time.time() - start < timeout:
        if is_port_in_use(port):
            print(f"Port {port} is ready!")
            return True
        time.sleep(1)
    print(f"Port {port} not ready after {timeout}s")
    return False

def save_files_to_dir(files, temp_dir):
    for f in files:
        filename = f.get('filename', 'unknown')
        content = f.get('content', '')
        is_zip = f.get('is_zip', False)
        is_binary = f.get('binary', False)
        ext = f.get('extension', '')

        file_path = os.path.join(temp_dir, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        if is_zip or ext == 'zip':
            try:
                zip_bytes = base64.b64decode(content)
                with open(file_path, 'wb') as fp:
                    fp.write(zip_bytes)
                print(f"Extracting ZIP: {filename}")
                with zipfile.ZipFile(file_path, 'r') as zf:
                    for member in zf.namelist():
                        if '__MACOSX' in member or member.startswith('.'):
                            continue
                        zf.extract(member, temp_dir)
                os.remove(file_path)
                print(f"ZIP extracted to: {temp_dir}")
            except Exception as e:
                print(f"ZIP extraction error: {e}")
        elif is_binary:
            try:
                binary_bytes = base64.b64decode(content)
                with open(file_path, 'wb') as fp:
                    fp.write(binary_bytes)
            except Exception as e:
                print(f"Binary file save error {filename}: {e}")
        else:
            try:
                with open(file_path, 'w', encoding='utf-8', errors='replace') as fp:
                    fp.write(content)
            except Exception as e:
                print(f"Text file save error {filename}: {e}")

def detect_entrypoint(temp_dir, hint_entrypoint):
    hint_path = os.path.join(temp_dir, hint_entrypoint)
    if os.path.exists(hint_path):
        return hint_path

    candidates = ['app.py', 'main.py', 'run.py', 'server.py', 'index.py']
    for candidate in candidates:
        direct = os.path.join(temp_dir, candidate)
        if os.path.exists(direct):
            return direct
        for root, dirs, fls in os.walk(temp_dir):
            dirs[:] = [d for d in dirs if d not in
                       ['node_modules', '.git', '__pycache__', '.venv', 'venv']]
            for fl in fls:
                if fl == candidate:
                    return os.path.join(root, fl)

    return hint_path

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'python': sys.version})

@app.route('/screenshot', methods=['POST'])
def take_screenshot():
    data = request.json
    files = data.get('files', [])
    entrypoint_hint = data.get('entrypoint', 'app.py')

    # Step 1: Port free karo
    if is_port_in_use(8502):
        print("Port 8502 busy — killing...")
        kill_port(8502)
        time.sleep(3)

    # Step 2: Files save karo
    temp_dir = tempfile.mkdtemp()
    save_files_to_dir(files, temp_dir)
    print(f"Files saved to: {temp_dir}")

    # Step 3: Entrypoint detect karo
    app_path = detect_entrypoint(temp_dir, entrypoint_hint)
    print(f"Entrypoint: {app_path}")

    if not os.path.exists(app_path):
        return jsonify({
            'screenshot': None,
            'screenshot_b64': None,
            'public_url': None,
            'success': False,
            'error': f'Entrypoint not found: {app_path}'
        }), 500

    # Step 4: Streamlit run karo
    proc = subprocess.Popen(
        [
            sys.executable, '-m', 'streamlit', 'run', app_path,
            '--server.port', '8502',
            '--server.headless', 'true',
            '--server.address', '127.0.0.1'
        ],
        env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # FIX: Port ready hone tak wait karo — fixed time nahi
    print("Waiting for Streamlit to start on port 8502...")
    port_ready = wait_for_port(8502, timeout=40)

    if not port_ready:
        proc.terminate()
        return jsonify({
            'screenshot': None,
            'screenshot_b64': None,
            'public_url': None,
            'success': False,
            'error': 'Streamlit did not start in time'
        }), 500

    # Extra wait for UI render
    time.sleep(5)

    # Step 5: Screenshot lo
    screenshot_b64 = None
    error_msg = None
    driver = None

    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1280,1200')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36'
        )

        # FIX: Cached ChromeDriver use karo
        service = get_chrome_service()
        driver = webdriver.Chrome(service=service, options=chrome_options)

        target_url = "http://127.0.0.1:8502"
        print(f"Opening: {target_url}")
        driver.get(target_url)
        time.sleep(5)

        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '[data-testid="stAppViewContainer"]')
                )
            )
            print("Streamlit container found!")
            time.sleep(5)
        except Exception as wait_err:
            print(f"Wait failed: {wait_err} — continuing anyway")
            time.sleep(5)

        screenshot_bytes = driver.get_screenshot_as_png()
        print("Raw screenshot taken")

        img = Image.open(io.BytesIO(screenshot_bytes))
        print(f"Original size: {img.size}")
        width, height = img.size

        img_cropped = img.crop((0, 76, width, height))
        final_width = 1200
        ratio = final_width / img_cropped.width
        final_height = int(img_cropped.height * ratio)
        img_resized = img_cropped.resize((final_width, final_height), Image.LANCZOS)

        output = io.BytesIO()
        img_resized.save(output, format='PNG', optimize=True)
        screenshot_b64 = base64.b64encode(output.getvalue()).decode('utf-8')
        print(f"Screenshot done! Final size: {img_resized.size}")

    except Exception as e:
        error_msg = str(e)
        print(f"Screenshot error: {e}")

    finally:
        try:
            if driver:
                driver.quit()
        except Exception:
            pass

    # Cleanup
    try:
        proc.terminate()
        proc.wait(timeout=5)
        print("Cleanup done.")
    except Exception as e:
        print(f"Cleanup error: {e}")

    try:
        kill_port(8502)
    except Exception:
        pass

    return jsonify({
        'screenshot': screenshot_b64,
        'screenshot_b64': screenshot_b64,
        'public_url': 'http://127.0.0.1:8502',
        'success': screenshot_b64 is not None,
        'error': error_msg
    })


if __name__ == '__main__':
    # FIX: App start hone pe ChromeDriver cache karo
    print(f"Python: {sys.executable}")
    print("Pre-loading ChromeDriver...")
    try:
        get_chrome_service()
        print("ChromeDriver ready!")
    except Exception as e:
        print(f"ChromeDriver pre-load warning: {e}")

    print("Screenshot service starting on http://0.0.0.0:9000")
    app.run(host='0.0.0.0', port=9000, debug=False)