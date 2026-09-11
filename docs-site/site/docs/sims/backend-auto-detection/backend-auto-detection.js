// Backend Auto-Detection
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">Backend Auto-Detection</div>
            <div id="scenarios" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Scenario</div>
                <button class="sc-btn" data-sc="explicit" style="padding:3px 8px;margin:2px 0;display:block;width:100%;border:1px solid #008080;background:#fff;color:#008080;border-radius:4px;cursor:pointer;font-size:10px;">Explicit backend=</button>
                <button class="sc-btn" data-sc="polars" style="padding:3px 8px;margin:2px 0;display:block;width:100%;border:1px solid #E74C3C;background:#fff;color:#E74C3C;border-radius:4px;cursor:pointer;font-size:10px;">Polars DataFrame</button>
                <button class="sc-btn" data-sc="pandas" style="padding:3px 8px;margin:2px 0;display:block;width:100%;border:1px solid #3498DB;background:#fff;color:#3498DB;border-radius:4px;cursor:pointer;font-size:10px;">pandas DataFrame</button>
                <button class="sc-btn" data-sc="unknown" style="padding:3px 8px;margin:2px 0;display:block;width:100%;border:1px solid #999;background:#fff;color:#999;border-radius:4px;cursor:pointer;font-size:10px;">Unknown type</button>
            </div>
            <div id="info" style="position:absolute;bottom:10px;left:50%;transform:translateX(-50%);max-width:500px;background:rgba(255,255,255,0.95);padding:10px 14px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;text-align:center;"></div>
        </div>
    `;

    var teal = '#008080';
    var gold = '#DAA520';
    var green = '#27AE60';
    var red = '#E74C3C';
    var dimColor = '#D0D0D0';

    var treeNodes = [
        { id: 'start', label: 'relation(df)', x: 400, y: 60, bg: teal },
        { id: 'explicit', label: 'Explicit\nbackend= param?', x: 400, y: 140, bg: teal },
        { id: 'yes-explicit', label: 'Use specified\nbackend', x: 200, y: 220, bg: green },
        { id: 'walk-ast', label: 'Walk AST for\nReadRelNode', x: 500, y: 220, bg: teal },
        { id: 'identify', label: 'identify_backend()\ntype inspection', x: 500, y: 310, bg: gold },
        { id: 'polars-det', label: 'Polars detected\n→ PolarsSystem', x: 350, y: 400, bg: '#E74C3C' },
        { id: 'pandas-det', label: 'pandas detected\n→ NarwhalsSystem', x: 500, y: 400, bg: '#3498DB' },
        { id: 'fallback', label: 'Fallback:\nPolarsSystem', x: 650, y: 400, bg: '#999' }
    ];

    var treeEdges = [
        { id: 'e1', from: 'start', to: 'explicit', label: '' },
        { id: 'e2', from: 'explicit', to: 'yes-explicit', label: 'Yes' },
        { id: 'e3', from: 'explicit', to: 'walk-ast', label: 'No' },
        { id: 'e4', from: 'walk-ast', to: 'identify', label: 'found' },
        { id: 'e5', from: 'identify', to: 'polars-det', label: 'pl.DataFrame' },
        { id: 'e6', from: 'identify', to: 'pandas-det', label: 'pd.DataFrame' },
        { id: 'e7', from: 'identify', to: 'fallback', label: 'unknown' }
    ];

    var scenarios = {
        'explicit': { path: ['start', 'explicit', 'yes-explicit'], edges: ['e1', 'e2'], desc: '<b>Explicit backend</b>: User passes backend="polars". No auto-detection needed; the specified system is used directly.' },
        'polars': { path: ['start', 'explicit', 'walk-ast', 'identify', 'polars-det'], edges: ['e1', 'e3', 'e4', 'e5'], desc: '<b>Polars DataFrame</b>: No explicit backend. AST walk finds ReadRelNode holding a Polars DataFrame. identify_backend() returns "polars".' },
        'pandas': { path: ['start', 'explicit', 'walk-ast', 'identify', 'pandas-det'], edges: ['e1', 'e3', 'e4', 'e6'], desc: '<b>pandas DataFrame</b>: No explicit backend. AST walk finds ReadRelNode holding a pandas DataFrame. identify_backend() returns "narwhals".' },
        'unknown': { path: ['start', 'explicit', 'walk-ast', 'identify', 'fallback'], edges: ['e1', 'e3', 'e4', 'e7'], desc: '<b>Unknown type</b>: identify_backend() cannot match the DataFrame type. Falls back to Polars as default backend.' }
    };

    var activeScenario = '';

    function buildData() {
        var activePath = activeScenario ? scenarios[activeScenario].path : [];
        var activeEdges = activeScenario ? scenarios[activeScenario].edges : [];
        var pathSet = {};
        activePath.forEach(function(id) { pathSet[id] = true; });
        var edgeSet = {};
        activeEdges.forEach(function(id) { edgeSet[id] = true; });

        var nodeData = treeNodes.map(function(n) {
            var isActive = !activeScenario || pathSet[n.id];
            var bg = isActive ? n.bg : dimColor;
            return {
                id: n.id, label: n.label, x: n.x, y: n.y, fixed: true, shape: 'box',
                color: { background: bg, border: isActive ? shadeColor(n.bg, -30) : '#BBB', highlight: { background: isActive ? lightenColor(n.bg, 20) : dimColor, border: isActive ? shadeColor(n.bg, -30) : '#BBB' }, hover: { background: isActive ? lightenColor(n.bg, 20) : dimColor, border: isActive ? shadeColor(n.bg, -30) : '#BBB' } },
                font: { color: isActive ? '#fff' : '#aaa', size: 12, multi: true },
                borderWidth: isActive && activeScenario ? 3 : 2
            };
        });

        var edgeData = treeEdges.map(function(e) {
            var isActive = !activeScenario || edgeSet[e.id];
            return {
                id: e.id, from: e.from, to: e.to, label: isActive ? e.label : '',
                arrows: { to: { enabled: true, scaleFactor: 0.7 } },
                color: { color: isActive ? teal : '#ddd' },
                width: isActive ? 2.5 : 1,
                font: { size: 10, color: isActive ? '#333' : '#ccc' }
            };
        });

        return { nodes: new vis.DataSet(nodeData), edges: new vis.DataSet(edgeData) };
    }

    var container = document.getElementById('network');
    var data = buildData();
    var network = new vis.Network(container, data, {
        interaction: { zoomView: false, dragView: false, dragNodes: false, hover: true },
        physics: { enabled: false },
        layout: { improvedLayout: false }
    });

    var infoPanel = document.getElementById('info');

    document.querySelectorAll('.sc-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            activeScenario = this.getAttribute('data-sc');
            var data = buildData();
            network.setData(data);
            if (scenarios[activeScenario]) {
                infoPanel.innerHTML = scenarios[activeScenario].desc;
                infoPanel.style.display = 'block';
            }
        });
    });

    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            var nodeId = params.nodes[0];
            var node = treeNodes.find(function(n) { return n.id === nodeId; });
            if (node) {
                infoPanel.innerHTML = '<b>' + node.label.replace(/\n/g, ' ') + '</b><br>Click a scenario button to see this node in context.';
                infoPanel.style.display = 'block';
            }
        }
    });

    function shadeColor(hex, percent) {
        var num = parseInt(hex.replace('#', ''), 16);
        var r = Math.max(0, Math.min(255, (num >> 16) + percent));
        var g = Math.max(0, Math.min(255, ((num >> 8) & 0x00FF) + percent));
        var b = Math.max(0, Math.min(255, (num & 0x0000FF) + percent));
        return '#' + (0x1000000 + r * 0x10000 + g * 0x100 + b).toString(16).slice(1);
    }
    function lightenColor(hex, percent) { return shadeColor(hex, percent); }
});
