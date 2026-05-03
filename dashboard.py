"""
Product Studio — local order management dashboard.
Run: python dashboard.py
Open: http://localhost:5000
"""

import os
import json
import uuid
import threading
from datetime import datetime
from flask import Flask, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from pipeline import run_full_pipeline
from templates import PRODUCT_TEMPLATES
from detect_product import detect_product_type

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

# DATA_DIR: set to /data on Railway (persistent volume), defaults to local dir
DATA_DIR = os.getenv("DATA_DIR", ".")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
PLAYBOOK_FILE = "playbook.json"  # always local — it's source-controlled
UPLOAD_DIR = os.path.join(DATA_DIR, "inputs")

PRODUCTS = {
    "soap":    {"label": "Soap",    "icon": "🧼"},
    "candle":  {"label": "Candle",  "icon": "🕯️"},
    "staging": {"label": "Staging", "icon": "🏠"},
}

TIERS = {
    "basic":    {"template_count": 1, "variations": 4,  "label": "Basic",    "desc": "4 images · 1 scene"},
    "standard": {"template_count": 2, "variations": 4,  "label": "Standard", "desc": "8 images · 2 scenes"},
    "premium":  {"template_count": 8, "variations": 3,  "label": "Premium",  "desc": "24 images · 8 scenes"},
}

_lock = threading.Lock()


def load_orders():
    if not os.path.exists(ORDERS_FILE):
        return []
    with open(ORDERS_FILE) as f:
        return json.load(f)


def save_orders(orders):
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=2)


def update_order(order_id, **kwargs):
    with _lock:
        orders = load_orders()
        for o in orders:
            if o["id"] == order_id:
                o.update(kwargs)
        save_orders(orders)


def load_playbook():
    if not os.path.exists(PLAYBOOK_FILE):
        return {"gigs": []}
    with open(PLAYBOOK_FILE) as f:
        return json.load(f)


def save_playbook(pb):
    with open(PLAYBOOK_FILE, "w") as f:
        json.dump(pb, f, indent=2)


def run_order_bg(order_id, reference_image, product, tier, buyer_name):
    tier_config = TIERS[tier]
    templates = PRODUCT_TEMPLATES[product][: tier_config["template_count"]]
    output_root = os.path.join(DATA_DIR, "output", product, order_id)
    os.makedirs(output_root, exist_ok=True)

    try:
        update_order(order_id, status="running")
        result = run_full_pipeline(
            reference_image=reference_image,
            output_root=output_root,
            variations_per_template=tier_config["variations"],
            templates=templates,
            product=product,
        )
        image_dir = result["output_dir"]
        zip_path = image_dir + ".zip"

        images = []
        if os.path.isdir(image_dir):
            for f in sorted(os.listdir(image_dir)):
                if f.endswith(".jpg"):
                    images.append(os.path.join(image_dir, f).replace("\\", "/"))

        update_order(order_id, status="done", zip_path=zip_path, images=images)
    except Exception as e:
        update_order(order_id, status="failed", error=str(e))


# --- Routes ---

@app.route("/")
def index():
    return DASHBOARD_HTML


@app.route("/files/<path:filename>")
def serve_image(filename):
    return send_from_directory(".", filename)


@app.route("/orders", methods=["GET"])
def list_orders():
    product = request.args.get("product")
    orders = load_orders()
    if product and product != "all":
        orders = [o for o in orders if o["product"] == product]
    return jsonify(orders)


@app.route("/orders", methods=["POST"])
def create_order():
    file = request.files.get("photo")
    product = request.form.get("product", "soap")
    tier = request.form.get("tier", "basic")
    buyer_name = request.form.get("buyer_name", "").strip() or "Unknown Buyer"

    if not file or file.filename == "":
        return jsonify({"error": "No photo uploaded"}), 400
    if product not in PRODUCT_TEMPLATES:
        return jsonify({"error": "Invalid product"}), 400
    if tier not in TIERS:
        return jsonify({"error": "Invalid tier"}), 400

    order_id = str(uuid.uuid4())[:8]
    filename = f"{order_id}_{secure_filename(file.filename)}"
    photo_path = os.path.join(UPLOAD_DIR, filename)
    file.save(photo_path)

    order = {
        "id": order_id,
        "buyer_name": buyer_name,
        "product": product,
        "tier": tier,
        "photo_path": photo_path,
        "status": "queued",
        "zip_path": None,
        "images": [],
        "error": None,
        "created_at": datetime.now().strftime("%b %d, %Y %I:%M %p"),
    }

    with _lock:
        orders = load_orders()
        orders.insert(0, order)
        save_orders(orders)

    thread = threading.Thread(
        target=run_order_bg,
        args=(order_id, photo_path, product, tier, buyer_name),
        daemon=True,
    )
    thread.start()
    return jsonify(order), 201


