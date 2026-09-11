// Backend Execution Models
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">Backend Execution Models</div>
            <div id="controls" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Highlight Backend</div>
                <button class="sel-btn" data-backend="polars" style="padding:3px 10px;margin:2px;border:2px solid #E74C3C;background:#fff;color:#E74C3C;border-radius:4px;cursor:pointer;font-size:11px;">Polars</button>
                <button class="sel-btn" data-backend="narwhals" style="padding:3px 10px;margin:2px;border:2px solid #3498DB;background:#fff;color:#3498DB;border-radius:4px;cursor:pointer;font-size:11px;">Narwhals</button>
                <button class="sel-btn" data-backend="ibis" style="padding:3px 10px;margin:2px;border:2px solid #2ECC71;background:#fff;color:#2ECC71;border-radius:4px;cursor:pointer;font-size:11px;">Ibis</button>
                <button class="sel-btn" data-backend="" style="padding:3px 10px;margin:2px;border:2px solid #999;background:#fff;color:#999;border-radius:4px;cursor:pointer;font-size:11px;">All</button>
            </div>
            <div id="info" style="position:absolute;bottom:10px;left:50%;transform:translateX(-50%);max-width:500px;background:rgba(255,255,255,0.95);padding:10px 14px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;text-align:center;"></div>
        </div>
    `;

    var polarsColor = '#E74C3C';
    var narwhalsColor = '#3498DB';
    var ibisColor = '#2ECC71';
    var dimColor = '#D0D0D0';
    var queryColor = '#008080';

    // Common query at top
    var queryY = 70;
    var colX = { polars: 180, narwhals: 400, ibis: 620 };

    var operations = [
        { key: 'read', label: 'Read', polars: 'lf = pl.scan_csv()', narwhals: 'df = pd.read_csv()', ibis: 'tbl = con.table()' },
        { key: 'filter', label: 'Filter', polars: 'lf.filter(col > 18)', narwhals: 'df[df.col > 18]', ibis: 'tbl.filter(tbl.col > 18)' },
        { key: 'project', label: 'Project', polars: 'lf.select([...])', narwhals: 'df[["name","email"]]', ibis: 'tbl.select([...])' },
        { key: 'sort', label: 'Sort', polars: 'lf.sort("name")', narwhals: 'df.sort_values()', ibis: 'tbl.order_by("name")' },
        { key: 'collect', label: 'Execute', polars: 'lf.collect()', narwhals: '(already eager)', ibis: 'tbl.to_pandas()' }
    ];

    var nodeData = [];
    var edgeData = [];

    // Query node
    nodeData.push({
        id: 'query', label: 'relation(df).filter(...).select(...).sort(...)', x: 400, y: queryY, fixed: true, shape: 'box',
        color: { background: queryColor, border: '#006060' }, font: { color: '#fff', size: 12 }, borderWidth: 2,
        widthConstraint: { minimum: 350 }, backend: 'query'
    });

    // Column headers
    ['Polars', 'Narwhals', 'Ibis'].forEach(function(name, i) {
        var colors = [polarsColor, narwhalsColor, ibisColor];
        var keys = ['polars', 'narwhals', 'ibis'];
        var x = [colX.polars, colX.narwhals, colX.ibis][i];
        nodeData.push({
            id: 'header-' + keys[i], label: name + '\n(LazyFrame plan)', x: x, y: queryY + 60, fixed: true, shape: 'box',
            color: { background: colors[i], border: shadeColor(colors[i], -30) },
            font: { color: '#fff', size: 12, multi: true }, borderWidth: 2, backend: keys[i]
        });
        if (keys[i] === 'narwhals') nodeData[nodeData.length - 1].label = name + '\n(eager pandas ops)';
        if (keys[i] === 'ibis') nodeData[nodeData.length - 1].label = name + '\n(generated SQL)';
        edgeData.push({ from: 'query', to: 'header-' + keys[i], color: { color: colors[i] }, width: 2, arrows: { to: { enabled: true, scaleFactor: 0.6 } }, backend: keys[i] });
    });

    // Operation rows
    operations.forEach(function(op, rowIdx) {
        var y = queryY + 130 + rowIdx * 65;
        var cols = [
            { key: 'polars', text: op.polars, color: polarsColor, x: colX.polars },
            { key: 'narwhals', text: op.narwhals, color: narwhalsColor, x: colX.narwhals },
            { key: 'ibis', text: op.ibis, color: ibisColor, x: colX.ibis }
        ];
        cols.forEach(function(c) {
            nodeData.push({
                id: op.key + '-' + c.key, label: op.label + '\n' + c.text, x: c.x, y: y, fixed: true, shape: 'box',
                color: { background: c.color, border: shadeColor(c.color, -30), highlight: { background: lightenColor(c.color, 20), border: shadeColor(c.color, -30) }, hover: { background: lightenColor(c.color, 20), border: shadeColor(c.color, -30) } },
                font: { color: '#fff', size: 10, multi: true }, borderWidth: 1, backend: c.key,
                widthConstraint: { minimum: 130 }
            });
            // Vertical chain edges
            var fromId = rowIdx === 0 ? 'header-' + c.key : operations[rowIdx - 1].key + '-' + c.key;
            edgeData.push({ from: fromId, to: op.key + '-' + c.key, color: { color: c.color, opacity: 0.4 }, width: 1.5, arrows: { to: { enabled: true, scaleFactor: 0.4 } }, backend: c.key });
        });
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

    // Hover info for operations
    var hoverInfo = {
        'polars': 'Polars builds a lazy query plan. Operations are not executed until .collect() triggers the optimizer.',
        'narwhals': 'Narwhals wraps pandas for eager execution. Each operation runs immediately on the DataFrame.',
        'ibis': 'Ibis builds deferred expressions that compile to SQL. Execution happens on .to_pandas() or .execute().'
    };

    network.on('hoverNode', function(params) {
        var node = nodes.get(params.node);
        if (node && node.backend && hoverInfo[node.backend]) {
            infoPanel.innerHTML = hoverInfo[node.backend];
            infoPanel.style.display = 'block';
        }
    });
    network.on('blurNode', function() { infoPanel.style.display = 'none'; });

    // Backend selector
    var selectedBackend = '';
    document.querySelectorAll('.sel-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            selectedBackend = this.getAttribute('data-backend');
            nodeData.forEach(function(nd) {
                var node = nodes.get(nd.id);
                if (!node) return;
                var isQuery = node.backend === 'query';
                var match = !selectedBackend || isQuery || node.backend === selectedBackend;
                var origColor = nd.color.background;
                nodes.update({
                    id: nd.id,
                    color: { background: match ? origColor : dimColor, border: match ? shadeColor(origColor, -30) : '#BBB' },
                    font: { color: match ? '#fff' : '#aaa', size: nd.font.size, multi: nd.font.multi }
                });
            });
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
