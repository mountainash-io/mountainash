// LazyFrame Pipeline
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">LazyFrame Pipeline</div>
            <div id="controls" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <label style="cursor:pointer;"><input type="checkbox" id="toggle-opt" checked> Query Optimizer</label>
            </div>
            <div id="info" style="position:absolute;bottom:10px;left:50%;transform:translateX(-50%);max-width:550px;background:rgba(255,255,255,0.95);padding:10px 14px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;text-align:center;"></div>
        </div>
    `;

    var teal = '#008080';
    var gold = '#DAA520';
    var green = '#2E8B57';
    var orange = '#E67E22';

    var stages = [
        { id: 'read', label: 'Read\nDF→LazyFrame', x: 80, y: 150, bg: teal, plan: 'LogicalPlan: [Scan]', info: '<b>Read Stage</b><br>Wraps DataFrame as LazyFrame. Creates initial Scan node in logical plan. No data is materialized yet.' },
        { id: 'filter', label: 'Filter\nage > 18', x: 230, y: 150, bg: teal, plan: 'LogicalPlan: [Scan → Filter]', info: '<b>Filter Stage</b><br>Appends Filter predicate to plan. Predicate pushdown may later move this closer to the scan.' },
        { id: 'project', label: 'Project\nname, email', x: 380, y: 150, bg: teal, plan: 'LogicalPlan: [Scan → Filter → Proj]', info: '<b>Project Stage</b><br>Appends column projection. Projection pushdown may narrow the scan to only needed columns.' },
        { id: 'sort', label: 'Sort\nby name', x: 530, y: 150, bg: teal, plan: 'LogicalPlan: [Scan → Filter → Proj → Sort]', info: '<b>Sort Stage</b><br>Adds sort key. Sort is preserved in the logical plan for the optimizer to reason about.' },
        { id: 'collect', label: 'Collect\n(materialize)', x: 700, y: 150, bg: green, plan: 'Execute optimized plan → DataFrame', info: '<b>Collect Stage</b><br>Triggers optimization and execution. The optimizer rewrites the plan, then the engine executes it to produce a concrete DataFrame.' }
    ];

    var nodeData = [];
    var edgeData = [];

    stages.forEach(function(s) {
        nodeData.push({
            id: s.id, label: s.label, x: s.x, y: s.y, fixed: true, shape: 'box',
            color: { background: s.bg, border: shadeColor(s.bg, -30), highlight: { background: lightenColor(s.bg, 20), border: shadeColor(s.bg, -30) }, hover: { background: lightenColor(s.bg, 20), border: shadeColor(s.bg, -30) } },
            font: { color: '#fff', size: 12, multi: true }, borderWidth: 2,
            plan: s.plan, stageInfo: s.info
        });
    });

    // Plan state labels below each stage
    stages.forEach(function(s) {
        nodeData.push({
            id: s.id + '-plan', label: s.plan, x: s.x, y: 240, fixed: true, shape: 'box',
            color: { background: '#E8E8E8', border: '#CCC' },
            font: { color: '#555', size: 9 }, borderWidth: 1,
            widthConstraint: { minimum: 100, maximum: 140 }
        });
        edgeData.push({ from: s.id, to: s.id + '-plan', color: { color: '#CCC' }, width: 1, dashes: [3, 3], arrows: { to: { enabled: false } } });
    });

    // Flow edges
    for (var i = 0; i < stages.length - 1; i++) {
        edgeData.push({
            from: stages[i].id, to: stages[i + 1].id,
            arrows: { to: { enabled: true, scaleFactor: 0.7 } },
            color: { color: teal }, width: 2
        });
    }

    // Optimizer box
    nodeData.push({
        id: 'optimizer', label: 'Query Optimizer\n(predicate pushdown,\nprojection pushdown,\ncommon subexpression)', x: 390, y: 370, fixed: true, shape: 'box',
        color: { background: orange, border: '#CC6600', highlight: { background: '#F09030', border: '#CC6600' }, hover: { background: '#F09030', border: '#CC6600' } },
        font: { color: '#fff', size: 11, multi: true }, borderWidth: 2,
        widthConstraint: { minimum: 200 }
    });
    edgeData.push({ from: 'sort-plan', to: 'optimizer', color: { color: orange, opacity: 0.5 }, width: 1.5, dashes: [6, 4], arrows: { to: { enabled: true, scaleFactor: 0.5 } }, label: 'plan in', font: { size: 9, color: '#888' } });
    edgeData.push({ from: 'optimizer', to: 'collect', color: { color: orange, opacity: 0.5 }, width: 1.5, dashes: [6, 4], arrows: { to: { enabled: true, scaleFactor: 0.5 } }, label: 'optimized', font: { size: 9, color: '#888' }, smooth: { type: 'curvedCCW', roundness: 0.3 } });

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
            if (node && node.stageInfo) { infoPanel.innerHTML = node.stageInfo; infoPanel.style.display = 'block'; }
            else { infoPanel.style.display = 'none'; }
        } else { infoPanel.style.display = 'none'; }
    });

    // Toggle optimizer visibility
    document.getElementById('toggle-opt').addEventListener('change', function() {
        var show = this.checked;
        nodes.update({ id: 'optimizer', hidden: !show });
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
