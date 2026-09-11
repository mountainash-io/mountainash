// Terminal Operations — Decision tree with backend matrix
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">Terminal Operations</div>
            <div id="legend" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Legend</div>
                <div><span style="color:#20B2AA;">&#9679;</span> Decision node</div>
                <div><span style="color:#2ECC71;">&#9679;</span> Zero-copy / fast</div>
                <div><span style="color:#F39C12;">&#9679;</span> Conversion required</div>
                <div style="margin-top:4px;font-size:10px;color:#666;">Click a terminal to<br/>see compilation path</div>
            </div>
            <div id="info" style="position:absolute;bottom:10px;right:10px;width:280px;background:rgba(255,255,255,0.95);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;"></div>
        </div>
    `;

    var teal    = '#20B2AA';
    var tealDk  = '#178F89';
    var green   = '#2ECC71';
    var greenDk = '#25A25A';
    var amber   = '#F39C12';
    var amberDk = '#D4860E';

    function makeColor(bg, border) {
        return { background: bg, border: border,
                 highlight: { background: lighten(bg, 20), border: border },
                 hover: { background: lighten(bg, 20), border: border } };
    }

    var nodesList = [
        // Root decision
        { id: 'root', label: 'What output\nformat?', x: 400, y: 60, fixed: true,
          shape: 'diamond', size: 35, borderWidth: 2,
          color: makeColor(teal, tealDk),
          font: { color: '#fff', size: 12, multi: true } },

        // Three terminal options
        { id: 'to_polars', label: '  to_polars()  \n✅ zero-copy', x: 150, y: 180, fixed: true,
          shape: 'box', borderWidth: 2,
          color: makeColor(green, greenDk),
          font: { color: '#fff', size: 13, multi: true, bold: true },
          widthConstraint: { minimum: 120 },
          info: '<b>to_polars()</b><br><br><b>Cost:</b> ✅ Zero-copy when backend is Polars<br><br><b>Compilation path:</b><br>1. DAG compiles to Polars Expr chain<br>2. Polars executes natively<br>3. Returns pl.DataFrame directly<br><br><b>Best when:</b> Backend is already Polars, or you need lazy evaluation and fast columnar ops.' },
        { id: 'to_pandas', label: '  to_pandas()  \n⚠️ conversion', x: 400, y: 180, fixed: true,
          shape: 'box', borderWidth: 2,
          color: makeColor(amber, amberDk),
          font: { color: '#fff', size: 13, multi: true, bold: true },
          widthConstraint: { minimum: 120 },
          info: '<b>to_pandas()</b><br><br><b>Cost:</b> ⚠️ Arrow-to-pandas conversion<br><br><b>Compilation path:</b><br>1. DAG compiles to backend expressions<br>2. Backend executes query<br>3. Result converted via <code>.to_pandas()</code><br>4. Memory copy from Arrow to NumPy<br><br><b>Best when:</b> Downstream code requires pandas API (matplotlib, sklearn, etc.).' },
        { id: 'collect', label: '  collect()  \n✅ native result', x: 650, y: 180, fixed: true,
          shape: 'box', borderWidth: 2,
          color: makeColor(green, greenDk),
          font: { color: '#fff', size: 13, multi: true, bold: true },
          widthConstraint: { minimum: 120 },
          info: '<b>collect()</b><br><br><b>Cost:</b> ✅ Returns native backend result<br><br><b>Compilation path:</b><br>1. DAG compiles to backend expressions<br>2. Backend executes query<br>3. Returns whatever the backend produces<br>4. No conversion overhead<br><br><b>Best when:</b> You want the raw result from the active backend without format assumptions.' },

        // Backend x Format matrix header
        { id: 'matrix-title', label: 'Backend × Format Matrix', x: 400, y: 290, fixed: true,
          shape: 'text', font: { color: '#333', size: 14, bold: true } },

        // Matrix: backends (rows)
        { id: 'b-polars', label: 'Polars', x: 200, y: 330, fixed: true,
          shape: 'box', borderWidth: 1,
          color: makeColor('#E8F0FE', '#4682B4'),
          font: { color: '#333', size: 11, bold: true }, widthConstraint: { minimum: 80 } },
        { id: 'b-narwhals', label: 'Narwhals', x: 200, y: 370, fixed: true,
          shape: 'box', borderWidth: 1,
          color: makeColor('#E8F0FE', '#4682B4'),
          font: { color: '#333', size: 11, bold: true }, widthConstraint: { minimum: 80 } },
        { id: 'b-ibis', label: 'Ibis', x: 200, y: 410, fixed: true,
          shape: 'box', borderWidth: 1,
          color: makeColor('#E8F0FE', '#4682B4'),
          font: { color: '#333', size: 11, bold: true }, widthConstraint: { minimum: 80 } },

        // Matrix cells: to_polars column
        { id: 'c-pol-pol', label: '✅ zero-copy', x: 350, y: 330, fixed: true,
          shape: 'box', borderWidth: 1,
          color: makeColor('#E8FCE8', greenDk),
          font: { color: '#333', size: 10 }, widthConstraint: { minimum: 90 } },
        { id: 'c-nar-pol', label: '⚠️ convert', x: 350, y: 370, fixed: true,
          shape: 'box', borderWidth: 1,
          color: makeColor('#FFF8E0', amberDk),
          font: { color: '#333', size: 10 }, widthConstraint: { minimum: 90 } },
        { id: 'c-ibi-pol', label: '⚠️ convert', x: 350, y: 410, fixed: true,
          shape: 'box', borderWidth: 1,
          color: makeColor('#FFF8E0', amberDk),
          font: { color: '#333', size: 10 }, widthConstraint: { minimum: 90 } },

        // Matrix cells: to_pandas column
        { id: 'c-pol-pan', label: '⚠️ convert', x: 470, y: 330, fixed: true,
          shape: 'box', borderWidth: 1,
          color: makeColor('#FFF8E0', amberDk),
          font: { color: '#333', size: 10 }, widthConstraint: { minimum: 90 } },
        { id: 'c-nar-pan', label: '⚠️ convert', x: 470, y: 370, fixed: true,
          shape: 'box', borderWidth: 1,
          color: makeColor('#FFF8E0', amberDk),
          font: { color: '#333', size: 10 }, widthConstraint: { minimum: 90 } },
        { id: 'c-ibi-pan', label: '⚠️ convert', x: 470, y: 410, fixed: true,
          shape: 'box', borderWidth: 1,
          color: makeColor('#FFF8E0', amberDk),
          font: { color: '#333', size: 10 }, widthConstraint: { minimum: 90 } },

        // Matrix cells: collect column
        { id: 'c-pol-col', label: '✅ pl.DataFrame', x: 600, y: 330, fixed: true,
          shape: 'box', borderWidth: 1,
          color: makeColor('#E8FCE8', greenDk),
          font: { color: '#333', size: 10 }, widthConstraint: { minimum: 100 } },
        { id: 'c-nar-col', label: '✅ native frame', x: 600, y: 370, fixed: true,
          shape: 'box', borderWidth: 1,
          color: makeColor('#E8FCE8', greenDk),
          font: { color: '#333', size: 10 }, widthConstraint: { minimum: 100 } },
        { id: 'c-ibi-col', label: '✅ ibis.Table', x: 600, y: 410, fixed: true,
          shape: 'box', borderWidth: 1,
          color: makeColor('#E8FCE8', greenDk),
          font: { color: '#333', size: 10 }, widthConstraint: { minimum: 100 } },

        // Column headers
        { id: 'h-polars', label: 'to_polars()', x: 350, y: 300, fixed: true,
          shape: 'text', font: { color: '#555', size: 10, bold: true } },
        { id: 'h-pandas', label: 'to_pandas()', x: 470, y: 300, fixed: true,
          shape: 'text', font: { color: '#555', size: 10, bold: true } },
        { id: 'h-collect', label: 'collect()', x: 600, y: 300, fixed: true,
          shape: 'text', font: { color: '#555', size: 10, bold: true } }
    ];

    var nodes = new vis.DataSet(nodesList);

    var edgesList = [
        // Root to terminals
        { from: 'root', to: 'to_polars', color: { color: teal }, width: 2,
          arrows: { to: { enabled: true, scaleFactor: 0.7 } },
          smooth: { type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.3 } },
        { from: 'root', to: 'to_pandas', color: { color: teal }, width: 2,
          arrows: { to: { enabled: true, scaleFactor: 0.7 } },
          smooth: false },
        { from: 'root', to: 'collect', color: { color: teal }, width: 2,
          arrows: { to: { enabled: true, scaleFactor: 0.7 } },
          smooth: { type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.3 } }
    ];
    var edges = new vis.DataSet(edgesList);

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
            if (node && node.info) {
                infoPanel.innerHTML = node.info;
                infoPanel.style.display = 'block';
            } else {
                infoPanel.style.display = 'none';
            }
        } else {
            infoPanel.style.display = 'none';
        }
    });

    function lighten(hex, amt) {
        hex = hex.replace('#', '');
        var num = parseInt(hex, 16);
        var r = Math.min(255, (num >> 16) + amt);
        var g = Math.min(255, ((num >> 8) & 0xFF) + amt);
        var b = Math.min(255, (num & 0xFF) + amt);
        return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
    }
});