@app.route("/orders/<order_id>")
def get_order(order_id):
    orders = load_orders()
    order = next((o for o in orders if o["id"] == order_id), None)
    if not order:
        return jsonify({"error": "Not found"}), 404
    return jsonify(order)


@app.route("/orders/<order_id>/download")
def download_order(order_id):
    orders = load_orders()
    order = next((o for o in orders if o["id"] == order_id), None)
    if not order or not order.get("zip_path"):
        return jsonify({"error": "Zip not ready"}), 404
    zip_path = order["zip_path"]
    if not os.path.exists(zip_path):
        return jsonify({"error": "Zip file missing"}), 404
    name = f"{order['buyer_name'].replace(' ', '_')}_{order['product']}_{order['tier']}.zip"
    return send_file(zip_path, as_attachment=True, download_name=name)


@app.route("/playbook")
def get_playbook():
    return jsonify(load_playbook())


@app.route("/playbook/<gig_id>/steps/<step_id>", methods=["POST"])
def toggle_step(gig_id, step_id):
    done = request.json.get("done", False)
    pb = load_playbook()
    for gig in pb["gigs"]:
        if gig["id"] == gig_id:
            for step in gig["steps"]:
                if step["id"] == step_id:
                    step["done"] = done
    save_playbook(pb)
    return jsonify({"ok": True})


@app.route("/detect", methods=["POST"])
def detect_photo():
    """Detect product type from a photo. Called by the drop zone before order creation."""
    file = request.files.get("photo")
    if not file:
        return jsonify({"product": "unknown"})

    ext = os.path.splitext(secure_filename(file.filename))[1] or ".jpg"
    tmp_path = os.path.join(UPLOAD_DIR, f"tmp_{uuid.uuid4().hex[:8]}{ext}")
    try:
        file.save(tmp_path)
        result = detect_product_type(tmp_path)
        if result not in PRODUCT_TEMPLATES:
            result = "unknown"
    except Exception as e:
        print(f"[detect] Error: {e}")
        result = "unknown"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return jsonify({"product": result})


# --- HTML ---

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Product Studio</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0d0d0d; color: #e0e0e0; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }

