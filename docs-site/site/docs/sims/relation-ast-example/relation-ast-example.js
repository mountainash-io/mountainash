// Relation AST Example
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">Relation AST Example</div>
            <div id="query-box" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px 12px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Query</div>
                <code style="font-size:10px;color:#2C3E50;">relation(df).filter(col("age")&gt;18)<br>.select("name","email").head(10)</code>
            </div>
            <div id="info" style="position:absolute;top:10px;right:10px;width:240px;background:rgba(255,255,255,0.95);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;"></div>
        </div>
    `;

    var teal = '#008080';
    var tealLight = '#20B2AA';
    var tealDark = '#006060';
    var cx = 400;

    var astNodes = [
        { id: 'fetch', label: 'FetchRelNode\nn=10', y: 80, attrs: '<b>FetchRelNode</b><br><br><b>offset:</b> 0<br><b>count:</b> 10<br><br>Limits output to first 10 rows. Applied last in the pipeline.' },
        { id: 'project', label: 'ProjectRelNode\n["name","email"]', y: 190, attrs: '<b>ProjectRelNode</b><br><br><b>expressions:</b> [col("name"), col("email")]<br><b>output_schema:</b> {name: str, email: str}<br><br>Selects only the name and email columns.' },
        { id: 'filter', label: 'FilterRelNode\ncol("age") > 18', y: 300, attrs: '<b>FilterRelNode</b><br><br><b>predicate:</b> col("age") > lit(18)<br><b>predicate_type:</b> comparison (gt)<br><br>Filters rows where age exceeds 18.' },
        { id: 'read', label: 'ReadRelNode\nsource=df', y: 410, attrs: '<b>ReadRelNode</b><br><br><b>source:</b> DataFrame (in-memory)<br><b>schema:</b> {name: str, email: str, age: int, ...}<br><b>row_count:</b> ~10,000<br><br>Leaf node: reads the input DataFrame.' }
    ];

    var nodeData = astNodes.map(function(n) {
        return {
            id: n.id, label: n.label, x: cx, y: n.y, fixed: true, shape: 'box',
            color: { background: teal, border: tealDark, highlight: { background: tealLight, border: tealDark }, hover: { background: tealLight, border: tealDark } },
            font: { color: '#fff', size: 13, multi: true }, borderWidth: 2,
            widthConstraint: { minimum: 180 },
            attrs: n.attrs
        };
    });

    var edgeData = [
        { from: 'fetch', to: 'project', arrows: { to: { enabled: true, scaleFactor: 0.7 } }, color: { color: teal }, width: 2, label: 'input', font: { size: 10, color: '#666' } },
        { from: 'project', to: 'filter', arrows: { to: { enabled: true, scaleFactor: 0.7 } }, color: { color: teal }, width: 2, label: 'input', font: { size: 10, color: '#666' } },
        { from: 'filter', to: 'read', arrows: { to: { enabled: true, scaleFactor: 0.7 } }, color: { color: teal }, width: 2, label: 'input', font: { size: 10, color: '#666' } }
    ];

    // Direction labels
    nodeData.push({
        id: 'label-top', label: 'TOP (output)', x: cx + 220, y: 80, fixed: true, shape: 'text',
        font: { color: '#999', size: 11, face: 'Arial' }
    });
    nodeData.push({
        id: 'label-bottom', label: 'BOTTOM (leaf)', x: cx + 220, y: 410, fixed: true, shape: 'text',
        font: { color: '#999', size: 11, face: 'Arial' }
    });

    var nodes = new vis.DataSet(nodeData);
    var edges = new vis.DataSet(edgeData);

    var container = document.getElementById('network');
    var network = new vis.Network(container, { nodes: nodes, edges: edges }, {
        interaction: { zoomView: false, dragView: false, dragNodes: false, hover: true },
        physics: { enabled: false },
        layout: { improvedLayout: false }
    });

    var infoPanel = document.getElementById('info');

    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            var node = nodes.get(params.nodes[0]);
            if (node && node.attrs) {
                infoPanel.innerHTML = node.attrs;
                infoPanel.style.display = 'block';
            }
        } else {
            infoPanel.style.display = 'none';
        }
    });
});
