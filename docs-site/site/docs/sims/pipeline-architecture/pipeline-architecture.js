// Pipeline Framework Architecture
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">Pipeline Framework Architecture</div>
            <div id="legend" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Layers</div>
                <div><span style="color:#7B2D8E;">&#9679;</span> User API</div>
                <div><span style="color:#9B59B6;">&#9679;</span> Specification</div>
                <div><span style="color:#6C3483;">&#9679;</span> Execution</div>
                <div><span style="color:#D4A017;">&#9679;</span> Cross-cutting</div>
            </div>
            <div id="info" style="position:absolute;top:50px;right:10px;width:260px;background:rgba(255,255,255,0.95);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;"></div>
        </div>
    `;

    // Layout constants
    var W = 800;
    var topY = 70, midY = 230, botY = 400;
    var leftX = 250, rightX = 550;
    var sideX = 700;

    // Layer background labels
    var layerLabels = [
        { id: 'layer-api', label: '── User API Layer ──', x: W/2, y: topY - 30, font: { size: 11, color: '#999' }, shape: 'text', fixed: true },
        { id: 'layer-spec', label: '── Specification Layer ──', x: W/2, y: midY - 30, font: { size: 11, color: '#999' }, shape: 'text', fixed: true },
        { id: 'layer-exec', label: '── Execution Layer ──', x: W/2, y: botY - 30, font: { size: 11, color: '#999' }, shape: 'text', fixed: true }
    ];

    var nodeColor = function(bg, border) {
        return {
            background: bg, border: border,
            highlight: { background: lighten(bg, 20), border: border },
            hover: { background: lighten(bg, 20), border: border }
        };
    };

    var nodes = new vis.DataSet([
        // Layer labels
        ...layerLabels,

        // User API layer
        { id: 'pipeline-builder', label: 'PipelineBuilder', x: leftX, y: topY, fixed: true,
          shape: 'box', color: nodeColor('#7B2D8E', '#5B1D6E'),
          font: { color: '#fff', size: 14 }, borderWidth: 2,
          info: '<b>PipelineBuilder</b><br><br>Fluent builder API for constructing pipelines. Chains .add_step() calls to assemble a pipeline specification before execution.<br><br><b>Fields:</b> name, steps[], config' },

        { id: 'step-decorator', label: '@step_decorator', x: rightX, y: topY, fixed: true,
          shape: 'box', color: nodeColor('#7B2D8E', '#5B1D6E'),
          font: { color: '#fff', size: 14 }, borderWidth: 2,
          info: '<b>@step_decorator</b><br><br>Decorator that converts a plain function into a pipeline step. Automatically infers input/output parameters from type annotations.<br><br><b>Usage:</b> @step(name, params)' },

        // Specification layer
        { id: 'pipeline-spec', label: 'PipelineSpec', x: leftX, y: midY, fixed: true,
          shape: 'box', color: nodeColor('#9B59B6', '#7D3C98'),
          font: { color: '#fff', size: 14 }, borderWidth: 2,
          info: '<b>PipelineSpec</b><br><br>Immutable specification describing a complete pipeline. Contains ordered list of StepDefinitions and global configuration.<br><br><b>Fields:</b> name, steps: List[StepDefinition], params: dict' },

        { id: 'step-definition', label: 'StepDefinition', x: rightX, y: midY, fixed: true,
          shape: 'box', color: nodeColor('#9B59B6', '#7D3C98'),
          font: { color: '#fff', size: 14 }, borderWidth: 2,
          info: '<b>StepDefinition</b><br><br>Describes a single step: its callable, expected inputs/outputs, and parameter schema.<br><br><b>Fields:</b> name, callable, input_schema, output_schema, params: List[ParamSpec]' },

        // Execution layer
        { id: 'pipeline-runner', label: 'SimplePipelineRunner', x: 180, y: botY, fixed: true,
          shape: 'box', color: nodeColor('#6C3483', '#4A235A'),
          font: { color: '#fff', size: 13 }, borderWidth: 2,
          info: '<b>SimplePipelineRunner</b><br><br>Default runner that executes steps sequentially. Manages context creation and result collection for each step.<br><br><b>Methods:</b> run(spec, context) -> PipelineResult' },

        { id: 'step-context', label: 'StepContext', x: 400, y: botY, fixed: true,
          shape: 'box', color: nodeColor('#6C3483', '#4A235A'),
          font: { color: '#fff', size: 14 }, borderWidth: 2,
          info: '<b>StepContext</b><br><br>Runtime context passed to each step during execution. Provides access to parameters, previous results, and shared state.<br><br><b>Fields:</b> params, results, state, logger' },

        { id: 'step-result', label: 'StepResult', x: 600, y: botY, fixed: true,
          shape: 'box', color: nodeColor('#6C3483', '#4A235A'),
          font: { color: '#fff', size: 14 }, borderWidth: 2,
          info: '<b>StepResult</b><br><br>Outcome of executing a single step. Contains output data, timing, and status.<br><br><b>Fields:</b> status, output, duration_ms, error' },

        // Cross-cutting
        { id: 'param-spec', label: 'ParamSpec', x: sideX, y: (midY + botY) / 2, fixed: true,
          shape: 'box', color: nodeColor('#D4A017', '#B8860B'),
          font: { color: '#fff', size: 14 }, borderWidth: 2,
          info: '<b>ParamSpec</b><br><br>Describes a single parameter: name, type, default value, and validation rules. Used at both specification and execution time.<br><br><b>Fields:</b> name, type, default, required, validator' }
    ]);

    var edges = new vis.DataSet([
        // User API -> Specification
        { from: 'pipeline-builder', to: 'pipeline-spec', arrows: 'to', color: { color: '#9B59B6' }, width: 2, label: 'builds', font: { size: 10, color: '#666' } },
        { from: 'step-decorator', to: 'step-definition', arrows: 'to', color: { color: '#9B59B6' }, width: 2, label: 'creates', font: { size: 10, color: '#666' } },

        // Specification -> Execution
        { from: 'pipeline-spec', to: 'pipeline-runner', arrows: 'to', color: { color: '#6C3483' }, width: 2, label: 'executed by', font: { size: 10, color: '#666' } },
        { from: 'step-definition', to: 'step-context', arrows: 'to', color: { color: '#6C3483' }, width: 2, dashes: true, label: 'configures', font: { size: 10, color: '#666' } },

        // Execution internal
        { from: 'pipeline-runner', to: 'step-context', arrows: 'to', color: { color: '#6C3483' }, width: 1.5 },
        { from: 'step-context', to: 'step-result', arrows: 'to', color: { color: '#6C3483' }, width: 1.5 },

        // ParamSpec cross-cutting
        { from: 'param-spec', to: 'step-definition', arrows: 'to', color: { color: '#D4A017' }, width: 2, dashes: [5, 5], label: 'defines', font: { size: 10, color: '#999' } },
        { from: 'param-spec', to: 'step-context', arrows: 'to', color: { color: '#D4A017' }, width: 2, dashes: [5, 5], label: 'resolves in', font: { size: 10, color: '#999' } }
    ]);

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
            }
        } else {
            infoPanel.style.display = 'none';
        }
    });

    network.on('hoverNode', function(params) {
        var node = nodes.get(params.node);
        if (node && node.info) {
            container.style.cursor = 'pointer';
        }
    });

    network.on('blurNode', function() {
        container.style.cursor = 'default';
    });

    function lighten(hex, amt) {
        var num = parseInt(hex.replace('#', ''), 16);
        var r = Math.min(255, (num >> 16) + amt);
        var g = Math.min(255, ((num >> 8) & 0xFF) + amt);
        var b = Math.min(255, (num & 0xFF) + amt);
        return '#' + (0x1000000 + r * 0x10000 + g * 0x100 + b).toString(16).slice(1);
    }
});
