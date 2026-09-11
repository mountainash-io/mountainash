// Backend Architecture End-to-End
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">Backend Architecture End-to-End</div>
            <div id="controls" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Highlight Backend</div>
                <button class="be-btn" data-be="polars" style="padding:3px 10px;margin:2px;border:2px solid #E74C3C;background:#fff;color:#E74C3C;border-radius:4px;cursor:pointer;font-size:11px;">Polars</button>
                <button class="be-btn" data-be="narwhals" style="padding:3px 10px;margin:2px;border:2px solid #3498DB;background:#fff;color:#3498DB;border-radius:4px;cursor:pointer;font-size:11px;">Narwhals</button>
                <button class="be-btn" data-be="ibis" style="padding:3px 10px;margin:2px;border:2px solid #2ECC71;background:#fff;color:#2ECC71;border-radius:4px;cursor:pointer;font-size:11px;">Ibis</button>
                <button class="be-btn" data-be="" style="padding:3px 10px;margin:2px;border:2px solid #999;background:#fff;color:#999;border-radius:4px;cursor:pointer;font-size:11px;">All</button>
            </div>
            <div id="info" style="position:absolute;bottom:10px;left:50%;transform:translateX(-50%);max-width:520px;background:rgba(255,255,255,0.95);padding:10px 14px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;text-align:center;"></div>
        </div>
    `;

    var teal = '#008080';
    var gold = '#DAA520';
    var polarsC = '#E74C3C';
    var narwhalsC = '#3498DB';
    var ibisC = '#2ECC71';
    var resultC = '#8E44AD';
    var dimColor = '#D0D0D0';

    // Architecture layers: User API → AST → Auto-Detection → Visitor → System → Result
    var archNodes = [
        // User API (left)
        { id: 'user-api', label: 'User API\nrelation(df).filter()\n.select().head()', x: 100, y: 120, bg: teal, backends: ['polars', 'narwhals', 'ibis'] },
        // AST
        { id: 'ast', label: 'Relation AST\n(tree of RelNodes)', x: 280, y: 120, bg: teal, backends: ['polars', 'narwhals', 'ibis'] },
        // Auto-detection
        { id: 'detect', label: 'Auto-Detection\nidentify_backend()', x: 400, y: 50, bg: gold, backends: ['polars', 'narwhals', 'ibis'] },
        // Visitor
        { id: 'visitor', label: 'Unified\nRelationVisitor', x: 400, y: 200, bg: teal, backends: ['polars', 'narwhals', 'ibis'] },
        // Three systems
        { id: 'sys-polars', label: 'PolarsRelation\nSystem', x: 560, y: 80, bg: polarsC, backends: ['polars'] },
        { id: 'sys-narwhals', label: 'NarwhalsRelation\nSystem', x: 560, y: 200, bg: narwhalsC, backends: ['narwhals'] },
        { id: 'sys-ibis', label: 'IbisRelation\nSystem', x: 560, y: 320, bg: ibisC, backends: ['ibis'] },
        // Execution detail
        { id: 'exec-polars', label: 'LazyFrame\nplan + optimize', x: 680, y: 80, bg: polarsC, backends: ['polars'] },
        { id: 'exec-narwhals', label: 'Eager pandas\noperations', x: 680, y: 200, bg: narwhalsC, backends: ['narwhals'] },
        { id: 'exec-ibis', label: 'SQL generation\n+ execute', x: 680, y: 320, bg: ibisC, backends: ['ibis'] },
        // Result
        { id: 'result', label: 'Result\nDataFrame', x: 400, y: 420, bg: resultC, backends: ['polars', 'narwhals', 'ibis'] }
    ];

    var archEdges = [
        { id: 'e1', from: 'user-api', to: 'ast', label: 'builds', backends: ['polars', 'narwhals', 'ibis'] },
        { id: 'e2', from: 'ast', to: 'detect', label: 'inspects', backends: ['polars', 'narwhals', 'ibis'] },
        { id: 'e3', from: 'detect', to: 'visitor', label: 'selects system', backends: ['polars', 'narwhals', 'ibis'], smooth: { type: 'curvedCW', roundness: 0.2 } },
        { id: 'e4', from: 'ast', to: 'visitor', label: 'traverses', backends: ['polars', 'narwhals', 'ibis'] },
        { id: 'e5p', from: 'visitor', to: 'sys-polars', label: 'compiles via', backends: ['polars'] },
        { id: 'e5n', from: 'visitor', to: 'sys-narwhals', label: 'compiles via', backends: ['narwhals'] },
        { id: 'e5i', from: 'visitor', to: 'sys-ibis', label: 'compiles via', backends: ['ibis'] },
        { id: 'e6p', from: 'sys-polars', to: 'exec-polars', label: '', backends: ['polars'] },
        { id: 'e6n', from: 'sys-narwhals', to: 'exec-narwhals', label: '', backends: ['narwhals'] },
        { id: 'e6i', from: 'sys-ibis', to: 'exec-ibis', label: '', backends: ['ibis'] },
        { id: 'e7p', from: 'exec-polars', to: 'result', label: '', backends: ['polars'], smooth: { type: 'curvedCCW', roundness: 0.3 } },
        { id: 'e7n', from: 'exec-narwhals', to: 'result', label: '', backends: ['narwhals'] },
        { id: 'e7i', from: 'exec-ibis', to: 'result', label: '', backends: ['ibis'], smooth: { type: 'curvedCW', roundness: 0.3 } }
    ];

    var selectedBackend = '';

    function buildData() {
        var nodeData = archNodes.map(function(n) {
            var match = !selectedBackend || n.backends.indexOf(selectedBackend) >= 0;
            var bg = match ? n.bg : dimColor;
            return {
                id: n.id, label: n.label, x: n.x, y: n.y, fixed: true, shape: 'box',
                color: { background: bg, border: match ? shadeColor(n.bg, -30) : '#BBB', highlight: { background: match ? lightenColor(n.bg, 20) : dimColor, border: match ? shadeColor(n.bg, -30) : '#BBB' }, hover: { background: match ? lightenColor(n.bg, 20) : dimColor, border: match ? shadeColor(n.bg, -30) : '#BBB' } },
                font: { color: match ? '#fff' : '#aaa', size: 11, multi: true },
                borderWidth: match && selectedBackend ? 3 : 2,
                widthConstraint: { minimum: 100 }
            };
        });

        var edgeData = archEdges.map(function(e) {
            var match = !selectedBackend || e.backends.indexOf(selectedBackend) >= 0;
            var obj = {
                id: e.id, from: e.from, to: e.to, label: match ? e.label : '',
                arrows: { to: { enabled: true, scaleFactor: 0.6 } },
                color: { color: match ? teal : '#ddd' },
                width: match ? 2.5 : 1,
                font: { size: 9, color: match ? '#444' : '#ccc' }
            };
            if (e.smooth) obj.smooth = e.smooth;
            return obj;
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
    var nodeInfo = {
        'user-api': 'The fluent Python API (relation(), .filter(), .select(), etc.) that builds the AST without executing anything.',
        'ast': 'A tree of RelationNode objects representing the query. Each node type corresponds to a relational algebra operation.',
        'detect': 'Walks the AST to find ReadRelNode, inspects the source DataFrame type, and selects the appropriate RelationSystem.',
        'visitor': 'UnifiedRelationVisitor traverses the AST bottom-up, calling the selected system\'s methods for each node type.',
        'sys-polars': 'PolarsRelationSystem: builds a Polars LazyFrame plan with automatic query optimization.',
        'sys-narwhals': 'NarwhalsRelationSystem: executes eagerly via the Narwhals compatibility layer (pandas, cuDF).',
        'sys-ibis': 'IbisRelationSystem: generates SQL expressions via Ibis for database backends.',
        'exec-polars': 'Polars compiles the LazyFrame plan, applies predicate pushdown and projection pruning, then collects results.',
        'exec-narwhals': 'Narwhals wraps pandas operations for immediate eager execution on each step.',
        'exec-ibis': 'Ibis compiles expressions to SQL, sends to the connected database engine, and fetches results.',
        'result': 'The final materialized DataFrame returned to the user, regardless of which backend executed the query.'
    };

    network.on('click', function(params) {
        if (params.nodes.length > 0 && nodeInfo[params.nodes[0]]) {
            infoPanel.innerHTML = nodeInfo[params.nodes[0]];
            infoPanel.style.display = 'block';
        } else {
            infoPanel.style.display = 'none';
        }
    });

    document.querySelectorAll('.be-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            selectedBackend = this.getAttribute('data-be');
            var data = buildData();
            network.setData(data);
            if (selectedBackend) {
                infoPanel.innerHTML = 'Showing the <b>' + selectedBackend + '</b> execution path through the architecture.';
                infoPanel.style.display = 'block';
            } else {
                infoPanel.style.display = 'none';
            }
        });
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
