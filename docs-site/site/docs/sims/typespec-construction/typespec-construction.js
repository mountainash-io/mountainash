// TypeSpec Construction — Hub-and-spoke sources
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">TypeSpec Construction Sources</div>
            <div id="legend" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Legend</div>
                <div><span style="color:#9370DB;">&#9679;</span> Input Source</div>
                <div><span style="color:#6A5ACD;">&#9679;</span> TypeSpec (target)</div>
                <div style="margin-top:4px;font-size:10px;color:#666;">Hover a source to<br/>see a code snippet</div>
            </div>
            <div id="info" style="position:absolute;bottom:10px;left:50%;transform:translateX(-50%);max-width:500px;background:rgba(255,255,255,0.95);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;"></div>
        </div>
    `;

    var centerX = 400;
    var centerY = 240;
    var radius = 170;

    var sources = [
        { id: 'dict', label: 'Simple\nDict', angle: -90,
          snippet: '<code style="font-size:11px;white-space:pre;">ts = TypeSpec.from_dict({\n  "name": "str",\n  "age": "int",\n  "score": "float"\n})</code>' },
        { id: 'frictionless', label: 'Frictionless\nJSON', angle: -18,
          snippet: '<code style="font-size:11px;white-space:pre;">ts = TypeSpec.from_frictionless(\n  "datapackage.json",\n  resource="main"\n)</code>' },
        { id: 'polars', label: 'Polars\nDataFrame', angle: 54,
          snippet: '<code style="font-size:11px;white-space:pre;">import polars as pl\ndf = pl.read_csv("data.csv")\nts = TypeSpec.from_polars(df)</code>' },
        { id: 'dataclass', label: 'Python\nDataclass', angle: 126,
          snippet: '<code style="font-size:11px;white-space:pre;">@dataclass\nclass Record:\n  name: str\n  age: int\n\nts = TypeSpec.from_dataclass(Record)</code>' },
        { id: 'pydantic', label: 'Pydantic\nModel', angle: 198,
          snippet: '<code style="font-size:11px;white-space:pre;">class Record(BaseModel):\n  name: str\n  age: int\n\nts = TypeSpec.from_pydantic(Record)</code>' }
    ];

    var nodesList = [
        { id: 'typespec', label: 'TypeSpec', x: centerX, y: centerY, fixed: true,
          shape: 'box', borderWidth: 3,
          color: { background: '#6A5ACD', border: '#483D8B',
                   highlight: { background: '#7B68EE', border: '#483D8B' },
                   hover: { background: '#7B68EE', border: '#483D8B' } },
          font: { color: '#fff', size: 18, bold: true },
          widthConstraint: { minimum: 100 }, heightConstraint: { minimum: 40 }
        }
    ];

    var edgesList = [];

    sources.forEach(function(s) {
        var rad = s.angle * Math.PI / 180;
        var x = centerX + radius * Math.cos(rad);
        var y = centerY + radius * Math.sin(rad);
        nodesList.push({
            id: s.id, label: s.label, x: x, y: y, fixed: true,
            shape: 'box', borderWidth: 2,
            color: { background: '#9370DB', border: '#7B60CB',
                     highlight: { background: '#A88DE0', border: '#7B60CB' },
                     hover: { background: '#A88DE0', border: '#7B60CB' } },
            font: { color: '#fff', size: 12, multi: true, align: 'center' },
            widthConstraint: { minimum: 100 },
            snippet: s.snippet
        });
        edgesList.push({
            from: s.id, to: 'typespec',
            color: { color: '#9370DB', highlight: '#6A5ACD', hover: '#7B68EE' },
            width: 2,
            arrows: { to: { enabled: true, scaleFactor: 0.8 } },
            smooth: { type: 'curvedCW', roundness: 0.15 }
        });
    });

    var nodes = new vis.DataSet(nodesList);
    var edges = new vis.DataSet(edgesList);

    var container = document.getElementById('network');
    var network = new vis.Network(container, { nodes: nodes, edges: edges }, {
        interaction: { zoomView: false, dragView: false, dragNodes: false, hover: true },
        physics: { enabled: false },
        layout: { improvedLayout: false }
    });

    var infoPanel = document.getElementById('info');

    network.on('hoverNode', function(params) {
        var node = nodes.get(params.node);
        if (node && node.snippet) {
            infoPanel.innerHTML = '<b>' + node.label.replace('\n', ' ') + '</b><br><br>' + node.snippet;
            infoPanel.style.display = 'block';
        }
    });

    network.on('blurNode', function() {
        infoPanel.style.display = 'none';
    });
});
