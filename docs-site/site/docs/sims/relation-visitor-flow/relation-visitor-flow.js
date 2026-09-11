// Relation Visitor Flow
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">Visitor Pattern Execution Flow</div>
            <div id="controls" style="position:absolute;bottom:10px;left:50%;transform:translateX(-50%);display:flex;gap:8px;">
                <button id="btn-prev" style="padding:6px 16px;border:2px solid #008080;background:#fff;color:#008080;border-radius:6px;cursor:pointer;font-weight:bold;">&#9664; Back</button>
                <span id="step-label" style="padding:6px 12px;font-size:13px;font-weight:bold;color:#333;line-height:28px;">Step 1 / 6</span>
                <button id="btn-next" style="padding:6px 16px;border:2px solid #008080;background:#008080;color:#fff;border-radius:6px;cursor:pointer;font-weight:bold;">Next &#9654;</button>
            </div>
            <div id="desc" style="position:absolute;bottom:50px;left:50%;transform:translateX(-50%);max-width:500px;background:rgba(255,255,255,0.95);padding:8px 14px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);text-align:center;"></div>
        </div>
    `;

    var teal = '#008080';
    var tealLight = '#20B2AA';
    var gold = '#DAA520';
    var goldLight = '#FFD700';
    var dimColor = '#C0C0C0';
    var dimBorder = '#A0A0A0';

    // Nodes: left column = AST nodes, right column = backend calls
    var astX = 220, backX = 580, startY = 100, gapY = 100;

    var allNodes = [
        { id: 'visitor', label: 'Unified\nRelationVisitor', x: 400, y: 40, bg: teal, type: 'visitor' },
        { id: 'project', label: 'ProjectRelNode', x: astX, y: startY, bg: teal, type: 'ast' },
        { id: 'filter', label: 'FilterRelNode', x: astX, y: startY + gapY, bg: teal, type: 'ast' },
        { id: 'read', label: 'ReadRelNode', x: astX, y: startY + gapY * 2, bg: teal, type: 'ast' },
        { id: 'b-read', label: 'backend.read()', x: backX, y: startY + gapY * 2, bg: gold, type: 'backend' },
        { id: 'b-filter', label: 'backend.filter()', x: backX, y: startY + gapY, bg: gold, type: 'backend' },
        { id: 'b-project', label: 'backend.project_select()', x: backX, y: startY, bg: gold, type: 'backend' }
    ];

    var steps = [
        { active: ['visitor', 'project'], edges: ['v-project'], desc: 'Visitor receives ProjectRelNode. Before processing, it must recurse into the input child.' },
        { active: ['project', 'filter'], edges: ['project-filter'], desc: 'Visitor recurses down: ProjectRelNode\'s input is FilterRelNode.' },
        { active: ['filter', 'read'], edges: ['filter-read'], desc: 'Visitor recurses again: FilterRelNode\'s input is ReadRelNode (leaf).' },
        { active: ['read', 'b-read'], edges: ['read-bread'], desc: 'At the leaf: visitor calls backend.read() to load the source data.' },
        { active: ['b-read', 'filter', 'b-filter'], edges: ['bread-bfilter'], desc: 'Unwinding: visitor calls backend.filter() with the read result and predicate.' },
        { active: ['b-filter', 'project', 'b-project'], edges: ['bfilter-bproject'], desc: 'Final unwind: visitor calls backend.project_select() to produce the output.' }
    ];

    var allEdges = [
        { id: 'v-project', from: 'visitor', to: 'project', label: 'visit', arrows: 'to' },
        { id: 'project-filter', from: 'project', to: 'filter', label: 'recurse', arrows: 'to' },
        { id: 'filter-read', from: 'filter', to: 'read', label: 'recurse', arrows: 'to' },
        { id: 'read-bread', from: 'read', to: 'b-read', label: 'call', arrows: 'to', dashes: true },
        { id: 'bread-bfilter', from: 'b-read', to: 'b-filter', label: 'unwind', arrows: 'to' },
        { id: 'bfilter-bproject', from: 'b-filter', to: 'b-project', label: 'unwind', arrows: 'to' }
    ];

    var currentStep = 0;

    function buildVis() {
        var step = steps[currentStep];
        var activeSet = {};
        step.active.forEach(function(id) { activeSet[id] = true; });
        var activeEdgeSet = {};
        step.edges.forEach(function(id) { activeEdgeSet[id] = true; });

        var nodeData = allNodes.map(function(n) {
            var isActive = activeSet[n.id];
            var bg = isActive ? n.bg : dimColor;
            var border = isActive ? shadeColor(n.bg, -30) : dimBorder;
            return {
                id: n.id, label: n.label, x: n.x, y: n.y, fixed: true, shape: 'box',
                color: { background: bg, border: border, highlight: { background: bg, border: border }, hover: { background: isActive ? lightenColor(n.bg, 20) : dimColor, border: border } },
                font: { color: isActive ? '#fff' : '#999', size: 13, multi: true },
                borderWidth: isActive ? 3 : 1
            };
        });

        var edgeData = allEdges.map(function(e) {
            var isActive = activeEdgeSet[e.id];
            return {
                id: e.id, from: e.from, to: e.to, label: isActive ? e.label : '',
                arrows: { to: { enabled: true, scaleFactor: 0.7 } },
                color: { color: isActive ? teal : '#ddd' },
                width: isActive ? 3 : 1,
                dashes: e.dashes || false,
                font: { size: 10, color: isActive ? '#333' : '#ccc' }
            };
        });

        return { nodes: new vis.DataSet(nodeData), edges: new vis.DataSet(edgeData) };
    }

    var container = document.getElementById('network');
    var data = buildVis();
    var network = new vis.Network(container, data, {
        interaction: { zoomView: false, dragView: false, dragNodes: false, hover: true },
        physics: { enabled: false },
        layout: { improvedLayout: false }
    });

    function updateDisplay() {
        var data = buildVis();
        network.setData(data);
        document.getElementById('step-label').textContent = 'Step ' + (currentStep + 1) + ' / ' + steps.length;
        document.getElementById('desc').innerHTML = steps[currentStep].desc;
        document.getElementById('btn-prev').disabled = currentStep === 0;
        document.getElementById('btn-next').disabled = currentStep === steps.length - 1;
    }

    document.getElementById('btn-next').addEventListener('click', function() {
        if (currentStep < steps.length - 1) { currentStep++; updateDisplay(); }
    });
    document.getElementById('btn-prev').addEventListener('click', function() {
        if (currentStep > 0) { currentStep--; updateDisplay(); }
    });

    updateDisplay();

    function shadeColor(hex, percent) {
        var num = parseInt(hex.replace('#', ''), 16);
        var r = Math.max(0, Math.min(255, (num >> 16) + percent));
        var g = Math.max(0, Math.min(255, ((num >> 8) & 0x00FF) + percent));
        var b = Math.max(0, Math.min(255, (num & 0x0000FF) + percent));
        return '#' + (0x1000000 + r * 0x10000 + g * 0x100 + b).toString(16).slice(1);
    }
    function lightenColor(hex, percent) { return shadeColor(hex, percent); }
});
