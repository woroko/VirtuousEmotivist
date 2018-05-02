// HistogramModule.js
var HistogramModule = function(bins, canvas_width, canvas_height, belief_label) {
    // Create the elements

    // Create the tag:
    var canvas_tag = "<canvas id=\"test\" width='" + canvas_width + "' height='" + canvas_height + "' ";
    //var canvas_tag = "<canvas width='200' height='200' ";
    canvas_tag += "style='border:1px dotted; margin: 0px auto; overflow: hidden;'></canvas>";
    // Append it to body:
    var canvas = $(canvas_tag)[0];
    //$("#elements").append(canvas);
    $("#elements").after(canvas);
    // Create the context and the drawing controller:
    var context = canvas.getContext("2d");

    // Prep the chart properties and series:
    var datasets = [{
        label: belief_label,
        fillColor: "rgba(151,187,205,0.5)",
        strokeColor: "rgba(151,187,205,0.8)",
        highlightFill: "rgba(151,187,205,0.75)",
        highlightStroke: "rgba(151,187,205,1)",
        data: []
    }];

    // Add a zero value for each bin
    for (var i in bins)
        datasets[0].data.push(0);

    var data = {
        labels: bins,
        datasets: datasets
    };

    var options = {
        scaleBeginsAtZero: true,
        responsive:false
    };

    // Create the chart object
    var chart = new Chart(context, {type: 'bar', data: data, options: options});//.Bar(data, options);

    // Now what?
    // ...Everything from above...
    this.render = function(data) {
        //for (var i in data)
        //    chart.data.datasets[0].bars[i].value = data[i];
        $.each(chart.data.datasets, function (i, dataset) {
            for (var i in data)
                dataset.data[i] = data[i];
        });
        chart.update();
    };

    this.reset = function() {
        chart.destroy();
        chart = new Chart(context, {type: 'bar', data: data, options: options});
    };
};