header { background: #161616; border-bottom: 1px solid #252525; padding: 0 20px; height: 52px; display: flex; align-items: center; justify-content: space-between; flex-shrink: 0; }
.header-left { display: flex; align-items: center; gap: 10px; }
header h1 { font-size: 15px; font-weight: 700; color: #fff; letter-spacing: -0.3px; }
.header-tagline { font-size: 11px; color: #333; border-left: 1px solid #252525; padding-left: 10px; }
.tabs { display: flex; gap: 2px; }
.tab { padding: 6px 14px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; color: #555; background: none; border: none; }
.tab.active { background: #252525; color: #ddd; }

.workspace { display: flex; flex: 1; overflow: hidden; }

.sidebar { width: 190px; background: #111; border-right: 1px solid #1e1e1e; display: flex; flex-direction: column; padding: 12px 8px; gap: 2px; flex-shrink: 0; overflow-y: auto; }
.sidebar-label { font-size: 10px; font-weight: 700; color: #333; text-transform: uppercase; letter-spacing: 0.1em; padding: 8px 8px 4px; }
.nav-item { display: flex; align-items: center; justify-content: space-between; padding: 8px 10px; border-radius: 7px; cursor: pointer; font-size: 13px; color: #666; transition: background 0.15s, color 0.15s; }
.nav-item:hover { background: #1a1a1a; color: #aaa; }
.nav-item.active { background: #1e1a2e; color: #c4a8ff; }
.nav-count { background: #222; color: #555; font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 10px; }
.nav-item.active .nav-count { background: #2e2545; color: #9b7fe8; }
.sidebar-gap { flex: 1; }
.new-btn { margin: 8px; background: #6d4fc7; color: #fff; border: none; padding: 10px; border-radius: 8px; font-size: 13px; font-weight: 700; cursor: pointer; text-align: center; }
.new-btn:hover { background: #5e42b0; }

.content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

.drop-header { border-bottom: 1px solid #1a1a1a; padding: 16px 24px; flex-shrink: 0; }
.drop-zone { border: 2px dashed #252525; border-radius: 10px; padding: 18px; text-align: center; cursor: pointer; transition: border-color 0.2s, background 0.2s; }
.drop-zone.drag-over { border-color: #6d4fc7; background: #17122a; }
.drop-zone p { font-size: 13px; color: #444; }
.drop-zone .hint { font-size: 11px; color: #333; margin-top: 4px; }

.orders-scroll { flex: 1; overflow-y: auto; padding: 16px 24px; display: flex; flex-direction: column; gap: 12px; }

.order-card { background: #161616; border: 1px solid #1e1e1e; border-radius: 12px; overflow: hidden; }
.order-card-header { padding: 14px 16px; display: flex; align-items: center; gap: 12px; }
.order-card-info { flex: 1; }
.order-name { font-size: 14px; font-weight: 700; color: #fff; }
.order-meta { font-size: 12px; color: #444; margin-top: 2px; }
.badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; }
.badge-queued  { background: #1e1e1e; color: #555; }
.badge-running { background: #251d00; color: #e8a020; }
.badge-done    { background: #0d200d; color: #4caf50; }
.badge-failed  { background: #200d0d; color: #e05252; }

.image-grid { padding: 0 16px 14px; display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 6px; }
.image-thumb { width: 100%; aspect-ratio: 1; object-fit: cover; border-radius: 6px; cursor: pointer; transition: transform 0.15s, opacity 0.15s; background: #1e1e1e; }
.image-thumb:hover { transform: scale(1.03); opacity: 0.9; }
.order-actions { padding: 0 16px 14px; display: flex; gap: 8px; align-items: center; }
.dl-btn { background: #0d200d; color: #4caf50; border: 1px solid #1a3a1a; padding: 7px 14px; border-radius: 7px; font-size: 12px; font-weight: 700; cursor: pointer; text-decoration: none; }
.dl-btn:hover { background: #102810; }
.progress-text { font-size: 12px; color: #444; }

.spin { display: inline-block; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.empty-state { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #2a2a2a; gap: 10px; }
.empty-state .big-icon { font-size: 48px; }
.empty-state p { font-size: 14px; }

#lightbox { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.92); z-index: 1000; align-items: center; justify-content: center; cursor: zoom-out; }
#lightbox.open { display: flex; }
#lightbox img { max-width: 90vw; max-height: 90vh; border-radius: 8px; object-fit: contain; box-shadow: 0 0 60px rgba(0,0,0,0.8); }
#lightbox-close { position: absolute; top: 20px; right: 24px; color: #888; font-size: 28px; cursor: pointer; background: none; border: none; }

#quick-panel { display: none; background: #161616; border-top: 1px solid #252525; padding: 16px 24px; flex-shrink: 0; }
#quick-panel.open { display: block; }
.quick-form { display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap; }
.qf-field { display: flex; flex-direction: column; gap: 5px; }
.qf-label { font-size: 10px; font-weight: 700; color: #444; text-transform: uppercase; letter-spacing: 0.06em; display: flex; align-items: center; gap: 6px; }
.qf-input { background: #111; border: 1px solid #252525; border-radius: 7px; padding: 8px 12px; color: #fff; font-size: 13px; min-width: 160px; }
.qf-input:focus { outline: none; border-color: #6d4fc7; }
.qf-select { background: #111; border: 1px solid #252525; border-radius: 7px; padding: 8px 28px 8px 12px; color: #fff; font-size: 13px; min-width: 140px; cursor: pointer; appearance: none; -webkit-appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%23555'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 10px center; }
.qf-select:focus { outline: none; border-color: #6d4fc7; }
.detect-badge { font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 8px; letter-spacing: 0.04em; }
.detect-badge.detecting { color: #555; background: #1e1e1e; animation: pulse 1.2s ease-in-out infinite; }
.detect-badge.detected { color: #9b7fe8; background: #1e1a2e; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
.tier-pills { display: flex; gap: 6px; }
.tier-pill { padding: 7px 12px; border-radius: 7px; border: 1px solid #252525; background: #111; color: #666; font-size: 12px; font-weight: 700; cursor: pointer; }
.tier-pill.selected { border-color: #6d4fc7; background: #17122a; color: #c4a8ff; }
.run-btn { background: #6d4fc7; color: #fff; border: none; padding: 8px 18px; border-radius: 7px; font-size: 13px; font-weight: 700; cursor: pointer; height: 36px; }
.run-btn:hover { background: #5e42b0; }
.cancel-btn { background: none; border: none; color: #444; font-size: 13px; cursor: pointer; padding: 8px; }
.file-chip { background: #1a1a2e; border: 1px solid #2a2a4a; color: #9b7fe8; padding: 7px 12px; border-radius: 7px; font-size: 12px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.playbook-wrap { flex: 1; overflow-y: auto; padding: 24px; }
.playbook-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; }
.gig-card { background: #161616; border: 1px solid #1e1e1e; border-radius: 12px; overflow: hidden; }
.gig-head { padding: 14px 16px 10px; border-bottom: 1px solid #1a1a1a; }
.gig-title-row { display: flex; justify-content: space-between; align-items: flex-start; }
.gig-name { font-size: 13px; font-weight: 700; color: #fff; }
.gig-sub { font-size: 11px; color: #444; margin-top: 3px; }
.gig-status { font-size: 10px; font-weight: 700; white-space: nowrap; }
.gig-pills { display: flex; gap: 6px; margin-top: 8px; }
.pill { font-size: 10px; padding: 2px 7px; border-radius: 10px; font-weight: 700; }
.pill-price { background: #0d200d; color: #4caf50; }
.pill-high { background: #0d1520; color: #5b8dd9; }
.pill-med { background: #201500; color: #d4a843; }
.gig-prog { padding: 8px 16px; border-bottom: 1px solid #141414; display: flex; align-items: center; gap: 8px; }
.prog-bar { flex: 1; height: 3px; background: #1e1e1e; border-radius: 2px; overflow: hidden; }
.prog-fill { height: 100%; background: #6d4fc7; border-radius: 2px; transition: width 0.3s; }
.prog-label { font-size: 10px; color: #444; }
.gig-steps { padding: 10px 16px; display: flex; flex-direction: column; gap: 7px; }
.step { display: flex; align-items: flex-start; gap: 8px; cursor: pointer; }
.step input { margin-top: 2px; accent-color: #6d4fc7; flex-shrink: 0; cursor: pointer; }
.step-text { font-size: 12px; color: #888; line-height: 1.4; }
.step.done .step-text { color: #333; text-decoration: line-through; }

.view { display: none; flex: 1; overflow: hidden; flex-direction: column; }
.view.active { display: flex; }
</style>
</head>
<body>

<header>
  <div class="header-left">
    <h1>Product Studio</h1>
    <span class="header-tagline">AI photo generation &middot; Fiverr fulfillment</span>
  </div>
  <div class="tabs">
    <button class="tab active" onclick="showTab('orders',this)">Orders</button>
    <button class="tab" onclick="showTab('playbook',this)">Playbook</button>
  </div>
</header>

<div class="view active" id="view-orders">
  <div class="workspace">

    <div class="sidebar">
      <div class="sidebar-label">Business</div>
      <div class="nav-item active" data-product="all" onclick="selectSection('all',this)">
        <span>All Orders</span>
        <span class="nav-count" id="count-all">0</span>
      </div>
      <div class="nav-item" data-product="soap" onclick="selectSection('soap',this)">
        <span>Soap</span>
        <span class="nav-count" id="count-soap">0</span>
      </div>
      <div class="nav-item" data-product="candle" onclick="selectSection('candle',this)">
        <span>Candle</span>
        <span class="nav-count" id="count-candle">0</span>
      </div>
      <div class="nav-item" data-product="staging" onclick="selectSection('staging',this)">
        <span>Staging</span>
        <span class="nav-count" id="count-staging">0</span>
      </div>
      <div class="sidebar-gap"></div>
      <button class="new-btn" onclick="openGlobalNew()">+ New Order</button>
    </div>

    <div class="content">

      <div class="drop-header">
        <div class="drop-zone" id="section-drop-zone">
          <p>Drop any buyer photo here &mdash; AI detects the product type automatically</p>
          <p class="hint">Soap, candle, or room staging &mdash; or click to browse files</p>
        </div>
      </div>

      <div class="orders-scroll" id="orders-list"></div>

      <div id="quick-panel">
        <div class="quick-form">
          <div class="qf-field">
            <div class="qf-label">File</div>
            <div class="file-chip" id="qp-filename">&mdash;</div>
          </div>
          <div class="qf-field">
            <div class="qf-label">
              Product
              <span class="detect-badge" id="detect-badge"></span>
            </div>
            <select class="qf-select" id="qp-product">
              <option value="soap">Soap</option>
              <option value="candle">Candle</option>
              <option value="staging">Staging</option>
            </select>
          </div>
          <div class="qf-field">
            <div class="qf-label">Buyer Name</div>
            <input class="qf-input" type="text" id="qp-buyer" placeholder="e.g. Sarah's Shop">
          </div>
          <div class="qf-field">
            <div class="qf-label">Tier</div>
            <div class="tier-pills">
              <div class="tier-pill selected" data-tier="basic" onclick="selectTier(this)">Basic</div>
              <div class="tier-pill" data-tier="standard" onclick="selectTier(this)">Standard</div>
              <div class="tier-pill" data-tier="premium" onclick="selectTier(this)">Premium</div>
            </div>
          </div>
          <button class="run-btn" onclick="submitQuick()">Run Pipeline</button>
          <button class="cancel-btn" onclick="cancelQuick()">&#10005;</button>
        </div>
      </div>

    </div>
  </div>
</div>

<div class="view" id="view-playbook">
  <div class="playbook-wrap">
    <div class="playbook-grid" id="playbook-grid">
      <p style="color:#333">Loading...</p>
    </div>
  </div>
</div>

<div id="lightbox" onclick="closeLightbox()">
  <button id="lightbox-close" onclick="closeLightbox()">&#10005;</button>
  <img id="lightbox-img" src="" alt="">
</div>

<script>
let currentProduct = 'all';
let pendingFile = null;
let pendingTier = 'basic';
let pollers = {};
const allOrders = {};

function showTab(tab, btn) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('view-' + tab).classList.add('active');
  btn.classList.add('active');
  if (tab === 'playbook') loadPlaybook();
}

function selectSection(product, el) {
  currentProduct = product;
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  el.classList.add('active');
  renderOrders();
}

const dropZone = document.getElementById('section-drop-zone');
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {
  e.preventDefault(); dropZone.classList.remove('drag-over');
  const f = e.dataTransfer.files[0];
  if (f) openQuickPanel(f);
});
dropZone.addEventListener('click', () => {
  const inp = document.createElement('input');
  inp.type = 'file'; inp.accept = 'image/*';
  inp.onchange = () => { if (inp.files[0]) openQuickPanel(inp.files[0]); };
  inp.click();
});

function openGlobalNew() {
  const inp = document.createElement('input');
  inp.type = 'file'; inp.accept = 'image/*';
  inp.onchange = () => { if (inp.files[0]) openQuickPanel(inp.files[0]); };
  inp.click();
}

function openQuickPanel(file) {
  pendingFile = file;
  document.getElementById('qp-filename').textContent = file.name;
  document.getElementById('qp-buyer').value = '';
  document.getElementById('quick-panel').classList.add('open');

  const sel = document.getElementById('qp-product');
  if (currentProduct !== 'all') sel.value = currentProduct;

  const badge = document.getElementById('detect-badge');
  badge.className = 'detect-badge detecting';
  badge.textContent = 'detecting...';

  const fd = new FormData();
  fd.append('photo', file);
  fetch('/detect', { method: 'POST', body: fd })
    .then(r => r.json())
    .then(({ product }) => {
      if (product && product !== 'unknown') {
        sel.value = product;
        badge.className = 'detect-badge detected';
        badge.textContent = 'auto-detected';
      } else {
        badge.className = '';
        badge.textContent = '';
      }
    })
    .catch(() => { badge.className = ''; badge.textContent = ''; });

  document.getElementById('qp-buyer').focus();
}

function cancelQuick() {
  pendingFile = null;
  document.getElementById('quick-panel').classList.remove('open');
  document.getElementById('detect-badge').className = '';
  document.getElementById('detect-badge').textContent = '';
}

function selectTier(el) {
  document.querySelectorAll('.tier-pill').forEach(p => p.classList.remove('selected'));
  el.classList.add('selected');
  pendingTier = el.dataset.tier;
}

async function submitQuick() {
  if (!pendingFile) return;
  const product = document.getElementById('qp-product').value;
  const buyer = document.getElementById('qp-buyer').value.trim() || 'Unknown Buyer';

  const fd = new FormData();
  fd.append('photo', pendingFile);
  fd.append('buyer_name', buyer);
  fd.append('product', product);
  fd.append('tier', pendingTier);

  cancelQuick();
  const res = await fetch('/orders', { method: 'POST', body: fd });
  const order = await res.json();
  allOrders[order.id] = order;
  renderOrders();
  startPoller(order.id);
}

async function loadOrders() {
  const all = await (await fetch('/orders')).json();
  all.forEach(o => allOrders[o.id] = o);
  updateCounts();
  renderOrders();
  all.filter(o => o.status === 'running' || o.status === 'queued').forEach(o => startPoller(o.id));
}

function updateCounts() {
  const all = Object.values(allOrders);
  document.getElementById('count-all').textContent = all.length;
  ['soap','candle','staging'].forEach(p => {
    const el = document.getElementById('count-' + p);
    if (el) el.textContent = all.filter(o => o.product === p).length;
  });
}

function renderOrders() {
  const list = document.getElementById('orders-list');
  let orders = Object.values(allOrders);
  if (currentProduct !== 'all') orders = orders.filter(o => o.product === currentProduct);
  orders.sort((a,b) => b.created_at < a.created_at ? -1 : 1);

  if (!orders.length) {
    list.innerHTML = '<div class="empty-state"><div class="big-icon">&#128219;</div><p>No orders yet &mdash; drop a photo above to get started</p></div>';
    return;
  }
  list.innerHTML = orders.map(renderCard).join('');
}

function renderCard(o) {
  const prodLabel = {soap:'Soap',candle:'Candle',staging:'Staging'}[o.product] || o.product;
  const tierLabel = {basic:'Basic',standard:'Standard',premium:'Premium'}[o.tier] || o.tier;
  const badgeMap = {
    queued:  '<span class="badge badge-queued">Queued</span>',
    running: '<span class="badge badge-running"><span class="spin">&#8987;</span> Running&hellip;</span>',
    done:    '<span class="badge badge-done">&#10003; Done</span>',
    failed:  '<span class="badge badge-failed">&#10007; Failed</span>',
  };

  let body = '';
  if (o.status === 'done' && o.images && o.images.length) {
    const thumbs = o.images.map(p =>
      '<img class="image-thumb" src="/files/' + p + '" loading="lazy" onclick="openLightbox(\\'/files/' + p + '\\')" title="Click to view full size">'
    ).join('');
    body = '<div class="image-grid">' + thumbs + '</div>' +
           '<div class="order-actions">' +
           '<a class="dl-btn" href="/orders/' + o.id + '/download">&#8659; Download ZIP</a>' +
           '<span class="progress-text">' + o.images.length + ' photos ready to send</span>' +
           '</div>';
  } else if (o.status === 'running' || o.status === 'queued') {
    body = '<div class="order-actions"><span class="progress-text">Pipeline running &mdash; photos will appear here when done</span></div>';
  } else if (o.status === 'failed') {
    body = '<div class="order-actions"><span class="progress-text" style="color:#e05252">Error: ' + (o.error || 'Unknown error') + '</span></div>';
  }

  return '<div class="order-card" id="card-' + o.id + '">' +
    '<div class="order-card-header">' +
    '<div class="order-card-info">' +
    '<div class="order-name">' + o.buyer_name + '</div>' +
    '<div class="order-meta">' + prodLabel + ' &middot; ' + tierLabel + ' &middot; ' + o.created_at + '</div>' +
    '</div>' +
    (badgeMap[o.status] || '') +
    '</div>' +
    body +
    '</div>';
}

function startPoller(id) {
  if (pollers[id]) return;
  pollers[id] = setInterval(async () => {
    const o = await (await fetch('/orders/' + id)).json();
    allOrders[id] = o;
    const card = document.getElementById('card-' + id);
    if (card) { const t = document.createElement('div'); t.innerHTML = renderCard(o); card.replaceWith(t.firstElementChild); }
    updateCounts();
    if (o.status === 'done' || o.status === 'failed') { clearInterval(pollers[id]); delete pollers[id]; }
  }, 3000);
}

function openLightbox(src) {
  document.getElementById('lightbox-img').src = src;
  document.getElementById('lightbox').classList.add('open');
}
function closeLightbox() { document.getElementById('lightbox').classList.remove('open'); }
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeLightbox(); });

async function loadPlaybook() {
  const { gigs } = await (await fetch('/playbook')).json();
  const grid = document.getElementById('playbook-grid');
  grid.innerHTML = gigs.map((g,i) => renderGig(g,i)).join('');
}

function renderGig(g, i) {
  const done = g.steps.filter(s=>s.done).length, total = g.steps.length;
  const pct = Math.round(done/total*100);
  const color = done===total?'#4caf50':done>0?'#e8a020':'#333';
  const status = done===total?'Complete':done>0?'In Progress':'Not Started';
  const autoPill = g.automation.includes('high')
    ? '<span class="pill pill-high">Auto: ' + g.automation + '</span>'
    : '<span class="pill pill-med">Auto: ' + g.automation + '</span>';
  const steps = g.steps.map(s =>
    '<label class="step ' + (s.done?'done':'') + '" id="gs-' + g.id + '-' + s.id + '">' +
    '<input type="checkbox" ' + (s.done?'checked':'') + ' onchange="toggleStep(\\'' + g.id + '\\',\\'' + s.id + '\\',this.checked)">' +
    '<span class="step-text">' + s.text + '</span></label>'
  ).join('');
  return '<div class="gig-card">' +
    '<div class="gig-head"><div class="gig-title-row">' +
    '<div><div class="gig-name">' + (i+1) + '. ' + g.name + '</div><div class="gig-sub">' + g.subtitle + '</div></div>' +
    '<span class="gig-status" style="color:' + color + '">' + status + '</span>' +
    '</div><div class="gig-pills"><span class="pill pill-price">' + g.price_range + '</span>' + autoPill + '</div></div>' +
    '<div class="gig-prog"><div class="prog-bar"><div class="prog-fill" id="pb-' + g.id + '" style="width:' + pct + '%"></div></div>' +
    '<span class="prog-label" id="pl-' + g.id + '">' + done + '/' + total + '</span></div>' +
    '<div class="gig-steps">' + steps + '</div></div>';
}

async function toggleStep(gid, sid, done) {
  await fetch('/playbook/' + gid + '/steps/' + sid, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({done})});
  const lbl = document.getElementById('gs-' + gid + '-' + sid);
  if (lbl) lbl.className = 'step ' + (done?'done':'');
  const {gigs} = await (await fetch('/playbook')).json();
  const gig = gigs.find(g => g.id === gid);
  if (gig) {
    const d = gig.steps.filter(s=>s.done).length, t = gig.steps.length;
    const bar = document.getElementById('pb-' + gid), lbl2 = document.getElementById('pl-' + gid);
    if (bar) bar.style.width = Math.round(d/t*100) + '%';
    if (lbl2) lbl2.textContent = d + '/' + t;
  }
}

loadOrders();
</script>
</body>
</html>"""


if __name__ == "__main__":
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "output"), exist_ok=True)
    port = int(os.getenv("PORT", 5000))
    print("\n=== Product Studio ===")
    print(f"Open in browser: http://localhost:{port}\n")
    app.run(debug=False, host="0.0.0.0", port=port, threaded=True)
