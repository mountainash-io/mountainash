// Function Registry Architecture — Three-Column Flow
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:8px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">Function Registry Architecture</div>
            <div id="legend" style="position:absolute;bottom:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Legend</div>
                <div><span style="color:#006400;">&#9679;</span> API Layer</div>
                <div><span style="color:#32CD32;">&#9679;</span> Registry</div>
                <div><span style="color:#FFD700;">&#9679;</span> Compilation</div>
            </div>
            <div id="detail" style="position:absolute;bottom:10px;right:10px;width:280px;background:rgba(255,255,255,0.97);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 8px rgba(0,0,0,0.15);display:none;"></div>
        </div>
    `;

    var darkGreen = '#006400';
    var limeGreen = '#32CD32';
    var gold = '#FFD700';
    var darkGold = '#B8860B';

    var colLeft = 120;
    var colMid = 400;
    var colRight = 680;
    var headerY = 50;
    var startY = 100;
    var spacing = 70;

    var nodes = new vis.DataSet();
    var edges = new vis.DataSet();

    // Column headers (using ellipse shape for visual distinction)
    nodes.add({ id: 'h_api', label: 'API Layer', x: colLeft, y: headerY, fixed: true, shape: 'box',
        color: { background: darkGreen, border: '#003000', hover: { background: '#228B22', border: '#003000' } },
        font: { color: '#fff', size: 13, bold: true }, borderWidth: 2, widthConstraint: { minimum: 120 } });
    nodes.add({ id: 'h_reg', label: 'Registry', x: colMid, y: headerY, fixed: true, shape: 'box',
        color: { background: limeGreen, border: '#228B22', hover: { background: '#90EE90', border: '#228B22' } },
        font: { color: '#000', size: 13, bold: true }, borderWidth: 2, widthConstraint: { minimum: 120 } });
    nodes.add({ id: 'h_comp', label: 'Compilation', x: colRight, y: headerY, fixed: true, shape: 'box',
        color: { background: gold, border: darkGold, hover: { background: '#FFEC8B', border: darkGold } },
        font: { color: '#000', size: 13, bold: true }, borderWidth: 2, widthConstraint: { minimum: 120 } });

    // API nodes (left)
    var apiNodes = [
        { id: 'api_col', label: 'col()', y: startY, detail: 'col("name") creates a ColumnExpr referencing a named column in the DataFrame.' },
        { id: 'api_lit', label: 'lit()', y: startY + spacing, detail: 'lit(42) wraps a scalar Python value as a LiteralExpr node in the expression tree.' },
        { id: 'api_when', label: 'when()', y: startY + spacing * 2, detail: 'when(pred).then(val).otherwise(default) builds a ConditionalExpr chain.' },
        { id: 'api_str', label: '.str.upper()', y: startY + spacing * 3, detail: 'Namespace accessor: triggers Descriptor.__get__, creates StringNamespace, resolves to FunctionKey("upper","string").' },
        { id: 'api_dt', label: '.dt.year()', y: startY + spacing * 4, detail: 'Temporal namespace accessor: resolves to FunctionKey("year","temporal") via the datetime descriptor.' }
    ];

    // Registry nodes (middle)
    var regNodes = [
        { id: 'reg_hub', label: 'Expression\nFunction\nRegistry', y: startY + spacing * 1.5, detail: 'Central registry (ExpressionFunctionRegistry) that maps FunctionKey -> implementation. Singleton per backend context.' },
        { id: 'fk_upper', label: 'FK: upper\n(string)', y: startY, detail: 'FunctionKey("upper", "string") — maps to string uppercase operation across all backends.' },
        { id: 'fk_year', label: 'FK: year\n(temporal)', y: startY + spacing, detail: 'FunctionKey("year", "temporal") — extracts year component from date/datetime values.' },
        { id: 'fk_sum', label: 'FK: sum\n(aggregate)', y: startY + spacing * 3, detail: 'FunctionKey("sum", "aggregate") — aggregation function, compiles to backend-specific SUM.' },
        { id: 'fk_when', label: 'FK: when\n(conditional)', y: startY + spacing * 4, detail: 'FunctionKey("when", "conditional") — conditional branching compiled to CASE WHEN or equivalent.' }
    ];

    // Compilation nodes (right)
    var compNodes = [
        { id: 'comp_polars', label: 'Polars\ncompile()', y: startY, detail: 'Polars backend: translates FunctionKey to Polars native expression (e.g., pl.col().str.to_uppercase()).' },
        { id: 'comp_pandas', label: 'pandas\ncompile()', y: startY + spacing, detail: 'pandas backend: translates FunctionKey to pandas Series method (e.g., ser.str.upper()).' },
        { id: 'comp_arrow', label: 'PyArrow\ncompute()', y: startY + spacing * 2, detail: 'PyArrow backend: maps to pyarrow.compute kernel (e.g., pc.utf8_upper()).' },
        { id: 'comp_ibis', label: 'Ibis\ncompile()', y: startY + spacing * 3, detail: 'Ibis backend: compiles to Ibis expression (e.g., col.upper()), then to SQL via Ibis engine.' },
        { id: 'comp_sql', label: 'SQL\ngenerate()', y: startY + spacing * 4, detail: 'SQL generation: emits standard SQL (e.g., UPPER(col)) for database backends.' }
    ];

    apiNodes.forEach(function(n) {
        nodes.add({ id: n.id, label: n.label, x: colLeft, y: n.y, fixed: true, shape: 'box',
            widthConstraint: { minimum: 100 },
            color: { background: darkGreen, border: '#003000', hover: { background: '#228B22', border: '#003000' } },
            font: { color: '#fff', size: 12, multi: true }, borderWidth: 1, detail: n.detail });
    });

    regNodes.forEach(function(n) {
        var isHub = n.id === 'reg_hub';
        nodes.add({ id: n.id, label: n.label, x: colMid, y: n.y, fixed: true,
            shape: isHub ? 'box' : 'box',
            widthConstraint: { minimum: isHub ? 140 : 100 },
            color: { background: isHub ? limeGreen : '#90EE90', border: isHub ? '#228B22' : limeGreen,
                hover: { background: '#c8ffc8', border: '#228B22' } },
            font: { color: '#000', size: isHub ? 13 : 11, multi: true, bold: isHub }, borderWidth: isHub ? 2 : 1,
            detail: n.detail });
    });

    compNodes.forEach(function(n) {
        nodes.add({ id: n.id, label: n.label, x: colRight, y: n.y, fixed: true, shape: 'box',
            widthConstraint: { minimum: 100 },
            color: { background: gold, border: darkGold, hover: { background: '#FFEC8B', border: darkGold } },
            font: { color: '#000', size: 12, multi: true }, borderWidth: 1, detail: n.detail });
    });

    // Edges: API -> Registry hub
    apiNodes.forEach(function(n) {
        edges.add({ from: n.id, to: 'reg_hub', color: { color: darkGreen, hover: '#228B22' }, width: 1.5,
            arrows: { to: { enabled: true, scaleFactor: 0.6 } }, smooth: { type: 'cubicBezier', roundness: 0.2 } });
    });

    // Edges: FK nodes -> hub (bidirectional conceptually, show as from hub)
    ['fk_upper', 'fk_year', 'fk_sum', 'fk_when'].forEach(function(fk) {
        edges.add({ from: 'reg_hub', to: fk, color: { color: limeGreen, hover: '#90EE90' }, width: 1,
            dashes: true, smooth: false });
    });

    // Edges: Registry hub -> Compilation
    compNodes.forEach(function(n) {
        edges.add({ from: 'reg_hub', to: n.id, color: { color: darkGold, hover: gold }, width: 1.5,
            arrows: { to: { enabled: true, scaleFactor: 0.6 } }, smooth: { type: 'cubicBezier', roundness: 0.2 } });
    });

    var container = document.getElementById('network');
    var network = new vis.Network(container, { nodes: nodes, edges: edges }, {
        interaction: { zoomView: false, dragView: false, dragNodes: false, hover: true },
        physics: { enabled: false },
        layout: { improvedLayout: false }
    });

    var detailPanel = document.getElementById('detail');

    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            var node = nodes.get(params.nodes[0]);
            if (node && node.detail) {
                detailPanel.innerHTML = '<b>' + node.label.replace(/\n/g, ' ') + '</b><br><br>' + node.detail;
                detailPanel.style.display = 'block';
            } else {
                detailPanel.style.display = 'none';
            }
        } else {
            detailPanel.style.display = 'none';
        }
    });

    network.on('hoverNode', function(params) {
        var node = nodes.get(params.node);
        if (node && node.detail) {
            detailPanel.innerHTML = '<b>' + node.label.replace(/\n/g, ' ') + '</b><br><br>' + node.detail;
            detailPanel.style.display = 'block';
        }
    });

    network.on('blurNode', function() {
        detailPanel.style.display = 'none';
    });
});
