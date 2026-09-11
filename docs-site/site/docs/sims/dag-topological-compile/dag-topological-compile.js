// DAG Topological Compile — Step-through Animation
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:70%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">dag.collect("enriched") — Step Through</div>
            <div id="sidebar" style="position:absolute;top:10px;right:10px;width:26%;background:rgba(255,255,255,0.95);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:8px;font-size:14px;">Compile Order</div>
                <div id="order-display" style="margin-bottom:12px;line-height:1.8;"></div>
                <div style="font-weight:bold;margin-bottom:8px;font-size:14px;">Cache State</div>
                <div id="cache-display" style="margin-bottom:12px;font-family:monospace;font-size:11px;line-height:1.6;"></div>
                <div id="step-label" style="font-weight:bold;margin-bottom:8px;color:#E67E22;font-size:13px;"></div>
                <div style="display:flex;gap:8px;">
                    <button id="btn-back" style="flex:1;padding:6px 12px;border:none;border-radius:4px;background:#95A5A6;color:#fff;cursor:pointer;font-size:13px;" disabled>&#9664; Back</button>
                    <button id="btn-fwd" style="flex:1;padding:6px 12px;border:none;border-radius:4px;background:#E67E22;color:#fff;cursor:pointer;font-size:13px;">Forward &#9654;</button>
                </div>
            </div>
        </div>
    `;

    // Topological order for collect("enriched"): customers -> orders -> enriched
    var steps = [
        { id: null, label: 'Initial state — cache empty', cache: {} },
        { id: 'customers', label: 'Compile "customers" — no dependencies, load from source',
          cache: { customers: 'DataFrame(3 rows)' } },
        { id: 'orders', label: 'Compile "orders" — depends on customers (cached), load from source',
          cache: { customers: 'DataFrame(3 rows)', orders: 'DataFrame(5 rows)' } },
        { id: 'enriched', label: 'Compile "enriched" — join customers + orders from cache',
          cache: { customers: 'DataFrame(3 rows)', orders: 'DataFrame(5 rows)', enriched: 'DataFrame(5 rows)' } },
        { id: null, label: 'Done! Return cached enriched DataFrame',
          cache: { customers: 'DataFrame(3 rows)', orders: 'DataFrame(5 rows)', enriched: 'DataFrame(5 rows)' } }
    ];

    var currentStep = 0;
    var compileOrder = ['customers', 'orders', 'enriched'];

    // Node positions: left-to-right flow
    var nodeX = { customers: 150, orders: 350, enriched: 550 };
    var nodeY = 260;

    function nc(bg, border) {
        return { background: bg, border: border,
            highlight: { background: bg, border: border },
            hover: { background: bg, border: border } };
    }

    var defaultColor = nc('#D35400', '#922B00');
    var activeColor = nc('#F1C40F', '#D4AC0F');
    var doneColor = nc('#27AE60', '#1E8449');

    var nodes = new vis.DataSet([
        { id: 'customers', label: 'customers', x: nodeX.customers, y: nodeY, fixed: true,
          shape: 'box', color: defaultColor, font: { color: '#fff', size: 14 }, borderWidth: 2 },
        { id: 'orders', label: 'orders', x: nodeX.orders, y: nodeY, fixed: true,
          shape: 'box', color: defaultColor, font: { color: '#fff', size: 14 }, borderWidth: 2 },
        { id: 'enriched', label: 'enriched', x: nodeX.enriched, y: nodeY, fixed: true,
          shape: 'box', color: defaultColor, font: { color: '#fff', size: 14 }, borderWidth: 2 }
    ]);

    var edges = new vis.DataSet([
        { from: 'customers', to: 'orders', arrows: 'to', color: { color: '#D35400' }, width: 2 },
        { from: 'customers', to: 'enriched', arrows: 'to', color: { color: '#D35400' }, width: 2,
          smooth: { type: 'curvedCW', roundness: 0.3 } },
        { from: 'orders', to: 'enriched', arrows: 'to', color: { color: '#D35400' }, width: 2 }
    ]);

    var container = document.getElementById('network');
    var network = new vis.Network(container, { nodes: nodes, edges: edges }, {
        interaction: { zoomView: false, dragView: false, dragNodes: false, hover: true },
        physics: { enabled: false },
        layout: { improvedLayout: false }
    });

    var btnBack = document.getElementById('btn-back');
    var btnFwd = document.getElementById('btn-fwd');

    function render() {
        var step = steps[currentStep];

        // Update node colors
        compileOrder.forEach(function(nid, idx) {
            var color;
            if (step.id === nid) {
                color = activeColor; // currently being compiled
            } else if (step.cache[nid]) {
                color = doneColor; // already cached
            } else {
                color = defaultColor; // not yet compiled
            }
            nodes.update({ id: nid, color: color,
                font: { color: '#fff', size: 14 } });
        });

        // Update compile order display
        var orderHtml = compileOrder.map(function(nid, idx) {
            var marker = '';
            if (step.id === nid) marker = ' style="font-weight:bold;color:#F1C40F;"';
            else if (step.cache[nid]) marker = ' style="color:#27AE60;"';
            else marker = ' style="color:#999;"';
            var icon = step.cache[nid] ? '&#10003;' : (step.id === nid ? '&#9654;' : '&#9675;');
            return '<div' + marker + '>' + icon + ' ' + (idx + 1) + '. ' + nid + '</div>';
        }).join('');
        document.getElementById('order-display').innerHTML = orderHtml;

        // Update cache display
        var cacheEntries = Object.keys(step.cache);
        var cacheHtml = cacheEntries.length === 0
            ? '<div style="color:#999;">{ }</div>'
            : '{<br>' + cacheEntries.map(function(k) {
                return '&nbsp;&nbsp;"' + k + '": ' + step.cache[k];
            }).join(',<br>') + '<br>}';
        document.getElementById('cache-display').innerHTML = cacheHtml;

        // Step label
        document.getElementById('step-label').textContent =
            'Step ' + currentStep + '/' + (steps.length - 1) + ': ' + step.label;

        // Button states
        btnBack.disabled = currentStep === 0;
        btnFwd.disabled = currentStep === steps.length - 1;
        btnBack.style.background = currentStep === 0 ? '#BDC3C7' : '#95A5A6';
        btnFwd.style.background = currentStep === steps.length - 1 ? '#BDC3C7' : '#E67E22';
    }

    btnFwd.addEventListener('click', function() {
        if (currentStep < steps.length - 1) { currentStep++; render(); }
    });

    btnBack.addEventListener('click', function() {
        if (currentStep > 0) { currentStep--; render(); }
    });

    render();
});
