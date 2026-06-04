// DataFrame Structure and Backend Mapping
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">DataFrame Backend Mapping</div>
            <div id="legend" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Legend</div>
                <div><span style="color:#4682B4;">&#9679;</span> Abstract DataFrame</div>
                <div><span style="color:#E74C3C;">&#9679;</span> Polars</div>
                <div><span style="color:#3498DB;">&#9679;</span> pandas</div>
                <div><span style="color:#F39C12;">&#9679;</span> PyArrow</div>
                <div><span style="color:#2ECC71;">&#9679;</span> Ibis</div>
            </div>
            <div id="info" style="position:absolute;top:50px;right:10px;width:260px;background:rgba(255,255,255,0.95);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;"></div>
        </div>
    `;

    var centerX = 400;
    var centerY = 250;
    var radius = 160;

    var backendData = [
        { id: 'polars-df', label: 'Polars\nDataFrame', color: '#E74C3C', angle: 0,
          info: '<b>Polars DataFrame</b><br><br>Eager evaluation mode. Executes operations immediately. Best for small-to-medium datasets that fit in memory. Uses Apache Arrow columnar format internally.' },
        { id: 'polars-lf', label: 'Polars\nLazyFrame', color: '#E74C3C', angle: 1,
          info: '<b>Polars LazyFrame</b><br><br>Lazy evaluation mode. Builds a query plan before execution, enabling automatic optimization. Preferred for large datasets and complex pipelines.' },
        { id: 'pandas-df', label: 'pandas\nDataFrame', color: '#3498DB', angle: 2,
          info: '<b>pandas DataFrame</b><br><br>The most widely-used Python DataFrame. Row-oriented operations, extensive ecosystem. Supports NumPy and Arrow backends. Best for interoperability.' },
        { id: 'pyarrow-t', label: 'PyArrow\nTable', color: '#F39C12', angle: 3,
          info: '<b>PyArrow Table</b><br><br>Apache Arrow native table. Zero-copy reads, columnar memory layout. Ideal for interprocess communication and Parquet/IPC file operations.' },
        { id: 'ibis-t', label: 'Ibis\nTable', color: '#2ECC71', angle: 4,
          info: '<b>Ibis Table</b><br><br>Deferred expression API that compiles to multiple backends (DuckDB, Spark, BigQuery). Provides a unified interface for local and remote data.' }
    ];

    var nodes = new vis.DataSet([
        { id: 'df', label: 'DataFrame', x: centerX, y: centerY, fixed: true,
          shape: 'box', color: { background: '#4682B4', border: '#2C5F8A', highlight: { background: '#5A9BD4', border: '#2C5F8A' }, hover: { background: '#5A9BD4', border: '#2C5F8A' } },
          font: { color: '#fff', size: 16, bold: true }, borderWidth: 2, size: 30,
          info: '<b>mountainash DataFrame</b><br><br>The central abstraction that provides a unified API across all backends. User code targets this interface; the backend is resolved at runtime.' }
    ]);

    var edges = new vis.DataSet();

    backendData.forEach(function(b, i) {
        var angle = (2 * Math.PI * i / backendData.length) - Math.PI / 2;
        var x = centerX + radius * Math.cos(angle);
        var y = centerY + radius * Math.sin(angle);
        nodes.add({
            id: b.id, label: b.label, x: x, y: y, fixed: true,
            shape: 'box',
            color: { background: b.color, border: shadeColor(b.color, -20), highlight: { background: lightenColor(b.color, 20), border: shadeColor(b.color, -20) }, hover: { background: lightenColor(b.color, 20), border: shadeColor(b.color, -20) } },
            font: { color: '#fff', size: 13, multi: true }, borderWidth: 2,
            info: b.info
        });
        edges.add({
            from: 'df', to: b.id,
            color: { color: b.color, highlight: b.color, hover: b.color },
            width: 2, arrows: { to: { enabled: true, scaleFactor: 0.8 } },
            smooth: { type: 'curvedCW', roundness: 0.1 }
        });
    });

    var container = document.getElementById('network');
    var network = new vis.Network(container, { nodes: nodes, edges: edges }, {
        interaction: { zoomView: false, dragView: false, dragNodes: false, navigationButtons: false, hover: true },
        physics: { enabled: false },
        layout: { improvedLayout: false }
    });

    var infoPanel = document.getElementById('info');

    network.on('hoverNode', function(params) {
        var node = nodes.get(params.node);
        if (node && node.info) {
            infoPanel.innerHTML = node.info;
            infoPanel.style.display = 'block';
        }
    });

    network.on('blurNode', function() {
        infoPanel.style.display = 'none';
    });

    function shadeColor(hex, percent) {
        var num = parseInt(hex.replace('#', ''), 16);
        var r = Math.max(0, Math.min(255, (num >> 16) + percent));
        var g = Math.max(0, Math.min(255, ((num >> 8) & 0x00FF) + percent));
        var b = Math.max(0, Math.min(255, (num & 0x0000FF) + percent));
        return '#' + (0x1000000 + r * 0x10000 + g * 0x100 + b).toString(16).slice(1);
    }

    function lightenColor(hex, percent) {
        return shadeColor(hex, percent);
    }
});
