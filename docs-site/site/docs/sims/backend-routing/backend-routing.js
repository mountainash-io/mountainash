// Backend Routing — Input Types to Backend Systems
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">Backend Routing</div>
            <div id="legend" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Legend</div>
                <div><span style="color:#483D8B;">&#9679;</span> Input Type</div>
                <div><span style="color:#6A5ACD;">&#9679;</span> CONST_BACKEND</div>
                <div><span style="color:#8B008B;">&#9679;</span> Backend System</div>
                <div style="margin-top:4px;color:#888;">Hover to trace path</div>
            </div>
            <div id="info" style="position:absolute;top:50px;right:10px;width:260px;background:rgba(255,255,255,0.95);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;"></div>
        </div>
    `;

    var col1X = 120;
    var col2X = 400;
    var col3X = 680;

    var inputTypes = [
        { id: 'in-polars-df', label: 'Polars\nDataFrame', y: 80, info: '<b>Polars DataFrame</b><br><br>Eager Polars frame. Routes to POLARS backend enum.' },
        { id: 'in-polars-lf', label: 'Polars\nLazyFrame', y: 170, info: '<b>Polars LazyFrame</b><br><br>Lazy Polars frame. Routes to POLARS backend enum.' },
        { id: 'in-pandas', label: 'pandas\nDataFrame', y: 260, info: '<b>pandas DataFrame</b><br><br>Standard pandas frame. Routes to PANDAS backend enum.' },
        { id: 'in-pyarrow', label: 'PyArrow\nTable', y: 350, info: '<b>PyArrow Table</b><br><br>Arrow-native table. Routes to PYARROW backend enum.' },
        { id: 'in-ibis', label: 'Ibis\nTable', y: 440, info: '<b>Ibis Table</b><br><br>Deferred expression table. Routes to IBIS backend enum.' }
    ];

    var enumValues = [
        { id: 'enum-polars', label: 'POLARS', y: 125, info: '<b>CONST_BACKEND.POLARS</b><br><br>Handles both eager DataFrame and LazyFrame inputs. Dispatches to the Polars execution system.' },
        { id: 'enum-pandas', label: 'PANDAS', y: 260, info: '<b>CONST_BACKEND.PANDAS</b><br><br>Routes pandas DataFrames to the pandas execution system.' },
        { id: 'enum-pyarrow', label: 'PYARROW', y: 350, info: '<b>CONST_BACKEND.PYARROW</b><br><br>Routes PyArrow Tables to the Arrow-native execution system.' },
        { id: 'enum-ibis', label: 'IBIS', y: 440, info: '<b>CONST_BACKEND.IBIS</b><br><br>Routes Ibis Tables to the deferred/SQL compilation system.' }
    ];

    var systems = [
        { id: 'sys-native', label: 'Native\nExecution', y: 170, info: '<b>Native Execution</b><br><br>Direct library calls (Polars/pandas). Operations execute in-process with the library\'s own engine.' },
        { id: 'sys-arrow', label: 'Arrow\nCompute', y: 310, info: '<b>Arrow Compute</b><br><br>Apache Arrow compute kernels. Zero-copy columnar operations for PyArrow Tables.' },
        { id: 'sys-deferred', label: 'Deferred\nCompilation', y: 440, info: '<b>Deferred Compilation</b><br><br>Compiles expressions to SQL or backend-specific IR. Used by Ibis for remote execution.' }
    ];

    var inputColor = { background: '#483D8B', border: '#362D6B', highlight: { background: '#5A4DA0', border: '#362D6B' }, hover: { background: '#5A4DA0', border: '#362D6B' } };
    var enumColor = { background: '#6A5ACD', border: '#5040B0', highlight: { background: '#7B6BDD', border: '#5040B0' }, hover: { background: '#7B6BDD', border: '#5040B0' } };
    var sysColor = { background: '#8B008B', border: '#6B006B', highlight: { background: '#A020A0', border: '#6B006B' }, hover: { background: '#A020A0', border: '#6B006B' } };

    var nodes = new vis.DataSet();
    var edges = new vis.DataSet();

    inputTypes.forEach(function(t) {
        nodes.add({ id: t.id, label: t.label, x: col1X, y: t.y, fixed: true, shape: 'box', color: inputColor, font: { color: '#fff', size: 11 }, borderWidth: 2, info: t.info });
    });

    enumValues.forEach(function(e) {
        nodes.add({ id: e.id, label: e.label, x: col2X, y: e.y, fixed: true, shape: 'box', color: enumColor, font: { color: '#fff', size: 13, bold: true }, borderWidth: 2, info: e.info });
    });

    systems.forEach(function(s) {
        nodes.add({ id: s.id, label: s.label, x: col3X, y: s.y, fixed: true, shape: 'box', color: sysColor, font: { color: '#fff', size: 12 }, borderWidth: 2, info: s.info });
    });

    // Input -> Enum edges
    var inputToEnum = [
        ['in-polars-df', 'enum-polars'], ['in-polars-lf', 'enum-polars'],
        ['in-pandas', 'enum-pandas'], ['in-pyarrow', 'enum-pyarrow'], ['in-ibis', 'enum-ibis']
    ];
    inputToEnum.forEach(function(pair) {
        edges.add({ from: pair[0], to: pair[1], color: { color: '#8888CC', highlight: '#483D8B', hover: '#483D8B' }, width: 1.5, arrows: { to: { enabled: true, scaleFactor: 0.7 } }, smooth: { type: 'cubicBezier', roundness: 0.3 } });
    });

    // Enum -> System edges
    var enumToSys = [
        ['enum-polars', 'sys-native'], ['enum-pandas', 'sys-native'],
        ['enum-pyarrow', 'sys-arrow'], ['enum-ibis', 'sys-deferred']
    ];
    enumToSys.forEach(function(pair) {
        edges.add({ from: pair[0], to: pair[1], color: { color: '#AA88CC', highlight: '#8B008B', hover: '#8B008B' }, width: 1.5, arrows: { to: { enabled: true, scaleFactor: 0.7 } }, smooth: { type: 'cubicBezier', roundness: 0.3 } });
    });

    var container = document.getElementById('network');
    var network = new vis.Network(container, { nodes: nodes, edges: edges }, {
        interaction: { zoomView: false, dragView: false, dragNodes: false, navigationButtons: false, hover: true },
        physics: { enabled: false },
        layout: { improvedLayout: false }
    });

    var infoPanel = document.getElementById('info');

    // Build full path map for highlight-on-hover
    var pathMap = {
        'in-polars-df': ['in-polars-df', 'enum-polars', 'sys-native'],
        'in-polars-lf': ['in-polars-lf', 'enum-polars', 'sys-native'],
        'in-pandas': ['in-pandas', 'enum-pandas', 'sys-native'],
        'in-pyarrow': ['in-pyarrow', 'enum-pyarrow', 'sys-arrow'],
        'in-ibis': ['in-ibis', 'enum-ibis', 'sys-deferred'],
        'enum-polars': ['in-polars-df', 'in-polars-lf', 'enum-polars', 'sys-native'],
        'enum-pandas': ['in-pandas', 'enum-pandas', 'sys-native'],
        'enum-pyarrow': ['in-pyarrow', 'enum-pyarrow', 'sys-arrow'],
        'enum-ibis': ['in-ibis', 'enum-ibis', 'sys-deferred'],
        'sys-native': ['in-polars-df', 'in-polars-lf', 'in-pandas', 'enum-polars', 'enum-pandas', 'sys-native'],
        'sys-arrow': ['in-pyarrow', 'enum-pyarrow', 'sys-arrow'],
        'sys-deferred': ['in-ibis', 'enum-ibis', 'sys-deferred']
    };

    network.on('hoverNode', function(params) {
        var node = nodes.get(params.node);
        if (node && node.info) {
            infoPanel.innerHTML = node.info;
            infoPanel.style.display = 'block';
        }
        var path = pathMap[params.node];
        if (path) {
            nodes.forEach(function(n) {
                nodes.update({ id: n.id, opacity: path.indexOf(n.id) >= 0 ? 1.0 : 0.25 });
            });
        }
    });

    network.on('blurNode', function() {
        infoPanel.style.display = 'none';
        nodes.forEach(function(n) {
            nodes.update({ id: n.id, opacity: 1.0 });
        });
    });
});
