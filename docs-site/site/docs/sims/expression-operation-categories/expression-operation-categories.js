// Expression Operation Categories
// CANVAS_HEIGHT: 450
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:450px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div style="text-align:center;padding-top:8px;font-size:16px;font-weight:bold;">Expression Operation Categories</div>
            <div style="width:95%;height:380px;margin:0 auto;">
                <canvas id="barChart"></canvas>
            </div>
            <div id="popup" style="position:absolute;top:60px;right:20px;width:240px;background:rgba(255,255,255,0.97);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 8px rgba(0,0,0,0.15);display:none;max-height:340px;overflow-y:auto;"></div>
        </div>
    `;

    var categories = [
        { name: 'Comparison', count: 6, ops: ['eq', 'ne', 'lt', 'le', 'gt', 'ge'] },
        { name: 'Arithmetic', count: 7, ops: ['add', 'sub', 'mul', 'div', 'floordiv', 'mod', 'pow'] },
        { name: 'Boolean', count: 5, ops: ['and_', 'or_', 'not_', 'xor', 'is_null'] },
        { name: 'String', count: 12, ops: ['upper', 'lower', 'strip', 'lstrip', 'rstrip', 'contains', 'starts_with', 'ends_with', 'replace', 'slice', 'split', 'concat'] },
        { name: 'Pattern', count: 4, ops: ['like', 'ilike', 'regex', 'glob'] },
        { name: 'Temporal', count: 24, ops: ['year', 'month', 'day', 'hour', 'minute', 'second', 'microsecond', 'nanosecond', 'date', 'time', 'datetime', 'timestamp', 'epoch', 'weekday', 'week', 'quarter', 'ordinal_day', 'truncate', 'round', 'offset_by', 'combine', 'replace', 'duration', 'total_days'] },
        { name: 'Conditional', count: 3, ops: ['when/then/otherwise', 'coalesce', 'if_else'] },
        { name: 'Aggregation', count: 8, ops: ['sum', 'mean', 'min', 'max', 'count', 'std', 'var', 'median'] },
        { name: 'Window', count: 6, ops: ['over', 'rank', 'dense_rank', 'row_number', 'lag', 'lead'] }
    ];

    var popup = document.getElementById('popup');

    var ctx = document.getElementById('barChart').getContext('2d');
    var chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories.map(function(c) { return c.name; }),
            datasets: [{
                label: 'Operation Count',
                data: categories.map(function(c) { return c.count; }),
                backgroundColor: '#006400',
                hoverBackgroundColor: '#228B22',
                borderColor: '#004000',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            onClick: function(evt, elements) {
                if (elements.length > 0) {
                    var idx = elements[0].index;
                    var cat = categories[idx];
                    popup.innerHTML = '<b>' + cat.name + ' (' + cat.count + ' operations)</b><br><br>' +
                        cat.ops.map(function(o) { return '<span style="display:inline-block;margin:2px 4px;padding:2px 8px;background:#e8f5e9;border-radius:4px;font-family:monospace;font-size:11px;">' + o + '</span>'; }).join('');
                    popup.style.display = 'block';
                } else {
                    popup.style.display = 'none';
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(ctx) { return ctx.parsed.x + ' operations'; }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: { display: true, text: 'Number of Operations', font: { size: 12 } },
                    grid: { color: 'rgba(0,0,0,0.05)' }
                },
                y: {
                    grid: { display: false },
                    ticks: { font: { size: 12 } }
                }
            }
        }
    });
});
